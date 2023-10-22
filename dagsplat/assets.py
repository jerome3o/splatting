from dagster import asset, define_asset_job, get_dagster_logger, Config

from dagsplat.marshaller import Marshaller

_logger = get_dagster_logger()


class FramesConfig(Config):
    frames_per_second: int = 6


@asset
def frames(
    marshaller: Marshaller,
    config: FramesConfig,
) -> str:
    return "todo"


@asset
def point_cloud(frames: str) -> str:
    _logger.info(frames)
    return "todo"


@asset
def trained_ply_file(point_cloud: str) -> str:
    _logger.info(point_cloud)
    return "todo"


@asset
def splat_file(trained_ply_file: str) -> str:
    _logger.info(trained_ply_file)
    return "todo"


splat_job = define_asset_job(
    name="gaussian_splat_job",
    selection=[
        frames,
        point_cloud,
        trained_ply_file,
        splat_file,
    ],
    # config={
    #     "execution": {
    #         "config": {
    #             "multiprocess": {
    #                 "max_concurrent": 1,
    #             }
    #         }
    #     },
    # },
)
