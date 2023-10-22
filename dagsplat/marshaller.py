from pathlib import Path
from dagster import ConfigurableResource
import shutil


class Marshaller(ConfigurableResource):

    # copies/loads dir to local fs
    def load_dir(self, location: str) -> str:
        if not Path(location).exists():
            raise ValueError(f"Location not found {location}")

        return location

    def upload_dir(self, location: str, target: str):
        if location == target:
            return

        # just copy the whole directory

        # ensure location exists
        if not Path(location).exists():
            raise ValueError(f"Location not found {location}")

        # make target dir
        Path(target).mkdir(parents=True, exist_ok=True)

        # copy, overwriting existing files
        shutil.copytree(location, target, dirs_exist_ok=True)
