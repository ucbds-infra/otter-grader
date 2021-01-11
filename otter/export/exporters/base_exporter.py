"""
ABC for Otter Export exporters
"""

import nbformat
import nbconvert
import pkg_resources

from abc import ABC, abstractmethod

from .utils import has_begin, has_end, sub_end_for_new_page

NBFORMAT_VERSION = 4
NBCONVERT_6 = int(nbconvert.__version__.split(".")[0]) >= 6    # for determining template inheritance
TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")

class BaseExporter(ABC):
    """
    Abstract base class for Otter Export exporters
    
    Defines methods that read in notebooks from file paths and filter cells with pagebreak annotations 
    if necessary. Sublcasses are not meant to be instatiated but have class methods called. The abstract
    class method ``BaseExporter.convert_notebook`` does the heavy lifting of converting a notebook 
    file path into a PDF file.
    
    Attributes:
        default_options (``dict``): the default options for all exporters
    """

    default_options = {
        "filtering": False,
        "pagebreaks": True,
    }

    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     cls.default_options = 

    @classmethod
    @abstractmethod
    def convert_notebook(cls, nb_path, dest, debug=False, **kwargs):
        """
        Writes a notebook at ``nb_path`` to a PDF file
        
        Args:
            nb_path (``str``): path to notebook
            dest (``str``): path to write PDF
            debug (``bool``, optional): whether to run export in debug mode
            **kwargs: additional arguments use during conversion by subclasses
        """
        ...

    @classmethod
    def load_notebook(cls, nb_path, filtering=False, pagebreaks=True):
        """
        Loads notebook at ``nb_path`` with nbformat and returns the parsed notebook, optionally filtered
        and with pagebreak metadata hidden in HTML comments.

        Args:
            nb_path (``str``): path to notebook
            filtering (``bool``, optional): whetheer cells should be filtered
            pagebreaks (``bool``, optional): whether to include pagebreaks between each question; ignored
                if ``filtering`` is ``False``

        Returns:
            ``nbformat.NotebookNode``: the parsed and (optionally) filtered notebook
        """
        with open(nb_path) as f:
            notebook = nbformat.read(f, as_version=NBFORMAT_VERSION)
        if filtering:
            notebook = cls.filter_cells(notebook, pagebreaks=pagebreaks)
        return notebook

    @classmethod
    def filter_cells(cls, notebook, pagebreaks=True):
        """
        Filters a parsed notebook using HTML comments in Markdown cells. Optionally inserts pagebreak
        metadata as HTML comments.

        Args:
            notebook (``nbformat.NotebookNode``): the parsed notebook
            pagebreaks (``bool``, optional): whether to include pagebreaks between questions

        Returns:
            ``nbformat.NotebookNode``: the filtered notebook with (optional) pagebreaks
        """
        cells = notebook["cells"]

        idx_to_delete, in_question = [], False
        for curr_idx, cell in enumerate(cells):

            if isinstance(cell["source"], str):
                source = cell["source"].split("\n")
            elif isinstance(cell["source"], list):
                source = [line.strip("\n") for line in cell["source"]]
            else:
                raise Exception("Invalid notebook cell source: {}".format(cell))

            lines_before_begin, lines_after_end = -1, -1
            for line_idx, line in enumerate(source):

                # check for begin question regex in source
                if not in_question:
                    if has_begin(line) and lines_before_begin == -1:
                        lines_before_begin = line_idx
                        in_question = True
                
                # check for end question regex in source
                else:
                    if has_end(line):
                        lines_after_end = line_idx
                        in_question = False
                        
                        # if we are creating pagebreaks, sub the end regex for a newpage directive
                        if pagebreaks:
                            source[line_idx] = sub_end_for_new_page(line)

            # if we are not in question and there is no begin/end comment, delete the cell
            if lines_before_begin == -1 and lines_after_end == -1 and not in_question:
                idx_to_delete.append(curr_idx)

            # if both are in cell and before is after end, delete intervening lines
            elif lines_before_begin != -1 and lines_after_end != -1 and lines_after_end < lines_before_begin:
                del source[lines_after_end+1:lines_before_begin]
            
            else:
                # if there is an end comment, delete lines after that
                if lines_after_end != -1:
                    del source[lines_after_end+1:]

                # if there is a begin comment, delete lines before that
                if lines_before_begin != -1:
                    del source[:lines_before_begin]

            # update source
            cell["source"] = "\n".join(source)
        
        # reverse indices list so that we do not need to decrement while deleting
        idx_to_delete.reverse()

        # delete at indices
        for idx in idx_to_delete:
            del cells[idx]

        return notebook

