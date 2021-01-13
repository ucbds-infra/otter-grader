"""
Module for running otter command-line utilities
Added because Windows can't shebang correctly and thus needs otter to be run via `python3 -m`
"""

import sys

from textwrap import dedent

from .argparser import get_parser
from .version import print_version_info

from . import assign
from . import check
from . import export
from . import generate
from . import grade
from . import run

MISSING_PACKAGES = False
try:
    from . import service
except ImportError:
    MISSING_PACKAGES = True

PARSER = get_parser()

def run_otter(unparsed_args=None):
    """
    Runs Otter's CLI by parsing the arguments in ``unparsed_args`` if provided or ``sys.argv`` if not

    Args:
        unparsed_args (``list[str]``, optional): unparsed arguments for running Otter; if not provided,
            ``sys.argv`` is used
    """
    args = PARSER.parse_args(unparsed_args)

    if args.version:
        print_version_info(logo=True)
        return

    if hasattr(args, 'func_str'):
        if args.func_str.startswith("service") and MISSING_PACKAGES:
            raise ImportError(
                "Missing some packages required for otter service. "
                "Please install all requirements at "
                "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
            )

        args.func = eval(args.func_str)

        if args.func_str.startswith("service"):
            args.func(args)
        else:
            kwargs = vars(args)
            args.func(**kwargs)

    elif len(sys.argv) > 1 and sys.argv[1] == "generate":
        print(dedent("""\
        You must specify a command for Otter Generate:
            autograder
            token"""))

    elif len(sys.argv) > 1 and sys.argv[1] == "service":
        print(dedent("""\
        You must specify a command for Otter Service:
            build
            create
            start"""))

    else:
        print(dedent("""\
        You must specify a command for Otter:
            assign
            check
            export
            generate
            grade
            service"""))
