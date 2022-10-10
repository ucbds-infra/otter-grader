"""Runs Otter-Grader's autograding process"""

from otter.run.run_autograder import main as run_autograder

if __name__ == "__main__":
    run_autograder("{{ autograder_dir }}")
