import ast
import astunparse
import json
import nbformat as nbf
import os
import tempfile

from nbconvert.exporters import PythonExporter
from nbconvert.preprocessors import Preprocessor
from textwrap import dedent
from traitlets import Dict, Instance, Integer, List, Unicode
from typing import Optional, Tuple

from ..check.logs import Log
from ..utils import id_generator


CELL_METADATA_KEY = "otter"
IGNORE_CELL_TAG = "otter_ignore"


# TODO: make setting up debug logging cleaner

INIT_CELL_SOURCE = """\
from otter import Notebook as {notebook_name}
{notebook_name}.init_grading_mode("{test_dir}")

# set up Otter's logging
import logging
from otter.utils import loggers
loggers.set_level(logging.DEBUG)
"""

EXPORT_CELL_SOURCE = """\
from otter.execute import Checker
for t in {tests_glob_json}:
    Checker.check_if_not_already_checked(t)

from otter.test_files import GradingResults
results = GradingResults(Checker.get_results())

import pickle
with open("{results_path}", "wb") as f:
    pickle.dump(results, f)
"""


class GradingPreprocessor(Preprocessor):

    cwd = Unicode(allow_none=True).tag(config=True)

    test_dir = Unicode().tag(config=True)

    tests_glob = List(Unicode()).tag(config=True)

    results_path = Unicode().tag(config=True)

    seed = Integer(allow_none=True).tag(config=True)

    seed_variable = Unicode(allow_none=True).tag(config=True)

    otter_log: Optional[Log] = Instance(Log, allow_none=True).tag(config=True)

    variables = Dict(value_trait=Unicode(), key_trait=Unicode(), allow_none=True).tag(config=True)

    _notebook_name: str

    _log_temp_file: Optional[Tuple[int, str]] = None

    @property
    def from_log(self):
        return self.otter_log is not None

    def preprocess(self, nb, resources = None):
        self._notebook_name = f"notebook_{id_generator()}"
        self.filter_ignored_cells(nb)
        self.logging_transform(nb)
        self.add_checks(nb)
        self.add_seeds(nb)
        self.add_cwd_to_path(nb)
        self.add_init_and_export_cells(nb)  # this should always be the last call
        return nb, resources

    def add_init_and_export_cells(self, nb):
        nb.cells.insert(0, nbf.v4.new_code_cell(INIT_CELL_SOURCE.format(
            notebook_name = self._notebook_name, test_dir = self.test_dir)))
        nb.cells.append(nbf.v4.new_code_cell(EXPORT_CELL_SOURCE.format(
            tests_glob_json = json.dumps(self.tests_glob), results_path = self.results_path)))

    def add_cwd_to_path(self, nb):
        if self.cwd:
            nb.cells.insert(
                0, nbf.v4.new_code_cell(f"import sys\nsys.path.append(r\"{self.cwd}\")"))

    def add_seeds(self, nb):
        if self.seed is None or self.from_log: return

        skip_first = False
        if self.seed_variable is None:
            skip_first = True
            np_name, rand_name = f"np_{id_generator()}", f"random_{id_generator()}"
            nb.cells.insert(
                0, nbf.v4.new_code_cell(f"import numpy as {np_name}\nimport random as {rand_name}"))
            do_seed = f"{np_name}.random.seed({self.seed})\n{rand_name}.seed({self.seed})"

        else:
            do_seed = f"{self.seed_variable} = {self.seed}"

        cells = nb.cells[1:] if skip_first else nb.cells
        for cell in cells:
            if cell.cell_type == "code":
                cell.source = f"{do_seed}\n{cell.source}"

    def add_checks(self, nb):
        if self.from_log: return

        new_cells = []
        for cell in nb.cells:
            new_cells.append(cell)

            config = cell.get("metadata", {}).get(CELL_METADATA_KEY, {})
            if config.get("tests"):
                source = ""
                for test in config["tests"]:
                    source += f"{self._notebook_name}().check(\"{test}\")\n"

                new_cells.append(nbf.v4.new_code_cell(source))

        nb.cells = new_cells

    def filter_ignored_cells(self, nb):
        new_cells = []
        for cell in nb.cells:
            m = cell.get("metadata", {})
            if IGNORE_CELL_TAG in m.get("tags", []) or \
                    m.get(CELL_METADATA_KEY, {}).get("ignore", False):
                continue

            new_cells.append(cell)

        nb.cells = new_cells

    def logging_transform(self, nb):
        if not self.from_log: return

        self.filter_out_non_imports(nb)

        self._log_temp_file = tempfile.mkstemp()
        log_fn = self._log_temp_file[1]
        for e in self.otter_log.entries:
            e.flush_to_file(log_fn)

        nb.cells.append(nbf.v4.new_code_cell(dedent(f"""\
            import json
            from otter import Notebook
            from otter.check.logs import Log
            from otter.utils import get_variable_type

            variables = json.loads(\"\"\"{json.dumps(self.variables)}\"\"\")
            log = Log.from_file("{log_fn}")
            logged_questions = []
            grader = Notebook()

            for entry in log.question_iterator():
                shelf = entry.unshelve(globals())

                if variables is not None:
                    for k, v in shelf.items():
                        full_type = get_variable_type(v)
                        if not (k in variables and variables[k] == full_type):
                            del shelf[k]
                            print(f"Found variable of different type than expected: {{k}}")

                globals().update(shelf)
                grader.check(entry.question)
                logged_questions.append(entry.question)

            print(f"Questions executed from log: {{', '.join(logged_questions)}}")
        """)))

    def filter_out_non_imports(self, nb):
        e = PythonExporter()
        ic = ImportCollector()
        tree = ast.parse(e.from_notebook_node(nb)[0])
        ic.visit(tree)
        nb.cells = [nbf.v4.new_code_cell(ic.to_script())]

    def cleanup(self):
        if self._log_temp_file:
            os.close(self._log_temp_file[0])


class ImportCollector(ast.NodeVisitor):
    imports = []

    def visit_Import(self, node):
        self.imports.append(node)

    def visit_ImportFrom(self, node):
        self.imports.append(node)

    def to_module(self):
        return ast.Module(body=self.imports)

    def to_script(self):
        return astunparse.unparse(self.to_module())
