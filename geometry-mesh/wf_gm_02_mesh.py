# Copyright (C) 2024 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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
.. _ref_geometry-mesh_02-mesh:

Mesh generation
###############

This example shows how to generate a mesh from a CAD model. The CAD model is
imported from a file, and the mesh is generated using the Ansys PRIME API.

"""  # noqa: D400, D415

# sphinx_gallery_thumbnail_number = 2

import os
from pathlib import Path

from ansys.meshing import prime
from ansys.meshing.prime.graphics import Graphics

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gm_02_mesh.py")
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
# Start a PRIME session
# ---------------------
# Start a PRIME session and get the model from the client.
#
prime_client = prime.launch_prime(timeout=120)
print(prime_client)

# Get the model from the client
model = prime_client.model

###############################################################################
# Load the CAD file
# -----------------
# Load the CAD file from the previous example. The file is loaded into the
# model, and the part is extracted. The part is then summarized to get the
# details of the part.

# Load the FMD file
modeling_file = Path(OUTPUT_DIR, "modeling_demo.fmd")
file_io = prime.FileIO(model)
file_io.import_cad(
    file_name=str(modeling_file),
    params=prime.ImportCadParams(
        model=model,
    ),
)

# Review the part
part = model.get_part_by_name("modelingdemo")
part_summary_res = part.get_summary(prime.PartSummaryParams(model, print_mesh=False))
print(part_summary_res)

###############################################################################
# Mesh generation
# ---------------
# The mesh is generated using the Ansys PRIME API. The mesh is generated using
# the following steps:
#
# 1. Mesh the surfaces of the part.
# 2. Mesh the volume of the part.
# 3. Write the mesh to a file.
#

# Element size
element_size = 2.0

# Get topoface IDs
faces = part.get_topo_faces()

###############################################################################
# Surface meshing
# ---------------
# The surface mesh is generated using the previous element size and the
# topological faces of the part.
#

surfer_params = prime.SurferParams(
    model=model,
    size_field_type=prime.SizeFieldType.CONSTANT,
    constant_size=element_size,
)

surfer_result = prime.Surfer(model).mesh_topo_faces(part.id, topo_faces=faces, params=surfer_params)

###############################################################################
# Volume meshing
# ---------------
#

volume_mesh = prime.AutoMesh(model)
auto_mesh_param = prime.AutoMeshParams(
    model,
    size_field_type=prime.SizeFieldType.GEOMETRIC,
    volume_fill_type=prime.VolumeFillType.TET,
)
volume_mesh.mesh(part.id, auto_mesh_param)

# Display the mesh
if GRAPHICS_BOOL:
    display = Graphics(model=model)
    display()

# Review the mesh
part = model.get_part_by_name("modelingdemo")
part_summary_res = part.get_summary(prime.PartSummaryParams(model, print_mesh=True))
print(part_summary_res)

###############################################################################
# Export the mesh
# ---------------
# The mesh is exported to a CDB file. The CDB file can be used to create a
# MAPDL case.
#
mapdl_cdb = Path(OUTPUT_DIR, "modeling_demo.cdb")
file_io.export_mapdl_cdb(str(mapdl_cdb), params=prime.ExportMapdlCdbParams(model))
assert os.path.exists(mapdl_cdb)
print(f"MAPDL case exported at {mapdl_cdb}")

###############################################################################
# Close the PRIME session
# -----------------------
# Close the PRIME session to release the resources. This is important to
# prevent memory leaks.
prime_client.exit()
