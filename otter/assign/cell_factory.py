"""Miscellaneous cell generators for Otter Assign"""

import nbformat

from textwrap import dedent

from .assignment import Assignment
from .constants import MD_RESPONSE_CELL_SOURCE
from .feature_toggle import FeatureToggle
from .utils import lock


# TODO: update docstrings
class CellFactory:
    """
    Attributes:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """

    assignment: Assignment

    def __init__(self, assignment):
        self.assignment = assignment

    def check_feature_toggle(self, feature_toggle: FeatureToggle):
        return feature_toggle.value.is_enabled(self.assignment)

    def create_init_cells(self):
        """
        Generates a cell to initialize Otter in the notebook.

        Returns:
            ``list[nbformat.NotebookNode]``: the init cell
        """
        if self.assignment.runs_on == "colab":
            args = "colab=True"
        elif self.assignment.runs_on == "jupyterlite":
            args = "jupyterlite=True"
        else:
            args  = f"\"{self.assignment.master.name}\""

        if self.assignment.tests.url_prefix:
            args += f", tests_url_prefix=\"{self.assignment.tests.url_prefix}\""

        contents = f'# Initialize Otter\nimport otter\ngrader = otter.Notebook({args})'
        cell = nbformat.v4.new_code_cell(contents)
        lock(cell)
        return [cell]

    def create_check_cells(self, question):
        """
        Parses a list of test named tuples and creates a single test file. Adds this test file as a value
        to ``tests_dict`` with a key corresponding to the test's name, taken from ``question``. Returns
        a code cell that runs the check on this test.
        
        Args:
            question (``dict``): question metadata
            tests (``list`` of ``Test``): tests to be written
            tests_dict (``dict``): the tests for this assignment
            assignment (``otter.assign.assignment.Assignment``): the assignment configurations

        Returns:
            ``nbformat.NotebookNode``: code cell calling ``otter.Notebook.check`` on this test
        """
        cell = nbformat.v4.new_code_cell()
        cell.source = ['grader.check("{}")'.format(question.name)]
        lock(cell)
        return [cell]

    def create_check_all_cells(self):
        """
        Generates a check-all cell and a Markdown cell with instructions to run all tests in the
        notebook. The Markdown cell has the following contents:

        .. code-block:: markdown

            ---
            
            To double-check your work, the cell below will rerun all of the autograder tests.

        The code cell has the following contents:

        .. code-block:: python

            grader.check_all()
        
        Returns:
            ``list`` of ``nbformat.NotebookNode``: generated check-all cells
        """
        instructions = nbformat.v4.new_markdown_cell()
        instructions.source = "---\n\nTo double-check your work, the cell below will rerun all " \
            "of the autograder tests."

        check_all = nbformat.v4.new_code_cell("grader.check_all()")

        lock(instructions)
        lock(check_all)

        return [instructions, check_all]

    def _get_export_cell_config(self):
        export_cell_config = self.assignment.export_cell
        if export_cell_config is True:
            export_cell_config = {}
        return export_cell_config

    def create_export_cells(self):
        """
        Generates export cells that instruct the student the run a code cell calling 
        ``otter.Notebook.export`` to generate and download their submission. The Markdown cell
        contains:

        .. code-block:: markdown

            ## Submission
            
            Make sure you have run all cells in your notebook in order before running the cell
            below, so that all images/graphs appear in the output. The cell below will generate a 
            zip file for you to submit. **Please save before exporting!**

        Additional instructions can be appended to this cell by passing a string to
        ``instruction_text``.

        The code cell contains:

        .. code-block:: python

            # Save your notebook first, then run this cell to export your submission.
            grader.export()
        
        The call to ``grader.export()`` contains different arguments based on the values passed to
        ``pdf`` and ``filtering``. 
        
        Args:
            instruction_text (``str``): extra instructions for students when exporting
            pdf (``bool``, optional): whether a PDF is needed
            filtering (``bool``, optional): whether PDF filtering is needed
            force_save (``bool``, optional): whether or not to set the ``force_save`` argument of 
                ``otter.Notebook.export`` to ``True``
            run_tests (``bool``, optional): whether to set the ``run_tests`` argument of 
                ``otter.Notebook.export`` to ``True``
        
        Returns:
            ``list`` of ``nbformat.NotebookNode``: generated export cells
        """
        export_cell_config = self._get_export_cell_config()

        instructions = nbformat.v4.new_markdown_cell()
        instructions.source = "## Submission\n\nMake sure you have run all cells in your " \
            "notebook in order before running the cell below, so that all images/graphs appear " \
            "in the output. The cell below will generate a zip file for you to submit."

        force_save = export_cell_config.get("force_save", False)

        # only include save text if force_save is false
        if not force_save:
            instructions.source += " **Please save before exporting!**"
        
        if export_cell_config.get("instructions", ""):
            instructions.source += '\n\n' + export_cell_config["instructions"]

        export = nbformat.v4.new_code_cell()
        source_lines = []

        # only include save text if force_save is false
        if not force_save:
            source_lines.append(
                "# Save your notebook first, then run this cell to export your submission.")

        args = []
        if not export_cell_config.get("filtering", True):
            args += ["filtering=False"]
        if not export_cell_config.get("pdf", True):
            args += ["pdf=False"]
        if force_save:
            args += ["force_save=True"]
        if export_cell_config.get("run_tests", False):
            args += ["run_tests=True"]

        source_lines.append(f"grader.export({', '.join(args)})")
        export.source = "\n".join(source_lines)

        lock(instructions)
        lock(export)

        cells = [instructions, export]
        if self.check_feature_toggle(FeatureToggle.EMPTY_MD_BOUNDARY_CELLS):
            cells.append(nbformat.v4.new_markdown_cell(" "))  # add buffer cell

        return cells

    @staticmethod
    def create_markdown_response_cell():
        """
        Generates a Markdown response cell with the following contents:

        .. code-block:: markdown

            _Type your answer here, replacing this text._

        Note that, unlike the other methods, this method returns a single cell rather than a list of
        cells.

        Returns:
            ``nbformat.NotebookNode``: the response cell
        """
        return nbformat.v4.new_markdown_cell(MD_RESPONSE_CELL_SOURCE)
