"""Cell generators for R notebooks"""

import nbformat

from otter.assign.feature_toggle import FeatureToggle

from ..cell_factory import CellFactory
from ..utils import lock


class RCellFactory(CellFactory):
    """
    """

    def create_init_cells(self):
        return []

    def create_check_cells(self, question):
        cell = nbformat.v4.new_code_cell()
        cell.source = ['. = ottr::check("tests/{}.R")'.format(question.name)]
        lock(cell)
        return cell

    def create_check_all_cells(self):
        return []

    def create_export_cells(self):
        """
        Generates export cells that instruct the student the run a code cell calling 
        ``ottr::export`` to generate and download their submission. The Markdown cell contains:

        .. code-block:: markdown

            ## Submission
            
            Make sure you have run all cells in your notebook in order before running the cell below, so 
            that all images/graphs appear in the output. The cell below will generate a zipfile for you 
            to submit. **Please save before exporting!**

        Additional instructions can be appended to this cell by passing a string to ``instruction_text``.

        The code cell contains:

        .. code-block:: python

            # Save your notebook first, then run this cell to export your submission.
            ottr::export("path/to/notebook.ipynb")
        
        Returns:
            ``list[nbformat.NotebookNode]``: generated export cells
        """
        export_cell_config = self._get_export_cell_config()

        instructions = nbformat.v4.new_markdown_cell()
        instructions.source = "## Submission\n\nMake sure you have run all cells in your " \
            "notebook in order before running the cell below, so that all images/graphs appear " \
            "in the output. The cell below will generate a zip file for you to submit. **Please " \
            "save before exporting!**"
        
        if export_cell_config.get("instructions", ""):
            instructions.source += '\n\n' + export_cell_config["instructions"]

        export = nbformat.v4.new_code_cell()
        source_lines = ["# Save your notebook first, then run this cell to export your submission."]
        source_lines.append(f'ottr::export("{self.assignment.notebook_basename}")')
        export.source = "\n".join(source_lines)

        lock(instructions)
        lock(export)

        cells = [instructions, export]
        if self.check_feature_toggle(FeatureToggle.EMPTY_MD_BOUNDARY_CELLS):
            cells.append(nbformat.v4.new_markdown_cell(" "))  # add buffer cell

        return cells
