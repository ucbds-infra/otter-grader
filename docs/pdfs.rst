.. _pdfs:

PDF Generation and Filtering
============================

Otter includes a tool for generating PDFs of notebooks that optionally incorporates notebook 
filtering for generating PDFs for manual grading. There are two options for exporting PDFs:


* **PDF via LaTeX:** this uses nbconvert, pandoc, and LaTeX to generate PDFs from TeX files
* **PDF via HTML:** this uses nbconvert's WebPDF exporter to generate PDFs from HTML

Otter Export is used by Otter Assign to generate Gradescope PDF templates and solutions, in the 
Gradescope autograder to generate the PDFs of notebooks, by ``otter.Notebook`` to generate PDFs and 
in Otter Grade when PDFs are requested.


Cell Filtering
--------------

Otter Export uses HTML comments in Markdown cells to perform cell filtering. Filtering is the 
default behavior of most exporter implementations, but not of the exporter itself.

You can place HTML comments in Markdown cells to capture everything in between them in the output. 
To start a filtering group, place the comment ``<!-- BEGIN QUESTION -->`` whereever you want to 
start exporting and place ``<!-- END QUESTION -->`` at the end of the filtering group. Everything 
capture between these comments will be exported, and everything outside them removed. You can have 
multiple filtering groups in a notebook. When using Otter Export, you can also optionally add page 
breaks after an ``<!-- END QUESTION -->`` by setting ``pagebreaks=True`` in 
``otter.export.export_notebook`` or using the corresponding flags/arguments in whichever utility is 
calling Otter Export.
