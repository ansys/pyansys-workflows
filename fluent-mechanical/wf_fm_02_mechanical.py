# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
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
"""
.. _ref_fluent_mechanical_02-mechanical:

Mechanical -
#############################

"""  # noqa: D400, D415

import os
from pathlib import Path

from ansys.mechanical.core import launch_mechanical
from ansys.mechanical.core.examples import download_file
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

###############################################################################
# Preparing the environment
# -------------------------
# This section is only necessary for workflow runs and docs generation. It checks
# the environment variables to determine which image to use for the mechanical service.
# If you are running this script outside of a workflow, you can ignore this section.
#

version = None
if "ANSYS_MECHANICAL_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_MECHANICAL_RELEASE"]
    version = int(image_tag.replace(".", ""))

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gmd_02_mechanical.py")
# sphinx_gallery_end_ignore

###############################################################################
# Parameters for the script
# -------------------------
# The following parameters are used to control the script execution. You can
# modify these parameters to suit your needs.
#
GRAPHICS_BOOL = False  # Set to True to display the graphics
OUTPUT_DIR = Path(Path(__file__).parent, "outputs")  # Output directory

# sphinx_gallery_start_ignore
if "DOC_BUILD" in os.environ:
    GRAPHICS_BOOL = True
# sphinx_gallery_end_ignore

###############################################################################
# Start a PyMechanical app
# ------------------------
#
mechanical = launch_mechanical(batch=False, cleanup_on_exit=False)
print(mechanical)


def display_image(image_name):
    plt.figure(figsize=(16, 9))
    plt.imshow(mpimg.imread(os.path.join(OUTPUT_DIR, image_name)))
    plt.xticks([])
    plt.yticks([])
    plt.axis("off")
    plt.show()


geometry_path = download_file(
    "Exhaust_Manifold_Geometry.pmdb", "pyansys-workflow", "exhaust-manifold", "pymechanical"
)
material_path = download_file(
    "Nonlinear_Material.xml", "pyansys-workflow", "exhaust-manifold", "pymechanical"
)


print("Hello World")
