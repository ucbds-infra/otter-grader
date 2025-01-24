"""Runs Otter-Grader's autograding process"""

try:
    from otter.run.run_autograder import main as run_autograder
except ModuleNotFoundError as e:
    if "'otter'" in str(e):
        raise RuntimeError(
            "The 'otter' module could not be imported. This is usually caused by errors while building the "
            "grading image, so check the image build logs and include them when requesting "
            "support."
        )
    raise e


if __name__ == "__main__":
    run_autograder("{{ autograder_dir }}")
