import pandas as pd
import subprocess
from subprocess import PIPE
import json
import re

def grade_assignments(tests_dir, notebooks_dir, id, image="otter-grader"):
    """
    Args:
        tests_dir: directory of test files
        notebooks_dir: directory of notebooks to grade
        id: id of this function for mc use
        image: docker image to do grading in
    Returns:
        A dataframe of file to grades information
    """
    # launch our docker conainer
    launch_command = ["docker", "run", "-d","-it", image]
    launch = subprocess.run(launch_command, stdout=PIPE, stderr=PIPE)
    
    # print(launch.stderr)
    container_id = launch.stdout.decode('utf-8')[:-1]
    
    # copy the notebook files to the container
    copy_command = ["docker", "cp", notebooks_dir, container_id+ ":/home/notebooks/"]
    copy = subprocess.run(copy_command, stdout=PIPE, stderr=PIPE)
    
    # copy the test files to the container
    tests_command = ["docker", "cp", tests_dir, container_id+ ":/home/tests/"]
    tests = subprocess.run(tests_command, stdout=PIPE, stderr=PIPE)
    
    # Now we have the notebooks in hom/notebooks, we should tell the container to execute the grade command....
    # Placeholder just copy over some csv for now
    grade_command = ["docker", "exec", "-t", container_id, "python3", "-m", "otter.grade", "/home/notebooks"]
    grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)
    
    ls = ["docker", "exec", "-t", container_id, "ls", "-a", "/home/notebooks"]
    ls_out = subprocess.run(ls, stdout=PIPE, stderr=PIPE)

    # get the grades back from the container and read to date frame so we can merge later
    csv_command = ["docker", "cp", container_id+ ":/home/grades.csv", "./grades"+id+".csv"]
    csv = subprocess.run(csv_command, stdout=PIPE, stderr=PIPE)
    df = pd.read_csv("./grades"+id+".csv")

    mkdir_pdf = ["mkdir", "manual_submissions"]
    subprocess.run(mkdir_pdf, stdout=PIPE, stderr=PIPE)
    
    # copy out manual submissions
    for pdf in df["manual"]:
        copy_cmd = ["docker", "cp", container_id + ":" + pdf, "./manual_submissions/" + re.search(r"\/([\w\-\_]*?\.pdf)", pdf)[1]]
        copy = subprocess.run(copy_cmd, stdout=PIPE, stderr=PIPE)

    def clean_pdf_filepaths(row):
        path = row["manual"]
        return re.sub(r"\/home\/notebooks", "manual_submissions", path)

    df["manual"] = df.apply(clean_pdf_filepaths, axis=1)
    
    # delete the file we just read
    csv_cleanup_command = ["rm", "./grades"+id+".csv"]
    csv_cleanup = subprocess.run(csv_cleanup_command, stdout=PIPE, stderr=PIPE)
    
    # cleanup the docker container
    stop_command = ["docker", "stop", container_id]
    stop = subprocess.run(stop_command, stdout=PIPE, stderr=PIPE)
    remove_command = ["docker", "rm", container_id]
    remove = subprocess.run(remove_command, stdout=PIPE, stderr=PIPE)
    
    # check that no commands errored, if they did rais an informative exception
    all_commands = [launch, copy, tests, grade, csv, csv_cleanup, stop, remove]
    for command in all_commands:
        if command.stderr.decode('utf-8') != '':
            raise Exception("Error running ", command, " failed with error: ", command.stderr.decode('utf-8'))
    return df
