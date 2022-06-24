"""Functions for converting Assign-formatted Rmarkdown files to and from notebook objects"""

import jupytext
import os


class RMarkdownConverter:
    """
    """

    @staticmethod
    def read_as_notebook(rmd_path):
        """
        """
        nb = jupytext.read(rmd_path)

        new_cells = []
        for cell in nb["cells"]:
            if cell["cell_type"] == "markdown":
                pass # TODO:

            new_cells.append(cell)

        nb["cells"] = new_cells
        return nb

    @staticmethod
    def write_as_rmd(nb, rmd_path):
        """
        """
        if os.path.splitext(rmd_path)[1] != ".Rmd":
            raise ValueError("The provided path does not have the .Rmd extension")

        jupytext.write(nb, rmd_path)
