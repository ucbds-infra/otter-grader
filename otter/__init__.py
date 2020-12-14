"""
otter Python API
"""

import platform

from .check import logs
from .check.notebook import Notebook
from .run import api
from .version import __version__

# whether Otter is running on Window
_WINDOWS = platform.system() == "Windows"
