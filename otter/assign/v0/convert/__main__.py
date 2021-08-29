"""CLI for converting v0-formatted notebooks to v1 format"""

import click
import nbformat

from .notebook_transformer import get_transformed_cells
from ..constants import NB_VERSION
from ...utils import remove_cell_ids


@click.command()
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
@click.argument("dst", type=click.Path())
def main(src, dst):
    """
    Convert the Assign master notebook SRC from v0 format to v1 format and write the resulting
    notebook at DST.
    """
    nb = nbformat.read(src, as_version=NB_VERSION)
    cells = get_transformed_cells(nb["cells"])
    nb["cells"] = cells
    remove_cell_ids(nb)
    nbformat.write(nb, dst)


if __name__ == "__main__":
    main()
