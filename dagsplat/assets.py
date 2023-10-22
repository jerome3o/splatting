import time

from dagster import Definitions, asset, define_asset_job, get_dagster_logger

_logger = get_dagster_logger()


@asset
def frames() -> str:
    return "todo"


@asset
def point_cloud(test_asset: str) -> str:
    return "todo"


@asset
def ply_file(point_cloud: None) -> str:
    return "todo"


@asset
def splat_file(ply_file: str) -> str:
    return "todo"


test_job = define_asset_job(
    name="test_job",
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


definitions = Definitions(
    assets=[
        frames,
        point_cloud,
    ],
    jobs=[test_job],
)
