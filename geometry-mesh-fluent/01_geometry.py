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
from typing import List, Union

from ansys.geometry.core import Modeler, launch_modeler
from ansys.geometry.core.connection import GEOMETRY_SERVICE_DOCKER_IMAGE, GeometryContainers
from ansys.geometry.core.math import Plane, Point2D, Point3D
from ansys.geometry.core.plotting import PlotterHelper
from ansys.geometry.core.sketch import Sketch
import numpy as np

####################################################################################################
# Default parameters - when running the script directly
####################################################################################################

# Type of airfoil to generate
NACA_AIRFOIL = "6412"

# Dimensions of the fluid domain
# LENGTH - X-axis
# WIDTH - Z-axis
# HEIGHT - Y-axis
#
BOX_SIZE_LENGTH = 10
BOX_SIZE_WIDTH = 5
BOX_SIZE_HEIGHT = 2

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

####################################################################################################
# Functions
####################################################################################################


def naca_airfoil_4digits(number: Union[int, str], n_points: int = 200) -> List[Point2D]:
    """
    Generate a NACA 4-digits airfoil.

    Parameters
    ----------
    number : int or str
        NACA 4-digit number.
    n_points : int
        Number of points to generate the airfoil. The default is ``200``.
        Number of points in the upper side of the airfoil.
        The total number of points is ``2 * n_points - 1``.

    Returns
    -------
    List[Point2D]
        List of points that define the airfoil.
    """
    # Check if the number is a string
    if isinstance(number, str):
        number = int(number)

    # Calculate the NACA parameters
    m = number // 1000 * 0.01
    p = number // 100 % 10 * 0.1
    t = number % 100 * 0.01

    # Generate the airfoil
    points = []
    for i in range(n_points):

        # Make it a exponential distribution so the points are more concentrated
        # near the leading edge
        x = (1 - np.cos(i / (n_points - 1) * np.pi)) / 2

        # Check if it is a symmetric airfoil or not
        if p == 0 and m == 0:
            # Camber line is zero in this case
            yc = 0
            dyc_dx = 0
        else:
            # Compute the camber line
            if x < p:
                yc = m / p**2 * (2 * p * x - x**2)
                dyc_dx = 2 * m / p**2 * (p - x)
            else:
                yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2)
                dyc_dx = 2 * m / (1 - p) ** 2 * (p - x)

        # Compute the thickness
        yt = 5 * t * (0.2969 * x**0.5 - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)

        # Compute the angle
        theta = np.arctan(dyc_dx)

        # Compute the points (upper and lower side of the airfoil)
        xu = x - yt * np.sin(theta)
        yu = yc + yt * np.cos(theta)
        xl = x + yt * np.sin(theta)
        yl = yc - yt * np.cos(theta)

        # Append the points
        points.append(Point2D([xu, yu]))
        points.insert(0, Point2D([xl, yl]))

        # Remove the first point since it is repeated
        if i == 0:
            points.pop(0)

    return points


####################################################################################################
# Main logic
####################################################################################################


def generate_geometry(
    naca_airfoil: str,
    box_size_length: int,
    box_size_width: int,
    box_size_height: int,
    data_dir: str,
    modeler: Modeler,
):
    """
    Generate the geometry of a NACA airfoil and the surrounding fluid domain
    using PyAnsys Geometry.

    Parameters
    ----------
    naca_airfoil : str
        NACA 4-digits airfoil.
    box_size_length : int
        Length of the fluid domain along the X-axis.
    box_size_width : int
        Width of the fluid domain along the Z-axis.
    box_size_height : int
        Height of the fluid domain along the Y-axis.
    data_dir : str
        Directory to save the generated geometry.
    modeler : Modeler
        PyAnsys Geometry Modeler instance.
    """
    # Create the design
    design = modeler.create_design(f"NACA_Airfoil_{naca_airfoil}")

    # Create a sketch
    airfoil_sketch = Sketch()

    # Generate the points of the airfoil
    points = naca_airfoil_4digits(naca_airfoil)

    # Create the segments of the airfoil
    for i in range(len(points) - 1):
        airfoil_sketch.segment(points[i], points[i + 1])

    # Close the airfoil
    airfoil_sketch.segment(points[-1], points[0])

    # Plot the airfoil
    airfoil_sketch.plot()

    # Extrude the airfoil
    airfoil = design.extrude_sketch("Airfoil", airfoil_sketch, 1)

    # Plot the design
    design.plot()

    # Create the surrounding fluid domain
    #
    # The airfoil has the following dimensions:
    # - Chord length: 1 (X-axis)
    # - Thickness: depends on NACA value (Y-axis)
    #
    # The fluid domain will be a large box with the following dimensions:
    # - Length  (X-axis)
    # - Width   (Z-axis)
    # - Height  (Y-axis)
    #
    # The airfoil will be placed at the center of the fluid domain
    #
    # Create the sketch
    fluid_sketch = Sketch(plane=Plane(origin=Point3D([0, 0, 0.5 - (box_size_width / 2)])))
    fluid_sketch.box(
        center=Point2D([0.5, 0]),
        height=box_size_height,
        width=box_size_length,
    )
    fluid_sketch.plot()

    # Extrude the fluid domain
    fluid = design.extrude_sketch("Fluid", fluid_sketch, box_size_width)

    # Create named selections in the fluid domain - inlet, outlet, and surrounding faces
    # Add also the airfoil as a named selection
    fluid_faces = fluid.faces
    surrounding_faces = []
    inlet_faces = []
    outlet_faces = []
    for face in fluid_faces:
        if face.normal().x == 1:
            outlet_faces.append(face)
        elif face.normal().x == -1:
            inlet_faces.append(face)
        else:
            surrounding_faces.append(face)

    design.create_named_selection("Outlet Fluid", faces=outlet_faces)
    design.create_named_selection("Inlet Fluid", faces=inlet_faces)
    design.create_named_selection("Surrounding Faces", faces=surrounding_faces)
    design.create_named_selection("Airfoil Faces", faces=airfoil.faces)

    # Plot the design intelligently...
    plotter_helper = PlotterHelper()
    plotter_helper.add(airfoil, color="blue")
    plotter_helper.add(fluid, color="green", opacity=0.25)
    plotter_helper.show_plotter()

    # Save the design
    file = design.export_to_pmdb(data_dir)
    print(f"Design saved to {file}")

    return


####################################################################################################

if __name__ == "__main__":
    # Check env vars to see which image to launch
    #
    # --- ONLY FOR WORKFLOW RUNS ---
    image = None
    if "ANSYS_GEOMETRY_RELEASE" in os.environ:
        image_tag = os.environ["ANSYS_GEOMETRY_RELEASE"]
        for geom_services in GeometryContainers:
            if image_tag == f"{GEOMETRY_SERVICE_DOCKER_IMAGE}:{geom_services.value[2]}":
                image = geom_services
                break

    # Instantiate the modeler
    modeler = launch_modeler(image=image)

    # Generate the geometry
    generate_geometry(
        NACA_AIRFOIL, BOX_SIZE_LENGTH, BOX_SIZE_WIDTH, BOX_SIZE_HEIGHT, DATA_DIR, modeler
    )

    # Close the modeler
    modeler.close()
