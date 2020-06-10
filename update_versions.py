# UPDATE VERSIONS SCRIPT by Chris Pyles
# Updates version numbers in all files that need to know the exact version

# Execute this file in order to update all those files. Add any files that 
# need updating to the FILES_WITH_VERSIONS variable. Update the 
# CURRENT_VERSION and NEW_VERSION variables before running.

# Arguments:
# CURRENT_VERSION: current version of the package (what to change)
# NEW_VERSION: new version of the package (what to change it to)
# FILES_WITH_VERSIONS: list of files that need to be updated
# BETA: whether the new release is the current beta version
# UNDO_BETA: whether we're undoing a beta release

import re
import subprocess

CURRENT_VERSION = "0.4.7"
NEW_VERSION = "1.0.0"

FROM_GIT = True
TO_GIT = True

FILES_WITH_VERSIONS = [        # do not include setup.py
    "Dockerfile",
    "otter/generate/autograder.py",
    "test/test_generate/test-autograder/autograder-correct/requirements.txt",
    # "requirements.txt",
    # "Makefile"
]

def main():
    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        old_version = "otter-grader=={}".format(CURRENT_VERSION)
        if FROM_GIT:
            old_version = r"git\+https:\/\/github\.com\/ucbds-infra\/otter-grader\.git@\w+"
        
        new_version = "otter-grader=={}".format(NEW_VERSION)
        if TO_GIT:
            new_hash = (
                subprocess
                .run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
                .stdout
                .decode("utf-8")
                .strip()
            )
            new_version = f"git+https://github.com/ucbds-infra/otter-grader.git@{new_hash}"

        contents = re.sub(
            old_version, 
            new_version, 
            contents
        )

        with open(file, "w") as f:
            f.write(contents)
    
    if TO_GIT:
        # fix documentation
        with open("docs/conf.py") as f:
            contents = f.read()

        contents = re.sub("master_doc = 'index'", "master_doc = 'index_beta'", contents)

        with open("docs/conf.py", "w") as f:
            f.write(contents)

        # fix Makefile
        with open("Makefile") as f:
            contents = f.read()

        contents = re.sub(r"ucbdsinfra/otter-grader$", "ucbdsinfra/otter-grader:beta", contents)

        with open("Makefile", "w") as f:
            f.write(contents)

    elif FROM_GIT:
        # fix documentation
        with open("docs/conf.py") as f:
            contents = f.read()

        contents = re.sub("master_doc = 'index_beta'", "master_doc = 'index'", contents)

        with open("docs/conf.py", "w") as f:
            f.write(contents)

        # fix Makefile
        with open("Makefile") as f:
            contents = f.read()

        contents = re.sub("ucbdsinfra/otter-grader:beta", "ucbdsinfra/otter-grader", contents)

        with open("Makefile", "w") as f:
            f.write(contents)
    
    # else:
    with open("setup.py") as f:
        contents = f.read()

    contents = re.sub(
        "version = \"{}\",".format(CURRENT_VERSION),
        "version = \"{}\",".format(NEW_VERSION),
        contents
    )

    with open("setup.py", "w") as f:
        f.write(contents)

    with open("otter/__init__.py") as f:
        contents = f.read()

    contents = re.sub(
        "__version__ = \"{}\"".format(CURRENT_VERSION),
        "__version__ = \"{}\"".format(NEW_VERSION),
        contents
    )

    with open("otter/__init__.py", "w") as f:
        f.write(contents)

    if TO_GIT:
        print(f"Versions updated. New commit hash is {new_hash}. Commit and push to release.")
    
    else:
        print(f"Versions updated. New version is {NEW_VERSION}. Run 'make distro' to release.")

if __name__ == "__main__":
    main()
