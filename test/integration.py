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
        inspect_command = ["docker", "image", "inspect","otter-grader"]
        inspect = subprocess.run(inspect_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(inspect.stderr), 0)

if __name__ == '__main__':
    unittest.main()
