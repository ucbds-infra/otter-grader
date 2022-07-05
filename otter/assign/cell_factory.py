"""Cell factory for Otter Assign"""

import nbformat

from .assignment import Assignment
from .constants import MD_RESPONSE_CELL_SOURCE
from .feature_toggle import FeatureToggle
from .utils import lock


class CellFactory:
    """
    A factory for cells that make use of Otter's client package (e.g. init cell, check cell).

    All (non-static cell-generating) methods in this factory should return a
    ``list[nbformat.NotebookNode]``.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """

    assignment: Assignment
    """the assignment config"""

    def __init__(self, assignment):
        self.assignment = assignment

    def check_feature_toggle(self, feature_toggle: FeatureToggle):
        """
        Check whether the specified feature is enabled for this assignment.

        Args:
            feature_toggle (``otter.assign.feature_toggle.FeatureToggle``): the feature

        Returns:
            ``bool``: whether the feature is enabled
        """
        return feature_toggle.value.is_enabled(self.assignment)

    def create_init_cells(self):
        """
        Generate a cell to initialize Otter in the notebook.

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
        Create a cell calling ``otter.Notebook.check`` for the specified question.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``list[nbformat.NotebookNode]``: the check cell
        """
        cell = nbformat.v4.new_code_cell()
        cell.source = ['grader.check("{}")'.format(question.name)]
        lock(cell)
        return [cell]

    def create_check_all_cells(self):
        """
        Generate a check-all cell and a Markdown cell with instructions to run all tests in the
        notebook.

        Returns:
            ``list[nbformat.NotebookNode]``: the check-all cells
        """
        instructions = nbformat.v4.new_markdown_cell()
        instructions.source = "---\n\nTo double-check your work, the cell below will rerun all " \
            "of the autograder tests."

        check_all = nbformat.v4.new_code_cell("grader.check_all()")

        lock(instructions)
        lock(check_all)

        return [instructions, check_all]

    def _get_export_cell_config(self):
        """
        Get the configurations from ``self.assignment`` for the export cell, coercing ``True`` to
        an empty ``dict`` if necessary.

        Returns:
            ``bool | dict``: the configurations dict or ``False`` if the configuration is specified
                as ``False``
        """
        export_cell_config = self.assignment.export_cell
        if export_cell_config is True:
            export_cell_config = {}
        return export_cell_config

    def create_export_cells(self):
        """
        Generate export cells that instruct the student the run a code cell calling 
        ``otter.Notebook.export`` to generate and download their submission.

        Returns:
            ``list[nbformat.NotebookNode]``: the export cells
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
        Generate a Markdown response cell with the following contents:

        .. code-block:: markdown

            _Type your answer here, replacing this text._

        Note that, unlike the other methods, this method returns a single cell rather than a list of
        cells (since it is not used in the same context).

        Returns:
            ``nbformat.NotebookNode``: the response cell
        """
        return nbformat.v4.new_markdown_cell(MD_RESPONSE_CELL_SOURCE)
