
def run_tests(nb_path, debug=False, seed=None):
    """
    Runs tests in the autograder version of the notebook
    
    Args:
        nb_path (``pathlib.Path``): Path to iPython notebooks
        debug (``bool``, optional): ``True`` if errors should not be ignored
        seed (``int``, optional): Random seed for notebook execution
    """
    curr_dir = os.getcwd()
    os.chdir(nb_path.parent)
    results = grade_notebook(nb_path.name, glob(os.path.join("tests", "*.py")), cwd=os.getcwd(), 
    	test_dir=os.path.join(os.getcwd(), "tests"), ignore_errors = not debug, seed=seed)
    assert results["total"] == results["possible"], "Some autograder tests failed:\n\n" + pprint.pformat(results, indent=2)
    os.chdir(curr_dir)

def main(args):
    """
    Runs Otter Assign
    
    Args:
        ``argparse.Namespace``: parsed command line arguments
    """
    master, result = pathlib.Path(args.master), pathlib.Path(args.result)
    print("Generating views...")

    assignment = Assignment()
    
    # TODO: update this condition
    if True:
        result = get_relpath(master.parent, result)
        orig_dir = os.getcwd()
        os.chdir(master.parent)
        master = pathlib.Path(master.name)

    # if args.jassign:
    #     jassign_views(master, result, args)
    # else:
    gen_views(master, result, assignment, args)

    # check that we have a seed if needed
    if assignment.seed_required:
        assert not assignment.generate or assignment.generate.get('seed', None) is not None, \
            "Seeding cell found but no seed provided"
    
    # generate PDF of solutions with nb2pdf
    if assignment.solutions_pdf:
        print("Generating solutions PDF...")
        filtering = assignment.solutions_pdf == 'filtered'
        nb2pdf.convert(
            str(result / 'autograder' / master.name),
            dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
            filtering=filtering
        )

    # generate a tempalte PDF for Gradescope
    if assignment.template_pdf:
        print("Generating template PDF...")
        export_notebook(
            str(result / 'autograder' / master.name),
            dest=str(result / 'autograder' / (master.stem + '-template.pdf')), 
            filtering=True, 
            pagebreaks=True
        )

    # generate the .otter file if needed
    if assignment.service or assignment.save_environment:
        gen_otter_file(master, result)

    # generate Gradescope autograder zipfile
    if assignment.generate:
        # TODO: move this to another function
        print("Generating autograder zipfile...")

        generate_args = assignment.generate
        if generate_args is True:
            generate_args = {}

        curr_dir = os.getcwd()
        os.chdir(str(result / 'autograder'))
        generate_cmd = ["otter", "generate", "autograder"]

        if generate_args.get('points', None) is not None:
            generate_cmd += ["--points", generate_args.get('points', None)]
        
        if generate_args.get('threshold', None) is not None:
            generate_cmd += ["--threshold", generate_args.get('threshold', None)]
        
        if generate_args.get('show_stdout', False):
            generate_cmd += ["--show-stdout"]
        
        if generate_args.get('show_hidden', False):
            generate_cmd += ["--show-hidden"]
        
        if generate_args.get('grade_from_log', False):
            generate_cmd += ["--grade-from-log"]
        
        if generate_args.get('seed', None) is not None:
            generate_cmd += ["--seed", str(generate_args.get('seed', None))]

        if generate_args.get('public_multiplier', None) is not None:
            generate_cmd += ["--public-multiplier", str(generate_args.get('public_multiplier', None))]

        if generate_args.get('pdfs', {}):
            pdf_args = generate_args.get('pdfs', {})
            token = APIClient.get_token()
            generate_cmd += ["--token", token]
            generate_cmd += ["--course-id", str(pdf_args["course_id"])]
            generate_cmd += ["--assignment-id", str(pdf_args["assignment_id"])]

            if not pdf_args.get("filtering", True):
                generate_cmd += ["--unfiltered-pdfs"]

        requirements = assignment.requirements or args.requirements
        requirements = get_relpath(result / 'autograder', pathlib.Path(requirements))
        if os.path.isfile(requirements):
            generate_cmd += ["-r", requirements]
            if assignment.overwrite_requirements or args.overwrite_requirements:
                generate_cmd += ["--overwrite-requirements"]
        
        if assignment.files or args.files:
            generate_cmd += assignment.files or args.files

        if assignment.variables:
            generate_cmd += ["--serialized-variables", str(assignment.variables)]
        
        # TODO: change this to import and direct call
        subprocess.run(generate_cmd)

        os.chdir(curr_dir)

    # run tests on autograder notebook
    if assignment.run_tests and not args.no_run_tests:
        print("Running tests...")
        with block_print():
            if isinstance(assignment.generate, bool):
                seed = None
            else:
                seed = assignment.generate.get('seed', None)
            run_tests(result / 'autograder' / master.name, debug=args.debug, seed=seed)
        print("All tests passed!")

    # TODO: change this condition
    if True:
        os.chdir(orig_dir)
