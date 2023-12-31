import sys
import os
import tempfile
import math
from pathlib import Path
from pydantic import Field
import subprocess
import shutil

from PIL import Image

from dagster import (
    asset,
    define_asset_job,
    get_dagster_logger,
    Config,
    ConfigurableResource,
)

from dagsplat.marshaller import Marshaller
from dagsplat.constants import SPLAT_PYTHON_INTERPRETER, SPLAT_DIR

_logger = get_dagster_logger()

# TODO(j.swannack): make case insensitive
_VIDEO_FILE_EXTENSIONS = [
    "mp4",
    "mkv",
    "flv",
    "mov",
    "avi",
    "MP4",
    "MKV",
    "FLV",
    "MOV",
    "AVI",
]
_IMAGE_FILE_EXTENSIONS = ["jpg", "jpeg", "png"]
_N_PIXELS_1080p = 2073600

class GaussianSplatConfig(ConfigurableResource):
    input_dir: str
    root_dir: str = None
    splatting_repo_dir: str = SPLAT_DIR
    splatting_python_interpreter: str = SPLAT_PYTHON_INTERPRETER

    def get_root_dir(self) -> str:
        if self.root_dir:
            return self.root_dir

        # otherwise take the last folder of the input dir and add it to "data/outputs/"
        return str(Path("data/outputs") / Path(self.input_dir).parts[-1])


class FramesConfig(Config):
    frames_per_second: int = 6
    max_frames: int = 600
    max_pixels: int = _N_PIXELS_1080p
    video_file_extensions: list[str] = Field(
        default_factory=lambda: list(_VIDEO_FILE_EXTENSIONS)
    )
    image_file_extensions: list[str] = Field(
        default_factory=lambda: list(_IMAGE_FILE_EXTENSIONS)
    )


def get_length(filename: str):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )
    return float(result.stdout)


def get_video_dimensions(filename: str) -> tuple[int, int]:
    # ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 input.mp4
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )
    dimensions = result.stdout.decode().strip().split("x")
    return int(dimensions[0]), int(dimensions[1])


def resize_video(filename: str, w: int, h: int) -> str:
    out_filename = str(Path(filename).with_stem(Path(filename).stem + "_resized"))
    result = subprocess.run(
        [
            "ffmpeg",
            "-i",
            filename,
            "-vf",
            f"scale={w}:{h}",
            "-y",
            out_filename,
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    result.check_returncode()
    return out_filename


def resize_video_if_needed(filename: str, max_pixels: int) -> str:
    w, h = get_video_dimensions(filename)
    n_pixels = w*h
    if n_pixels <= max_pixels:
        return filename


    ratio = math.sqrt(max_pixels / n_pixels)
    new_w, new_h = int(w * ratio), int(h * ratio)
    _logger.info(f"Resizing {filename} to {new_w}x{new_h}")
    return resize_video(filename, new_w, new_h)


def resize_image_if_needed(filename: str, max_pixels: int) -> None:
    image = Image.open(filename)
    w, h = image.size
    n_pixels = w*h
    if n_pixels <= max_pixels:
        return

    ratio = math.sqrt(max_pixels / n_pixels)
    new_w, new_h = int(w * ratio), int(h * ratio)
    _logger.info(f"Resizing {filename} to {new_w}x{new_h}")
    image = image.resize((new_w, new_h), Image.ANTIALIAS)
    image.save(filename)


@asset
def frames(
    marshaller: Marshaller,
    config: FramesConfig,
    gaussian_splat_config: GaussianSplatConfig,
) -> None:
    output_dir = Path(gaussian_splat_config.get_root_dir()) / "input"
    output_dir.mkdir(exist_ok=True, parents=True)

    input_dir = marshaller.load_dir(gaussian_splat_config.input_dir)

    # search for video files
    video_files = [
        p
        for extension in config.video_file_extensions
        for p in Path(input_dir).glob(f"**/*.{extension}")
    ]
    _logger.info(f"Found {len(video_files)} video files")

    images = [
        p
        for extension in config.image_file_extensions
        for p in Path(input_dir).glob(f"**/*.{extension}")
    ]
    _logger.info(f"Found {len(images)} images")

    total_video_duration = sum([get_length(str(p)) for p in video_files])
    fps = config.frames_per_second

    if total_video_duration * fps + len(images) > config.max_frames:
        fps = max(int((config.max_frames - len(images)) / total_video_duration), 1)
        if fps == 0:
            _logger.warning(
                "Unable to reduce fps to stay under max frames, using fps = 1"
            )
        else:
            _logger.warning(f"Reducing fps to {fps} to stay under max frames")

    with tempfile.TemporaryDirectory() as tmp_dir:
        _logger.info("Loading inputs")

        _logger.info(f"Found {len(video_files)} video files")

        if fps > 0:
            for i, file in enumerate(video_files):
                _logger.info(f"Processing video file {file}")
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        str(file),
                        "-qscale:v",
                        "1",
                        "-qmin",
                        "1",
                        "-vf",
                        f"fps={fps}",
                        f"{tmp_dir}/frame_{i}%04d.jpg",
                    ],
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
                if result.returncode != 0:
                    raise ValueError(
                        f"ffmpeg failed on file {file} with code {result.returncode}, and stderr:\n\n{result.stderr.decode()}"
                    )

        _logger.info("Copying images to output dir")
        # copy all images to output dir
        for p in images:
            shutil.copy(p, f"{tmp_dir}/input_image_{p.name}")

        for i, image_fn in enumerate(Path(tmp_dir).iterdir()):
            image_fn.rename(image_fn.with_stem(f"{i:05}"))

        for i, image_fn in enumerate(Path(tmp_dir).iterdir()):
            resize_image_if_needed(image_fn, config.max_pixels)

        _logger.info("Uploading images to output dir")
        marshaller.upload_dir(tmp_dir, output_dir)


@asset(deps=[frames])
def point_cloud(
    marshaller: Marshaller,
    gaussian_splat_config: GaussianSplatConfig,
) -> None:
    # python convert.py -s $DATA_DIR

    data_dir = marshaller.load_dir(gaussian_splat_config.get_root_dir())

    # a better way to do this would be to use a python API
    # but there isn't one for for this script, it's meant to be run from the command line
    executable = sys.executable
    script = str(Path(gaussian_splat_config.splatting_repo_dir) / "convert.py")
    result = subprocess.run(
        [
            executable,
            script,
            "-s",
            str(data_dir),
            "--resize",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if result.returncode != 0:
        raise ValueError(
            f"convert.py failed with code {result.returncode} and stderr:\n\n{result.stderr.decode()}"
        )

    marshaller.upload_dir(data_dir, gaussian_splat_config.get_root_dir())


@asset(deps=[point_cloud])
def trained_ply_file(
    marshaller: Marshaller,
    gaussian_splat_config: GaussianSplatConfig,
) -> None:
    # python train.py -s $DATA_DIR

    data_dir = marshaller.load_dir(gaussian_splat_config.get_root_dir())

    # a better way to do this would be to use a python API
    # but there isn't one for for this script, it's meant to be run from the command line
    script = str(Path(gaussian_splat_config.splatting_repo_dir) / "train.py")
    output_dir = Path(data_dir) / "output"
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "gaussian_splatting",
            "--no-capture-output",
            "python",
            script,
            "-s",
            str(Path(data_dir).resolve()),
            "--model_path",
            str(output_dir.resolve()),
        ],
        env={
            **os.environ,
            "PYTHONPATH": str(Path(gaussian_splat_config.splatting_repo_dir).resolve()),
        },
        cwd=gaussian_splat_config.splatting_repo_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if result.returncode != 0:
        raise ValueError(
            f"{script} failed with code {result.returncode} and stderr:\n\n{result.stderr.decode()}"
        )

    marshaller.upload_dir(
        output_dir, str(Path(gaussian_splat_config.get_root_dir()) / "output")
    )


@asset(deps=[trained_ply_file])
def splat_file() -> None:
    pass


splat_job = define_asset_job(
    name="gaussian_splat_job",
    selection=[
        frames,
        point_cloud,
        trained_ply_file,
        splat_file,
    ],
)
