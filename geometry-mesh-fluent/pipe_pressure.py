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

# import ansys.fluent.core as pyfluent
# from ansys.geometry.core import Modeler
# from ansys.geometry.core.math import Plane, Point2D, Point3D, Vector3D
# from ansys.geometry.core.misc import UNITS
# from ansys.geometry.core.misc.measurements import Distance
# from ansys.geometry.core.sketch import Sketch
# from pint import Quantity

# print("Hello World")

# # draw pipe
# plane = Plane(origin=Point3D([0,0,0]),
#               direction_x=Vector3D([1,0,0]),
#               direction_y=Vector3D([0,0,1])
#               )
# sketch = Sketch(plane)

# sketch = Sketch()
# (
#     sketch.circle(Point2D([0, 0], UNITS.mm), Quantity(2, UNITS.cm))
#       .circle(Point2D([0, 0], UNITS.mm), Quantity(3, UNITS.cm))
# )


# sketch2 = Sketch()
# (
#     sketch2.circle(Point2D([10, 0], UNITS.cm), Quantity(2, UNITS.cm))
#       .circle(Point2D([10, 0], UNITS.cm), Quantity(3, UNITS.cm))
# )

# # sketch.plot()


# # Start by creating the Design
# modeler = Modeler()
# design = modeler.create_design("Pipe")

# # Create a body directly on the design by extruding the sketch
# body = design.extrude_sketch(
#     name="Pipe_Body", sketch=sketch, distance=Distance(15, unit=UNITS.cm)
# )

# body = design.extrude_sketch(
#     name="Pipe_Body", sketch=sketch2, distance=Distance(15, unit=UNITS.cm)
# )


# sketch3 = Sketch()
# plane = Plane(origin=Point3D([-4,0,0], UNITS.cm),
#               direction_x=Vector3D([0,-1,0]),
#               direction_y=Vector3D([0,0,-1]))
# sketch3 = Sketch(plane)
# sketch3.box(Point2D([0,0]), Quantity(6, UNITS.cm), Quantity(6, UNITS.cm))

# sketch4 = Sketch()
# plane = Plane(origin=Point3D([-4,0,0], UNITS.cm),
#               direction_x=Vector3D([0,-1,0]),
#               direction_y=Vector3D([0,0,-1]))
# sketch4 = Sketch(plane)
# sketch4.box(Point2D([0,0]), Quantity(3, UNITS.cm), Quantity(3, UNITS.cm))


# # sketch3.plot()

# main_rectangle = design.extrude_sketch(
#     name="Pipe_Body", sketch=sketch3, distance=Distance(17, unit=UNITS.cm)
# )


# second_rectangle = design.extrude_sketch(
#     name="Pipe_Body2", sketch=sketch4, distance=Distance(15, unit=UNITS.cm)
# )

# main_rectangle.subtract(second_rectangle)


# # Plot the body
# design.plot()

# # Download and save design
# cad_file = "D:\\test.scdocx"
# design.download(cad_file)


# # Import the geometry and mesh it
# import os
# import tempfile

# from ansys.meshing import prime
# from ansys.meshing.prime.graphics import Graphics

# prime_client = prime.launch_prime(version="23.2")
# model = prime_client.model
# mesh_util = prime.lucid.Mesh(model=model)

# # with prime.launch_prime() as session:
# #     model = session.model

# #     with prime.FileIO(model) as io:
# #         _ = io.import_cad(cad_file, params=prime.ImportCADParams(model))
# #     prime.lucid.Mesh(model=model)

# mesh_util.read(file_name=cad_file)
# mesh_util.create_zones_from_labels("inlet,outlet")

# # Surface meshing
# mesh_util.surface_mesh(min_size=5, max_size=20)

# # Volume meshing
# mesh_util.volume_mesh(
#     volume_fill_type=prime.VolumeFillType.POLY,
#     prism_surface_expression="* !inlet !outlet",
#     prism_layers=3,
# )

# # Display the mesh
# display = Graphics(model=model)
# display()

# # Write the mesh
# # with tempfile.TemporaryDirectory() as temp_folder:
# #     print(temp_folder)
# #     mesh_file = os.path.join(temp_folder, "pipe.cas")
# #     mesh_util.write(mesh_file)
# #     assert os.path.exists(mesh_file)
# #     print("\nExported file:\n", mesh_file)

# mesh_file = "D:\\pipe.cas"
# mesh_util.write(mesh_file)
# assert os.path.exists(mesh_file)

# # Fluent
# solver = pyfluent.launch_fluent(precision="double", processor_count=2, mode="solver")

# # Import mesh and perform mesh check
# solver.file.read(file_type="case", file_name=mesh_file)
# solver.tui.mesh.check()

# # Set working units for mesh
# solver.tui.define.units("length", "cm")

# # Create material
# solver.setup.materials.database.copy_by_name(type="fluid", name="water-liquid")

# # Set up cell zone conditions
# solver.setup.cell_zone_conditions.fluid["pipe_body."].material = "water-liquid"

# cold_inlet = solver.setup.boundary_conditions.velocity_inlet["inlet1"]
# cold_inlet.vmag = 0.4
# cold_inlet.ke_spec = "Intensity and Hydraulic Diameter"
# cold_inlet.turb_intensity = 0.05
# cold_inlet.turb_hydraulic_diam = "4 [in]"
# cold_inlet.t = 293.15

# hot_inlet = solver.setup.boundary_conditions.velocity_inlet["outlet"]
# hot_inlet.vmag = 1.2
# hot_inlet.ke_spec = "Intensity and Hydraulic Diameter"
# hot_inlet.turb_hydraulic_diam = "1 [in]"
# hot_inlet.t = 313.15

# solver.setup.boundary_conditions.pressure_outlet["outlet"].turb_viscosity_ratio = 4

# # Initialize the flow field using hybrid initialization.
# solver.solution.initialization.hybrid_initialize()

# # Create velocity vectors

# solver.results.graphics.vector["velocity_vector_symmetry"] = {}
# velocity_symmetry = solver.results.graphics.vector["velocity_vector_symmetry"]
# velocity_symmetry.print_state()
# velocity_symmetry.field = "temperature"
# velocity_symmetry.surfaces_list = ["symmetry-xyplane"]
# velocity_symmetry.scale.scale_f = 4
# velocity_symmetry.style = "arrow"


# # Display contour
# solver.results.graphics.contour.create("contour_vf_vapor")

# contour_vf_vapor = {
#     "coloring": {"option": "banded", "smooth": False},
#     "field": "vapor-vof",
#     "filled": True,
# }

# solver.results.graphics.contour["contour_vf_vapor"] = contour_vf_vapor

# solver.results.graphics.contour["contour_vf_vapor"].display()

# solver.results.graphics.picture.save_picture(file_name="contour_vf_vapor.png")
