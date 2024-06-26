"""Sphinx documentation configuration file."""

from datetime import datetime
import os

from ansys_sphinx_theme import ansys_favicon, pyansys_logo_black as logo, pyansys_logo_white
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
    "github_url": "https://github.com/ansys-internal/pyansys-workflows",
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
    'pyvista.ext.viewer_directive',
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

# Sphinx gallery configuration
sphinx_gallery_conf = {
    # path to your examples scripts
    "examples_dirs": [#"../../geometry-mechanical-dpf",
                    #   "../../geometry-mesh",
                    #   "../../geometry-mesh-fluent",
                      ],
    # path where to save gallery generated examples
    "gallery_dirs": [#"examples/geometry-mechanical-dpf",
                    #  "examples/geometry-mesh",
                    #  "examples/geometry-mesh-fluent",
                     ],
    # Pattern to search for example files
    "filename_pattern": ".py",
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
suppress_warnings = []
