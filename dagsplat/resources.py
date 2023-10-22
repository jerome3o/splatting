import os
from dagsplat.marshaller import Marshaller

_env = os.getenv("DAGSTER_ENVIRONMENT", "local")

_ENV_RESOURCES = {
    "local": {
        "marshaller": Marshaller(),
    },
    "production": {
        # TODO(j.swannack): implement S3 marshaller
        "marshaller": Marshaller(),
    }
}

RESOURCES = _ENV_RESOURCES[_env]
