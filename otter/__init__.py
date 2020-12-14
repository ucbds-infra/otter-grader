"""
otter Python API
"""

import platform

from . import api
from .check import logs
from .check.notebook import Notebook
from .version import __version__

# whether Otter is running on Window
_WINDOWS = platform.system() == "Windows"
