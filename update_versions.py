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
import argparse

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--git", action="store_true", help="Indicates that new release should be installed via git")

CURRENT_VERSION = "1.0.0.b7"
NEW_VERSION = "1.0.0.b7"

from_beta = "b" in CURRENT_VERSION.split(".")[-1]
to_beta = "b" in NEW_VERSION.split(".")[-1]

FILES_WITH_VERSIONS = [        # do not include setup.py
    "Dockerfile",
    "otter/generate/templates/requirements.txt",
    "test/test_generate/test-autograder/autograder-correct/requirements.txt",
    "test/test-assign/gs-autograder-correct/requirements.txt",
    "test/test-assign/pdf-autograder-correct/requirements.txt",
    "test/test-assign/r-autograder-correct/requirements.txt",
    "test/test-assign/rmd-autograder-correct/requirements.txt",
]

with open(FILES_WITH_VERSIONS[0]) as f:
    FROM_GIT = bool(re.search(r"https://github.com/ucbds-infra/otter-grader\.git@", f.read()))

TO_GIT = False

def main(args):
    global TO_GIT
    TO_GIT = bool(args.git)

    if TO_GIT and subprocess.run(["git", "diff"], stdout=subprocess.PIPE).stdout.decode("utf-8").strip():
        warnings.warn(
            "You have uncommitted changes that will not be included in this release. To include "
            "them, commit your changes and rerun this script.",
            UserWarning
        )
    
    old_version = fr"otter-grader=={CURRENT_VERSION}$"
    if FROM_GIT:
        old_version = r"git\+https:\/\/github\.com\/ucbds-infra\/otter-grader\.git@\w+"
    
    new_version = f"otter-grader=={NEW_VERSION}"
    if TO_GIT:
        new_hash = (
            subprocess
            .run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
            .stdout
            .decode("utf-8")
            .strip()
        )
        new_version = f"git+https://github.com/ucbds-infra/otter-grader.git@{new_hash}"

    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        contents = re.sub(
            old_version, 
            new_version, 
            contents,
            flags=re.MULTILINE
        )

        with open(file, "w") as f:
            f.write(contents)

    if from_beta or FROM_GIT:
        # fix Makefile
        with open("Makefile") as f:
            contents = f.read()
        
        contents = re.sub("ucbdsinfra/otter-grader:beta", "ucbdsinfra/otter-grader", contents, flags=re.MULTILINE)

        with open("Makefile", "w") as f:
            f.write(contents)

    if to_beta or TO_GIT:
        # fix Makefile
        with open("Makefile", "r+") as f:
            contents = f.read()

        contents = re.sub(r"ucbdsinfra/otter-grader$", "ucbdsinfra/otter-grader:beta", contents, flags=re.MULTILINE)

        with open("Makefile", "w") as f:
            f.write(contents)

    # fix otter.__version__
    with open("otter/version.py") as f:
        contents = f.read()

    contents = re.sub(
        fr"__version__ = ['\"]{CURRENT_VERSION}['\"]",
        f"__version__ = \"{NEW_VERSION}\"",
        contents
    )

    with open("otter/version.py", "w") as f:
        f.write(contents)

    if TO_GIT:
        print(f"Versions updated. Release commit hash is {new_hash} -- commit and push to release.")

    else:
        print(f"Versions updated. Release version is {NEW_VERSION} -- run 'make distro' to release.")

if __name__ == "__main__":
    args = PARSER.parse_args()
    main(args)
