from pint import Quantity

from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.sketch import Sketch

# draw pipe
# plane = Plane(origin=Point3D([0,0,0]), direction_x=Vector3D([1,0,0]), direction_y=Vector3D([0,0,1]))

sketch = Sketch(plane)

(
    sketch.circle(Point2D([0, 0], UNITS.mm), Quantity(2, UNITS.cm), "input")
      .circle(Point2D([0, 0], UNITS.mm), Quantity(3, UNITS.cm), "output")
)

sketch.plot()


# Start by creating the Design
design = modeler.create_design("Pipe")

# Create a body directly on the design by extruding the sketch
body = design.extrude_sketch(
    name="Pipe_Body", sketch=sketch, distance=Distance(15, unit=UNITS.cm)
)

# Plot the body
design.plot()