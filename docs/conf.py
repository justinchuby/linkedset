# Copyright (c) Justin Chu
# SPDX-License-Identifier: MIT
"""Sphinx configuration for the linkedset documentation."""

from __future__ import annotations

from importlib import metadata

project = "linkedset"
author = "Justin Chu"
copyright = "2026, Justin Chu"  # noqa: A001

try:
    release = metadata.version("linkedset")
except metadata.PackageNotFoundError:
    release = "0.0.0"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path: list[str] = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML output -------------------------------------------------------------
html_theme = "furo"
html_title = f"linkedset {release}"
html_static_path = ["_static"]

# -- Autodoc -----------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "special-members": "__iter__,__reversed__,__getitem__,__contains__,__eq__,__len__",
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Intersphinx -------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- MyST --------------------------------------------------------------------
myst_enable_extensions = ["colon_fence", "deflist"]
