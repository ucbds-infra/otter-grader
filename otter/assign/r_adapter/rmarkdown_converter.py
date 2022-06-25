"""Functions for converting Assign-formatted Rmarkdown files to and from notebook objects"""

import jupytext
import os
import re

import nbformat

import sys
sys.path.insert(0, ".")

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
        for i, l in enumerate(lines):
            if in_comment and l.strip() == HTML_COMMENT_END:
                    # new_lines.insert(insert_at, "<!-- #raw -->")
                    new_lines.append("<!-- #endraw -->")
                    in_comment = False
            elif l.startswith(HTML_COMMENT_START):
                if HTML_COMMENT_END in l and CONFIG_START_REGEX.search(l): # CONFIG_START_REGEX prevents us from matching pdf export comment in ag notebooks
                    # pre_comment_lines = lines[from_index:i]
                    # if any(pcl != "" for pcl in pre_comment_lines):
                    #     new_cells.append(cell_from_source("markdown", pre_comment_lines))
                    # raw_cell = cell_from_source("raw", [EXTRACT_COMMENT_REGEX.match(l).group(1)])
                    # new_cells.append(raw_cell)
                    # from_index = i + 1
                    new_lines.append("<!-- #raw -->")
                    new_lines.append(EXTRACT_COMMENT_REGEX.match(l).group(1))
                    new_lines.append("<!-- #endraw -->")
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

        nb = jupytext.reads("\n".join(new_lines), "Rmd", as_version=4) # TODO: use constant
        nb["metadata"]["kernelspec"] = {"language": "r"}

        nbformat.write(nb, "hw01-2-2-2.ipynb")
        return nb

    @staticmethod
    def write_as_rmd(nb, rmd_path, strip_metadata=False):
        """
        """
        if os.path.splitext(rmd_path)[1] != ".Rmd":
            raise ValueError("The provided path does not have the .Rmd extension")

        config = None
        if strip_metadata:
            config = JupytextConfiguration(cell_metadata_filter="-all")

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
