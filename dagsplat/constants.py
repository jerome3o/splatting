import os
import sys

SPLAT_PYTHON_INTERPRETER = os.getenv("SPLAT_PYTHON_INTERPRETER", sys.executable)
SPLAT_DIR = os.getenv("SPLAT_DIR", "gaussian-splatting")
