# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

import nbconvert

from glob import glob
from jinja2 import Template

from otter.generate import CondaEnvironment
from otter.utils import print_full_width


# -- Project information -----------------------------------------------------

project = "Otter-Grader"
copyright = "2019-2023, UC Berkeley Data Science Education Program"
author = "UC Berkeley Data Science Education Program Infrastructure Team"

# The short X.Y version
version = ""
# The full version, including alpha/beta/rc tags
release = ""


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx_markdown_tables",
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinx_click",
    "fica.sphinx",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False

apidoc_module_dir = "../otter"
apidoc_output_dir = "."
apidoc_excluded_paths = []

autosummary_generate = False

# imports for IPython
ipython_execlines = [
    "import json",
    "import yaml",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = [".rst"]

# The master toctree document.
master_doc = "index"

github_doc_root = "https://github.com/ucbds-infra/otter-grader/tree/master/docs/"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "modules.rst", "otter*.rst", "modules.rst"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"
html_logo = "../logo/otter-logo-smallest.png"

html_theme_options = {
    "github_url": "https://github.com/ucbds-infra/otter-grader",
    "repository_url": "https://github.com/ucbds-infra/otter-grader",
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["style.css"]
html_favicon = "_static/favicon.ico"

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = { '**': ['globaltoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html'] }


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "otterdoc"


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "otterdoc.tex",
        "Otter-Grader Documentation",
        "UCBDS Infrastructure Team",
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "Otter-Grader", "Otter-Grader Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "Otter-Grader",
        "Otter-Grader Documentation",
        author,
        "Otter-Grader",
        "One line description of project.",
        "Miscellaneous",
    ),
]


def convert_static_notebooks():
    exporter = nbconvert.HTMLExporter()

    print_full_width("=", "CONVERTING NOTEBOOKS")

    for file in glob("_static/notebooks/*.ipynb"):
        html, _ = exporter.from_filename(file)
        parent, path = os.path.split(file)

        new_parent = os.path.join(parent, "html")
        os.makedirs(new_parent, exist_ok=True)

        new_path = os.path.join(new_parent, os.path.splitext(path)[0] + ".html")

        with open(new_path, "w+") as f:
            f.write(html)

        print(f"Converted {file} to HTML")

    print_full_width("=")


def make_setup_sh_files():
    ctx = {
        "autograder_dir": "/autograder",
        "otter_env_name": "otter-env",
        "has_r_requirements": True,
    }

    for l in ["python", "r"]:
        with open(f"../otter/generate/templates/{l}/setup.sh") as f:
            t = Template(f.read())
        s = t.render(ctx)
        with open(f"_static/{l}_setup.sh", "w+") as f:
            f.write(s)


# -- Extension configuration -------------------------------------------------
def setup(app):
    # run nbconvert on all of the notebooks in _static/notebooks
    convert_static_notebooks()

    # convert templates to valid setup.sh files
    make_setup_sh_files()

    with open("_static/grading-environment.yml", "w+") as f:
        f.write(CondaEnvironment("3.9", False, [], False, None, False).to_str())

    with open("_static/grading-environment-r.yml", "w+") as f:
        f.write(CondaEnvironment("3.9", True, [], False, None, False).to_str())
