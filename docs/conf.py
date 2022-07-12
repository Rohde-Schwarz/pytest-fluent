"""Configuration file for Sphinx documentation builder."""

project = "pytest-fluent"
copyright = "Rohde & Schwarz GmbH & Co. KG 2022"
author = "Rohde & Schwarz GmbH & Co. KG"
release = version = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",  # Automatically documents modules etc.
    "sphinx.ext.autodoc.typehints",  # Includes typehints for autodoc
    "sphinx.ext.napoleon",  # Parses the docstrings Google style
    "sphinx.ext.viewcode",  # Includes the source code and links in documentation
    "myst_parser",  # Allows the use of .md files instead of .rst files
]
autoclass_content = "both"  # Display class and __init__ docstring
autodoc_typehints = "description"  # Move type annotations to description
myst_enable_extensions = [
    "tasklist",
]
suppress_warnings = ["myst.header"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["images"]
