"""Cell generators for R notebooks"""

import nbformat

from ..cell_factory import CellFactory
from ..feature_toggle import FeatureToggle
from ..utils import lock


class RCellFactory(CellFactory):
    """
    A cell factory for R assignments.
    """

    def create_init_cells(self):
        return []

    def create_check_cells(self, question):
        cell = nbformat.v4.new_code_cell()
        cell.source = ['. = ottr::check("tests/{}.R")'.format(question.name)]
        lock(cell)
        return [cell]

    def create_check_all_cells(self):
        return []

    def create_export_cells(self):
        if not self.assignment.export_cell:
            return []

        force_save = not self.assignment.is_rmd and self.assignment.export_cell.force_save

        instructions = nbformat.v4.new_markdown_cell()
        instructions.source = (
            "## Submission\n\nMake sure you have run all cells in your "
            "notebook in order before running the cell below, so that all images/graphs appear "
            "in the output. The cell below will generate a zip file for you to submit."
        )

        if not force_save:
            instructions.source += " **Please save before exporting!**"

        if self.assignment.export_cell.instructions:
            instructions.source += "\n\n" + self.assignment.export_cell.instructions

        args = []
        if self.assignment.export_cell.pdf:
            args.append("pdf = TRUE")
        if force_save:
            args.append("force_save = TRUE")

        if args:
            args = ", " + ", ".join(args)
        else:
            args = ""

        export = nbformat.v4.new_code_cell()
        source_lines = (
            []
            if force_save
            else ["# Save your notebook first, then run this cell to export your submission."]
        )
        source_lines.append(f'ottr::export("{self.assignment.notebook_basename}"{args})')
        export.source = "\n".join(source_lines)

        lock(instructions)
        lock(export)

        cells = [instructions, export]
        if self.check_feature_toggle(FeatureToggle.EMPTY_MD_BOUNDARY_CELLS):
            cells.append(nbformat.v4.new_markdown_cell(" "))  # add buffer cell

        return cells
