import nbformat as nbf

from nbconvert.preprocessors import Preprocessor
from textwrap import dedent
from traitlets import Integer, List, Unicode


CELL_METADATA_KEY = "otter"


class SeedPreprocessor(Preprocessor):

    seed = Integer.tag(allow_none=True)

    seed_variable = Unicode(allow_none=True)

    def _get_code(self):
        if self.seed_variable is None:
            return f"np.random.seed({self.seed})\nrandom.seed({self.seed})"
        return f"{self.seed_variable} = {self.seed}"

    def preprocess_cell(self, cell, resources, index):
        if self.seed is not None:
            cell.source = f"{self._get_code()}\n{cell.source}"
        return cell, resources


class CheckInsertionPreprocessor(Preprocessor):

    notebook_class_name = Unicode()

    test_dir = Unicode()

    test_files = List(Unicode())

    def preprocess(self, nb, resources):
        new_cells = []
        for i, cell in enumerate(nb.cells):
            new_cells.append(cell)
            tests = cell.get("metadata", {}).get(CELL_METADATA_KEY, {}).get("tests", [])
            new_cells.append(nbf.v4.new_code_cell(
                "\n".join(f"{self.notebook_class_name}(tests_dir='{self.test_dir}').check('{t}')" for t in tests)))
        nb.cells = new_cells
        return nb, resources


class BoilerplatePreprocessor(Preprocessor):

    output_path = Unicode()

    def preprocess(self, nb, resources):
        nb.cells.insert(0, nbf.v4.new_code_cell("""\
            import otter
            
        """))
