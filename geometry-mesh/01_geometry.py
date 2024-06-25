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

import os
from pathlib import Path

from ansys.geometry.core import launch_modeler
from ansys.geometry.core.connection import GEOMETRY_SERVICE_DOCKER_IMAGE, GeometryContainers
from ansys.geometry.core.designer import DesignFileFormat
from ansys.geometry.core.math import Point2D
from ansys.geometry.core.misc import DEFAULT_UNITS, UNITS, Distance
from ansys.geometry.core.sketch import Sketch

# Check env vars to see which image to launch
#
# --- ONLY FOR WORKFLOW RUNS ---
image = None
if "ANSYS_GEOMETRY_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_GEOMETRY_RELEASE"]
    for geom_services in GeometryContainers:
        if image_tag == f"{GEOMETRY_SERVICE_DOCKER_IMAGE}:{geom_services.value[2]}":
            print(f"Using {image_tag} image")
            image = geom_services
            break

# -- Parameters --
#
GRAPHICS_BOOL = False  # Set to True to display the graphics
OUTPUT_DIR = Path(Path(__file__).parent, "outputs")  # Output directory

# -- Start a modeler session --
#
modeler = launch_modeler(image=image)
print(modeler)

# -- Create and plot a sketch --
#
# Define default length units
DEFAULT_UNITS.LENGTH = UNITS.cm

# Define the radius of the outer holes
outer_hole_radius = Distance(0.5)

sketch = Sketch()
(
    sketch.segment(start=Point2D([-4, 5]), end=Point2D([4, 5]))
    .segment_to_point(end=Point2D([4, -5]))
    .segment_to_point(end=Point2D([-4, -5]))
    .segment_to_point(end=Point2D([-4, 5]))
    .box(
        center=Point2D([0, 0]),
        width=Distance(3),
        height=Distance(3),
    )
    .circle(center=Point2D([3, 4]), radius=outer_hole_radius)
    .circle(center=Point2D([-3, -4]), radius=outer_hole_radius)
    .circle(center=Point2D([-3, 4]), radius=outer_hole_radius)
    .circle(center=Point2D([3, -4]), radius=outer_hole_radius)
)

# -- Perform some modeling operations --
#
# Now that the sketch is ready to be extruded, perform some modeling operations,
# including creating the design, creating the body directly on the design, and
# plotting the body.

# Start by creating the Design
design = modeler.create_design("ModelingDemo")

# Create a body directly on the design by extruding the sketch
body = design.extrude_sketch(name="Design_Body", sketch=sketch, distance=Distance(1))

# Plot the body
if GRAPHICS_BOOL:
    design.plot()

# -- Export file --
#
# Once modeling operations are finalized, you can export files
# in different formats. For the formats supported by DMS, see the
# ``DesignFileFormat`` class in the ``Design`` module documentation.
#
# Export files in SCDOCX and FMD formats.

# Download the design in FMD format
OUTPUT_DIR.mkdir(exist_ok=True)
download_file = Path(OUTPUT_DIR, "modeling_demo.fmd")
design.download(file_location=download_file, format=DesignFileFormat.FMD)

# -- Close session --
#
# When you finish interacting with your modeling service, you should close the active
# server session. This frees resources wherever the service is running.
#
# Close the server session.
modeler.close()
