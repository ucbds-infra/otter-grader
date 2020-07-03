#######################################################
#####                Otter Assign                 #####
##### forked from https://github.com/okpy/jassign #####
#######################################################

# TODO: move seed to inside solution cell

import copy
import json
import pprint
import os
import re
import shutil
import yaml
import subprocess
import pathlib
import nbformat
import nb2pdf

from collections import namedtuple
from glob import glob
from getpass import getpass

from .execute import grade_notebook
# from .jassign import gen_views as jassign_views
from .export import export_notebook
from .utils import block_print, str_to_doctest, get_relpath
from .generate.token import APIClient


NB_VERSION = 4
BLOCK_QUOTE = "```"
COMMENT_PREFIX = "#"
TEST_HEADERS = ["TEST", "HIDDEN TEST"]
ALLOWED_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
NB_VERSION = 4

TEST_REGEX = r"(##\s*(hidden\s*)?test\s*##|#\s*(hidden\s*)?test)"
SOLUTION_REGEX = r"##\s*solution\s*##"
MD_SOLUTION_REGEX = r"(<strong>|\*{2})solution:?(<\/strong>|\*{2})"
SEED_REGEX = r"##\s*seed\s*##"

MD_ANSWER_CELL_TEMPLATE = "_Type your answer here, replacing this text._"

SEED_REQUIRED = False

ASSIGNMENT_METADATA = {}

class EmptyCellException(Exception):
    """Exception for empty cells to indicate deletion"""


def run_tests(nb_path, debug=False, seed=None):
    """Run tests in the autograder version of the notebook.
    
    Args:
        nb_path (``str``): Path to iPython notebooks
        debug (``bool``, optional): ``True`` if errors should not be ignored
        seed (``int``, optional): Random seed for numpy
    """
    curr_dir = os.getcwd()
    os.chdir(nb_path.parent)
    results = grade_notebook(nb_path.name, glob(os.path.join("tests", "*.py")), cwd=os.getcwd(), 
    	test_dir=os.path.join(os.getcwd(), "tests"), ignore_errors = not debug, seed=seed)
    assert results["total"] == results["possible"], "Some autograder tests failed:\n\n" + pprint.pformat(results, indent=2)
    os.chdir(curr_dir)


def main(args):
    """Runs Otter Assign
    
    Args:
        ``argparse.Namespace``: parsed command line arguments
    """
    master, result = pathlib.Path(args.master), pathlib.Path(args.result)
    print("Generating views...")
    
    # TODO: update this condition
    if True:
        result = get_relpath(master.parent, result)
        orig_dir = os.getcwd()
        os.chdir(master.parent)
        master = pathlib.Path(master.name)

    # if args.jassign:
    #     jassign_views(master, result, args)
    # else:
    gen_views(master, result, args)

    # check that we have a seed if needed
    if SEED_REQUIRED:
        assert not ASSIGNMENT_METADATA.get('generate', {})  or \
            ASSIGNMENT_METADATA.get('generate', {}).get('seed', None) is not None, "Seeding cell found but no seed provided"
    
    # generate PDF of solutions with nb2pdf
    if ASSIGNMENT_METADATA.get('solutions_pdf', False):
        print("Generating solutions PDF...")
        filtering = ASSIGNMENT_METADATA.get('solutions_pdf') == 'filtered'
        nb2pdf.convert(
            str(result / 'autograder' / master.name),
            dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
            filtering=filtering
        )

    # generate a tempalte PDF for Gradescope
    if ASSIGNMENT_METADATA.get('template_pdf', False):
        print("Generating template PDF...")
        export_notebook(
            str(result / 'autograder' / master.name),
            dest=str(result / 'autograder' / (master.stem + '-template.pdf')), 
            filtering=True, 
            pagebreaks=True
        )

    # generate the .otter file if needed
    if ASSIGNMENT_METADATA.get('service', {}) or ASSIGNMENT_METADATA.get('save_environment', False):
        gen_otter_file(master, result)

    # generate Gradescope autograder zipfile
    if ASSIGNMENT_METADATA.get('generate', {}):
        print("Generating autograder zipfile...")

        generate_args = ASSIGNMENT_METADATA.get('generate', {})
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

        requirements = ASSIGNMENT_METADATA.get('requirements', None) or args.requirements
        requirements = get_relpath(result / 'autograder', pathlib.Path(requirements))
        if os.path.isfile(requirements):
            generate_cmd += ["-r", requirements]
            if ASSIGNMENT_METADATA.get('overwrite_requirements', False) or args.overwrite_requirements:
                generate_cmd += ["--overwrite-requirements"]
        
        if ASSIGNMENT_METADATA.get('files', []) or args.files:
            # os.path.split fixes issues due to relative paths
            generate_cmd += ASSIGNMENT_METADATA.get('files', []) or args.files
            # [os.path.split(file)[1] for file in ASSIGNMENT_METADATA.get('files', []) or args.files]

        if ASSIGNMENT_METADATA.get('variables', {}):
            generate_cmd += ["--serialized-variables", str(ASSIGNMENT_METADATA["variables"])]
        
        subprocess.run(generate_cmd)

        os.chdir(curr_dir)

    # run tests on autograder notebook
    if ASSIGNMENT_METADATA.get('run_tests', True) and not args.no_run_tests:
        print("Running tests...")
        with block_print():
            if isinstance(ASSIGNMENT_METADATA.get('generate', {}), bool):
                seed = None
            else:
                seed = ASSIGNMENT_METADATA.get('generate', {}).get('seed', None)
            run_tests(result / 'autograder' / master.name, debug=args.debug, seed=seed)
        print("All tests passed!")

    # TODO: change this condition
    if True:
        os.chdir(orig_dir)


def gen_otter_file(master, result):
    """Creates an Otter config file

    Uses ``ASSIGNMENT_METADATA`` to generate a ``.otter`` file to configure student use of Otter tools, 
    including saving environments and submission to an Otter Service deployment

    Args:
        master (``pathlib.Path``): path to master notebook
        result (``pathlib.Path``): path to result directory
    """
    config = {}

    service = ASSIGNMENT_METADATA.get('service', {})
    if service:
        config.update({
            "endpoint": service["endpoint"],
            "auth": service.get("auth", "google"),
            "assignment_id": service["assignment_id"],
            "class_id": service["class_id"]
        })

    config["notebook"] = service.get('notebook', master.name)
    config["save_environment"] = ASSIGNMENT_METADATA.get("save_environment", False)
    config["ignore_modules"] = ASSIGNMENT_METADATA.get("ignore_modules", [])

    if ASSIGNMENT_METADATA.get("variables", None):
        config["variables"] = ASSIGNMENT_METADATA.get("variables")

    config_name = master.stem + '.otter'
    with open(result / 'autograder' / config_name, "w+") as f:
        json.dump(config, f, indent=4)
    with open(result / 'student' / config_name, "w+") as f:
        json.dump(config, f, indent=4)


def convert_to_ok(nb_path, dir, args):
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

    requirements = ASSIGNMENT_METADATA.get('requirements', None) or args.requirements
    if os.path.isfile(requirements):
        shutil.copy(requirements, str(dir / 'requirements.txt'))

    with open(nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    ok_cells = gen_ok_cells(nb['cells'], tests_dir)

    # copy files
    for file in ASSIGNMENT_METADATA.get('files', []) or args.files:
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

    if ASSIGNMENT_METADATA.get('init_cell', True) and not args.no_init_cell:
        init = gen_init_cell()
        nb['cells'] = [init] + ok_cells
    else:
        nb['cells'] = ok_cells

    if ASSIGNMENT_METADATA.get('check_all_cell', True) and not args.no_check_all:
        nb['cells'] += gen_check_all_cell()
    
    if ASSIGNMENT_METADATA.get('export_cell', True) and not args.no_export_cell:
        export_cell = ASSIGNMENT_METADATA.get("export_cell", True)
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


def gen_init_cell():
    """Generates a cell to initialize Otter in the notebook
    
    Returns:
        cell (``nbformat.NotebookNode``): new code cell
    """
    cell = nbformat.v4.new_code_cell("# Initialize Otter\nimport otter\ngrader = otter.Notebook()")
    lock(cell)
    return cell


def gen_export_cells(nb_path, instruction_text, pdf=True, filtering=True):
    """Generates export cells
    
    Args:
        nb_path (``str``): path to master notebook
        instruction_text (``str``): extra instructions for students when exporting
        pdf (``bool``, optional): whether a PDF is needed
        filtering (``bool``, optional): whether PDF filtering is needed
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: generated export cells

    """
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "## Submission\n\nMake sure you have run all cells in your notebook in order before \
    running the cell below, so that all images/graphs appear in the output. The cell below will generate \
    a zipfile for you to submit. **Please save before exporting!**"
    
    if instruction_text:
        instructions.source += '\n\n' + instruction_text

    export = nbformat.v4.new_code_cell()
    source_lines = ["# Save your notebook first, then run this cell to export your submission."]
    if filtering and pdf:
        source_lines.append(f"grader.export()")
    elif not filtering:
        source_lines.append(f"grader.export(filtering=False)")
    else:
        source_lines.append(f"grader.export(pdf=False)")
    export.source = "\n".join(source_lines)

    lock(instructions)
    lock(export)

    return [instructions, export, nbformat.v4.new_markdown_cell(" ")]     # last cell is buffer


def gen_check_all_cell():
    """Generates an ``otter.Notebook.check_all`` cell
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: generated check-all cells
    """
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "---\n\nTo double-check your work, the cell below will rerun all of the autograder tests."

    check_all = nbformat.v4.new_code_cell("grader.check_all()")

    lock(instructions)
    lock(check_all)

    return [instructions, check_all]


def gen_ok_cells(cells, tests_dir):
    """Generate notebook cells for the Otter version of a master notebook

    Args:
        cells (``list`` of ``nbformat.NotebookNode``): original code cells
        tests_dir (``str``): path to directory of tests
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: cleaned notebook cells
    """
    global SEED_REQUIRED, ASSIGNMENT_METADATA
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
                ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))

            elif is_test_cell(cell):
                no_solution = True
                gen_test_cell(question, tests, tests_dir)

            elif is_seed_cell(cell):
                SEED_REQUIRED = True
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
                ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))
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
                assert not ASSIGNMENT_METADATA, "Two assignment metadata cells found"
                ASSIGNMENT_METADATA = read_assignment_metadata(cell)

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
                    ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))
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


def get_source(cell):
    """Get the source code of a cell in a way that works for both nbformat and JSON
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``list`` of ``str``: each line of the cell source
    """
    source = cell['source']
    if isinstance(source, str):
        return cell['source'].split('\n')
    elif isinstance(source, list):
        return [line.strip('\n') for line in source]
    assert 'unknown source type', type(source)


def is_question_cell(cell):
    """Whether cell contains BEGIN QUESTION in a block quote
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a question definition cell

    """
    if cell['cell_type'] != 'markdown':
        return False
    return find_question_spec(get_source(cell)) is not None


def is_assignment_cell(cell):
    """Whether cell contains BEGIN ASSIGNMENT in a block quote
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is an assignment definition cell
    """
    if cell['cell_type'] != 'markdown':
        return False
    return find_assignment_spec(get_source(cell)) is not None


def is_seed_cell(cell):
    """Whether cell is seed cell
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a seed cell
    """
    if cell['cell_type'] != 'code':
        return False
    source = get_source(cell)
    return source and re.match(SEED_REGEX, source[0], flags=re.IGNORECASE)


def is_markdown_solution_cell(cell):
    """Whether the cell matches MD_SOLUTION_REGEX
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a Markdown solution cell
    """
    source = get_source(cell)
    return is_solution_cell and any([re.match(MD_SOLUTION_REGEX, l, flags=re.IGNORECASE) for l in source])


def is_solution_cell(cell):
    """Whether the cell matches SOLUTION_REGEX or MD_SOLUTION_REGEX
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a solution cell
    """
    source = get_source(cell)
    if cell['cell_type'] == 'markdown':
        return source and any([re.match(MD_SOLUTION_REGEX, l, flags=re.IGNORECASE) for l in source])
    elif cell['cell_type'] == 'code':
        return source and re.match(SOLUTION_REGEX, source[0], flags=re.IGNORECASE)
    return False


def find_question_spec(source):
    """Return line number of the BEGIN QUESTION line or None
    
    Args:
        source (``list`` of ``str``): cell source as a list of lines of text
    
    Returns:
        ``int``: line number of BEGIN QUESTION, if present
        ``None``: if BEGIN QUESTION not present in the cell
    """
    block_quotes = [i for i, line in enumerate(source) if
                    line[:3] == BLOCK_QUOTE]
    assert len(block_quotes) % 2 == 0, 'cannot parse ' + str(source)
    begins = [block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) if
              source[block_quotes[i]+1].strip(' ') == 'BEGIN QUESTION']
    assert len(begins) <= 1, 'multiple questions defined in ' + str(source)
    return begins[0] if begins else None


def find_assignment_spec(source):
    """Return line number of the BEGIN ASSIGNMENT line or None
    
    Args:
        source (``list`` of ``str``): cell source as a list of lines of text
    
    Returns:
        ``int``: line number of BEGIN ASSIGNMENT, if present
        ``None``: if BEGIN ASSIGNMENT not present in the cell
    """
    block_quotes = [i for i, line in enumerate(source) if
                    line[:3] == BLOCK_QUOTE]
    assert len(block_quotes) % 2 == 0, 'cannot parse ' + str(source)
    begins = [block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) if
              source[block_quotes[i]+1].strip(' ') == 'BEGIN ASSIGNMENT']
    assert len(begins) <= 1, 'multiple assignments defined in ' + str(source)
    return begins[0] if begins else None


def gen_question_cell(cell, manual, format, need_close_export):
    """Return a locked question cell with metadata hidden in an HTML comment
    
    Args:
        cell (``nbformat.NotebookNode``): the original question cell
    
    Returns:
        ``nbformat.NotebookNode``: the updated question cell
    """
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    if manual:
        source = ["<!-- BEGIN QUESTION -->", ""] + source
    if need_close_export:
        source = ["<!-- END QUESTION -->", ""] + source
    begin_question_line = find_question_spec(source)
    start = begin_question_line - 1
    assert source[start].strip() == BLOCK_QUOTE
    end = begin_question_line
    while source[end].strip() != BLOCK_QUOTE:
        end += 1
    source[start] = "<!--"
    source[end] = "-->"
    cell['source'] = '\n'.join(source)

    # checkf or empty cell
    cell_text = source[:start]
    try:
        cell_text += source[end+1:]
    except IndexError:
        pass
    if not "".join(cell_text).strip():
        raise EmptyCellException()

    lock(cell)
    return cell


def gen_close_export_cell():
    """Returns a new cell to end question export
    
    Returns:
        ``nbformat.NotebookNode``: new Markdown cell with ``<!-- END QUESTION -->``
    """
    cell = nbformat.v4.new_markdown_cell("<!-- END QUESTION -->")
    lock(cell)
    return cell


def add_close_export_to_cell(cell):
    """Adds an export close to the top of the cell. Mutates the original cell
    
    Args:
        cell (``nbformat.NotebookNode``): the cell to add the close export to
    """
    source = get_source(cell)
    source = ["<!-- END QUESTION -->\n", "\n"] + source
    cell['source'] = "\n".join(source)


def read_question_metadata(cell):
    """Return question metadata from a question cell
    
    Args:
        cell (``nbformat.NotebookNode``): the question cell
    
    Returns:
        ``dict``: question metadata
    """
    source = get_source(cell)
    begin_question_line = find_question_spec(source)
    i, lines = begin_question_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    assert ALLOWED_NAME.match(metadata.get('name', '')), metadata
    return metadata


def read_assignment_metadata(cell):
    """Return assignment metadata from an assignment cell
    
    Args:
        cell (``nbformat.NotebookNode``): the assignment cell
    
    Returns:
        ``dict``: assignment metadata
    """
    source = get_source(cell)
    begin_assignment_line = find_assignment_spec(source)
    i, lines = begin_assignment_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    return metadata


def is_test_cell(cell):
    """Return whether the current cell is a test cell
    
    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the cell is a test cell
    """
    if cell['cell_type'] != 'code':
        return False
    source = get_source(cell)
    return source and re.match(TEST_REGEX, source[0], flags=re.IGNORECASE)


Test = namedtuple('Test', ['input', 'output', 'hidden'])


def read_test(cell):
    """Return the contents of a test as an (input, output, hidden) tuple
    
    Args:
        cell (``nbformat.NotebookNode``): a test cell

    Returns:
        ``otter.assign.Test``: test named tuple
    """
    hidden = bool(re.search("hidden", get_source(cell)[0], flags=re.IGNORECASE))
    output = ''
    for o in cell['outputs']:
        output += ''.join(o.get('text', ''))
        results = o.get('data', {}).get('text/plain')
        if results and isinstance(results, list):
            output += results[0]
        elif results:
            output += results
    return Test('\n'.join(get_source(cell)[1:]), output, hidden)


def write_test(path, test):
    """Write an OK test file
    
    Args:
        path (``str``): path of file to be written
        test (``dict``): OK test to be written
    """
    with open(path, 'w') as f:
        f.write('test = ')
        pprint.pprint(test, f, indent=4, width=200, depth=None)


def gen_test_cell(question, tests, tests_dir):
    """Write test files to tests directory
    
    Args:
        question (``dict``): question metadata
        tests (``list`` of ``otter.assign.Test``): tests to be written
        tests_dir (``pathlib.Path``): path to tests directory

    Returns:
        cell: code cell object with test
    """
    cell = nbformat.v4.new_code_cell()
    cell.source = ['grader.check("{}")'.format(question['name'])]
    suites = [gen_suite(tests)]
    points = question.get('points', 1)
    
    test = {
        'name': question['name'],
        'points': points,
        'suites': suites,
    }

    write_test(tests_dir / (question['name'] + '.py'), test)
    lock(cell)
    return cell


def gen_suite(tests):
    """Generate an OK test suite for a test
    
    Args:
        tests (``list`` of ``otter.assign.Test``): test cases

    Returns:
        ``dict``: OK test suite
    """
    cases = [gen_case(test) for test in tests]
    return  {
      'cases': cases,
      'scored': True,
      'setup': '',
      'teardown': '',
      'type': 'doctest'
    }


def gen_case(test):
    """Generate an OK test case for a test
    
    Args:
        test (``otter.assign.Test``): OK test for this test case

    Returns:
        ``dict``: the OK test case
    """
    code_lines = str_to_doctest(test.input.split('\n'), [])

    for i in range(len(code_lines) - 1):
        if code_lines[i+1].startswith('>>>') and len(code_lines[i].strip()) > 3 and not code_lines[i].strip().endswith("\\"):
            code_lines[i] += ';'

    code_lines.append(test.output)

    return {
        'code': '\n'.join(code_lines),
        'hidden': test.hidden,
        'locked': False
    }


solution_assignment_re = re.compile('(\\s*[a-zA-Z0-9_ ]*=)(.*) #[ ]?SOLUTION')
def solution_assignment_sub(match):
    prefix = match.group(1)
    return prefix + ' ...'


solution_line_re = re.compile('(\\s*)([^#\n]+) #[ ]?SOLUTION')
def solution_line_sub(match):
    prefix = match.group(1)
    return prefix + '...'


begin_solution_re = re.compile(r'(\s*)# BEGIN SOLUTION( NO PROMPT)?')
skip_suffixes = ['# SOLUTION NO PROMPT', '# BEGIN PROMPT', '# END PROMPT']


SUBSTITUTIONS = [
    (solution_assignment_re, solution_assignment_sub),
    (solution_line_re, solution_line_sub),
]


def replace_solutions(lines):
    """Replace solutions in lines, a list of strings
    
    Args:
        lines (``list`` of ``str``): solutions as a list of strings

    Returns:
        ``list`` of ``str``: stripped version of lines without solutions
    """
    stripped = []
    solution = False
    for line in lines:
        if any(line.endswith(s) for s in skip_suffixes):
            continue
        if solution and not line.endswith('# END SOLUTION'):
            continue
        if line.endswith('# END SOLUTION'):
            assert solution, 'END SOLUTION without BEGIN SOLUTION in ' + str(lines)
            solution = False
            continue
        begin_solution = begin_solution_re.match(line)
        if begin_solution:
            assert not solution, 'Nested BEGIN SOLUTION in ' + str(lines)
            solution = True
            if not begin_solution.group(2):
                line = begin_solution.group(1) + '...'
            else:
                continue
        for exp, sub in SUBSTITUTIONS:
            m = exp.match(line)
            if m:
                line = sub(m)
        stripped.append(line)
    assert not solution, 'BEGIN SOLUTION without END SOLUTION in ' + str(lines)
    return stripped


def strip_solutions(original_nb_path, stripped_nb_path):
    """Write a notebook with solutions stripped
    
    Args:
        original_nb_path (path-like): path to original notebook
        stripped_nb_path (path-like): path to new stripped notebook
    """
    with open(original_nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    md_solutions = []
    for i, cell in enumerate(nb['cells']):
        cell['source'] = '\n'.join(replace_solutions(get_source(cell)))
        if is_markdown_solution_cell(cell):
            md_solutions.append(i)
    md_solutions.reverse()
    for i in md_solutions:
        del nb['cells'][i]
    
    # remove output from student version
    remove_output(nb)
    with open(stripped_nb_path, 'w') as f:
        nbformat.write(nb, f, NB_VERSION)


def remove_output(nb):
    """Remove all outputs from a notebook
    
    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb['cells']:
        if 'outputs' in cell:
            cell['outputs'] = []


def lock(cell):
    """Makes a cell non-editable and non-deletable

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False


def remove_hidden_tests(test_dir):
    """Rewrite test files to remove hidden tests
    
    Args:
        test_dir (``pathlib.Path``): path to test files directory
    """
    for f in test_dir.iterdir():
        if f.name == '__init__.py' or f.suffix != '.py':
            continue
        locals = {}
        with open(f) as f2:
            exec(f2.read(), globals(), locals)
        test = locals['test']
        for suite in test['suites']:
            for i, case in list(enumerate(suite['cases']))[::-1]:
                if case['hidden']:
                    suite['cases'].pop(i)
        write_test(f, test)


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
