from dagster import asset, define_asset_job, get_dagster_logger

_logger = get_dagster_logger()


@asset
def frames() -> str:
    return "todo"


@asset
def point_cloud(test_asset: str) -> str:
    _logger.info(test_asset)
    return "todo"


@asset
def ply_file(point_cloud: None) -> str:
    _logger.info(point_cloud)
    return "todo"


@asset
def splat_file(ply_file: str) -> str:
    _logger.info(ply_file)
    return "todo"


splat_job = define_asset_job(
    name="gaussian_splat_job",
    selection=[
        frames,
        point_cloud,
        ply_file,
        splat_file,
    ],
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 1,
                }
            }
        }
    },
)
