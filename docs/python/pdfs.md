# PDF Generation and Filtering

Otter has two methods of generating PDFs of notebooks: Otter Export and the library nb2pdf. The former uses nbconvert, pandoc, and LaTeX to generate PDFs and the latter relies on nbpdfexport, pyppeteer, and chromium. Otter Export is used by Otter Assign to generate Gradescope PDF templates, in the Gradescope autograder to generate the PDFs of notebooks, and by `otter.Notebook` to generate PDFs. Otter Grade uses nb2pdf, as does the solutions PDF generation done by Otter Assign.

## Cell Filtering

Cell filtering is supported by both nb2pdf and Otter Export. Both allow the use of HTML comments in Markdown cells to perform this, while only nb2pdf supports the use of cell tags. Filtering is the default behavior of most exporters.

### HTML Comment Filtering

You can place HTML comments in Markdown cells to capture everything in between them in the output. To start a filtering group, place the comment `<!-- BEGIN QUESTION -->` whereever you want to start exporting and place `<!-- END QUESTION -->` at the end of the filtering group. Everything capture between these comments will be exported, and everything outside them removed. You can have multiple filtering groups in a notebook. When using Otter Export, you can also optionally add page breaks after an `<!-- END QUESTION -->` by setting `pagebreaks=True` in `otter.export.export_notebook`.

This filtering behavior is triggered with the `--html-filter` flag or in the default behavior of `otter.Notebook.export`.

### Cell Tag Filtering

Along with HTML comment filtering, nb2pdf supports filtering cells using cell tags. When generating the PDF (if filtering is indicated by the `--tag-filter` flag or by setting `filter_type="tags"` in `Notebook.export`), the following cells will be **included** in the export:

* All Markdown cells
* Code cells that have an image in their output
* All cells tagged with `include`

If you would like to override the behavior above, tag a cell with `ignore` and it will not be included.

## Otter Export Reference

```eval_rst
.. argparse::
   :module: otter.argparser
   :func: get_parser
   :prog: otter
   :path: export
   :nodefaultconst:
```
