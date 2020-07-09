import unittest
import sys

if len(sys.argv) == 1:
    module = None
    test_name = None

else:
    module = "test"
    test_name = None

    # extract top-level prog
    if len(sys.argv) >= 2:
        module += f".test_{sys.argv[1]}"

    # extract next prog if applicable
    if len(sys.argv) >= 3:
        if sys.argv[1] in ["generate", "service"]:
            module += f".test_{sys.argv[2]}"
        else:
            test_name = f"Test{sys.argv[1].capitalize()}.test_{sys.argv[2]}"

    # extract test name
    if len(sys.argv) >= 4:
        test_name = f"Test{sys.argv[2].capitalize()}.test_{sys.argv[3]}"

if __name__ == "__main__":
    unittest.main(module=module, argv=[__file__], defaultTest=test_name, verbosity=0)
