from dagster import Definitions

from .assets import splat_job, GaussianSplatConfig, frames, point_cloud, trained_ply_file, splat_file
from .resources import RESOURCES

all_assets = [frames, point_cloud, trained_ply_file, splat_file]

definitions = Definitions(
    assets=all_assets,
    jobs=[splat_job],
    resources={
        **RESOURCES,
        "gaussian_splat_config": GaussianSplatConfig.configure_at_launch(),
    },
)
