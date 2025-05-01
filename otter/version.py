"""Version and printable logo"""

import importlib
import sys

from textwrap import dedent, indent


__version__ = "6.1.3"


LOGO_WITH_VERSION = rf"""
  _________        __          __               
 /  _____  \    __|  |__    __|  |__               
|  /     \  |  |__    __|  |__    __|   _______    _  _____
| |       | |     |  |        |  |     |  ___  |  | |/ ____|
| |       | |     |  |        |  |     | |___| |  |   /    
| |       | |     |  |        |  |     | ______|  |  |
|  \_____/  |     |  |_       |  |_    | |_____   |  |
 \_________/       \ __|       \ __|    \______|  |__|
                                                v{__version__}
"""[
    1:
]  # remove beginning newline


_ADDITIONAL_PACKAGES = [
    "dill",
    "fica",
    "IPython",
    "nbconvert",
    "nbformat",
]


def print_version_info(logo: bool = False):
    """
    Prints the Otter logo and version information to stdout

    Args:
        logo (``bool``): whether to print the logo
    """
    if logo:
        print(LOGO_WITH_VERSION)
    print(
        dedent(
            f"""\
                Python version: {".".join(str(v) for v in sys.version_info[:3])}
                Otter-Grader version: {__version__}

                Additional package versions:
            """
        )
        + indent(_list_addl_package_versions(), "    ")
    )


def _list_addl_package_versions() -> str:
    """Generate a string listing versions of additional packages of interest."""
    versions = []
    for p in _ADDITIONAL_PACKAGES:
        try:
            m = importlib.import_module(p)
            versions.append(f"{p}: {m.__version__}")
        except Exception as e:
            versions.append(f"{p}: (failed) {type(e).__name__}: {e}")
    return "\n".join(versions)
