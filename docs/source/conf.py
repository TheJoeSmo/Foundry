# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".../foundry"))

source_suffix = ".rst"

master_doc = "index"


# -- Project information -----------------------------------------------------

project = "Foundry"
copyright = "2021, TheJoeSmo"
author = "TheJoeSmo"

# The full version, including alpha/beta/rc tags
release = "0.2.9"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for Extensions --------------------------------------------------

# The names and links to projects to reference.
intersphinx_mapping = {
    "python": ("https://docs.python.org/dev", None),
    "pytest": ("https://docs.pytest.org/en/stable", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# Configure sphinx.ext.coverage
coverage_show_missing_items = True

# Autosummary
autosummary_generate = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False


numpydoc_show_class_members = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# The logo to be shown on the site.
html_logo = "_static/foundry_logo.ico"
html_favicon = "_static/foundry_logo.ico"

html_theme_options = {"logo_link": "index", "github_url": "https://github.com/TheJoeSmo/foundry"}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
