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
"""
.. _ref_geometry_mech_dpf_01-geometry:

Geometry generation
###################

This example shows how to generate a simple PCB using PyAnsys Geometry via
the Ansys Geometry Service. The example demonstrates how to create a sketch,
perform modeling operations, and export the file in different formats (in this
specific case, PMDB).

"""  # noqa: D400, D415

import os
from pathlib import Path

from ansys.geometry.core import launch_modeler
from ansys.geometry.core.connection import GEOMETRY_SERVICE_DOCKER_IMAGE, GeometryContainers
from ansys.geometry.core.designer import DesignFileFormat
from ansys.geometry.core.math import Plane, Point2D, Point3D, UnitVector3D
from ansys.geometry.core.misc import DEFAULT_UNITS, UNITS
from ansys.geometry.core.sketch import Sketch

###############################################################################
# Preparing the environment
# -------------------------
# This section is only necessary for workflow runs and docs generation. It checks
# the environment variables to determine which image to use for the geometry service.
# If you are running this script outside of a workflow, you can ignore this section.
#
image = None
if "ANSYS_GEOMETRY_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_GEOMETRY_RELEASE"]
    for geom_services in GeometryContainers:
        if image_tag == f"{GEOMETRY_SERVICE_DOCKER_IMAGE}:{geom_services.value[2]}":
            print(f"Using {image_tag} image")
            image = geom_services
            break

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gmd_01_geometry.py")
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
# Start a modeler session
# -----------------------
# Start a modeler session to interact with the Ansys Geometry Service. The
# modeler object is used to create designs, sketches, and perform modeling
# operations.
#

modeler = launch_modeler(image=image)
print(modeler)

###############################################################################
# Create PCB geometry
# -----------------------
#

# Define default length units
DEFAULT_UNITS.LENGTH = UNITS.cm

# Define the radius of holes in pcb
pcb_hole_radius = 1

# Create PCB Substrate
sketch_substrate = Sketch()
(
    sketch_substrate.segment(Point2D([5, 0]), Point2D([122, 0]))
    .arc_to_point(Point2D([127, 5]), Point2D([122, 5]))
    .segment_to_point(Point2D([127, 135]))
    .arc_to_point(Point2D([122, 140]), Point2D([122, 135]))
    .segment_to_point(Point2D([5, 140]))
    .arc_to_point(Point2D([0, 135]), Point2D([5, 135]))
    .segment_to_point(Point2D([0, 5]))
    .arc_to_point(Point2D([5, 0]), Point2D([5, 5]))
    .circle(Point2D([6.35, 6.35]), radius=3.94 / 2)
    .circle(Point2D([127 - 6.35, 6.35]), radius=3.94 / 2)
    .circle(Point2D([127 - 6.35, 140 - 6.35]), radius=3.94 / 2)
    .circle(Point2D([6.35, 140 - 6.35]), radius=3.94 / 2)
)
substrate_height = 1.575
plane = Plane(
    origin=Point3D([0, 0, substrate_height]),
    direction_x=[1, 0, 0],
    direction_y=[0, 1, 0],
)

# create IC
sketch_IC = Sketch(plane)
sketch_IC.box(Point2D([62 / 2 + 7.5, 51 / 2 + 5]), 15, 10)

# create capacitor sketch
sketch_capacitor = Sketch(plane=plane)
sketch_capacitor.circle(center=Point2D([95, 104]), radius=4.4)

# create ic
sketch_ic_7 = Sketch(plane=plane)
sketch_ic_7.box(Point2D([25, 108]), 18, 24)

# create ic
sketch_ic_8 = Sketch(plane=plane)
sketch_ic_8.box(Point2D([21, 59]), 10, 18)

###############################################################################
# Modeling operations
# -------------------------
# Now that the sketch is ready to be extruded, perform some modeling operations,
# including creating the design, creating the body directly on the design, and
# plotting the body.
#

# Start by creating the Design
design = modeler.create_design("pcb_design")

# Create all necessary components for pcb
component = design.add_component("PCB")
component.extrude_sketch("substrate", sketch_substrate, distance=substrate_height)
ic_1 = component.extrude_sketch("ic-1", sketch_IC, distance=4.5)

ic_2 = ic_1.copy(parent=component, name="ic-2")
ic_2.translate(direction=UnitVector3D([1, 0, 0]), distance=17)

ic_3 = ic_1.copy(parent=component, name="ic-3")
ic_3.translate(direction=UnitVector3D([0, 1, 0]), distance=17)

ic_4 = ic_2.copy(parent=component, name="ic-4")
ic_4.translate(direction=UnitVector3D([1, 0, 0]), distance=17)

ic_5 = ic_2.copy(parent=component, name="ic-5")
ic_5.translate(direction=UnitVector3D([0, 1, 0]), distance=17)

ic_6 = ic_5.copy(parent=component, name="ic-6")
ic_6.translate(direction=UnitVector3D([1, 0, 0]), distance=17)

ic_7 = component.extrude_sketch("ic-7", sketch=sketch_ic_7, distance=2)
ic_8 = component.extrude_sketch("ic-8", sketch=sketch_ic_8, distance=2)

capacitor_1 = component.extrude_sketch("capacitor_1", sketch_capacitor, distance=20)
capacitor_2 = capacitor_1.copy(parent=component, name="capacitor_2")
capacitor_2.translate(direction=UnitVector3D([0, 1, 0]), distance=-20)
capacitor_3 = capacitor_1.copy(parent=component, name="capacitor_3")
capacitor_3.translate(direction=UnitVector3D([0, 1, 0]), distance=-40)
capacitor_4 = capacitor_1.copy(parent=component, name="capacitor_4")
capacitor_4.translate(direction=UnitVector3D([0, 1, 0]), distance=-60)

# Create named selections
for body in component.bodies:
    design.create_named_selection(name=body.name, bodies=[body])

# Plot the the entire geometry
if GRAPHICS_BOOL:
    design.plot()

###############################################################################
# Export the design
# -----------------
# Once modeling operations are finalized, you can export files
# in different formats. For the formats supported by DMS, see the
# ``DesignFileFormat`` class in the ``Design`` module documentation.
#

# Export files in PMDB format for Mechanical.
OUTPUT_DIR.mkdir(exist_ok=True)
download_file = Path(OUTPUT_DIR, "pcb.pmdb")
design.download(file_location=download_file, format=DesignFileFormat.PMDB)

###############################################################################
# Close session
# -------------
#
# When you finish interacting with your modeling service, you should close the active
# server session. This frees resources wherever the service is running.
#

# Close the server session.
modeler.close()

# HACK: Faking trigger for CI/CD pipeline
