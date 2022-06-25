"""Functions for converting Assign-formatted Rmarkdown files to and from notebook objects"""

import jupytext
import os
import re
import pprint

import nbformat

import sys
sys.path.insert(0, ".")

from copy import deepcopy
from jupytext.config import JupytextConfiguration

from otter.assign.utils import cell_from_source, get_source


HTML_COMMENT_START = "<!--"
HTML_COMMENT_END = "-->"
EXTRACT_COMMENT_REGEX = re.compile(fr"{HTML_COMMENT_START}\s*(#\s*[\w ]+)\s*{HTML_COMMENT_END}")
CONFIG_START_REGEX = re.compile(r"#\s+(ASSIGNMENT\s+CONFIG|(BEGIN|END)\s+\w+)", re.IGNORECASE)
YAML_COMMENT_CHAR = "#"


class RMarkdownConverter:
    """
    """

    @staticmethod
    def read_as_notebook(rmd_path):
        """
        """
        # nb = jupytext.read(rmd_path)

        # TODO: do these rules keep consistent whitespace?
        with open(rmd_path) as f:
            lines = [l.strip("\n") for l in f.readlines()]

        new_lines = []
        # from_index = 0
        in_comment = False
        # insert_at = None
        in_solution_region, just_closed_solution_region = False, False
        has_prompt = False
        for i, l in enumerate(lines):
            if just_closed_solution_region:
                just_closed_solution_region = False
                if l == "":
                    print("doing it")
                    print(new_lines)
                    continue

            if in_comment and l.strip() == HTML_COMMENT_END:
                    # new_lines.insert(insert_at, "<!-- #raw -->")
                    new_lines.append("<!-- #endraw -->")
                    in_comment = False
            elif l.startswith(HTML_COMMENT_START):
                if HTML_COMMENT_END in l:
                    if CONFIG_START_REGEX.search(l): # CONFIG_START_REGEX prevents us from matching pdf export comment in ag notebooks
                    # pre_comment_lines = lines[from_index:i]
                    # if any(pcl != "" for pcl in pre_comment_lines):
                    #     new_cells.append(cell_from_source("markdown", pre_comment_lines))
                    # raw_cell = cell_from_source("raw", [EXTRACT_COMMENT_REGEX.match(l).group(1)])
                    # new_cells.append(raw_cell)
                    # from_index = i + 1
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
                        # if "begin" in l.lower() and ("prompt" in l.lower() or "solution" in l.lower()) and :
                        #     has_prompt = True
                        #     new_lines.pop(len(new_lines) - 1)
                        new_lines.append("<!-- #raw -->")
                        new_lines.append(EXTRACT_COMMENT_REGEX.match(l).group(1))
                        new_lines.append("<!-- #endraw -->")
                    else:
                        if l == """<!-- #region tags=["otter_assign_solution_cell"] -->""":
                            in_solution_region = True
                        elif in_solution_region and l == "<!-- #endregion -->":
                            print(l)
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

        # if from_index < len(lines) - 1:
        #     new_cells.append(cell_from_source("markdown", lines[from_index:i]))
        assert not in_comment

        print("\n".join(new_lines))

        nb = jupytext.reads("\n".join(new_lines), "Rmd", as_version=4) # TODO: use constant
        nb["metadata"]["kernelspec"] = {"language": "r"}
        pprint.pprint(nb)

        nbformat.write(nb, "hw01-2-2-2.ipynb")
        return nb

    @staticmethod
    def write_as_rmd(nb, rmd_path, has_solutions):
        """
        """
        if os.path.splitext(rmd_path)[1] != ".Rmd":
            raise ValueError("The provided path does not have the .Rmd extension")
        pprint.pprint(nb)

        config = None
        # if strip_metadata:
        # config = JupytextConfiguration(split_at_heading=True)

        if not has_solutions:
            nb = deepcopy(nb)
            for i, cell in enumerate(nb["cells"]):
                if i < len(nb["cells"]) - 1 and cell["cell_type"] == "markdown" and nb["cells"][i + 1]["cell_type"] == "markdown":
                    cell["metadata"]["lines_to_next_cell"] = 0

        print(jupytext.writes(nb, fmt="Rmd"))

        jupytext.write(nb, rmd_path, config=config)


def main():
    nb = RMarkdownConverter.read_as_notebook("hw01.Rmd")
    nbformat.write(nb, "hw01-2.ipynb")
    RMarkdownConverter.write_as_rmd(nb, "hw01-2-2.Rmd")

if __name__ == "__main__":
    main()




# """Functions for converting Assign-formatted Rmarkdown files to and from notebook objects"""

# import jupytext
# import os
# import re

# import nbformat

# import sys
# sys.path.insert(0, ".")

# from otter.assign.utils import cell_from_source, get_source


# HTML_COMMENT_START = "<!--"
# HTML_COMMENT_END = "-->"
# EXTRACT_COMMENT_REGEX = re.compile(fr"{HTML_COMMENT_START}\s*(#\s*[\w ]+)\s*{HTML_COMMENT_END}")
# CONFIG_START_REGEX = re.compile(r"#\s+(ASSIGNMENT\s+CONFIG|(BEGIN|END)\s+\w+)", re.IGNORECASE)
# YAML_COMMENT_CHAR = "#"


# class RMarkdownConverter:
#     """
#     """

#     @staticmethod
#     def read_as_notebook(rmd_path):
#         """
#         """
#         nb = jupytext.read(rmd_path)

#         # TODO: do these rules keep consistent whitespace?
#         new_cells = []
#         for cell in nb["cells"]:
#             if cell["cell_type"] == "markdown":
#                 lines = get_source(cell)
#                 new_lines = []
#                 # from_index = 0
#                 # in_comment = False
#                 insert_at = None
#                 for i, l in enumerate(lines):
#                     new_lines.append(l)

#                     if in_comment:
#                         if l.strip() == HTML_COMMENT_END:
#                             raw_cell = cell_from_source("raw", lines[from_index:i])
#                             new_cells.append(raw_cell)
#                             from_index, in_comment = i + 1, False
#                     elif l.startswith(HTML_COMMENT_START):
#                         if HTML_COMMENT_END in l and YAML_COMMENT_CHAR in l: # YAML_COMMENT_CHAR prevents us from matching pdf export comment in ag notebooks
#                             pre_comment_lines = lines[from_index:i]
#                             if any(pcl != "" for pcl in pre_comment_lines):
#                                 new_cells.append(cell_from_source("markdown", pre_comment_lines))
#                             raw_cell = cell_from_source("raw", [EXTRACT_COMMENT_REGEX.match(l).group(1)])
#                             new_cells.append(raw_cell)
#                             from_index = i + 1
#                         elif l.strip() == HTML_COMMENT_START:
#                             if i + 1 < len(lines) and CONFIG_START_REGEX.match(lines[i + 1]):
#                                 from_index, in_comment = i + 1, True
                
#                 if from_index < len(lines) - 1:
#                     new_cells.append(cell_from_source("markdown", lines[from_index:i]))

#             else:
#                 new_cells.append(cell)

#         nb["cells"] = new_cells
#         nb["metadata"]["kernelspec"] = {"language": "r"}
#         return nb

#     @staticmethod
#     def write_as_rmd(nb, rmd_path):
#         """
#         """
#         if os.path.splitext(rmd_path)[1] != ".Rmd":
#             raise ValueError("The provided path does not have the .Rmd extension")

#         jupytext.write(nb, rmd_path)


# def main():
#     nb = RMarkdownConverter.read_as_notebook("hw01.Rmd")
#     nbformat.write(nb, "hw01-2.ipynb")
#     RMarkdownConverter.write_as_rmd(nb, "hw01-2-2.Rmd")

# if __name__ == "__main__":
#     main()
