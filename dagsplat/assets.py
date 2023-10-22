import time

from dagster import Definitions, asset, define_asset_job, get_dagster_logger

_logger = get_dagster_logger()


@asset
def test_asset() -> int:
    time.sleep(5)
    _logger.info("returning 1")
    return 1

@asset
def test_asset_2(test_asset: int):
    time.sleep(5)
    _logger.info("finishing asset 2")
    pass


test_job = define_asset_job(
    name="test_job",
    selection=[
        test_asset,
        test_asset_2,
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
        test_asset,
        test_asset_2,
    ],
    jobs=[test_job],
)
