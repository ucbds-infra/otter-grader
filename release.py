import argparse
import datetime as dt
import re
import subprocess
import sys


FILES_WITH_VERSIONS = [  # do not include pyproject.toml, CITATION.cff, otter/version.py
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
PARSER.add_argument(
    "--dry-run",
    action="store_true",
    default=False,
    help="Update files only but do not push release",
)
PARSER.add_argument(
    "-f",
    "--force",
    action="store_true",
    default=False,
    help="Force run (ignore uncommitted changes)",
)


OLD_VERSION_REGEX = r"otter-grader(?:\[[\w,]+\])?==\d+\.\d+\.\d+(?:\.\w+)?"


if __name__ == "__main__":
    args = PARSER.parse_args()

    if (
        subprocess.run(["git", "diff"], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()
        and not args.dry_run
        and not args.force
    ):
        raise RuntimeError(
            "You have uncommitted changes. Please add and commit these changes before pushing "
            "a release."
        )

    to_beta = False
    if args.new_version is not None:
        new_version_number = args.new_version
        to_beta = "b" in new_version_number.split(".")[-1]

    with open(FILES_WITH_VERSIONS[0]) as f:
        contents = f.read()

    from_beta = bool(re.search(r"otter-grader(?:\[[\w,]+\])?==\d+\.\d+\.\d+\.b\d+", contents))

    assert "new_version_number" in vars(), "Could not find a version -- did you specify one?"

    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        matches = re.findall(OLD_VERSION_REGEX, contents)
        for m in matches:
            # Split on "==" so that any extras specified in the requirement are included in the
            # result. e.g. "otter-grader[grading]==a.b.c" -> "otter-grader[grading]==a.b.d"
            left = m.split("==")[0]
            contents = contents.replace(m, f"{left}=={new_version_number}")

        with open(file, "w") as f:
            f.write(contents)

    # fix otter.__version__
    with open("otter/version.py") as f:
        contents = f.read()

    if args.new_version is not None:
        contents = re.sub(
            r"__version__\s*=\s*['\"]\d+\.\d+\.\d+(?:\.\w+)?['\"]",
            f'__version__ = "{new_version_number}"',
            contents,
        )

    with open("otter/version.py", "w") as f:
        f.write(contents)

    # fix pyproject.toml
    with open("pyproject.toml") as f:
        contents = f.read()

    if args.new_version is not None:
        contents = re.sub(
            r"version = \"\d+\.\d+\.\d+(?:\.\w+)?\"", f'version = "{new_version_number}"', contents
        )

    with open("pyproject.toml", "w") as f:
        f.write(contents)

    # fix CITATION.cff
    with open("CITATION.cff") as f:
        contents = f.read()

    if args.new_version is not None:
        contents = re.sub(
            r"^version:\s*\"\d+.\d+.\d+(?:\.\w+)?\"",
            f'version: "{new_version_number}"',
            contents,
            flags=re.MULTILINE,
        )

        contents = re.sub(
            r"^date-released:\s*\d{4}-\d{2}-\d{2}",
            f"date-released: {dt.date.today().strftime('%Y-%m-%d')}",
            contents,
            flags=re.MULTILINE,
        )

    with open("CITATION.cff", "w") as f:
        f.write(contents)

    print(f"Versions updated. Release version is {new_version_number}")

    if to_beta:
        sys.exit()

    print("Updating CHANGELOG.md")
    with open("CHANGELOG.md") as f:
        cl = f.read()

    new_version_regex = new_version_number.replace(".", r"\.")
    cl = re.sub(
        rf"{new_version_regex}\s*\(unreleased\)", new_version_number, cl, flags=re.IGNORECASE
    )

    with open("CHANGELOG.md", "w") as f:
        f.write(cl)
