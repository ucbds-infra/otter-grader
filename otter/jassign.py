"""Generate student & autograder views of a notebook in okpy format."""

import copy
import json
import nbformat
import pprint
import os
import re
import shutil
import subprocess
import yaml

from collections import namedtuple

NB_VERSION = 4
BLOCK_QUOTE = "```"
COMMENT_PREFIX = "#"
TEST_HEADERS = ["TEST", "HIDDEN TEST"]
ALLOWED_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
NB_VERSION = 4


def convert_to_ok(nb_path, dir, args):
    """Convert a master notebook to an ok notebook, tests dir, and .ok file.

    nb -- Path
    endpoint -- OK endpoint for notebook submission (e.g., cal/data100/sp19)
    dir -- Path
    """
    ok_nb_path = dir / nb_path.name
    tests_dir = dir / 'tests'
    os.makedirs(tests_dir, exist_ok=True)

    # copy files
    for file in args.files:
        shutil.copy(file, str(dir))

    with open(nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    ok_cells = gen_ok_cells(nb['cells'], tests_dir)

    if not args.no_init_cell:
        init = gen_init_cell()
        nb['cells'] = [init] + ok_cells
    else:
        nb['cells'] = ok_cells

    if not args.no_check_all:
        nb['cells'] += gen_check_all_cell()
    if not args.no_export_cell:
        nb['cells'] += gen_export_cells(nb_path, args.instructions, filtering = not args.no_filter)
        
    remove_output(nb)

    with open(ok_nb_path, 'w') as f:
        nbformat.write(nb, f, NB_VERSION)
    return ok_nb_path


def gen_init_cell():
    """Generate a cell to initialize ok object."""
    cell = nbformat.v4.new_code_cell("# Initialize Otter\nimport otter\ngrader = otter.Notebook()")
    lock(cell)
    return cell


def gen_export_cells(nb_path, instruction_text, filtering=True):
    """Generate submit cells."""
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "## Submission\n\nMake sure you have run all cells in your notebook in order before \
    running the cell below, so that all images/graphs appear in the output. **Please save before submitting!**"
    
    if instruction_text:
        instructions.source += '\n\n' + instruction_text

    export = nbformat.v4.new_code_cell()
    source_lines = ["# Save your notebook first, then run this cell to export."]
    if filtering:
        source_lines.append(f"grader.export(\"{ nb_path.name }\")")
    else:
        source_lines.append(f"grader.export(\"{ nb_path.name }\", filtering=False)")
    export.source = "\n".join(source_lines)

    lock(instructions)
    lock(export)

    return [instructions, export, nbformat.v4.new_markdown_cell(" ")]     # last cell is buffer


def gen_check_all_cell():
    """Generate submit cells."""
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "To double-check your work, the cell below will rerun all of the autograder tests."

    check_all = nbformat.v4.new_code_cell("grader.check_all()")

    lock(instructions)
    lock(check_all)

    return [instructions, check_all]


def gen_ok_cells(cells, tests_dir):
    """Generate notebook cells for the OK version of a master notebook.

    Returns:
        (ok_cells, list of manual question names)
    """
    ok_cells = []
    question = {}
    processed_response = False
    tests = []
    # hidden_tests = []
    manual_questions = []
    need_close_export = False

    for cell in cells:

        # this is the prompt cell or if a manual question then the solution cell
        if question and not processed_response:
            assert not is_question_cell(cell), cell
            assert not is_test_cell(cell), cell
            # assert not is_solution_cell(cell) or is_markdown_solution_cell(cell), cell

            # # if this isn't a MD solution cell but in a manual question, it has a prompt
            # if not is_solution_cell(cell) and question.get('manual', False):
            #     md_has_prompt = True
            
            # # if there is no prompt, add a prompt cell
            # elif is_markdown_solution_cell(cell) and not md_has_prompt:
            #     ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))

            ok_cells.append(cell)
            processed_response = True

        # if this is a test cell, parse and add to correct group
        elif question and processed_response and is_test_cell(cell):
            test = read_test(cell)
            # if test.hidden:
            #     hidden_tests.append(test)
            # else:
            tests.append(test)

        # # if this is a solution cell, append. if manual question and no prompt, also append prompt cell
        # elif question and processed_response and is_solution_cell(cell):
        #     if is_markdown_solution_cell(cell) and not md_has_prompt:
        #         ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))
        #     ok_cells.append(cell)

        else:
            # the question is over
            if question and processed_response:
                if tests:
                    ok_cells.append(gen_test_cell(question, tests, tests_dir))
                # if hidden_tests:
                #     gen_test_cell(question, hidden_tests, tests_dir, hidden=True)

                # add a cell with <!-- END QUESTION --> if a manually graded question
                manual = question.get('manual', False)
                if manual:
                    # ok_cells.append(gen_close_export_cell())
                    need_close_export = True
                
                question, processed_response, tests, hidden_tests = {}, False, [], []

            if is_question_cell(cell):
                question = read_question_metadata(cell)
                manual = question.get('manual', False)
                format = question.get('format', '')
                in_manual_block = False
                if manual and need_close_export:
                    manual_questions.append(question['name'])
                    in_manual_block = True
                elif need_close_export:
                    add_close_export_to_cell(cell)
                    need_close_export = False
                ok_cells.append(gen_question_cell(cell, manual, format, in_manual_block))

            # elif is_solution_cell(cell):
            #     if is_markdown_solution_cell(cell):
            #         ok_cells.append(nbformat.v4.new_markdown_cell(MD_ANSWER_CELL_TEMPLATE))
            #     ok_cells.append(cell)

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
        ok_cells.append(gen_test_cell(question, tests, tests_dir))
    # if hidden_tests:
    #     gen_test_cell(question, hidden_tests, tests_dir, hidden=True)

    return ok_cells


def get_source(cell):
    """Get the source code of a cell in a way that works for both nbformat and json."""
    source = cell['source']
    if isinstance(source, str):
        return cell['source'].split('\n')
    elif isinstance(source, list):
        return [line.strip('\n') for line in source]
    assert 'unknown source type', type(source)


def is_question_cell(cell):
    """Whether cell contains BEGIN QUESTION in a block quote."""
    if cell['cell_type'] != 'markdown':
        return False
    return find_question_spec(get_source(cell)) is not None


def find_question_spec(source):
    """Return line number of the BEGIN QUESTION line or None."""
    block_quotes = [i for i, line in enumerate(source) if
                    line == BLOCK_QUOTE]
    assert len(block_quotes) % 2 == 0, 'cannot parse ' + str(source)
    begins = [block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) if
              source[block_quotes[i]+1].strip(' ') == 'BEGIN QUESTION']
    assert len(begins) <= 1, 'multiple questions defined in ' + str(source)
    return begins[0] if begins else None


def gen_question_cell(cell, manual, format, in_manual_block):
    """Return the cell with metadata hidden in an HTML comment."""
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    if manual and not in_manual_block:
        source = ["<!-- BEGIN QUESTION -->", ""] + source
    begin_question_line = find_question_spec(source)
    start = begin_question_line - 1
    assert source[start].strip() == BLOCK_QUOTE
    end = begin_question_line
    while source[end].strip() != BLOCK_QUOTE:
        end += 1
    source[start] = "<!--"
    source[end] = "-->"
    cell['source'] = '\n'.join(source)
    lock(cell)
    return cell


def gen_close_export_cell():
    """Returns a new cell to end question export"""
    cell = nbformat.v4.new_markdown_cell("<!-- END QUESTION -->")
    lock(cell)
    return cell


def add_close_export_to_cell(cell):
    """Adds an export close to the top of the cell"""
    source = get_source(cell)
    source = ["<!-- END QUESTION -->\n", "\n"] + source
    cell['source'] = source


def read_question_metadata(cell):
    """Return question metadata from a question cell."""
    source = get_source(cell)
    begin_question_line = find_question_spec(source)
    i, lines = begin_question_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    assert ALLOWED_NAME.match(metadata.get('name', '')), metadata
    return metadata


def is_test_cell(cell):
    """Return whether it's a code cell containing a test."""
    if cell['cell_type'] != 'code':
        return False
    source = get_source(cell)
    delimiters = COMMENT_PREFIX + ' \n'
    return source and source[0].strip(delimiters) in TEST_HEADERS


Test = namedtuple('Test', ['input', 'output', 'hidden'])


def read_test(cell):
    """Return the contents of a test as an (input, output, hidden) tuple."""
    hidden = 'HIDDEN' in get_source(cell)[0]
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
    """Write an OK test file."""
    with open(path, 'w') as f:
        f.write('test = ')
        pprint.pprint(test, f, indent=4, width=200, depth=None)


def gen_test_cell(question, tests, tests_dir):
    """Return a test cell."""
    cell = nbformat.v4.new_code_cell()
    # if hidden:
    #     cell.source = ['grader.check("{}")'.format(question['name'] + "H")]
    # else:
    cell.source = ['grader.check("{}")'.format(question['name'])]
    suites = [gen_suite(tests)]

    # # if both keys, use those values
    # if 'public_points' in question and 'private_points' in question:
    #     if hidden:
    #         points = question['private_points']
    #     else:
    #         points = question['public_points']

    # # if only public points, assume public & private worth same
    # elif 'public_points' in question:
    #     points = question['public_points']

    # # if only private, assume public worth 0 points
    # elif 'private_points' in question:
    #     if hidden:
    #         points = question['private_points']
    #     else:
    #         points = 0

    # # else get points and default to 1 if not presnet
    # else:
    points = question.get('points', 1)
    
    test = {
        'name': question['name'],
        'points': points,
        # 'hidden': hidden,
        'suites': suites,
    }
    # if hidden:
    #     write_test(tests_dir / (question['name'] + "H" + '.py'), test)
    # else:
    write_test(tests_dir / (question['name'] + '.py'), test)
    lock(cell)
    return cell


def gen_suite(tests):
    """Generate an ok test suite for a test."""
    cases = [gen_case(test) for test in tests]
    return  {
      'cases': cases,
      'scored': True,
      'setup': '',
      'teardown': '',
      'type': 'doctest'
    }


def gen_case(test):
    """Generate an ok test case for a test."""
    # TODO(denero) This should involve a Python parser, but it doesn't...
    code_lines = []
    last_end_escape = False
    for line in test.input.split('\n'):
        if re.match(r"\s", line) or last_end_escape:
            code_lines.append('... ' + line)
        else:
            code_lines.append('>>> ' + line)
        last_end_escape = line.endswith("\\")
    # Suppress intermediate output from evaluation
    for i in range(len(code_lines) - 1):
        if code_lines[i+1].startswith('>>>') and len(code_lines[i].strip()) > 3 and not code_lines[i].endswith("\\"):
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
    # sol = match.group(2)
    return prefix + ' ...'


solution_line_re = re.compile('(\\s*)([^#\n]+) #[ ]?SOLUTION')
def solution_line_sub(match):
    prefix = match.group(1)
    return prefix + '...'


text_solution_line_re = re.compile(r'\s*\*\*SOLUTION:?\*\*:?.*')
begin_solution_re = re.compile(r'(\s*)# BEGIN SOLUTION( NO PROMPT)?')
skip_suffixes = ['# SOLUTION NO PROMPT', '# BEGIN PROMPT', '# END PROMPT']


SUBSTITUTIONS = [
    (solution_assignment_re, solution_assignment_sub),
    (solution_line_re, solution_line_sub),
]


def replace_solutions(lines):
    """Replace solutions in lines, a list of strings."""
    if text_solution_line_re.match(lines[0]):
        return ['*Write your answer here, replacing this text.*']
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
    """Write a notebook with solutions stripped."""
    with open(original_nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    for cell in nb['cells']:
        cell['source'] = '\n'.join(replace_solutions(get_source(cell)))
    with open(stripped_nb_path, 'w') as f:
        nbformat.write(nb, f, NB_VERSION)


def remove_output(nb):
    """Remove all outputs."""
    for cell in nb['cells']:
        if 'outputs' in cell:
            cell['outputs'] = []


def lock(cell):
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False


def remove_hidden_tests(test_dir):
    """Rewrite test files to remove hidden tests."""
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

    master_nb -- Dict of master notebook JSON
    result_dir -- Path to the result directory
    """
    autograder_dir = result_dir / 'autograder'
    student_dir = result_dir / 'student'
    os.makedirs(autograder_dir, exist_ok=True)
    ok_nb_path = convert_to_ok(master_nb, autograder_dir, args)
    shutil.rmtree(student_dir, ignore_errors=True)
    shutil.copytree(autograder_dir, student_dir)
    student_nb_path = student_dir / ok_nb_path.name
    os.remove(student_nb_path)
    strip_solutions(ok_nb_path, student_nb_path)
    remove_hidden_tests(student_dir / 'tests')
