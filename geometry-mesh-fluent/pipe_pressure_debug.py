from pint import Quantity

from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.sketch import Sketch

from ansys.geometry.core.misc.measurements import Distance

from ansys.geometry.core import Modeler

# Start by creating the Design
modeler = Modeler()
design = modeler.create_design("Pipe")

sketch3 = Sketch()
plane = Plane(origin=Point3D([-4,0,0], UNITS.cm), direction_x=Vector3D([0,-1,0]), direction_y=Vector3D([0,0,-1]))
sketch3 = Sketch(plane)
sketch3.box(Point2D([0,0]), Quantity(6, UNITS.cm), Quantity(6, UNITS.cm))

# sketch3.plot()

sketch4 = Sketch()
plane = Plane(origin=Point3D([-4,0,0], UNITS.cm), direction_x=Vector3D([0,-1,0]), direction_y=Vector3D([0,0,-1]))
sketch4 = Sketch(plane)
sketch4.box(Point2D([0,0]), Quantity(3, UNITS.cm), Quantity(3, UNITS.cm))

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