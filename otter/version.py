"""Version and printable logo"""

import sys

from textwrap import dedent


__version__ = "4.3.1"


LOGO_WITH_VERSION = fr"""
  _________        __          __               
 /  _____  \    __|  |__    __|  |__               
|  /     \  |  |__    __|  |__    __|   _______    _  _____
| |       | |     |  |        |  |     |  ___  |  | |/ ____|
| |       | |     |  |        |  |     | |___| |  |   /    
| |       | |     |  |        |  |     | ______|  |  |
|  \_____/  |     |  |_       |  |_    | |_____   |  |
 \_________/       \ __|       \ __|    \______|  |__|
                                                v{__version__}
"""[1:]  # remove beginning newline


def print_version_info(logo=False):
    """
    Prints the Otter logo and version information to stdout

    Args:
        logo (``bool``, optional): whether to print the logo
    """
    if logo:
        print(LOGO_WITH_VERSION)
    print(dedent(f"""\
        Python version: {".".join(str(v) for v in sys.version_info[:3])}
        Otter-Grader version: {__version__}"""))
