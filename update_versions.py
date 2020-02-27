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

CURRENT_VERSION = "0.4.0"
NEW_VERSION = "0.4.1"

FILES_WITH_VERSIONS = [        # do not include setup.py
    "docker/Dockerfile",
    "otter/gs_generator.py",
    "test/integration/autograder-correct/requirements.txt",
    "requirements.txt",
    "Makefile"
]

def main():
    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        contents = re.sub(
            "otter-grader=={}".format(CURRENT_VERSION), 
            "otter-grader=={}".format(NEW_VERSION), 
            contents
        )

        with open(file, "w") as f:
            f.write(contents)

    with open("setup.py") as f:
        contents = f.read()

    contents = re.sub(
        "version = \"{}\",".format(CURRENT_VERSION),
        "version = \"{}\",".format(NEW_VERSION),
        contents
    )

    with open("setup.py", "w") as f:
        f.write(contents)

if __name__ == "__main__":
    main()
