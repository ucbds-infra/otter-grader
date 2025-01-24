"""Master notebook transformer for Otter Assign"""

import copy
import fica
import nbformat as nbf
import pathlib

from typing import Union

from .assignment import Assignment
from .blocks import BlockType, get_cell_config, is_assignment_config_cell, is_block_boundary_cell
from .cell_factory import CellFactory
from .feature_toggle import FeatureToggle
from .plugins import replace_plugins_with_calls
from .question_config import QuestionConfig
from .r_adapter import rmarkdown_converter
from .r_adapter.cell_factory import RCellFactory
from .solutions import (
    ANSWER_CELL_TAG,
    has_seed,
    overwrite_seed_vars,
    SOLUTION_CELL_TAG,
    strip_ignored_lines,
    strip_solutions_and_output,
)
from .tests_manager import AssignmentTestsManager
from .utils import (
    add_tag,
    AssignNotebookFormatException,
    is_cell_type,
    is_ignore_cell,
    lock,
    remove_cell_ids_if_applicable,
)
from ..nbmeta_config import NBMetadataConfig
from ..utils import get_source, NOTEBOOK_METADATA_KEY


class NotebookTransformer:
    """
    A transformer for master notebooks that converts them to autograder- and
    student-formatted notebooks.

    A note on terminology: An *autograder-formatted* notebook is the same as the master notebook but
    with all metadata and structural cells removed, and cells that set up and use Otter's client
    package (e.g. init cells, check cells, etc.) added. A *student-formatted* notebook is the same
    as an autograder-formatted notebook but has had its solutions and hidden tests stripped. (The
    conversion from an autograder-formatted notebook to a student-formatted notebook is not actually
    handled in this class but in the TransformedNotebookContainer class.)

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
        tests_mgr (``otter.assign.tests_manager.AssignmentTestsManager``): the tests manager to
            populate
    """

    assignment: Assignment
    """the assignment config"""

    cell_factory: CellFactory
    """a factory for various kinds of cells for using Otter's client package"""

    tests_mgr: AssignmentTestsManager
    """the tests manager to populate"""

    def __init__(self, assignment: Assignment, tests_mgr: AssignmentTestsManager):
        self.assignment = assignment
        self.cell_factory = (RCellFactory if self.assignment.is_r else CellFactory)(self.assignment)
        self.tests_mgr = tests_mgr

    def add_export_tag_to_cell(self, cell: nbf.NotebookNode, end: bool = False) -> nbf.NotebookNode:
        """
        Add an HTML comment to open or close question export for PDF filtering to the top of
        ``cell``. ``cell`` should be a Markdown cell.

        Args:
            cell (``nbformat.NotebookNode``): the cell to add the close export to

        Returns:
            ``nbformat.NotebookNode``: a copy of ``cell`` with the close export comment at the top
        """
        if not FeatureToggle.PDF_FILTERING_COMMENTS.value.is_enabled(self.assignment):
            return cell

        cell = copy.deepcopy(cell)
        source = get_source(cell)
        tag = "<!-- " + ("END" if end else "BEGIN") + " QUESTION -->"
        source = [tag, ""] + source
        cell["source"] = "\n".join(source)
        lock(cell)
        return cell

    @staticmethod
    def add_point_value_info_to_cell(
        cell: nbf.NotebookNode,
        points: Union[int, float],
    ) -> nbf.NotebookNode:
        """
        Add the point value information to the provided cell, returning a copy.

        Args:
            cell (``nbformat.NotebookNode``): the cell to add to
            points (``int | float``): the point value of the question

        Returns:
            ``nbformat.NotebookNode``: a copy of ``cell`` with the point value
        """
        cell = copy.deepcopy(cell)
        source = get_source(cell)
        source.extend(["", f"_Points:_ {points}"])
        cell["source"] = "\n".join(source)
        return cell

    def transform_notebook(self, nb: nbf.NotebookNode) -> "TransformedNotebookContainer":
        """
        Transform a master notebook into an autograder-formatted notebook.

        Args:
            nb (``nbformat.NotebookNode``): the master notebook

        Returns:
            ``TransformedNotebookContainer``: the autograder-formatted notebook
        """
        transformed_cells = self._get_transformed_cells(nb["cells"])

        if self.assignment.init_cell:
            transformed_cells = self.cell_factory.create_init_cells() + transformed_cells

        if self.assignment.check_all_cell:
            transformed_cells += self.cell_factory.create_check_all_cells()

        if self.assignment.export_cell:
            transformed_cells += self.cell_factory.create_export_cells()

        transformed_nb = copy.deepcopy(nb)
        transformed_nb["cells"] = transformed_cells

        # replace plugins
        transformed_nb = replace_plugins_with_calls(transformed_nb)

        # strip out ignored lines
        transformed_nb = strip_ignored_lines(transformed_nb)

        remove_cell_ids_if_applicable(transformed_nb)

        return TransformedNotebookContainer(transformed_nb, self)

    def _get_transformed_cells(self, cells: list[nbf.NotebookNode]) -> list[nbf.NotebookNode]:
        """
        Takes in a list of cells from the master notebook and returns a list of cells for the
        autograder notebook.

        Args:
            cells (``list[nbf.NotebookNode]``): the cells of the master notebook

        Returns:
            ``list[nbf.NotebookNode]``: the cells of the autograder notebook
        """
        curr_block: list[BlockType] = []  # allow nested blocks
        transformed_cells: list[nbf.NotebookNode] = []

        question, has_prompt, no_solution, last_question_md_cell = None, False, False, None

        solution_has_md_cells, prompt_insertion_index = False, None

        need_begin_export, need_end_export = False, False

        for i, cell in enumerate(cells):
            if is_ignore_cell(cell):
                continue

            # check for assignment config
            if is_assignment_config_cell(cell):
                config = get_cell_config(cell)
                if config.get("config_file"):
                    self.assignment.load_config_file(config["config_file"])
                self.assignment.update(config)
                if self.assignment.runs_on == "colab" and not self.assignment.tests.files:
                    raise ValueError(
                        "notebooks that run on Colab must use test files and not notebook metadata tests"
                    )
                continue

            # check for an end to the current block
            if len(curr_block) > 0 and is_block_boundary_cell(cell, curr_block[-1], end=True):
                block_type = curr_block.pop()  # remove the block

                if block_type is BlockType.QUESTION:

                    if question.manual or question.export:
                        need_end_export = True

                    # generate a check cell if necessary
                    if self.tests_mgr.has_tests(question):
                        check_cells = self.cell_factory.create_check_cells(question)

                        # only add to notebook if there's a response cell or if there are public tests;
                        # don't add cell if the 'check_cell' key of question is false
                        if (
                            not no_solution or self.tests_mgr.any_public_tests(question)
                        ) and question.check_cell:
                            transformed_cells.extend(check_cells)
                        else:
                            last_cell_meta = transformed_cells[-1]["metadata"]
                            last_cell_meta.setdefault(NOTEBOOK_METADATA_KEY, {})
                            last_cell_meta[NOTEBOOK_METADATA_KEY]["tests"] = [question.name]

                    # add points to question cell if specified
                    if self.assignment.show_question_points and last_question_md_cell is not None:
                        points = self.tests_mgr.determine_question_point_value(question)
                        transformed_cells[last_question_md_cell] = (
                            self.add_point_value_info_to_cell(
                                transformed_cells[last_question_md_cell], points
                            )
                        )

                    question, has_prompt, no_solution, last_question_md_cell = (
                        None,
                        False,
                        False,
                        None,
                    )
                    solution_has_md_cells, prompt_insertion_index = False, None

                elif block_type is BlockType.SOLUTION:
                    if not has_prompt and solution_has_md_cells and question.manual:
                        if prompt_insertion_index is None:
                            raise RuntimeError("Could not find prompt insertion index")
                        transformed_cells.insert(
                            prompt_insertion_index, CellFactory.create_markdown_response_cell()
                        )
                        has_prompt = True

                continue  # if this is an end to the last nested block, we're OK

            # check for invalid block ends
            for block_type in BlockType:
                if is_block_boundary_cell(cell, block_type, end=True):

                    # if a child is missing an end block cell, raise an error
                    if block_type in curr_block:
                        raise AssignNotebookFormatException(
                            f"Found an end {block_type.value} cell with an un-ended child "
                            + f"{curr_block[-1].value} block",
                            question,
                            i,
                        )

                    # otherwise raise an error for an end with no begin
                    else:
                        raise AssignNotebookFormatException(
                            f"Found an end {block_type.value} cell with no begin block cell",
                            question,
                            i,
                        )

            # check for begin blocks
            found_begin = False
            for block_type in BlockType:
                if is_block_boundary_cell(cell, block_type):
                    found_begin = True
                    break

            if found_begin:
                if len(curr_block) == 0 and block_type is not BlockType.QUESTION:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell outside a question", question, i
                    )
                elif len(curr_block) > 0 and block_type is BlockType.QUESTION:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell inside another question",
                        question,
                        i,
                    )
                elif len(curr_block) > 1:
                    raise AssignNotebookFormatException(
                        f"Found a begin {block_type.value} cell inside a {curr_block[-1].value} "
                        "block",
                        question,
                        i,
                    )
                elif block_type is BlockType.PROMPT and has_prompt:
                    # has_prompt was set by the solution block
                    raise AssignNotebookFormatException(
                        "Found a prompt block after a solution block", question, i
                    )

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
                            "Found a begin question cell with no config", None, i
                        )

                    question = QuestionConfig(question_config)
                    self.tests_mgr.add_question(question)
                    if question.manual or question.export:
                        need_begin_export = True

                curr_block.append(block_type)
                continue

            # if in a block, process the current cell
            if len(curr_block) > 0:
                if curr_block[-1] == BlockType.TESTS:
                    if not is_cell_type(cell, "code"):
                        raise AssignNotebookFormatException(
                            "Found a non-code cell in tests block", question, i
                        )
                    self.tests_mgr.read_test(cell, question)
                    continue

                elif curr_block[-1] == BlockType.PROMPT:
                    cell = add_tag(cell, ANSWER_CELL_TAG)

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
                elif FeatureToggle.PDF_FILTERING_COMMENTS.value.is_enabled(self.assignment):
                    export_delim_cell = nbf.v4.new_markdown_cell()
                    export_delim_cell = self.add_export_tag_to_cell(export_delim_cell)
                need_begin_export = False
            if need_end_export:
                if is_cell_type(cell, "markdown"):
                    cell = self.add_export_tag_to_cell(cell, end=True)
                elif FeatureToggle.PDF_FILTERING_COMMENTS.value.is_enabled(self.assignment):
                    if export_delim_cell is None:
                        export_delim_cell = nbf.v4.new_markdown_cell()
                    export_delim_cell = self.add_export_tag_to_cell(export_delim_cell, end=True)
                need_end_export = False

            if export_delim_cell is not None:
                transformed_cells.append(export_delim_cell)

            if has_seed(cell):
                self.assignment.seed_required = True

            # if this cell is part of the question text, lock it
            if len(curr_block) == 1:
                lock(cell)

            # this is just a normal cell so add it to transformed_cells
            transformed_cells.append(cell)

        # if the last cell was the end of a manually-graded question, add a close export tag
        if need_end_export:
            transformed_cells.append(
                self.add_export_tag_to_cell(nbf.v4.new_markdown_cell(), end=True)
            )

        return transformed_cells


class TransformedNotebookContainer:
    """
    A container for the autograder notebook returned by ``NotebookTransformer.transform_notebook``
    that contains logic for writing the notebook file (both autograder and student versions) and
    the test files.

    Args:
        transformed_nb (``nbformat.NotebookNode``): the autograder notebook
        nb_transformer (``NotebookTransformer``): the notebook transformer used to create
            ``transformed_nb``
    """

    transformed_nb: nbf.NotebookNode
    """the autograder notebook"""

    nb_transformer: NotebookTransformer
    """the notebook transformer used to create ``transformed_nb``"""

    nbmeta_config: NBMetadataConfig
    """the notebook metadata config to include when writing the notebook"""

    def __init__(self, transformed_nb: nbf.NotebookNode, nb_transformer: NotebookTransformer):
        self.transformed_nb = transformed_nb
        self.nb_transformer = nb_transformer

        # populate NBMetadataConfig
        self.nbmeta_config = NBMetadataConfig({})
        if self.assignment.name:
            self.nbmeta_config.assignment_name = self.assignment.name
        if self.assignment.export_cell and self.assignment.export_cell.require_no_pdf_ack:
            self.nbmeta_config.require_no_pdf_confirmation = True
            if isinstance(self.assignment.export_cell.require_no_pdf_ack, fica.Config):
                self.nbmeta_config.export_pdf_failure_message = (
                    self.assignment.export_cell.require_no_pdf_ack.message
                )

    @property
    def assignment(self) -> Assignment:
        """the assignment config for this notebook"""
        return self.nb_transformer.assignment

    def _get_sanitized_nb(self) -> nbf.NotebookNode:
        """
        Return a copy of ``self.transformed_nb`` with solutions and outputs stripped and seed
        variables replaced.

        Returns:
            ``nbformat.NotebookNode``: the student notebook
        """
        nb = strip_solutions_and_output(self.assignment, self.transformed_nb)
        if self.nb_transformer.assignment.seed.variable:
            nb = overwrite_seed_vars(
                nb,
                self.nb_transformer.assignment.seed.variable,
                self.nb_transformer.assignment.seed.student_value,
            )
        return nb

    def _add_nbmeta_config(self, nb: nbf.NotebookNode):
        """
        Add the notebook metadata config to the provided notebook's metadata in-place.
        """
        uc = self.nbmeta_config.get_user_config()
        if uc:
            nb["metadata"][NOTEBOOK_METADATA_KEY] = uc

    def write_transformed_nb(self, output_path: Union[pathlib.Path, str], sanitize: bool):
        """
        Write the transformed notebook (either as an autograder or student notebook) to the
        specified file, converting to R Markdown if necessary.

        Args:
            output_path (``pathlib.Path | str``): the path at which to write the notebook
            sanitize (``bool``): whether to sanitize the notebook (i.e. write the student version)
        """
        nb = self._get_sanitized_nb() if sanitize else self.transformed_nb
        self._add_nbmeta_config(nb)

        if self.nb_transformer.assignment.is_rmd:
            rmarkdown_converter.write_as_rmd(nb, str(output_path), not sanitize)

        else:
            try:
                from nbformat.validator import normalize
            except ImportError:
                normalize = lambda nb: (0, nb)

            _, nb = normalize(nb)
            nbf.write(nb, str(output_path))

    def write_tests(
        self,
        tests_dir: Union[pathlib.Path, str, None],
        include_hidden: bool,
        force_files: bool,
    ):
        """
        Write the tests, either to the notebook metadata or files in ``tests_dir`` as indicated by
        the assignment config.

        Args:
            tests_dir (``pathlib.Path | str | None``): the path to the directory of tests, if any
            include_hidden (``bool``): whether to include hidden test cases
            force_files (``bool``): whether to force writing the tests as files (overriding the
                assignment config)
        """
        self.nb_transformer.tests_mgr.write_tests(
            self.nbmeta_config,
            tests_dir,
            include_hidden=include_hidden,
            force_files=force_files,
        )
