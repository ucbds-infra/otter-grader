import json

def gen_otter_file(master, result, assignment):
    """Creates an Otter config file

    Uses ``ASSIGNMENT_METADATA`` to generate a ``.otter`` file to configure student use of Otter tools, 
    including saving environments and submission to an Otter Service deployment

    Args:
        master (``pathlib.Path``): path to master notebook
        result (``pathlib.Path``): path to result directory
    """
    config = {}

    service = assignment.service
    if service:
        config.update({
            "endpoint": service["endpoint"],
            "auth": service.get("auth", "google"),
            "assignment_id": service["assignment_id"],
            "class_id": service["class_id"]
        })

    config["notebook"] = service.get('notebook', master.name)
    config["save_environment"] = assignment.save_environment
    config["ignore_modules"] = assignment.ignore_modules

    if assignment.variables:
        config["variables"] = assignment.variables

    config_name = master.stem + '.otter'
    with open(result / 'autograder' / config_name, "w+") as f:
        json.dump(config, f, indent=4)
    with open(result / 'student' / config_name, "w+") as f:
        json.dump(config, f, indent=4)

def gen_views(master_nb, result_dir, args):
    """Generate student and autograder views.

    Args:
        master_nb (``nbformat.NotebookNode``): the master notebook
        result_dir (``pathlib.Path``): path to the result directory
        args (``argparse.Namespace``): parsed command line arguments
    """
    autograder_dir = result_dir / 'autograder'
    student_dir = result_dir / 'student'
    shutil.rmtree(autograder_dir, ignore_errors=True)
    shutil.rmtree(student_dir, ignore_errors=True)
    os.makedirs(autograder_dir, exist_ok=True)
    ok_nb_path = convert_to_ok(master_nb, autograder_dir, args)
    shutil.rmtree(student_dir, ignore_errors=True)
    shutil.copytree(autograder_dir, student_dir)

    requirements = ASSIGNMENT_METADATA.get('requirements', None) or args.requirements
    if os.path.isfile(str(student_dir / os.path.split(requirements)[1])):
        os.remove(str(student_dir / os.path.split(requirements)[1]))

    student_nb_path = student_dir / ok_nb_path.name
    os.remove(student_nb_path)
    strip_solutions(ok_nb_path, student_nb_path)
    remove_hidden_tests(student_dir / 'tests')
