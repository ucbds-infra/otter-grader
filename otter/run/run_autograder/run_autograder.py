"""
Gradescope autograding internals for Python
"""

import os
import json
import shutil
import pickle
# import subprocess
import warnings
import zipfile

from glob import glob

from .utils import replace_notebook_instances
from ...check.logs import Log, QuestionNotInLogException
from ...check.notebook import _OTTER_LOG_FILENAME
from ...execute import grade_notebook
from ...export import export_notebook
from ...generate.token import APIClient
from ...plugins import PluginCollection
from ...utils import print_full_width

def prepare_files():
    """
    Copies and creates files needed for running the autograder

    Copies all files in ``source/files`` into ``submission`` so that they are accessible by the 
    submission being executed. Copies all test files in ``source/tests`` into ``submission/tests``.
    Creates ``__init__.py`` files in the autograding directory and ``submission`` to allow relative
    imports.
    """
    # put files into submission directory
    if os.path.exists("./source/files"):
        for file in os.listdir("./source/files"):
            fp = os.path.join("./source/files", file)
            if os.path.isdir(fp):
                if not os.path.exists(os.path.join("./submission", os.path.basename(fp))):
                    shutil.copytree(fp, os.path.join("./submission", os.path.basename(fp)))
            else:
                shutil.copy(fp, "./submission")

    # create __init__.py files
    open("__init__.py", "a").close()
    open("submission/__init__.py", "a").close()
    # subprocess.run(["touch", "./__init__.py"])
    # subprocess.run(["touch", "./submission/__init__.py"])

    os.makedirs("./submission/tests", exist_ok=True)
    tests_glob = glob("./source/tests/*.py")
    for file in tests_glob:
        shutil.copy(file, "./submission/tests")

def write_and_submit_pdf(client, nb_path, filtering, pagebreaks, course_id, assignment_id, submit=True):
    """
    Converts a notebook to a PDF and uploads it to a Gradescope assignment for manual grading

    Args:
        client (``otter.generate.token.APIClient``): the Gradescope client
        nb_path (``str``): path to the notebook
        filtering (``bool``): whether to filter the notebook
        pagebreaks (``bool``): whether to insert pagebreaks in the PDF
        course_id (``str``): Gradescope course ID
        assignment_id (``str``): Gradescope assignment ID
        submit (``bool``, optional): whether to upload the PDF instead of just converting
    """
    try:
        export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
        pdf_path = os.path.splitext(nb_path)[0] + ".pdf"

        if submit:
            # get student email
            with open("../submission_metadata.json") as f:
                metadata = json.load(f)

            student_emails = []
            for user in metadata["users"]:
                student_emails.append(user["email"])
            
            for student_email in student_emails:
                client.upload_pdf_submission(course_id, assignment_id, student_email, pdf_path)

            print("\n\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails)))

    except Exception as e:
        # print("\n\n")
        # warnings.warn("PDF generation or submission failed", RuntimeWarning)
        print(f"\n\nError encountered while generating and submitting PDF:\n{e}")

def run_autograder(options):
    """
    Runs autograder based on predefined configurations

    Args:
        options (``dict``): configurations for autograder; should contain all keys present in
            ``otter.run.run_adapter.constants.DEFAULT_OPTIONS``
        
    Returns:
        ``dict``: the results of grading as a JSON object
    """
    # options = DEFAULT_OPTIONS.copy()
    # options.update(config)

    # add miniconda back to path
    os.environ["PATH"] = f"{options['miniconda_path']}/bin:" + os.environ.get("PATH")
    
    abs_ag_path = os.path.abspath(options["autograder_dir"])
    os.chdir(abs_ag_path)

    prepare_files()

    os.chdir("./submission")

    if options["zips"]:
        zips = glob("*.zip")
        if len(zips) > 1:
            raise RuntimeError("More than one zip file found in submission and 'zips' config is true")

        with zipfile.ZipFile(zips[0])  as zf:
            zf.extractall()

    nbs = glob("*ipynb")

    if len(nbs) > 1:
        raise RuntimeError("More than one ipynb file found in submission")

    if len(nbs) == 1:
        nb_path = nbs[0]
        script = False
    else:
        pys = glob("*.py")
        pys = list(filter(lambda f: f != "__init__.py", pys))
        if len(pys) > 1:
            raise RuntimeError("More than one Python file found in submission")
        elif len(pys) == 1:
            nb_path = pys[0]
            script = True
        else:
            raise RuntimeError("No gradable files found in submission")

    replace_notebook_instances(nb_path)

    # load plugins
    plugins = options["plugins"]

    if plugins:
        with open("../submission_metadata.json") as f:
            submission_metadata = json.load(f)
        
        plugin_collection = PluginCollection(
            plugins, os.path.abspath(nb_path), submission_metadata
        )
    
    else:
        plugin_collection = None

    if plugin_collection:
        plugin_collection.run("before_grading", options)

    if options["token"] is not None:
        client = APIClient(token=options["token"])
        generate_pdf = True
        has_token = True
    else:
        generate_pdf = options["pdf"]
        has_token = False
        client = None

    if os.path.isfile(_OTTER_LOG_FILENAME):
        try:
            log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
        except Exception as e:
            if options["grade_from_log"]:
                raise e
            else:
                print(f"Could not deserialize the log due to an error:\n{e}")
                log = None
    else:
        assert not options["grade_from_log"], "missing log"
        log = None

    scores = grade_notebook(
        nb_path, 
        glob("./tests/*.py"), 
        name="submission", 
        cwd=".", 
        test_dir="./tests",
        ignore_errors=not options["debug"], 
        seed=options["seed"],
        log=log if options["grade_from_log"] else None,
        variables=options["serialized_variables"],
        plugin_collection=plugin_collection,
        script=script,
    )

    if options["print_summary"]:
        # print("\n" + "-" * 30 + " GRADING SUMMARY " + "-" * 30)
        print("\n\n\n\n", end="")
        print_full_width("-", mid_text="GRADING SUMMARY")

    # verify the scores against the log
    if options["print_summary"]:
        print()
        if log is not None:
            try:
                found_discrepancy = scores.verify_against_log(log)
                if not found_discrepancy and options["print_summary"]:
                    print("No discrepancies found while verifying scores against the log.")
            except BaseException as e:
                print(f"Error encountered while trying to verify scores with log:\n{e}")
        else:
            print("No log found with which to verify student scores.")

    if generate_pdf:
        write_and_submit_pdf(
            client, nb_path, options['filtering'], options['pagebreaks'], options['course_id'], 
            options['assignment_id'], submit=has_token
        )

    output = scores.to_gradescope_dict(options)

    if plugin_collection:
        report = plugin_collection.generate_report()
        if report.strip():
            print("\n\n" + report)

    os.chdir(abs_ag_path)

    with open("results/results.pkl", "wb+") as f:
        pickle.dump(scores, f)

    return output
