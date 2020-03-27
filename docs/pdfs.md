# PDF Generation and Filtering

When exporting IPython notebooks as PDFs, Otter uses the library nb2pdf that relies on nbpdfexport and chromium to export notebooks without pandoc or LaTeX. This requires that chromium be installed both in the Docker container being used for grading and on the JupyterHub distribution on which students export their notebooks from the `Notebook` API. 

The `Notebook.export` function encapsulates PDF generation on the student end, and by default filtering is turned on. To generate unfiltered PDFs with `Notebook.export`, set `filtering=False` in your call. To generate unfiltered PDFs from the command line, use the `--pdf` flag when calling `otter grade`.

## Cell Filtering

nb2pdf supports two different formats for filtering cells when exporting notebooks: using cell tags and using HTML comments. 

### Cell Tag Filtering

When generating the PDF (if filtering is indicated by the `--tag-filter` flag or by setting `filter_type="tags"` in `Notebook.export`), the following cells will be **included** in the export:

* All Markdown cells
* Code cells that have an image in their output
* All cells tagged with `include`

If you would like to override the behavior above, tag a cell with `ignore` and it will not be included.

### HTML Comment Filtering

Alternatively, you can place HTML comments in Markdown cells to capture everything in between them in the output. To start a filtering group, place the comment `<!-- BEGIN QUESTION -->` whereever you want to start exporting and place `<!-- END QUESTION -->` at the end of the filtering group. Everything capture between these comments will be exported, and everything outside them removed. You can have multiple filtering groups in a notebook.

This filtering behavior is triggered with the `--html-filter` flag or in the default behavior of `Notebook.export` (as the `filter_type` argument defaults to `"html"`).
