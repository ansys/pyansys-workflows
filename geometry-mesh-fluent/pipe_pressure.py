from pint import Quantity

from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.sketch import Sketch

from ansys.geometry.core import Modeler

import ansys.fluent.core as pyfluent

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

# Fluent
solver = pyfluent.launch_fluent(precision="double", processor_count=2, mode="solver")

# Import mesh and perform mesh check
solver.file.read(file_type="case", file_name=import_filename)
solver.tui.mesh.check()

# Set working units for mesh
solver.tui.define.units("length", "cm")

# Create material
solver.setup.materials.database.copy_by_name(type="fluid", name="water-liquid")

# Set up cell zone conditions
solver.setup.cell_zone_conditions.fluid["elbow-fluid"].material = "water-liquid"

cold_inlet = solver.setup.boundary_conditions.velocity_inlet["cold-inlet"]
cold_inlet.vmag = 0.4
cold_inlet.ke_spec = "Intensity and Hydraulic Diameter"
cold_inlet.turb_intensity = 0.05
cold_inlet.turb_hydraulic_diam = "4 [in]"
cold_inlet.t = 293.15

hot_inlet = solver.setup.boundary_conditions.velocity_inlet["hot-inlet"]
hot_inlet.vmag = 1.2
hot_inlet.ke_spec = "Intensity and Hydraulic Diameter"
hot_inlet.turb_hydraulic_diam = "1 [in]"
hot_inlet.t = 313.15

solver.setup.boundary_conditions.pressure_outlet["outlet"].turb_viscosity_ratio = 4

# Initialize the flow field using hybrid initialization.
solver.solution.initialization.hybrid_initialize()

# Create velocity vectors

solver.results.graphics.vector["velocity_vector_symmetry"] = {}
velocity_symmetry = solver.results.graphics.vector["velocity_vector_symmetry"]
velocity_symmetry.print_state()
velocity_symmetry.field = "temperature"
velocity_symmetry.surfaces_list = ["symmetry-xyplane"]
velocity_symmetry.scale.scale_f = 4
velocity_symmetry.style = "arrow"