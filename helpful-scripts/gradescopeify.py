# Gradescope AG generator script using otter-grader

# Assumes that all files in a directory are required and that the tests directory
# is a subdirectory of each argument

# Use by passing a list of directories from the command line, e.g.
#     python3 gradescopeify.py hw/*
# This will create an autograder.zip file in each subdirectory of hw

# Put any requirements in a requirements.txt file inside the directory being passed to
# this script, e.g. hw/hw01/requirements.txt in the example above


import subprocess
import sys
import os
from subprocess import PIPE

directories = sys.argv[1:]

for drct in directories:
    print(f"Zipping {drct}")
    assert os.path.isdir(drct), f"{drct} is not a direcrory"
    support_files = [f for f in os.listdir(drct) if os.path.isfile(os.path.join(drct, f)) and \
        f[-6:] != ".ipynb" and f != "requirements.txt" and f[0] != "." and f != "autograder.zip"]
    
    # change directories
    original_dir = os.getcwd()
    os.chdir(drct)

    # create subprocess command
    gen_cmd = ["otter", "gen"]
    
    if os.path.exists(os.path.join(drct, "requirements.txt")) and \
    os.path.isfile(os.path.join(drct, "requirements.txt")):
        gen_cmd += ["-r", os.path.join(drct, "requirements.txt")]

    gen_cmd += support_files

    cmd = subprocess.run(gen_cmd, stdout=PIPE, stderr=PIPE)

    assert len(cmd.stderr) == 0, cmd.stderr.decode('utf-8')

    # change directories back
    os.chdir(original_dir)
