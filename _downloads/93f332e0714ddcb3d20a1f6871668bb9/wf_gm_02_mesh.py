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
"""
.. _ref_geometry-mesh_02-mesh:

Mesh generation
###############

This example shows how to generate a mesh from a CAD model. The CAD model is
imported from a file, and the mesh is generated using the Ansys PRIME API.

"""  # noqa: D400, D415

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
    file_name=modeling_file,
    params=prime.ImportCadParams(
        model=model,
    ),
)

# Review the part
part = model.get_part_by_name("modelingdemo")
part_summary_res = part.get_summary(prime.PartSummaryParams(model, print_mesh=False))
print(part_summary_res)

if GRAPHICS_BOOL:
    display = Graphics(model=model)
    display()

###############################################################################
# Mesh generation
# ---------------
# The mesh is generated using the Ansys PRIME API. The mesh is generated using
# the following steps:
#
# 1. Initialize the connection tolerance and other parameters.
# 2. Scaffold the part.
# 3. Mesh the surfaces.
# 4. Write the mesh to a file.
#

# Initialize the connection tolerance and other parameters --
#
# Target element size
element_size = 0.5

# Initialize the parameters
params = prime.ScaffolderParams(
    model,
    absolute_dist_tol=0.1 * element_size,
    intersection_control_mask=prime.IntersectionMask.FACEFACEANDEDGEEDGE,
    constant_mesh_size=element_size,
)

# Get existing topoface or topoedge IDs
faces = part.get_topo_faces()
beams = []

scaffold_res = prime.Scaffolder(model, part.id).scaffold_topo_faces_and_beams(
    topo_faces=faces, topo_beams=beams, params=params
)
print(scaffold_res)

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
    generate_quads=True,
)

surfer_result = prime.Surfer(model).mesh_topo_faces(part.id, topo_faces=faces, params=surfer_params)

# Display the mesh
if GRAPHICS_BOOL:
    display = Graphics(model=model)
    display()

###############################################################################
# Export the mesh
# ---------------
# The mesh is exported to a CDB file. The CDB file can be used to create a
# MAPDL case.
#
mapdl_cdb = Path(OUTPUT_DIR, "modeling_demo.cdb")
file_io.export_mapdl_cdb(mapdl_cdb, params=prime.ExportMapdlCdbParams(model))
assert os.path.exists(mapdl_cdb)
print(f"MAPDL case exported at {mapdl_cdb}")

###############################################################################
# Close the PRIME session
# -----------------------
# Close the PRIME session to release the resources. This is important to
# prevent memory leaks.
prime_client.exit()
