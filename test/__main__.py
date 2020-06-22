import unittest
import sys

if len(sys.argv) == 1:
    module = None

else:
    module = "test"

    # extract top-level prog
    if len(sys.argv)== 2:
        module += f".test_{sys.argv[1]}"

    # extract next prog if applicable
    if len(sys.argv) == 3:
        module += f".test_{sys.argv[2]}"

if __name__ == "__main__":
    unittest.main(module=module, argv=[__file__])
