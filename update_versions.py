# UPDATE VERSIONS SCRIPT by Chris Pyles
# Updates version numbers in all files that need to know the exact version

# Execute this file in order to update all those files. Add any files that 
# need updating to the FILES_WITH_VERSIONS variable. Update the 
# CURRENT_VERSION and NEW_VERSION variables before running.

# Arguments:
# CURRENT_VERSION: current version of the package (what to change)
# NEW_VERSION: new version of the package (what to change it to)
# FILES_WITH_VERSIONS: list of files that need to be updated

import re
import subprocess
import warnings

CURRENT_VERSION = "1.0.0"
NEW_VERSION = "1.0.0.b1"

from_beta = "b" in CURRENT_VERSION.split(".")[-1]
to_beta = "b" in NEW_VERSION.split(".")[-1]

FILES_WITH_VERSIONS = [        # do not include setup.py
    "Dockerfile",
    "otter/generate/autograder.py",
    "test/test_generate/test-autograder/autograder-correct/requirements.txt",
]

def main():
    old_version = fr"otter-grader=={CURRENT_VERSION}$"
    new_version = f"otter-grader=={NEW_VERSION}"

    for file in FILES_WITH_VERSIONS:
        with open(file, "r+") as f:
            contents = f.read()
            f.seek(0)
            contents = re.sub(
                old_version, 
                new_version, 
                contents,
                flags=re.MULTILINE
            )
            f.write(contents)

    if from_beta:
        # fix Makefile
        with open("Makefile", "r+") as f:
            contents = f.read()
            f.seek(0)
            contents = re.sub("ucbdsinfra/otter-grader:beta", "ucbdsinfra/otter-grader", contents, flags=re.MULTILINE)
            f.write(contents)

    if to_beta:
        # fix Makefile
        with open("Makefile", "r+") as f:
            contents = f.read()
            f.seek(0)
            contents = re.sub(r"ucbdsinfra/otter-grader$", "ucbdsinfra/otter-grader:beta", contents, flags=re.MULTILINE)
            f.write(contents)

    # fix otter.__version__
    with open("otter/version.py", "r+") as f:
        contents = f.read()
        f.seek(0)
        contents = re.sub(
        fr"__version__ = ['\"]{CURRENT_VERSION}['\"]",
            f"__version__ = \"{NEW_VERSION}\"",
            contents
        )
        f.write(contents)

    print(f"Versions updated. Release version is {NEW_VERSION} -- run 'make distro' to release.")

if __name__ == "__main__":
    main()
