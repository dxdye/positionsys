# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "positionsys"
copyright = "2025, Tilman Bertram"
author = "Tilman Bertram"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ["_templates"]
exclude_patterns = []


extensions = [
        "sphinx.ext.autodoc",
        "sphinx.ext.doctest",
        "sphinx.ext.intersphinx",
        "sphinx.ext.todo",
        "sphinx.ext.coverage",
        "sphinx.ext.mathjax",
        "sphinx.ext.ifconfig",
        "sphinx.ext.viewcode",
        "sphinx.ext.githubpages",
        "sphinx.ext.napoleon",
        ]
extensions.append('sphinx_autodoc_typehints')

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]


import os
import sys

sys.path.insert(
        0, os.path.abspath("../src")
        )  # Adjust path to include your `src` directory
