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

""".. _exhaust_manifold_cfd_workflow:

Conjugate Heat Transfer Workflow for Exhaust Manifold
#####################################################

This workflow demonstrates the typical solver setup involved in performing a CFD
simulation for the conjugate heat transfer (CHT) analysis of an exhaust manifold.
A conjugate heat transfer analysis is a type of simulation that involves the
simultaneous solution of heat transfer in both solid and fluid domains. In this
case, the exhaust manifold is a solid domain, and the fluid domain is the gas
flowing through the manifold. The heat transfer between the solid and fluid domains
is modeled using the heat transfer coefficient (HTC) at the interface between the two
domains.
This workflow provides a step-by-step guide to set up a CHT analysis for an exhaust
manifold using Ansys Flueent Pyfluetn API's. The workflow includes usage of API's to
setup the physics, material properties, boundary conditions, solver settings, and
exporting the results to a CSV file for further use in a Thermo-Mechanical Analysis.

Problem Description:
-------------------

The geometry is an exhaust manifold with a fluid domain (gas) and a solid domain(metal)
meshed with a conformal Polyhedral mesh.The hot gas flows through the manifold,
and the heat is transferred to the solid domain. The objective is to calculate the
heat transfer coefficient (HTC) at the interface between the fluid and solid domains,
the temperature distribution in the solid domain, and export the results to a CSV
file for further use in a Thermo-Mechanical Analysis.
The workflow includes the following steps:
- Launch Fluent
- Load the mesh file
- Define the material properties
- Define the boundary conditions
- Define the solver settings
- Initialize the solution
- Run the solver
- Export the results to CSV file
- Close Fluent
This workflow will generate the following files as output:
- exhaust_manifold_results_HIGH_TEMP.cas.h5
- exhaust_manifold_results_MEDIUM_TEMP.cas.h5
- exhaust_manifold_results_LOW_TEMP.cas.h5
- exhaust_manifold_results_HIGH_TEMP.dat.h5
- exhaust_manifold_results_MEDIUM_TEMP.dat.h5
- exhaust_manifold_results_LOW_TEMP.dat.h5
- htc_temp_mapping_HIGH_TEMP.csv
- htc_temp_mapping_MEDIUM_TEMP.csv
- htc_temp_mapping_LOW_TEMP.csv
- Fluent transcript file (fluent-YYYYMMDD-HHMMSS-<processID>.trn)

"""  # noqa: D400, D415


# Perform required imports
# ------------------------
# Perform required imports, which includes downloading the mesh file from the
# examples.

import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples

import_mesh_file = examples.download_file(
    "exhaust_manifold_conf.msh.h5", "pyansys-workflow/exhaust-manifold/pyfluent"
)

###############################################################################
# Launch Fluent
# -------------
# Launch Fluent as a service in solver mode with double precision running on
# four processors and print Fluent version.

solver = pyfluent.launch_fluent(
    precision="double",
    processor_count=4,
    mode="solver",
)
print(solver.get_fluent_version())

###############################################################################
# Read the mesh file
# ------------------
# Read the mesh file into the Fluent solver and check the mesh information.

solver.settings.file.read_mesh(file_name=import_mesh_file)
solver.mesh.check()


###############################################################################
# Define the Physics
# ------------------
# Define the physics of the problem by setting energy and turbulence models.

solver.settings.setup.models.energy.enabled = True
solver.settings.setup.models.viscous.model.allowed_values()
solver.settings.setup.models.viscous.model = "k-epsilon"
solver.settings.setup.models.viscous.k_epsilon_model = "realizable"
solver.settings.setup.models.viscous.near_wall_treatment.wall_treatment = "enhanced-wall-treatment"

###############################################################################
# Define the Material Properties
# -------------------------------
# Define the material properties of the fluid, solid and assign the
# material to the appropriate cell zones.

# Fluid Material Properties
fluid_mat = solver.settings.setup.materials.fluid["air"]
fluid_mat.rename("fluid-material")
fluid_mat = solver.settings.setup.materials.fluid["fluid-material"]
fluid_mat.density.option = "ideal-gas"
fluid_mat.viscosity.value = 4.25e-05
fluid_mat.specific_heat.value = 1148
fluid_mat.thermal_conductivity.value = 0.0686

# Solid Material Properties
solid_mat = solver.settings.setup.materials.solid["aluminum"]
solid_mat.rename("solid-material")
solid_mat = solver.settings.setup.materials.solid["solid-material"]
solid_mat.density.value = 8030
solid_mat.specific_heat.value = 502.4
solid_mat.thermal_conductivity.value = 60.5

# Assign Material to Cell Zones
solver.settings.setup.cell_zone_conditions.fluid["*fluid*"].general.material = "fluid-material"
solver.settings.setup.materials.print_state()
solver.settings.setup.cell_zone_conditions.solid["*solid*"].general.material = "solid-material"

# Print the material properties for verification
solver.settings.setup.materials.print_state()

###############################################################################
# Define the Named Expressions
# ----------------------------
# Define the named expressions for the boundary conditions.

solver.settings.setup.named_expressions.create("in_temperature")
solver.settings.setup.named_expressions["in_temperature"].definition = "1023.15 [K]"
solver.settings.setup.named_expressions["in_temperature"].input_parameter = True
solver.settings.setup.named_expressions.create("mass_flow_rate")
solver.settings.setup.named_expressions["mass_flow_rate"].definition = (
    "abs((0.1559 [kg/s] *log(in_temperature/(1 [K^1])))-0.9759 [kg/s])"
)

solver.settings.setup.named_expressions.create("pressure_out")
solver.settings.setup.named_expressions["pressure_out"].definition = (
    "(-0.3383 [Pa]*in_temperature^2/(1 [K^2]))+954.75 [Pa]*in_temperature/(1 [K])-356085 [Pa]"
)

solver.settings.setup.named_expressions.create("temperature_out")
solver.settings.setup.named_expressions["temperature_out"].definition = "in_temperature-23.00 [K]"

###############################################################################
# Define the Boundary Conditions
# ------------------------------
# Define the boundary conditions for the problem.

# Convection Boundary Condition
solver.settings.setup.boundary_conditions.wall["solid:1"].thermal.thermal_condition = "Convection"
solver.settings.setup.boundary_conditions.wall["solid:1"].thermal.heat_transfer_coeff.value = 60

ref_temp = 200 + 273.15
solver.settings.setup.boundary_conditions.wall["solid:1"].thermal.free_stream_temp.value = ref_temp

# Inlet Boundary Conditions
solver.settings.setup.boundary_conditions.mass_flow_inlet.list()

for inlet_bc in solver.settings.setup.boundary_conditions.mass_flow_inlet.keys():
    solver.settings.setup.boundary_conditions.mass_flow_inlet[
        inlet_bc
    ].momentum.mass_flow_rate.value = "mass_flow_rate"
    solver.settings.setup.boundary_conditions.mass_flow_inlet[
        inlet_bc
    ].thermal.total_temperature.value = "in_temperature"

# Outlet Boundary Conditions
solver.settings.setup.boundary_conditions.pressure_outlet.list()
solver.settings.setup.boundary_conditions.pressure_outlet[
    "pressure_outlet"
].momentum.gauge_pressure.value = "pressure_out"
solver.settings.setup.boundary_conditions.pressure_outlet[
    "pressure_outlet"
].thermal.backflow_total_temperature.value = "temperature_out"

###############################################################################
# Define the Solution Methods and Solver Settings
# -----------------------------------------------
# Define the solution methods and solver settings for the problem.

# Solution Methods & controls
solver.settings.solution.methods.pseudo_time_method.formulation.coupled_solver = "off"
solver.settings.solution.controls.p_v_controls.flow_courant_number = 50

# Solver Settings initialization & set the iteration count
solver.settings.solution.initialization.hybrid_initialize()
solver.settings.solution.run_calculation.iter_count = 200


###############################################################################
# Run the Solver & Export the Results to CSV
# ------------------------------------------
# Run the solver to solve the problem and export the results to a CSV file.

# Define a tuple with temperature values
temperature_values = (
    ("HIGH_TEMP", 1023.15),
    ("MEDIUM_TEMP", 683.15),
    ("LOW_TEMP", 483.15),
)

# Retrieve fluid and solid zones
fluid_zones = list(solver.settings.setup.cell_zone_conditions.fluid.keys())
solid_zones = list(solver.settings.setup.cell_zone_conditions.solid.keys())
cell_zone_names = fluid_zones + solid_zones

# Iterate over the temperature values tuple
for temp_name, temp_value in temperature_values:
    # Running the simulation for each temperature value with initialization and iteration
    solver.solution.initialization.hybrid_initialize()
    solver.settings.setup.named_expressions["in_temperature"].definition = f"{temp_value} [K]"
    solver.solution.run_calculation.iterate(iter_count=200)

    # Exporting Data for Thermo-Mechanical Simulation
    mapping_file = f"htc_temp_mapping_{temp_name}.csv"
    solver.settings.file.export.ascii(
        file_name=mapping_file,
        surface_name_list=["interface_solid"],
        delimiter="comma",
        cell_func_domain=["temperature", "heat-transfer-coef-wall"],
        location="node",
    )

    # Export graphics result for the temperature distribution on interface_solid
    temp_interface_contour = solver.settings.results.graphics.contour.create(
        f"temp_interface_contour_{temp_name}"
    )
    temp_interface_contour(field="temperature", surfaces_list=["interface_solid"])
    temp_interface_contour.display()
    solver.settings.results.graphics.views.auto_scale()
    solver.settings.results.graphics.picture.save_picture(
        file_name=f"temp_interface_contour_{temp_name}.png"
    )

    solver.settings.file.write_case_data(file_name=f"exhaust_manifold_results_{temp_name}.cas.h5")

###############################################################################
# Exit the Solver
# ---------------
# Close the Fluent solver.

solver.exit()
