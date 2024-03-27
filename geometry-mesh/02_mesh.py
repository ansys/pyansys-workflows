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

from ansys.meshing import prime
from ansys.meshing.prime.graphics import Graphics

OUTPUT_DIR = Path(Path(__file__).parent, "outputs")

# -- Launch the PRIME client --
#
prime_client = prime.launch_prime()
model = prime_client.model

# Load the FMD file
modeling_file = Path(OUTPUT_DIR, "modeling_demo.fmd")
file_io = prime.FileIO(model)
file_io.import_cad(
    file_name=modeling_file,
    params=prime.ImportCadParams(
        model=model,
        length_unit=prime.LengthUnit.CM,
        part_creation_type=prime.PartCreationType.MODEL,
    ),
)

# -- Review the part --
#
part = model.get_part_by_name("Design_Body")
part_summary_res = part.get_summary(prime.PartSummaryParams(model, print_mesh=False))
print(part_summary_res)

display = Graphics(model=model)
display()

# -- Initialize the connection tolerance and other parameters --
#
# Target element size
element_size = 0.5

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

# -- Surface meshing --
#
surfer_params = prime.SurferParams(
    model=model,
    size_field_type=prime.SizeFieldType.CONSTANT,
    constant_size=element_size,
    generate_quads=True,
)

surfer_result = prime.Surfer(model).mesh_topo_faces(part.id, topo_faces=faces, params=surfer_params)

# Display the mesh
display = Graphics(model=model)
display()

# -- Write the mesh --
#
mapdl_cdb = Path(OUTPUT_DIR, "modeling_demo.cdb")
file_io.export_mapdl_cdb(mapdl_cdb, params=prime.ExportMapdlCdbParams(model))
assert os.path.exists(mapdl_cdb)
print(f"MAPDL case exported at {mapdl_cdb}")
