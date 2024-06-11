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

import ansys.fluent.core as pyfluent
import numpy as np

####################################################################################################

# NACA 4-digits airfoil geometry
NACA_AIRFOIL = "6412"

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# Simulation parameters
SIM_MACH = 0.3  # 0.8395 # Mach number
SIM_TEMPERATURE = 255.56  # In Kelvin
SIM_AOA = 3.06  # in degrees
SIM_PRESSURE = 80600  # in Pa

####################################################################################################
# Fluent
####################################################################################################


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
    solver.file.read_mesh(file_name=os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}.msh.h5"))

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
    inlet_fluid.gauge_pressure = 0
    inlet_fluid.m = sim_mach
    inlet_fluid.t = sim_temperature
    aoa = np.deg2rad(sim_aoa)
    inlet_fluid.flow_direction[0] = np.cos(aoa)
    inlet_fluid.flow_direction[1] = np.sin(aoa)
    inlet_fluid.turbulent_intensity = 0.05
    inlet_fluid.turbulent_viscosity_ratio_real = 10

    # Define operating conditions
    #
    solver.setup.general.operating_conditions.operating_pressure = sim_pressure

    # Initialize flow field
    solver.solution.initialization.hybrid_initialize()

    # Save case file
    solver.file.write(
        file_name=os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}_initialization.cas.h5"),
        file_type="case",
    )

    # Solve for 50 iterations
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    solver.file.write(
        file_name=os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}_resolved.cas.h5"),
        file_type="case",
    )
    # Write data file as well
    solver.file.write(
        file_name=os.path.join(data_dir, f"NACA_Airfoil_{naca_airfoil}_resolved.dat.h5"),
        file_type="data",
    )

    # Exit Fluent
    solver.exit()


if __name__ == "__main__":

    import os

    # Depending on the environment, the script will run in a container or locally
    if os.getenv("PYANSYS_WORKFLOWS_CI") == "true":
        container_dict = {
            "fluent_image": f"{os.environ['FLUENT_DOCKER_IMAGE']}:{os.environ['FLUENT_IMAGE_TAG']}",
            "host_mount_path": DATA_DIR,
            "license_server": os.environ["ANSYSLMD_LICENSE_FILE"],
            "timeout": 300,
        }
        # https://fluent.docs.pyansys.com/version/stable/api/general/launcher/fluent_container.html

        # Solve the flow around the airfoil
        solve_airfoil_flow(
            NACA_AIRFOIL,
            SIM_MACH,
            SIM_TEMPERATURE,
            SIM_AOA,
            SIM_PRESSURE,
            "/mnt/pyfluent",
            container_dict=container_dict,
        )
    else:
        # Solve the flow around the airfoil
        solve_airfoil_flow(NACA_AIRFOIL, SIM_MACH, SIM_TEMPERATURE, SIM_AOA, SIM_PRESSURE, DATA_DIR)
