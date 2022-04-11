# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import pathlib

import tomlkit

# -- Project information -----------------------------------------------------

project = "betterproto"
copyright = "2019 Daniel G. Taylor"
author = "danielgtaylor"
pyproject = tomlkit.loads(  # type: ignore
    (pathlib.Path(__file__).parent.parent / "pyproject.toml").read_text()
)

# The full version, including alpha/beta/rc tags.
release = str(pyproject["tool"]["poetry"]["version"])


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

autodoc_member_order = "bysource"
autodoc_typehints = "none"

extlinks = {
    "issue": ("https://github.com/danielgtaylor/python-betterproto/issues/%s", "GH-"),
}

# Links used for cross-referencing stuff in other documentation
intersphinx_mapping = {
    "py": ("https://docs.python.org/3", None),
}


# -- Options for HTML output -------------------------------------------------

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "friendly"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_rtd_theme"
