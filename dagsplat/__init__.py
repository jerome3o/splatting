from dagster import Definitions

from .assets import splat_job, frames, point_cloud, trained_ply_file, splat_file
from .resources import RESOURCES

all_assets = [frames, point_cloud, trained_ply_file, splat_file]

definitions = Definitions(
    assets=all_assets,
    jobs=[splat_job],
    resources=RESOURCES,
)
