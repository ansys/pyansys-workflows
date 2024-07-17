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
.. _ref_geometry-mesh-fluent_02-fluent-meshing:

Mesh generation
###############

This example demonstrates how to generate a mesh for a NACA airfoil using Fluent Meshing.

Starting from the geometry created in the previous example, the script generates a mesh
using Fluent Meshing. The parameters are set to generate a mesh with a surface mesh size
of 2 and 1000, and a volume mesh size of 512. It leverages the Fluent Meshing Workflow
API to create the mesh.

"""  # noqa: D400, D415

import os

import ansys.fluent.core as pyfluent

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
from pathlib import Path  # isort:skip

if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "02_fluent_meshing.py")
# sphinx_gallery_end_ignore

###############################################################################
# Parameters for the script
# -------------------------
# The following parameters are used to control the script execution. You can
# modify these parameters to suit your needs.
#

# NACA 4-digits airfoil geometry
NACA_AIRFOIL = "6412"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

###############################################################################
# Generate the mesh
# -----------------
# The function `generate_mesh` generates a mesh for a NACA airfoil using Fluent Meshing.
# The function takes the following parameters:
#
# - `naca_airfoil`: NACA 4-digits airfoil number.
# - `data_dir`: Directory to save the mesh file.
# - `ui_mode`: User interface mode. The default is None.
# - `container_dict`: Configuration for the Fluent container. The default is None.
#
# The function launches Fluent Meshing and initializes the workflow for watertight geometry.
# It imports the geometry, generates the surface mesh, describes the geometry, updates
# boundaries and regions, adds boundary layers, generates the volume mesh, checks the mesh,
# writes the mesh, and closes Fluent Meshing.
#


def generate_mesh(
    naca_airfoil: str,
    data_dir: str,
    ui_mode: str | None = None,
    container_dict: dict | None = None,
):
    """
    Generate a mesh for a NACA airfoil using Fluent Meshing.

    Parameters
    ----------
    naca_airfoil : str
        NACA 4-digits airfoil number.
    data_dir : str
        Directory to save the mesh file.
    ui_mode : str, optional
        User interface mode. The default is None.
    container_dict : dict, optional
        Configuration for the Fluent container. The default is None.
    """

    # Launch Fluent Meshing
    if container_dict is not None:
        meshing = pyfluent.launch_fluent(
            container_dict=container_dict,
            start_container=True,
            precision="double",
            processor_count=4,
            mode="meshing",
            ui_mode="no_gui_or_graphics",
            cwd=data_dir,
            cleanup_on_exit=False,
        )
    else:
        meshing = pyfluent.launch_fluent(
            precision="double",
            processor_count=4,
            mode="meshing",
            ui_mode=ui_mode,
            cwd=data_dir,
        )

    # Initialize workflow - Watertight Geometry
    meshing.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")

    # Import the geometry
    geo_import = meshing.workflow.TaskObject["Import Geometry"]
    geo_import.Arguments.set_state(
        {
            "FileName": os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}.pmdb"),
        }
    )
    geo_import.Execute()

    # Generate surface mesh
    surface_mesh_gen = meshing.workflow.TaskObject["Generate the Surface Mesh"]
    surface_mesh_gen.Arguments.set_state(
        {"CFDSurfaceMeshControls": {"MaxSize": 1000, "MinSize": 2}}
    )
    surface_mesh_gen.Execute()

    # Describe the geometry
    describe_geo = meshing.workflow.TaskObject["Describe Geometry"]
    describe_geo.UpdateChildTasks(SetupTypeChanged=False)
    describe_geo.Arguments.set_state(
        {"SetupType": "The geometry consists of only fluid regions with no voids"}
    )
    describe_geo.UpdateChildTasks(SetupTypeChanged=True)
    describe_geo.Execute()

    # Update boundaries
    meshing.workflow.TaskObject["Update Boundaries"].Execute()

    # Update regions
    meshing.workflow.TaskObject["Update Regions"].Execute()

    # Add boundary layers
    add_boundary_layer = meshing.workflow.TaskObject["Add Boundary Layers"]
    add_boundary_layer.Arguments.set_state({"NumberOfLayers": 12})
    add_boundary_layer.AddChildAndUpdate()

    # Generate volume mesh
    volume_mesh_gen = meshing.workflow.TaskObject["Generate the Volume Mesh"]
    volume_mesh_gen.Arguments.set_state(
        {
            "VolumeFill": "poly-hexcore",
            "VolumeFillControls": {"HexMaxCellLength": 512},
            "VolumeMeshPreferences": {
                "CheckSelfProximity": "yes",
                "ShowVolumeMeshPreferences": True,
            },
        }
    )
    volume_mesh_gen.Execute()

    # Check mesh
    meshing.tui.mesh.check_mesh()

    # Write mesh
    meshing.tui.file.write_mesh(os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}.msh.h5"))

    # Close Fluent Meshing
    meshing.exit()


###############################################################################
# Executing the mesh generation
# -----------------------------
# The previous function is called to generate the mesh for the NACA airfoil.
# The mesh is saved in the `outputs` directory. Depending on the environment,
# the script will run in a container or locally.
#
# Depending on the environment, the script will run in a container or locally.
#

if os.getenv("PYANSYS_WORKFLOWS_CI") == "true":
    container_dict = {
        "fluent_image": f"{os.environ['FLUENT_DOCKER_IMAGE']}:{os.environ['FLUENT_IMAGE_TAG']}",
        "host_mount_path": DATA_DIR,
        "license_server": os.environ["ANSYSLMD_LICENSE_FILE"],
        "timeout": 300,
    }
    # https://fluent.docs.pyansys.com/version/stable/api/general/launcher/fluent_container.html
    generate_mesh(NACA_AIRFOIL, "/mnt/pyfluent", container_dict=container_dict)
else:
    generate_mesh(NACA_AIRFOIL, DATA_DIR)
