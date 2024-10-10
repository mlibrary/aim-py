# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AIM"
copyright = "2024, Monique Rio"
author = "Monique Rio"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.napoleon", "sphinx.ext.viewcode", "sphinx.ext.autosummary",
              "sphinx.ext.autodoc", 'myst_parser', 'sphinxcontrib.mermaid', "sphinx_toolbox.more_autodoc.autonamedtuple"]
autosummary_generate = True

mermaid_d3_zoom = True
mermaid_version = "11.3.0"
myst_fence_as_directive = ["mermaid"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 5,
    "collapse_navigation": False,
    "titles_only": True
}
