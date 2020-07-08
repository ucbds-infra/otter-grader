import os
import shutil
import pathlib
import nbformat

from .assignment import is_assignment_cell, read_assignment_metadata
from .cell_generators import (
    gen_init_cell, gen_markdown_response_cell, gen_export_cells, gen_check_all_cell, 
    gen_close_export_cell, add_close_export_to_cell
)
from .defaults import NB_VERSION
from .questions import is_question_cell, read_question_metadata, gen_question_cell
from .solutions import is_solution_cell, is_markdown_solution_cell
from .tests import is_test_cell, read_test, gen_test_cell
from .utils import is_seed_cell, EmptyCellException

# TODO: move file writing to another file
def transform_notebook(nb_path, dir, assignment, args):
    """Converts a master notebook to an Otter-formatted solutions notebook and tests directory

    Args:
        nb_path (``pathlib.Path``): path to master notebook
        dir (``pathlib.Path``): output directory
        args (``argparse.Namespace``): parsed command line arguments

    Returns:
        ``str``: path to the solutions notebook

    """
    ok_nb_path = dir / nb_path.name
    tests_dir = dir / 'tests'
    os.makedirs(tests_dir, exist_ok=True)

    requirements = assignment.requirements or args.requirements
    if os.path.isfile(requirements):
        shutil.copy(requirements, str(dir / 'requirements.txt'))

    with open(nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    ok_cells = get_transformed_cells(nb['cells'], tests_dir)

    # copy files
    for file in assignment.files or args.files:
        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(dir / os.path.basename(file)))
        else:
            # check that file is in subdir
            assert os.path.abspath(nb_path.parent) in os.path.abspath(file), \
                f"{file} is not in a subdirectory of the master notebook directory"
            file_path = pathlib.Path(file)
            rel_path = file_path.parent.relative_to(nb_path.parent)
            os.makedirs(dir / rel_path, exist_ok=True)
            shutil.copy(file, str(dir / rel_path))

    if assignment.init_cell and not args.no_init_cell:
        init = gen_init_cell()
        nb['cells'] = [init] + ok_cells
    else:
        nb['cells'] = ok_cells

    if assignment.check_all_cell and not args.no_check_all:
        nb['cells'] += gen_check_all_cell()
    
    if assignment.export_cell and not args.no_export_cell:
        export_cell = assignment.export_cell
        if export_cell is True:
            export_cell = {}

        nb['cells'] += gen_export_cells(
            nb_path, 
            export_cell.get('instructions', ''), 
            pdf = export_cell.get('pdf', True),
            filtering = export_cell.get('filtering', True)
        )

    with open(ok_nb_path, 'w') as f:
        nbformat.write(nb, f, NB_VERSION)
    return ok_nb_path

def get_transformed_cells(cells, tests_dir, assignment):
    """Generate notebook cells for the Otter version of a master notebook

    Args:
        cells (``list`` of ``nbformat.NotebookNode``): original code cells
        tests_dir (``str``): path to directory of tests
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: cleaned notebook cells
    """
    # global SEED_REQUIRED, ASSIGNMENT_METADATA
    ok_cells = []
    question = {}
    processed_response = False
    tests = []
    # hidden_tests = []
    manual_questions = []
    md_has_prompt = False
    need_close_export = False
    no_solution = False

    for cell in cells:

        # this is the prompt cell or if a manual question then the solution cell
        if question and not processed_response:
            assert not is_question_cell(cell), cell
            # assert not is_test_cell(cell), cell
            # assert not is_solution_cell(cell) or is_markdown_solution_cell(cell), cell

            # if this isn't a MD solution cell but in a manual question, it has a prompt
            if not is_solution_cell(cell) and question.get('manual', False):
                md_has_prompt = True
            
            # if there is no prompt, add a prompt cell
            elif is_markdown_solution_cell(cell) and not md_has_prompt:
                ok_cells.append(gen_markdown_response_cell())

            elif is_test_cell(cell):
                no_solution = True
                gen_test_cell(question, tests, tests_dir)

            elif is_seed_cell(cell):
                assignment.seed_required = True
                continue

            if not no_solution:
                ok_cells.append(cell)
            
            processed_response = True

        # if this is a test cell, parse and add to correct group
        elif question and processed_response and is_test_cell(cell):
            test = read_test(cell)
            # if test.hidden:
            #     hidden_tests.append(test)
            # else:
            tests.append(test)

        # if this is a solution cell, append. if manual question and no prompt, also append prompt cell
        elif question and processed_response and is_solution_cell(cell):
            if is_markdown_solution_cell(cell) and not md_has_prompt:
                ok_cells.append(gen_markdown_response_cell())
            ok_cells.append(cell)

        else:
            # the question is over
            if question and processed_response:
                if tests:
                    check_cell = gen_test_cell(question, tests, tests_dir)
                    if not no_solution:
                        ok_cells.append(check_cell)
                # if hidden_tests:
                #     gen_test_cell(question, hidden_tests, tests_dir, hidden=True)

                # add a cell with <!-- END QUESTION --> if a manually graded question
                manual = question.get('manual', False)
                if manual:
                    # ok_cells.append(gen_close_export_cell())
                    need_close_export = True
                
                question, processed_response, tests, md_has_prompt, no_solution = {}, False, [], False, False

            if is_assignment_cell(cell):
                # assert not ASSIGNMENT_METADATA, "Two assignment metadata cells found"
                assignment.update(read_assignment_metadata(cell))

            elif is_question_cell(cell):
                question = read_question_metadata(cell)
                manual = question.get('manual', False)
                format = question.get('format', '')
                in_manual_block = False
                if manual:
                    manual_questions.append(question['name'])
                    # in_manual_block = True
                # if need_close_export:
                #     add_close_export_to_cell(cell)
                #     need_close_export = False
                try:
                    ok_cells.append(gen_question_cell(cell, manual, format, need_close_export))
                    need_close_export = False
                except EmptyCellException:
                    pass

            elif is_solution_cell(cell):
                if is_markdown_solution_cell(cell):
                    ok_cells.append(gen_markdown_response_cell())
                ok_cells.append(cell)

            else:
                assert not is_test_cell(cell), 'Test outside of a question: ' + str(cell)

                if need_close_export:
                    if cell['cell_type'] == 'code':
                        ok_cells.append(gen_close_export_cell())
                    else:
                        add_close_export_to_cell(cell)
                    need_close_export = False

                ok_cells.append(cell)

    if tests:
        check_cell = gen_test_cell(question, tests, tests_dir)
        if not no_solution:
            ok_cells.append(check_cell)
    # if hidden_tests:
    #     gen_test_cell(question, hidden_tests, tests_dir, hidden=True)

    return ok_cells
