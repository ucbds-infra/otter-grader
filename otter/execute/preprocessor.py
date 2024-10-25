import ast
import json
import nbformat as nbf
import os
import tempfile

from nbconvert.exporters import PythonExporter
from nbconvert.preprocessors import Preprocessor
from textwrap import dedent
from traitlets import Bool, Dict, Instance, Integer, List, Unicode
from typing import Optional, TypeVar

from ..check.logs import Log
from ..utils import id_generator, NOTEBOOK_METADATA_KEY


T = TypeVar("T")


IGNORE_CELL_TAG = "otter_ignore"

INIT_CELL_SOURCE = """\
from otter import Notebook as {notebook_name}
{notebook_name}.init_grading_mode("{test_dir}")

# set up Otter's logging
import logging
from otter import logging
logging.set_level(logging.DEBUG)
logging.send_logs("{logging_server_host}", {logging_server_port})
"""

EXPORT_CELL_SOURCE = """\
from otter.execute import Checker
for {tests_loop_var} in {tests_glob_json}:
    Checker.check_if_not_already_checked({tests_loop_var})

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

    _notebook_name: str = ""

    _log_temp_file: Optional[tuple[int, str]] = None

    logging_server_host = Unicode().tag(config=True)

    logging_server_port = Integer().tag(config=True)

    force_python3_kernel = Bool().tag(config=True)

    @property
    def from_log(self):
        return self.otter_log is not None

    def preprocess(self, nb: nbf.NotebookNode, resources: T = None) -> tuple[nbf.NotebookNode, T]:
        self._notebook_name = f"notebook_{id_generator()}"
        self.filter_ignored_cells(nb)
        self.logging_transform(nb)
        self.add_checks(nb)
        self.add_seeds(nb)
        self.add_cwd_to_path(nb)
        self.update_kernel(nb)
        self.add_init_and_export_cells(nb)  # this should always be the last call
        return nb, resources

    def add_init_and_export_cells(self, nb: nbf.NotebookNode):
        nb.cells.insert(
            0,
            nbf.v4.new_code_cell(
                INIT_CELL_SOURCE.format(
                    notebook_name=self._notebook_name,
                    test_dir=self.test_dir,
                    logging_server_host=self.logging_server_host,
                    logging_server_port=self.logging_server_port,
                )
            ),
        )
        nb.cells.append(
            nbf.v4.new_code_cell(
                EXPORT_CELL_SOURCE.format(
                    tests_loop_var=f"t_{id_generator()}",
                    tests_glob_json=json.dumps(self.tests_glob),
                    # ensure that "\" is properly-escaped for Windows paths since this is going to be
                    # rendered into a string literal
                    results_path=self.results_path.replace("\\", "\\\\"),
                )
            )
        )

    def add_cwd_to_path(self, nb: nbf.NotebookNode):
        if self.cwd:
            nb.cells.insert(0, nbf.v4.new_code_cell(f'import sys\nsys.path.append(r"{self.cwd}")'))

    def add_seeds(self, nb: nbf.NotebookNode):
        if self.seed is None or self.from_log:
            return

        skip_first = False
        if self.seed_variable is None:
            skip_first = True
            np_name, rand_name = f"np_{id_generator()}", f"random_{id_generator()}"
            nb.cells.insert(
                0, nbf.v4.new_code_cell(f"import numpy as {np_name}\nimport random as {rand_name}")
            )
            do_seed = f"{np_name}.random.seed({self.seed})\n{rand_name}.seed({self.seed})"

        else:
            do_seed = f"{self.seed_variable} = {self.seed}"

        cells = nb.cells[1:] if skip_first else nb.cells
        for cell in cells:
            if cell.cell_type == "code" and not cell.source.startswith("%%"):
                cell.source = f"{do_seed}\n{cell.source}"

    def add_checks(self, nb: nbf.NotebookNode):
        if self.from_log:
            return

        new_cells = []
        for cell in nb.cells:
            new_cells.append(cell)

            config = cell.get("metadata", {}).get(NOTEBOOK_METADATA_KEY, {})
            if config.get("tests"):
                source = ""
                for test in config["tests"]:
                    source += f'{self._notebook_name}().check("{test}")\n'

                new_cells.append(nbf.v4.new_code_cell(source))

        nb.cells = new_cells

    def filter_ignored_cells(self, nb: nbf.NotebookNode):
        new_cells = []
        for cell in nb.cells:
            m = cell.get("metadata", {})
            if IGNORE_CELL_TAG in m.get("tags", []) or m.get(NOTEBOOK_METADATA_KEY, {}).get(
                "ignore", False
            ):
                continue

            new_cells.append(cell)

        nb.cells = new_cells

    def logging_transform(self, nb: nbf.NotebookNode):
        if not self.from_log:
            return

        self.filter_out_non_imports(nb)

        self._log_temp_file = tempfile.mkstemp()
        log_fn = self._log_temp_file[1]
        for e in self.otter_log.entries:
            e.flush_to_file(log_fn)

        nb.cells.append(
            nbf.v4.new_code_cell(
                dedent(
                    f"""\
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
        """
                )
            )
        )

    def filter_out_non_imports(self, nb: nbf.NotebookNode):
        e = PythonExporter()
        ic = ImportCollector()
        tree = ast.parse(e.from_notebook_node(nb)[0])
        ic.visit(tree)
        nb.cells = [nbf.v4.new_code_cell(ic.to_script())]

    def update_kernel(self, nb: nbf.NotebookNode):
        if not self.force_python3_kernel:
            return
        nb["metadata"].get("kernelspec", {})["name"] = "python3"

    def cleanup(self):
        if self._log_temp_file:
            os.close(self._log_temp_file[0])
            os.remove(self._log_temp_file[1])


class ImportCollector(ast.NodeVisitor):
    imports = []

    def visit_Import(self, node: ast.Import):
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.imports.append(node)

    def to_module(self):
        return ast.Module(body=self.imports, type_ignores=[])

    def to_script(self):
        return ast.unparse(self.to_module())
