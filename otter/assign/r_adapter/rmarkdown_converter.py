"""Functions for converting Assign-formatted R Markdown files to and from notebook objects"""

import jupytext
import os
import re

from copy import deepcopy

from ...utils import get_source, NBFORMAT_VERSION, NOTEBOOK_METADATA_KEY


HTML_COMMENT_START = "<!--"
HTML_COMMENT_END = "-->"
EXTRACT_COMMENT_REGEX = re.compile(fr"{HTML_COMMENT_START}\s*(#\s*[\w ]+)\s*{HTML_COMMENT_END}")
CONFIG_START_REGEX = re.compile(r"#\s+(ASSIGNMENT\s+CONFIG|(BEGIN|END)\s+\w+)", re.IGNORECASE)
YAML_COMMENT_CHAR = "#"


def read_as_notebook(rmd_path):
    """
    Read an R Markdown file and convert it to a master notebook to be used with Otter Assign.

    Args:
        rmd_path (``pathlib.Path | str)``: the path to the master R Markdown file

    Returns:
        ``nbformat.NotebookNode``: the R Markdown file as a master notebook
    """
    with open(rmd_path) as f:
        lines = [l.strip("\n") for l in f.readlines()]

    new_lines = []
    in_comment = False
    in_solution_region, just_closed_solution_region = False, False
    has_prompt = False
    for i, l in enumerate(lines):
        # prevent excess whitespace in the student version of the notebook caused by the removal of
        # the lines containing the solution
        if just_closed_solution_region:
            just_closed_solution_region = False
            if l == "":
                continue

        if in_comment and l.strip() == HTML_COMMENT_END:
                new_lines.append("<!-- #endraw -->")
                in_comment = False

        elif l.startswith(HTML_COMMENT_START):
            if HTML_COMMENT_END in l:
                if CONFIG_START_REGEX.search(l):
                    if "begin" in l.lower() and "prompt" in l.lower():
                        has_prompt = True
                        if new_lines[len(new_lines) - 1].strip() == "":
                            new_lines.pop(len(new_lines) - 1)

                    if has_prompt:
                        if "begin" in l.lower() and "solution" in l.lower():
                            has_prompt = False
                            if new_lines[len(new_lines) - 1].strip() == "":
                                new_lines.pop(len(new_lines) - 1)

                        elif "end" in l.lower() and "prompt" not in l.lower():
                            has_prompt = False

                    new_lines.append("<!-- #raw -->")
                    new_lines.append(EXTRACT_COMMENT_REGEX.match(l).group(1))
                    new_lines.append("<!-- #endraw -->")

                else:
                    if l == """<!-- #region tags=["otter_assign_solution_cell"] -->""":
                        in_solution_region = True
                    elif in_solution_region and l == "<!-- #endregion -->":
                        in_solution_region, just_closed_solution_region = False, True

                    new_lines.append(l)

            elif l.strip() == HTML_COMMENT_START:
                if i + 1 < len(lines) and CONFIG_START_REGEX.match(lines[i + 1]):
                    new_lines.append("<!-- #raw -->")
                    in_comment = True

            else:
                new_lines.append(l)

        else:
            new_lines.append(l)

    if in_comment:
        raise ValueError("R Markdown file ends with an unclosed HTML comment")

    nb = jupytext.reads("\n".join(new_lines), "Rmd", as_version=NBFORMAT_VERSION)
    nb["metadata"]["kernelspec"] = {"language": "r"}

    return nb


def write_as_rmd(nb, rmd_path, has_solutions):
    """
    Write an autograder- or student-formatted R notebook as an R Markdown file.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to write
        rmd_path (``pathlib.Path | str``): the path at which to write the R Markdown file
        has_solutions (``bool``): whether the provided notebook is an autograder notebook
    """
    if os.path.splitext(rmd_path)[1] != ".Rmd":
        raise ValueError("The provided path does not have the .Rmd extension")

    nb = deepcopy(nb)

    # prevent neighboring markdown cells from having two lines inserted between them in the student
    # notebook (resolves whitespace issues caused by the use of prompts for written questions)
    if not has_solutions:
        for i, cell in enumerate(nb["cells"]):
            if i < len(nb["cells"]) - 1 and cell["cell_type"] == "markdown" and \
                    nb["cells"][i + 1]["cell_type"] == "markdown":
                cell["metadata"]["lines_to_next_cell"] = 0

    # add assignment name to Rmd metadata if necessary
    assignment_name = nb["metadata"].get(NOTEBOOK_METADATA_KEY, {}).get("assignment_name", None)
    if assignment_name:
        config_cell = nb["cells"][0]
        source = get_source(config_cell)
        source.insert(-1, f"assignment_name: \"{assignment_name}\"")
        config_cell["source"] = "\n".join(source)

    jupytext.write(nb, rmd_path)
