import re

CURRENT_VERSION = "0.1.13"
NEW_VERSION = "0.1.14"

FILES_WITH_VERSIONS = [        # do not include setup.py
    "docker/Dockerfile",
    "otter/gs_generator.py",
    "test/integration/autograder-correct/requirements.txt",
    "requirments.txt"
]

def main():
    for file in FILES_WITH_VERSIONS:
        with open(file) as f:
            contents = f.read()

        contents = re.sub(
            "otter-grader=={}".format(CURRENT_VERSION), 
            "otter-grader=={}".format(NEW_VERSION), 
            contents
        )

        with open(file, "w") as f:
            f.write(contents)

    with open("setup.py") as f:
        contents = f.read()

    contents = re.sub(
        "version = \"{}\",".format(CURRENT_VERSION),
        "version = \"{}\",".format(NEW_VERSION),
        contents
    )

    with open("setup.py", "w") as f:
        f.write(contents)

if __name__ == "__main__":
    main()
