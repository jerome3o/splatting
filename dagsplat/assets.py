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
    input_dir: str = "data/splat_inputs/bedroom"
    root_dir: str = "data/outputs/test"


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
    output_dir = Path(gaussian_splat_config.root_dir) / "input"
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
            subprocess.run(
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
                ]
            )

        _logger.info("Copying images to output dir")
        # copy all images to output dir
        for extension in config.image_file_extensions:
            for p in Path(input_dir).glob(f"**/*.{extension}"):
                # prefix copied file with "input_image"
                shutil.copy(p, f"{tmp_dir}/input_image_{p.name}")

        _logger.info("Uploading images to output dir")
        marshaller.upload_dir(tmp_dir, output_dir)


@asset(deps=[frames])
def point_cloud() -> None:
    pass


@asset(deps=[point_cloud])
def trained_ply_file() -> None:
    pass


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
