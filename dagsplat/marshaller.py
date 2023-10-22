from pathlib import Path
from dagster import ConfigurableResource
import shutil


class Marshaller(ConfigurableResource):
    # initial implementation just for local fs

    # copies/loads dir to local fs
    def load_dir(location: str) -> str:
        if not Path(location).exists():
            raise ValueError(f"Location not found {location}")

        return location

    def upload_dir(location: str, target: str) -> str:
        # just copy the whole directory

        # ensure location exists
        if not Path(location).exists():
            raise ValueError(f"Location not found {location}")

        # make target dir
        Path(target).mkdir(parents=True, exist_ok=True)

        # copy
        shutil.copytree(location, target)
