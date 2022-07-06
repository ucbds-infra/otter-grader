import argparse
import dill
import os
import shutil
import tempfile
import zipfile

from glob import glob

from ...execute import grade_notebook


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip-path", required=True)
    parser.add_argument("--nb-arcname", required=True)
    parser.add_argument("--tests-dir", required=True)
    parser.add_argument("--results-path", required=True)
    return parser


def main():
    args = get_parser().parse_args()

    nb_dir = tempfile.mkdtemp()

    try:
        with zipfile.ZipFile(args.zip_path, "r") as zf:
            nb_path = zf.extract(args.nb_arcname, path=nb_dir)

        results = grade_notebook(
            nb_path,
            tests_glob=glob(args.tests_dir + "/*.py"),
            cwd=os.getcwd()
        )

        with open(args.results_path, "wb") as f:
            dill.dump(results, f)

    finally:
        shutil.rmtree(nb_dir)


if __name__ == "__main__":
    main()
