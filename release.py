import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import warnings


FILES_WITH_VERSIONS = [        # do not include setup.py, otter/version.py
    "Dockerfile",
    "otter/generate/templates/python/requirements.txt",
    "otter/generate/templates/r/requirements.txt",
    "test/test_generate/test-autograder/autograder-correct/requirements.txt",
    "test/test_generate/test-autograder/autograder-token-correct/requirements.txt",
    "test/test_generate/test-autograder/autograder-custom-env/requirements.txt",
    "test/test_generate/test-autograder/autograder-r-correct/requirements.txt",
    "test/test-run/autograder/source/requirements.txt",
    "test/test-assign/gs-autograder-correct/requirements.txt",
    "test/test-assign/rmd-autograder-correct/requirements.txt",
]


def run_release_commands(test, beta, new_version, no_twine=False):
    assert shutil.which("hub") is not None, (
        "You must have the GitHub CLI installed to use this script. Please see "
        "https://github.com/github/hub to install it."
    )

    commands = [
        "rm dist/* || :",
        "python3 setup.py sdist bdist_wheel",
        f"python3 -m twine upload dist/*{' --repository-url https://test.pypi.org/legacy/' if test else ''}",
        "sleep 10", # this allows time for PyPI to update before we try to install the new version
        f"docker build . -t ucbdsinfra/otter-grader:{new_version} --build-arg BUILDKIT_INLINE_CACHE=1",
        f"docker push ucbdsinfra/otter-grader:{new_version}",
        f"docker build . -t ucbdsinfra/otter-grader{':beta' if beta else ''} --build-arg BUILDKIT_INLINE_CACHE=1",
        f"docker push ucbdsinfra/otter-grader{':beta' if beta else ''}",
        "make tutorial",
        f"git commit -am 'release v{new_version}'",
        f"git push upstream master",
        f"hub release create -a dist/*.tar.gz -a dist/*.whl -m 'v{new_version}' {' -p' if beta else ''} {new_version}",
    ]

    if not beta:
        commands.append(f"gh pr create --base 'stable' --head 'master' --title 'Release v{new_version}' " \
            f"--milestone 'v{new_version}' --project 'Otter-Grader Issues and Tasks' " \
            f"--repo 'ucbds-infra/otter-grader' --body ''")

    if no_twine:
        del commands[2]

    for cmd in commands:
        subprocess.run(cmd, shell=True, check=True)

    print("Releases pushed to PyPI, DockerHub, and GitHub. Commit and push to release documentation.")


PARSER = argparse.ArgumentParser()
PARSER.add_argument("new_version", nargs="?", default=None, help="Old version for regex search")
PARSER.add_argument("--dry-run", action="store_true", default=False, help="Update files only but do not push release")
PARSER.add_argument("--git", action="store_true", default=False, help="Indicates that new release should be installed via git")
PARSER.add_argument("--test", action="store_true", default=False, help="Indicates that new release should be pushed to test PyPI")
PARSER.add_argument("--no-twine", action="store_true", default=False, help="Don't upload the release to PyPI")
PARSER.add_argument("-f", "--force", action="store_true", default=False, help="Force run (ignore uncommitted changes)")


OLD_VERSION_REGEX = r"(otter-grader==\d+\.\d+\.\d+(?:\.\w+)?$|git\+https:\/\/github\.com\/ucbds-infra\/otter-grader\.git@[\w\.]+)$"


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

    if not to_git:
        if not to_beta:
            # do not allow non-git non-beta releases from any branch other than master
            branch = (
                subprocess
                .run(["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=subprocess.PIPE)
                .stdout
                .decode("utf-8")
                .strip()
            )
            if branch != "master":
                raise RuntimeError("Cannot create a release from a branch other than mater")

        # check that the upstream remote is correct
        upstream = (
            subprocess
            .run(["git", "config", "--get", "remote.upstream.url"], stdout=subprocess.PIPE)
            .stdout
            .decode("utf-8")
            .strip()
        )
        if upstream != "https://github.com/ucbds-infra/otter-grader":
            raise RuntimeError("You do not have the correct upstream repository configured")

    assert "new_version" in vars(), "Could not find a version -- did you specify one?"

    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        contents = re.sub(
            OLD_VERSION_REGEX, 
            new_version, 
            contents,
            flags=re.MULTILINE
        )

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

    else:
        print(f"Versions updated. Release version is {new_version_number}")

    if args.dry_run:
        sys.exit()
        
    run_release_commands(args.test, to_beta, new_version_number, no_twine=args.no_twine)
