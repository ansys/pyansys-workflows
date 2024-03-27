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

from ansys.geometry.core import Modeler
from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.misc.measurements import Distance
from ansys.geometry.core.sketch import Sketch
from pint import Quantity

# Start by creating the Design
modeler = Modeler()
design = modeler.create_design("Pipe")

sketch3 = Sketch()
plane = Plane(
    origin=Point3D([-4, 0, 0], UNITS.cm),
    direction_x=Vector3D([0, -1, 0]),
    direction_y=Vector3D([0, 0, -1]),
)
sketch3 = Sketch(plane)
sketch3.box(Point2D([0, 0]), Quantity(6, UNITS.cm), Quantity(6, UNITS.cm))

# sketch3.plot()

sketch4 = Sketch()
plane = Plane(
    origin=Point3D([-4, 0, 0], UNITS.cm),
    direction_x=Vector3D([0, -1, 0]),
    direction_y=Vector3D([0, 0, -1]),
)
sketch4 = Sketch(plane)
sketch4.box(Point2D([0, 0]), Quantity(3, UNITS.cm), Quantity(3, UNITS.cm))

# sketch4.plot()

main_rectangle = design.extrude_sketch(
    name="Pipe_Body", sketch=sketch3, distance=Distance(17, unit=UNITS.cm)
)


second_rectangle = design.extrude_sketch(
    name="Pipe_Body2", sketch=sketch4, distance=Distance(15, unit=UNITS.cm)
)

main_rectangle.subtract(second_rectangle)


# Plot the body
design.plot()

# Download and save design
cad_file = "D:\\test.scdocx"
design.download(cad_file)
