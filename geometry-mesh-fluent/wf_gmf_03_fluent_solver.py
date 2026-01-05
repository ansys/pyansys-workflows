# Copyright (C) 2024 - 2026 ANSYS, Inc. and/or its affiliates.
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
.. _ref_geometry-mesh-fluent_03-fluent-solver:

Fluids simulation
#################

This example demonstrates how to solve the flow around a NACA airfoil using Fluent.

Starting from the mesh created in the previous example, the script solves the
flow around a NACA airfoil using Fluent. The parameters are set to solve the flow
with a Mach number of 0.3, a temperature of 255.56 K, an angle of attack of 3.06 degrees,
and a pressure of 80600 Pa. Overall, these are the conditions for a compressible flow.

"""  # noqa: D400, D415

import os

import ansys.fluent.core as pyfluent
import numpy as np

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
from pathlib import Path  # isort:skip

if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gmf_03_fluent_solver.py")
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

# Simulation parameters
SIM_MACH = 0.3  # 0.8395 # Mach number
SIM_TEMPERATURE = 255.56  # In Kelvin
SIM_AOA = 3.06  # in degrees
SIM_PRESSURE = 80600  # in Pa

###############################################################################
# Solve the flow around the airfoil
# ---------------------------------
# The function `solve_airfoil_flow` solves the flow around a NACA airfoil using Fluent.
# The function takes the following parameters:
#
# - `naca_airfoil`: NACA 4-digits airfoil number.
# - `sim_mach`: Mach number.
# - `sim_temperature`: Temperature in Kelvin.
# - `sim_aoa`: Angle of attack in degrees.
# - `sim_pressure`: Pressure in Pascal.
# - `data_dir`: Directory to save the mesh file.
# - `container_dict`: Configuration for the Fluent container. The default is None.
# - `iter_count`: Number of iterations to solve. The default is ``25``.
# - `ui_mode`: User interface mode. The default is None.
#
# The function switches to the Fluent solver and loads the mesh. It defines the model,
# material, boundary conditions, operating conditions, initializes the flow field,
# saves the case file, solves for the requested iterations, and exits Fluent.
#


def solve_airfoil_flow(
    naca_airfoil: str,
    sim_mach: float,
    sim_temperature: float,
    sim_aoa: float,
    sim_pressure: float,
    data_dir: str,
    container_dict: dict | None = None,
    iter_count: int = 25,
    ui_mode: str | None = None,
):
    """
    Solve the flow around a NACA airfoil using Fluent.

    Parameters
    ----------
    naca_airfoil : str
        NACA 4-digits airfoil number.
    sim_mach : float
        Mach number.
    sim_temperature : float
        Temperature in Kelvin.
    sim_aoa : float
        Angle of attack in degrees.
    sim_pressure : float
        Pressure in Pascal.
    data_dir : str
        Directory to save the mesh file.
    container_dict : dict, optional
        Configuration for the Fluent container. The default is None.
    iter_count : int, optional
        Number of iterations to solve. The default is ``25``.
    ui_mode : str, optional
        User interface mode. The default is None.
    """

    # Switch to Fluent solver
    if container_dict is not None:
        solver = pyfluent.launch_fluent(
            container_dict=container_dict,
            start_container=True,
            precision="double",
            processor_count=4,
            mode="solver",
            ui_mode="no_gui_or_graphics",
            cwd=data_dir,
            cleanup_on_exit=False,
            start_timeout=300,
        )
    else:
        solver = pyfluent.launch_fluent(
            precision="double",
            processor_count=4,
            mode="solver",
            ui_mode=ui_mode,
            cwd=data_dir,
        )

    # Load mesh
    solver.file.read_mesh(file_name=f"{data_dir}/NACA_Airfoil_{naca_airfoil}.msh.h5")

    # Verify the mesh
    solver.mesh.check()

    # Define the model
    # model : k-omega
    # k-omega model : sst
    viscous = solver.setup.models.viscous
    viscous.model = "k-omega"
    viscous.k_omega_model = "sst"

    # Define material
    #
    # density : ideal-gas
    # viscosity : sutherland
    # viscosity method : three-coefficient-method
    # reference viscosity : 1.716e-05 [kg/(m s)]
    # reference temperature : 273.11 [K]
    # effective temperature : 110.56 [K]
    air = solver.setup.materials.fluid["air"]
    air.density.option = "ideal-gas"
    air.viscosity.option = "sutherland"
    air.viscosity.sutherland.option = "three-coefficient-method"
    air.viscosity.sutherland.reference_viscosity = 1.716e-05
    air.viscosity.sutherland.reference_temperature = 273.11
    air.viscosity.sutherland.effective_temperature = 110.56

    # Define Boundary conditions
    #
    # gauge pressure : 0 [Pa]
    # turbulent intensity : 5 [%]solve
    # turbulent viscosity ratio : 10
    #
    solver.setup.boundary_conditions.set_zone_type(
        zone_list=["inlet-fluid"], new_type="pressure-far-field"
    )

    inlet_fluid = solver.setup.boundary_conditions.pressure_far_field["inlet-fluid"]
    aoa = np.deg2rad(sim_aoa)
    if solver.get_fluent_version() < pyfluent.FluentVersion.v242:
        inlet_fluid.gauge_pressure = 0
        inlet_fluid.m = sim_mach
        inlet_fluid.t = sim_temperature
        inlet_fluid.flow_direction[0] = np.cos(aoa)
        inlet_fluid.flow_direction[1] = np.sin(aoa)
        inlet_fluid.turbulent_intensity = 0.05
        inlet_fluid.turbulent_viscosity_ratio_real = 10

    else:
        inlet_fluid.momentum.gauge_pressure = 0
        inlet_fluid.momentum.mach_number = sim_mach
        inlet_fluid.thermal.temperature = sim_temperature
        inlet_fluid.momentum.flow_direction[0] = np.cos(aoa)
        inlet_fluid.momentum.flow_direction[1] = np.sin(aoa)
        inlet_fluid.turbulence.turbulent_intensity = 0.05
        inlet_fluid.turbulence.turbulent_viscosity_ratio = 10

    # Define operating conditions
    #
    solver.setup.general.operating_conditions.operating_pressure = sim_pressure

    # Initialize flow field
    solver.solution.initialization.hybrid_initialize()

    # Save case file
    solver.file.write(
        file_name=f"{data_dir}/NACA_Airfoil_{naca_airfoil}_initialization.cas.h5",
        file_type="case",
    )

    # Solve for requested iterations
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    solver.file.write(
        file_name=f"{data_dir}/NACA_Airfoil_{naca_airfoil}_resolved.cas.h5",
        file_type="case",
    )
    # Write data file as well
    solver.file.write(
        file_name=f"{data_dir}/NACA_Airfoil_{naca_airfoil}_resolved.dat.h5",
        file_type="data",
    )

    # Exit Fluent
    solver.exit()


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
        "fluent_image": os.getenv("FLUENT_DOCKER_IMAGE"),
        "command": os.getenv("FLUENT_DOCKER_EXEC_COMMAND").split(),
        "mount_source": DATA_DIR,
    }
    # https://fluent.docs.pyansys.com/version/stable/api/general/launcher/fluent_container.html
    # Solve the flow around the airfoil
    solve_airfoil_flow(
        NACA_AIRFOIL,
        SIM_MACH,
        SIM_TEMPERATURE,
        SIM_AOA,
        SIM_PRESSURE,
        "/home/container/workdir",
        container_dict=container_dict,
    )
else:
    # Solve the flow around the airfoil
    solve_airfoil_flow(NACA_AIRFOIL, SIM_MACH, SIM_TEMPERATURE, SIM_AOA, SIM_PRESSURE, DATA_DIR)
