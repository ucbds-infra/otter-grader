import os
import pandas as pd
import unittest
import subprocess
from subprocess import PIPE

class TestIntegration(unittest.TestCase):

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect_command = ["docker", "image", "inspect","otter-grader"]
        inspect = subprocess.run(inspect_command, stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0)

    def test_hundred(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        # grade the 100 notebooks
        grade_command = ["otter", "-y", "meta.yml", "-n", "integration/manual-test/", "-t", "integration/tests/"]
        grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)

        # read the output and expected output
        df_test = pd.read_csv("final_grades.csv").sort_values("identifier").reset_index(drop=True)
        df_correct = pd.read_csv("integration/final_grades_correct.csv").sort_values("identifier").reset_index(drop=True)

        # remove the extra output
        cleanup_command = ["rm", "final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assertions (run at the end to make sure we do cleanup)
        self.assertEqual(len(grade.stderr), 0, grade.stderr)
        self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")

if __name__ == '__main__':
    unittest.main()
