
import os
import sys

DOCS_SOURCE = os.path.abspath(os.path.dirname(__file__))
MODULE_DIR = os.path.abspath(os.path.join(DOCS_SOURCE, "..", ".."))
SRC_DIR = os.path.join(MODULE_DIR, "src")
WEB_DIR = os.path.join(SRC_DIR, "web")
WORKER_DIR = os.path.join(SRC_DIR, "worker")

sys.path.insert(0, SRC_DIR)
sys.path.insert(0, WEB_DIR)
sys.path.insert(0, WORKER_DIR)

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GradCafe Analytics'
copyright = '2026, Amr Mansour'
author = 'Amr Mansour'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc",
    "sphinx.ext.napoleon",]


templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
