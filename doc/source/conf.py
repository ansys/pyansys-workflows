# Copyright (C) 2024 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Sphinx documentation configuration file."""

from datetime import datetime
import os
import re

from ansys_sphinx_theme import ansys_favicon
from ansys_sphinx_theme import pyansys_logo_black as logo
from ansys_sphinx_theme import pyansys_logo_white
import pyvista as pv
from pyvista.plotting.utilities.sphinx_gallery import DynamicScraper

# Env vars
os.environ["DOC_BUILD"] = "true"
os.environ["PYANSYS_VISUALIZER_DOC_MODE"] = "true"
pv.OFF_SCREEN = True
pv.BUILDING_GALLERY = True

# Project information
project = "pyansys-workflows"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = "0.1.0"
cname = os.getenv("DOCUMENTATION_CNAME", "no.cname")

# Select desired logo, theme, favicon, and declare the html title
html_logo = logo
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon
html_short_title = html_title = "PyAnsys Workflows"

# specify the location of your github repo
html_theme_options = {
    "github_url": "https://github.com/ansys/pyansys-workflows",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
}

# Sphinx extensions
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
    "pyvista.ext.viewer_directive",
    "myst_parser",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    # "matplotlib": ("https://matplotlib.org/stable", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    # "pyvista": ("https://docs.pyvista.org/", None),
    # "grpc": ("https://grpc.github.io/grpc/python/", None),
}

# static path
html_static_path = ["_static"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# Ignore anchors
linkcheck_anchors = False


def examples_gallery_dirs_and_filename_pattern():
    """Return the gallery directories to build.

    Notes
    -----
    This function checks for workflow environment variables to determine
    which directories to build. If variables are not provided, it will
    default to building all directories which may lead to failure. The
    environment variable expected is `BUILD_DOCS_SCRIPT` which should
    a path to a certain script.
    """
    examples_dirs = []
    gallery_dirs = []
    filename_pattern = ".py"

    # Check for environment variables
    if os.getenv("BUILD_DOCS_SCRIPT", None):
        dir_name, script_file = os.path.split(os.getenv("BUILD_DOCS_SCRIPT"))
        examples_dirs.append(f"../../{dir_name}")
        gallery_dirs.append(f"examples/{dir_name}")
        script_file_name = os.path.splitext(script_file)[0]
        filename_pattern = re.compile(f"{script_file_name}").pattern
        print(
            f"Building examples in {examples_dirs} to {gallery_dirs} with pattern {filename_pattern}"  # noqa: E501
        )
    else:
        examples_dirs = [
            "../../fluent-mechanical",
            "../../geometry-mechanical-dpf",
            "../../geometry-mesh",
            "../../geometry-mesh-fluent",
        ]
        gallery_dirs = [
            "examples/fluent-mechanical",
            "examples/geometry-mechanical-dpf",
            "examples/geometry-mesh",
            "examples/geometry-mesh-fluent",
        ]

    return examples_dirs, gallery_dirs, filename_pattern


# Sphinx gallery configuration
examples_dirs, gallery_dirs, filename_pattern = examples_gallery_dirs_and_filename_pattern()

sphinx_gallery_conf = {
    # path to your examples scripts
    "examples_dirs": examples_dirs,
    # path where to save gallery generated examples
    "gallery_dirs": gallery_dirs,
    # Pattern to search for example files
    "filename_pattern": filename_pattern,
    # Remove the "Download all examples" button from the top level gallery
    "download_all_examples": False,
    # Sort gallery example by file name instead of number of lines (default)
    "within_subsection_order": "FileNameSortKey",
    # directory where function granular galleries are stored
    "backreferences_dir": None,
    # Modules for which function level galleries are created.  In
    "ignore_pattern": "flycheck*",
    "thumbnail_size": (350, 350),
    "remove_config_comments": True,
    "default_thumb_file": pyansys_logo_white,
    "show_signature": False,
    "image_scrapers": (DynamicScraper(), "matplotlib"),
}


# Suppress warnings
suppress_warnings = ["toc.not_readable", "myst.header"]
