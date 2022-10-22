"""
Runs Otter on Gradescope with the configurations specified below
"""

import os
import subprocess

from otter.run.run_autograder import main as run_autograder

if __name__ == "__main__":
    run_autograder('test/test_generate/test-run-autograder/autograder')