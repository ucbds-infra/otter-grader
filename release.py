import argparse
import datetime as dt
import re
import subprocess
import sys


FILES_WITH_VERSIONS = [        # do not include setup.py, otter/version.py
    "docs/_static/grading-environment.yml",
    "docs/_static/grading-environment-r.yml",
    "test/test_generate/files/autograder-correct/environment.yml",
    "test/test_generate/files/autograder-token-correct/environment.yml",
    "test/test_generate/files/autograder-custom-env/environment.yml",
    "test/test_generate/files/autograder-r-correct/environment.yml",
    "test/test_generate/files/autograder-r-requirements-correct/environment.yml",
    "test/test_run/files/autograder/source/environment.yml",
    "test/test_assign/files/example-autograder-correct/environment.yml",
    "test/test_assign/files/gs-autograder-correct/environment.yml",
    "test/test_assign/files/rmd-autograder-correct/environment.yml",
]


PARSER = argparse.ArgumentParser()
PARSER.add_argument("new_version", nargs="?", default=None, help="Old version for regex search")
PARSER.add_argument("--dry-run", action="store_true", default=False, help="Update files only but do not push release")
PARSER.add_argument("--git", action="store_true", default=False, help="Indicates that new release should be installed via git")
PARSER.add_argument("--test", action="store_true", default=False, help="Indicates that new release should be pushed to test PyPI")
PARSER.add_argument("--no-twine", action="store_true", default=False, help="Don't upload the release to PyPI")
PARSER.add_argument("-f", "--force", action="store_true", default=False, help="Force run (ignore uncommitted changes)")


OLD_VERSION_REGEX = r"(otter-grader==\d+\.\d+\.\d+(?:\.\w+)?|git\+https:\/\/github\.com\/ucbds-infra\/otter-grader\.git@[\w\.]+)"


if __name__ == "__main__":
    args = PARSER.parse_args()
    to_git = args.git

    to_beta = False
    if args.new_version is not None:
        new_version_number = args.new_version
        new_version = f"otter-grader=={new_version_number}"
        to_beta = "b" in new_version.split(".")[-1]

    with open(FILES_WITH_VERSIONS[0]) as f:
        contents = f.read()

    from_git = bool(re.search(r"https://github.com/ucbds-infra/otter-grader\.git@", contents))
    from_beta = bool(re.search(r"otter-grader==\d+\.\d+\.\d+\.b\d+", contents))

    if subprocess.run(["git", "diff"], stdout=subprocess.PIPE).stdout.decode("utf-8").strip() and not args.dry_run and not args.force:
        # throw error because this will commit everything when you make a release
        raise RuntimeError(
            "You have uncommitted changes. Please add and commit these changes before pushing "
            "a release." 
        )

    if to_git:
        new_hash = (
            subprocess
            .run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
            .stdout
            .decode("utf-8")
            .strip()
        )
        new_version = f"git+https://github.com/ucbds-infra/otter-grader.git@{new_hash}"

    assert "new_version" in vars(), "Could not find a version -- did you specify one?"

    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        contents = re.sub(OLD_VERSION_REGEX, new_version, contents)

        with open(file, "w") as f:
            f.write(contents)

    # fix otter.__version__
    with open("otter/version.py") as f:
        contents = f.read()

    if args.new_version is not None:
        contents = re.sub(
            r"__version__\s*=\s*['\"]\d+\.\d+\.\d+(?:\.\w+)?['\"]",
            f"__version__ = \"{new_version_number}\"",
            contents
        )

    with open("otter/version.py", "w") as f:
        f.write(contents)

    # fix CITATION.cff
    with open("CITATION.cff") as f:
        contents = f.read()

    if args.new_version is not None:
        contents = re.sub(
            r"^version:\s*\"\d+.\d+.\d+(?:\.\w+)?\"",
            f"version: \"{new_version_number}\"",
            contents,
            flags = re.MULTILINE
        )

        contents = re.sub(
            r"^date-released:\s*\d{4}-\d{2}-\d{2}",
            f"date-released: {dt.date.today().strftime('%Y-%m-%d')}",
            contents,
            flags = re.MULTILINE
        )

    with open("CITATION.cff", "w") as f:
        f.write(contents)

    if to_git:
        print(f"Versions updated. Release commit hash is {new_hash} -- commit and push to release")
        sys.exit()

    print(f"Versions updated. Release version is {new_version_number}")

    if to_beta:
        sys.exit()

    print("Updating CHANGELOG.md")
    with open("CHANGELOG.md") as f:
        cl = f.read()

    new_version_regex = new_version_number.replace(".", r"\.")
    cl = re.sub(fr"{new_version_regex}\s*\(unreleased\)", new_version_number, cl, flags = re.IGNORECASE)

    with open("CHANGELOG.md", "w") as f:
        f.write(cl)
