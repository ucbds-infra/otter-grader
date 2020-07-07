#######################################################
#####                Otter Assign                 #####
##### forked from https://github.com/okpy/jassign #####
#######################################################

# TODO: move seed to inside solution cell

import copy
import json
import pprint
import os
import re
import shutil
import yaml
import subprocess
import pathlib
import nbformat
import nb2pdf

from collections import namedtuple
from glob import glob
from getpass import getpass

from .execute import grade_notebook
# from .jassign import gen_views as jassign_views
from .export import export_notebook
from .utils import block_print, str_to_doctest, get_relpath
from .generate.token import APIClient


NB_VERSION = 4
BLOCK_QUOTE = "```"
COMMENT_PREFIX = "#"
TEST_HEADERS = ["TEST", "HIDDEN TEST"]
ALLOWED_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
NB_VERSION = 4

TEST_REGEX = r"(##\s*(hidden\s*)?test\s*##|#\s*(hidden\s*)?test)"
SOLUTION_REGEX = r"##\s*solution\s*##"
MD_SOLUTION_REGEX = r"(<strong>|\*{2})solution:?(<\/strong>|\*{2})"
SEED_REGEX = r"##\s*seed\s*##"

MD_ANSWER_CELL_TEMPLATE = "_Type your answer here, replacing this text._"

SEED_REQUIRED = False

ASSIGNMENT_METADATA = {}
