from pint import Quantity

from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.sketch import Sketch

from ansys.geometry.core import Modeler

# draw pipe
# plane = Plane(origin=Point3D([0,0,0]), direction_x=Vector3D([1,0,0]), direction_y=Vector3D([0,0,1]))
# sketch = Sketch(plane)

sketch = Sketch()

(
    sketch.circle(Point2D([0, 0], UNITS.mm), Quantity(2, UNITS.cm), "input")
      .circle(Point2D([0, 0], UNITS.mm), Quantity(3, UNITS.cm), "output")
)

sketch.plot()


# Start by creating the Design
modeler = Modeler()
design = modeler.create_design("Pipe")

# Create a body directly on the design by extruding the sketch
body = design.extrude_sketch(
    name="Pipe_Body", sketch=sketch, distance=Distance(15, unit=UNITS.cm)
)

# Plot the body
design.plot()

# Download and save design
cad_file = "D:\\test"
design.download(cad_file, as_stream=False)


# Import the geometry and mesh it
import os
import tempfile

from ansys.meshing import prime
from ansys.meshing.prime.graphics import Graphics

prime_client = prime.launch_prime()
model = prime_client.model
mesh_util = prime.lucid.Mesh(model=model)

# with prime.launch_prime() as session:
#     model = session.model

#     with prime.FileIO(model) as io:
#         _ = io.import_cad(cad_file, params=prime.ImportCADParams(model))
#     prime.lucid.Mesh(model=model)

mesh_util.read(file_name=cad_file)
mesh_util.create_zones_from_labels("inlet,outlet")

# Surface meshing
mesh_util.surface_mesh(min_size=5, max_size=20)

# Volume meshing
mesh_util.volume_mesh(
    volume_fill_type=prime.VolumeFillType.POLY,
    prism_surface_expression="* !inlet !outlet",
    prism_layers=3,
)

# Display the mesh
display = Graphics(model=model)
display()

