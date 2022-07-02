"""Master notebook transformer for Otter Assign"""

import copy
import nbformat

from typing import Optional

from .assignment import Assignment
from .blocks import BlockType, get_cell_config, is_assignment_config_cell, is_block_boundary_cell
from .cell_factory import CellFactory
from .feature_toggle import FeatureToggle
from .plugins import replace_plugins_with_calls
from .question_config import QuestionConfig
from .r_adapter import rmarkdown_converter
from .r_adapter.cell_factory import RCellFactory
from .solutions import has_seed, SOLUTION_CELL_TAG, overwrite_seed_vars, strip_ignored_lines, \
    strip_solutions_and_output
from .tests_manager import AssignmentTestsManager
from .utils import add_tag, AssignNotebookFormatException, get_source, is_cell_type, \
    is_ignore_cell, remove_cell_ids


# TODO: docstrings
class NotebookTransformer:

    assignment: Assignment

    cell_factory: CellFactory

    tests_mgr: AssignmentTestsManager

    transformed_nb: Optional[nbformat.NotebookNode]

    def __init__(self, assignment, tests_mgr):
        self.assignment = assignment
        self.cell_factory = (RCellFactory if self.assignment.is_r else CellFactory)(self.assignment)
        self.tests_mgr = tests_mgr

    def add_export_tag_to_cell(self, cell, end=False):
        """
        Adds an HTML comment to open or close question export for PDF filtering to the top of
        ``cell``. ``cell`` should be a Markdown cell.

        Args:
            cell (``nbformat.NotebookNode``): the cell to add the close export to

        Returns:
            ``nbformat.NotebookNode``: the cell with the close export comment at the top
        """
        if not FeatureToggle.PDF_FILTERING_COMMENTS.value.is_enabled(self.assignment):
            return cell

        cell = copy.deepcopy(cell)
        source = get_source(cell)
        tag = "<!-- " + ("END" if end else "BEGIN") + " QUESTION -->"
        source = [tag, ""] + source
        cell['source'] = "\n".join(source)
        return cell

    @staticmethod
    def add_point_value_info_to_cell(cell, points):
        """
        Adds the point value information to the provided cell, returning a copy.
        """
        cell = copy.deepcopy(cell)
        source = get_source(cell)
        source.extend(["", f"_Points:_ {points}"])
        cell["source"] = "\n".join(source)
        return cell

    def transform_notebook(self, nb):
        """
        Converts a master notebook to an Otter-formatted solutions notebook, parsing test cells into
        dictionaries ready to be written as OK test files.

        Args:
            nb (``nbformat.NotebookNode``): the master notebook

        Returns:
            ``tuple[nbformat.NotebookNode, dict]``: the transformed notebook and a dictionary
            mapping test names to their parsed contents
        """
        transformed_cells, test_files = self._get_transformed_cells(nb['cells'])

        if self.assignment.init_cell:
            transformed_cells = self.cell_factory.create_init_cells() + transformed_cells

        if self.assignment.check_all_cell:
            transformed_cells += self.cell_factory.create_check_all_cells()

        if self.assignment.export_cell:
            export_cell = self.assignment.export_cell
            if export_cell is True:
                export_cell = {}

            transformed_cells += self.cell_factory.create_export_cells()

        transformed_nb = copy.deepcopy(nb)
        transformed_nb['cells'] = transformed_cells

        # replace plugins
        transformed_nb = replace_plugins_with_calls(transformed_nb)

        # strip out ignored lines
        transformed_nb = strip_ignored_lines(transformed_nb)

        # TODO: this is a bad practice and only a monkey-patch for #340. we should do some better parsing
        # of the nbformat version info to determine if this is necessary.
        remove_cell_ids(transformed_nb)

        self.transformed_nb = transformed_nb

        return transformed_nb, test_files

    def _get_sanitized_nb(self):
        """
        """
        nb = strip_solutions_and_output(self.transformed_nb)
        if self.assignment.seed.variable:
            nb = overwrite_seed_vars(nb, self.assignment.seed.variable, self.assignment.seed.student_value)
        return nb

    def write_transformed_nb(self, output_path, sanitize):
        """
        """
        nb = self._get_sanitized_nb() if sanitize else self.transformed_nb
        if self.assignment.is_rmd:
            rmarkdown_converter.write_as_rmd(nb, str(output_path), not sanitize)
        else:
            nbformat.write(nb, str(output_path))

    def write_tests(self, tests_dir, include_hidden, force_files):
        """
        """
        self.tests_mgr.write_tests(self.transformed_nb, tests_dir, include_hidden=include_hidden, force_files=force_files)

    def _get_transformed_cells(self, cells):
        """
        Takes in a list of cells from the master notebook and returns a list of cells for the '
        solutions notebook. 

        Replaces test cells with a cell calling ``otter.Notebook.check``, inserts Markdown
        response cells for manual questions with Markdown solutions, and comments out question
        metadata in question cells, among other things.

        Args:
            cells (``list[nbformat.NotebookNode]``): original code cells
            assignment (``otter.assign.assignment.Assignment``): the assignment configurations

        Returns:
            ``tuple[list, dict]``: list of cleaned notebook cells and a dictionary mapping test
            names to their parsed contents
        """
        # if self.assignment.is_r:
        #     from otter.assign.r_adapter.tests import read_test, gen_test_cell
        # else:
        #     from otter.assign.tests import read_test, gen_test_cell

        curr_block = []  # allow nested blocks
        transformed_cells = []

        question, has_prompt, no_solution, last_question_md_cell = None, False, False, None

        solution_has_md_cells, prompt_insertion_index = False, None

        need_begin_export, need_end_export = False, False

        for i, cell in enumerate(cells):
            if is_ignore_cell(cell):
                continue

            # check for assignment config
            if is_assignment_config_cell(cell):
                self.assignment.update_(get_cell_config(cell))
                continue

            # check for an end to the current block
            if len(curr_block) > 0 and is_block_boundary_cell(cell, curr_block[-1], end=True):
                block_type = curr_block.pop()  # remove the block

                if block_type is BlockType.QUESTION:

                    if question.manual or question.export:
                        need_end_export = True

                    # generate a check cell
                    check_cells = self.cell_factory.create_check_cells(question)

                    # only add to notebook if there's a response cell or if there are public tests;
                    # don't add cell if the 'check_cell' key of question is false
                    if (not no_solution or self.tests_mgr.any_public_tests(question)) and \
                            question.check_cell:
                        transformed_cells.extend(check_cells)

                    # add points to question cell if specified
                    if self.assignment.show_question_points and last_question_md_cell is not None:
                        points = self.tests_mgr.determine_question_point_value(question)
                        transformed_cells[last_question_md_cell] = \
                            self.add_point_value_info_to_cell(
                                transformed_cells[last_question_md_cell], points)

                    question, has_prompt, no_solution, last_question_md_cell = \
                        None, False, False, None
                    solution_has_md_cells, prompt_insertion_index = False, None

                elif block_type is BlockType.SOLUTION:
                    if not has_prompt and solution_has_md_cells:
                        if prompt_insertion_index is None:
                            raise RuntimeError("Could not find prompt insertion index")
                        transformed_cells.insert(
                            prompt_insertion_index, CellFactory.create_markdown_response_cell())
                        has_prompt = True

                continue  # if this is an end to the last nested block, we're OK

            # check for invalid block ends
            for block_type in BlockType:
                if is_block_boundary_cell(cell, block_type, end=True):

                    # if a child is missing an end block cell, raise an error
                    if block_type in curr_block:
                        raise AssignNotebookFormatException(
                            f"Found an end {block_type.value} cell with an un-ended child " + \
                                f"{curr_block[-1].value} block", question, i)

                    # otherwise raise an error for an end with no begin
                    else:
                        raise AssignNotebookFormatException(
                            f"Found an end {block_type.value} cell with no begin block cell",
                            question, i)

            # check for begin blocks
            found_begin = False
            for block_type in BlockType:
                if is_block_boundary_cell(cell, block_type):
                    found_begin = True
                    break

            if found_begin:
                if len(curr_block) == 0 and block_type is not BlockType.QUESTION:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell outside a question", 
                        question, i)
                elif len(curr_block) > 0 and block_type is BlockType.QUESTION:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell inside another question", 
                        question, i)
                elif len(curr_block) > 1:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell inside a {curr_block[-1].value} " \
                            "block", question, i)
                elif block_type is BlockType.PROMPT and has_prompt:
                    # has_prompt was set by the solution block
                    raise AssignNotebookFormatException(
                        "Found a prompt block after a solution block", question, i)

                # if not an invalid begin cell, update state
                if block_type is BlockType.PROMPT:
                    has_prompt = True

                elif block_type is BlockType.SOLUTION and not has_prompt:
                    prompt_insertion_index = len(transformed_cells)

                elif block_type is BlockType.TESTS and not has_prompt:
                    no_solution = True

                elif block_type is BlockType.QUESTION:
                    question_config = get_cell_config(cell)
                    if not isinstance(question_config, dict):
                        raise AssignNotebookFormatException(
                            "Found a begin question cell with no config", None, i)

                    question = QuestionConfig(question_config)
                    if question.manual or question.export:
                        need_begin_export = True

                curr_block.append(block_type)
                continue

            # if in a block, process the current cell
            if len(curr_block) > 0:
                if curr_block[-1] == BlockType.TESTS:
                    if not is_cell_type(cell, "code"):
                        raise AssignNotebookFormatException(
                            "Found a non-code cell in tests block", question, i)
                    self.tests_mgr.read_test(cell, question, self.assignment)
                    continue

                elif curr_block[-1] == BlockType.SOLUTION:
                    cell = add_tag(cell, SOLUTION_CELL_TAG)

                    if is_cell_type(cell, "markdown"):
                        solution_has_md_cells = True

                elif curr_block[-1] == BlockType.QUESTION and is_cell_type(cell, "markdown"):
                    last_question_md_cell = len(transformed_cells)

            # add export tags if needed
            export_delim_cell = None
            if need_begin_export:
                if is_cell_type(cell, "markdown"):
                    cell = self.add_export_tag_to_cell(cell)
                else:
                    export_delim_cell = nbformat.v4.new_markdown_cell()
                    export_delim_cell = self.add_export_tag_to_cell(export_delim_cell)
                need_begin_export = False
            if need_end_export:
                if is_cell_type(cell, "markdown"):
                    cell = self.add_export_tag_to_cell(cell, end=True)
                else:
                    if export_delim_cell is None:
                        export_delim_cell = nbformat.v4.new_markdown_cell()
                    export_delim_cell = self.add_export_tag_to_cell(export_delim_cell, end=True)
                need_end_export = False

            if export_delim_cell is not None:
                transformed_cells.append(export_delim_cell)

            if has_seed(cell):
                self.assignment.seed_required = True

            # this is just a normal cell so add it to transformed_cells
            transformed_cells.append(cell)

        # if the last cell was the end of a manually-graded question, add a close export tag
        if need_end_export:
            transformed_cells.append(
                self.add_export_tag_to_cell(nbformat.v4.new_markdown_cell(), end=True))

        return transformed_cells
