# Copyright (C) 2024 - 2024 ANSYS, Inc. and/or its affiliates.
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

import ansys.fluent.core as pyfluent

####################################################################################################
# Default parameters - when running the script directly
####################################################################################################

# NACA 4-digits airfoil geometry
NACA_AIRFOIL = "6412"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")


####################################################################################################
# Fluent Meshing
####################################################################################################


def generate_mesh(naca_airfoil: str, data_dir: str, ui_mode: str = "gui"):
    """
    Generate a mesh for a NACA airfoil using Fluent Meshing.

    Parameters
    ----------
    naca_airfoil : str
        NACA 4-digits airfoil number.
    data_dir : str
        Directory to save the mesh file.
    ui_mode : str, optional
        User interface mode. The default is "gui".
    """

    # Launch Fluent Meshing
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


if __name__ == "__main__":
    # Generate the mesh
    generate_mesh(NACA_AIRFOIL, DATA_DIR)
