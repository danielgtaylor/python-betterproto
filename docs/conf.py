# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import pathlib

import toml


# -- Project information -----------------------------------------------------

project = 'betterproto'
copyright = '2020, danielgtaylor'
author = 'danielgtaylor'
pyproject = toml.load(open(pathlib.Path(__file__).parent.parent / 'pyproject.toml'))


# The full version, including alpha/beta/rc tags.
release = pyproject["tool"]["poetry"]["version"]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
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

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']


# -- Options for HTML output -------------------------------------------------

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "friendly"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_iowmd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_theme_options = {
    # Specify a list of menu in Header.
    # Tuples forms:
    #  ('Name', 'external url or path of pages in the document', boolean, 'icon name')
    #
    # Third argument:
    # True indicates an external link.
    # False indicates path of pages in the document.
    #
    # Fourth argument:
    # Specify the icon name.
    # For details see link.
    # https://material.io/icons/
    'header_links' : [
        ('Home', 'index', False, 'home'),
        ("Slack", "https://betterproto.slack.com/", True, 'chat_bubble_outline'),
        ("GitHub", "https://github.com/danielgtaylor/python-betterproto", True, 'code')
    ],

    # Customize css colors.
    # For details see link.
    # https://getmdl.io/customize/index.html
    #
    # Values: amber, blue, brown, cyan deep_orange, deep_purple, green, grey, indigo, light_blue,
    #         light_green, lime, orange, pink, purple, red, teal, yellow(Default: indigo)
    'primary_color': 'indigo',
    # Values: Same as primary_color. (Default: pink)
    'accent_color': 'pink',

    # Customize layout.
    # For details see link.
    # https://getmdl.io/components/index.html#layout-section
    'fixed_drawer': False,
    'fixed_header': False,
    'header_waterfall': False,
    'header_scroll': True,

    # Render title in header.
    # Values: True, False (Default: False)
    'show_header_title': False,
    # Render title in drawer.
    # Values: True, False (Default: True)
    'show_drawer_title': True,
    # Render footer.
    # Values: True, False (Default: True)
    'show_footer': True
}
