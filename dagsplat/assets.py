import sys
import tempfile
from pathlib import Path
from pydantic import Field
import subprocess
import shutil

from dagster import asset, define_asset_job, get_dagster_logger, Config, ConfigurableResource

from dagsplat.marshaller import Marshaller

_logger = get_dagster_logger()

_VIDEO_FILE_EXTENSIONS = ["mp4", "mkv", "flv", "mov", "avi"]
_IMAGE_FILE_EXTENSIONS = ["jpg", "jpeg", "png"]


class GaussianSplatConfig(ConfigurableResource):
    input_dir: str
    root_dir: str = None
    splatting_repo_dir: str = "gaussian-splatting"

    def get_root_dir(self) -> str:
        if self.root_dir:
            return self.root_dir

        # otherwise take the last folder of the input dir and add it to "data/outputs/"
        return str(Path("data/outputs") / Path(self.input_dir).parts[-1])


class FramesConfig(Config):
    frames_per_second: int = 6
    video_file_extensions: list[str] = Field(default_factory=lambda: list(_VIDEO_FILE_EXTENSIONS))
    image_file_extensions: list[str] = Field(default_factory=lambda: list(_IMAGE_FILE_EXTENSIONS))


@asset
def frames(
    marshaller: Marshaller,
    config: FramesConfig,
    gaussian_splat_config: GaussianSplatConfig,
) -> None:
    output_dir = Path(gaussian_splat_config.get_root_dir()) / "input"
    output_dir.mkdir(exist_ok=True, parents=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        _logger.info("Loading inputs")
        input_dir = marshaller.load_dir(gaussian_splat_config.input_dir)

        # search for video files
        video_files = [
            p
            for extension in config.video_file_extensions
            for p in Path(input_dir).glob(f"**/*.{extension}")
        ]

        _logger.info(f"Found {len(video_files)} video files")

        # /bin/ffmpeg -i $FILE_NAME -qscale:v 1 -qmin 1 -vf fps=$FRAME_RATE {i}%04d.jpg
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
                    f"fps={config.frames_per_second}",
                    f"{tmp_dir}/{i}%04d.jpg",
                ],
                capture_output=True,
            )
            if result.returncode != 0:
                raise ValueError(f"ffmpeg failed on file {file} with code {result.returncode}, and stderr:\n\n{result.stderr.decode()}")

        _logger.info("Copying images to output dir")
        # copy all images to output dir
        for extension in config.image_file_extensions:
            for p in Path(input_dir).glob(f"**/*.{extension}"):
                # prefix copied file with "input_image"
                shutil.copy(p, f"{tmp_dir}/input_image_{p.name}")

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
        [executable, script, "-s", str(data_dir)],
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
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
    executable = sys.executable
    script = str(Path(gaussian_splat_config.splatting_repo_dir) / "train.py")
    result = subprocess.run(
        [executable, script, "-s", str(data_dir)],
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        raise ValueError(
            f"{script} failed with code {result.returncode} and stderr:\n\n{result.stderr.decode()}"
        )

    marshaller.upload_dir(data_dir, gaussian_splat_config.get_root_dir())


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
