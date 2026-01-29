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
.. _ref_wf_ml_01_ion_trap_modelling:

Maxwell2D - Simplified IonTrap Modelling
########################################

Problem description
-------------------

Surface electrodes adjacent to grating couplers render an integrated ion trap.
In this workflow surface electrodes are modeled using ANSYS Maxwell and grating couplers using
ANSYS Lumerical. ANSYS Maxwell electrostatic solver, based on the finite element method, allows to
evaluate the ion trap height.Then the coordinates of the ion trap are passed to an optimization
algorithm to define the optimal two dimensional grating coupler design, which will focus the laser
beam at the ion trap height.

The workflow is explained in detail in this article:
https://optics.ansys.com/hc/en-us/articles/20715978394131-Integrated-Ion-Traps-using-Surface-Electrodes-and-Grating-Couplers

The workflow includes the following steps:
- Set up the Maxwell 2D Parametric Model
- Identify the Electric Field Node Point for Each Design Point
- Export the Node Coordinates for the subsequent Lumerical Step
- Launch the Lumerical Scripts

"""  # noqa: D400, D415

# Perform required imports
# ------------------------

import os
from pathlib import Path
import shutil
import tempfile
import time

from PIL import Image
from ansys.aedt.core import Maxwell2d
from ansys.lumerical.core import FDTD

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_ml_01_ion_trap_modelling.py")
# sphinx_gallery_end_ignore

###############################################################################
# Prepare and launch Maxwell
# --------------------------
# Define constants

AEDT_VERSION = os.getenv("AEDT_VERSION", "2025.2")  # Set your AEDT version here
NUM_CORES = 4
NG_MODE = (
    os.getenv("ON_CI", "false").lower() == "true"
)  # Open AEDT UI when it is launched, unless running in CI
NODE_FILENAME = "NodePositionTable.tab"
LEGEND_FILENAME = "legend.txt"
PARENT_DIR_PATH = Path(__file__).parent.absolute()

# Create temporary directory.

temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")
lumerical_script_folder = Path(temp_folder.name)  # / "lumerical_scripts"
node_path = lumerical_script_folder / NODE_FILENAME
legend_path = lumerical_script_folder / LEGEND_FILENAME

# Launch AEDT and start a Maxwell2D Design.

project_name = os.path.join(temp_folder.name, "IonTrapMaxwell.aedt")
m2d = Maxwell2d(
    project=project_name,
    design="01_IonTrap_3binary2D",
    solution_type="Electrostatic",
    version=AEDT_VERSION,
    non_graphical=NG_MODE,
    new_desktop=True,
)
m2d.modeler.model_units = "um"

###############################################################################
# Preprocess
# ----------
# The preprocessing is performed using the following steps:
# 1. Define design variables.
# 2. Create design geometry.
# 3. Define excitations.
# 4. (Optional) Define mesh settings.

# Initialize dictionaries for design variables.

geom_params = {
    "div": str(73 / 41),
    "w_rf": "41um",
    "w_dc": "41um*div",
    "w_cut": "4um",
    "metal_thickness": "1um",
    "offset_glass": "50um",
    "glass_thickness": "10um",
    "x_dummy": "2um",
    "y_dummy": "300um",
}

# Define design variables from dictionaries.

for k, v in geom_params.items():
    m2d[k] = v

# Create design geometry

dc = m2d.modeler.create_rectangle(
    origin=["-w_dc/2", "-metal_thickness/2", "0"],
    sizes=["w_dc", "metal_thickness", 0],
    name="DC",
    material="aluminum",
)
# dc.color = (0, 0, 255)  # rgb
gnd = m2d.modeler.create_rectangle(
    origin=["-(w_dc/2+w_cut+w_rf+offset_glass)", "-(metal_thickness/2+glass_thickness)", "0"],
    sizes=["2*(w_dc/2+w_cut+w_rf+offset_glass)", "-metal_thickness", 0],
    name="gnd",
    material="aluminum",
)
rf = m2d.modeler.create_rectangle(
    origin=["-(w_dc/2+w_cut+w_rf)", "-metal_thickness/2", "0"],
    sizes=["w_rf", "metal_thickness", 0],
    name="RF",
    material="aluminum",
)
sub_glass = m2d.modeler.create_rectangle(
    origin=["-(w_dc/2+w_cut+w_rf+offset_glass)", "-metal_thickness/2", "0"],
    sizes=["2*(w_dc/2+w_cut+w_rf+offset_glass)", "-glass_thickness", 0],
    name="RF",
    material="glass",
)
ins = m2d.modeler.create_rectangle(
    origin=["-(w_dc/2+w_cut)", "-metal_thickness/2", "0"],
    sizes=["w_cut", "metal_thickness", 0],
    name="ins",
    material="vacuum",
)

# Create dummy objects for mesh and center_line for Post Processing and Region

dummy = m2d.modeler.create_rectangle(
    origin=["0", "metal_thickness/2", "0"],
    sizes=["-x_dummy", "y_dummy", 0],
    name="dummy",
    material="vacuum",
)

# Create region

region = m2d.modeler.create_region(
    pad_value=[100, 0, 100, 0], pad_type="Absolute Offset", name="Region"
)

# Create the center line for electric field maximum point identification

center_line = m2d.modeler.create_polyline(
    points=[["0", "metal_thickness/2", "0"], ["0", "metal_thickness/2+200um", "0"]],
    name="center_line",
)

# Define excitations

m2d.assign_voltage(assignment=gnd.id, amplitude=0, name="ground")
m2d.assign_voltage(assignment=dc.id, amplitude=0, name="V_dc")
m2d.assign_voltage(assignment=rf.id, amplitude=1, name="V_rf")

# Define mesh settings
# For good quality results, please uncomment the following  mesh operations lines
#
# m2d.mesh.assign_length_mesh(
#     assignment=center_line.id,
#     maximum_length=1e-7,
#     maximum_elements=None,
#     name="center_line_0.1um",
# )
# m2d.mesh.assign_length_mesh(
#     assignment=dummy.name, maximum_length=2e-6, maximum_elements=1e6, name="dummy_2um"
# )
# m2d.mesh.assign_length_mesh(
#     assignment=ins.id,
#     maximum_length=8e-7,
#     inside_selection=False,
#     maximum_elements=1e6,
#     name="ins_0.8um",
# )
# m2d.mesh.assign_length_mesh(
#     assignment=[dc.id, rf.id],
#     maximum_length=5e-6,
#     inside_selection=False,
#     maximum_elements=1e6,
#     name="dc_5um",
# )
# m2d.mesh.assign_length_mesh(
#     assignment=gnd.id,
#     maximum_length=1e-5,
#     inside_selection=False,
#     maximum_elements=1e6,
#     name="gnd_10um",
# )

# Duplicate structures and assignments to complete the model

m2d.modeler.duplicate_and_mirror(
    assignment=[rf.id, dummy.id, ins.id],
    origin=["0", "0", "0"],
    vector=["-1", "0", "0"],
    duplicate_assignment=True,
)

###############################################################################
# Run simulation adn parametric sweep
# -----------------------------------
# Create, validate, and analyze setup

setup_name = "MySetupAuto"
setup = m2d.create_setup(name=setup_name)
setup.props["PercentError"] = 0.1
setup.update()
m2d.validate_simple()
m2d.analyze_setup(name=setup_name, use_auto_settings=False, cores=NUM_CORES)

#  Create and solve parametric sweep
#  Keeping w_rf constant, we recompute the w_dc values from the desired ratios w_rf/w_dc

div_sweep_start = 1.4
div_sweep_stop = 2
sweep = m2d.parametrics.add(
    variable="div",
    start_point=div_sweep_start,
    end_point=div_sweep_stop,
    step=0.2,
    variation_type="LinearStep",
    name="w_dc_sweep",
)
add_points = [1, 1.3]
for p in add_points:
    sweep.add_variation(sweep_variable="div", start_point=p, variation_type="SingleValue")
sweep["SaveFields"] = True
sweep.analyze(cores=NUM_CORES)

###############################################################################
# Postprocess
# -----------
# Create the Ey expression in the PyAEDT Advanced Field Calculator
# Due to the symmetric nature of this specific geometry, the electric field
# node will be located along the center line. The electric field node is the
# point where the Ey will be zero and can be found directly by Maxwell post
# processing features

e_line = m2d.post.fields_calculator.add_expression(calculation="e_line", assignment=None)
my_plots = m2d.post.fields_calculator.expression_plot(
    calculation="e_line", assignment="center_line", names=[e_line]
)
my_plots[1].edit_x_axis_scaling(min_scale="20um", max_scale="200um")
my_plots[1].update_trace_in_report(
    my_plots[1].get_solution_data().expressions, variations={"div": ["All"]}, context="center_line"
)

# Identify the zero point for each trace.

my_plots[1].add_cartesian_y_marker("0")
my_plots[1].add_trace_characteristics(
    "XAtYVal", arguments=["0"], solution_range=["Full", "20", "200"]
)

# Export the points at which Ey=0 to a TXT file
my_plots[1].export_table_to_file(my_plots[1].plot_name, str(node_path), table_type="Legend")

###############################################################################
# Prepare and Run Lumerical Simulation
# ------------------------------------
# Edit the file outputted by Maxwell to be read in by Lumerical

new_line = []
with open(node_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_line.append(lines[0])
for line in lines[1:]:
    new_line.append(line.split("\t")[0])
    new_line.append("\n" + line.split("\t")[1].lstrip())

with open(legend_path, "w", encoding="utf-8") as f:
    for line in new_line:
        f.write(line)

# Copy Lumerical scripts and illustration to the local folder

gc_farfiled_path = shutil.copy(PARENT_DIR_PATH / "GC_farfield.lsf", lumerical_script_folder)
gc_opt_path = shutil.copy(PARENT_DIR_PATH / "GC_Opt.lsf", lumerical_script_folder)
read_data_path = shutil.copy(PARENT_DIR_PATH / "Readata.lsf", lumerical_script_folder)
img_path = shutil.copy(PARENT_DIR_PATH / "img_001.jpg", lumerical_script_folder)

# Start the Lumerical Process

gc_0 = FDTD(gc_opt_path)

# Run the first script: Build geometry & Run optimization

gc_1 = FDTD(read_data_path)
print(
    "Optimize for the Nodal point located",
    str(gc_1.getv("T5")),
    "um, above the linearly apodized grating coupler",
)

# Run the optimized design

gc_2 = FDTD(str(lumerical_script_folder / "Testsim_Intensity_best_solution"))
gc_2.save(str(lumerical_script_folder / "GC_farfields_calc"))
gc_2.run()

# Run the second script for calculating plots

gc_2.feval(gc_farfiled_path)
print(f"Target focal distance of output laser beam: {gc_2.getv('Mselect') * 1000000} (um)")
print(f"Actual focal distance for the optimised geometry: {gc_2.getv('Mactual') * 1000000} (um)")
print(f"Relative error: {gc_2.getv('RelVal') * 100}%")
print(f"FWHM of vertical direction at focus: {gc_2.getv('FWHM_X') * 1000000} (um)")
print(f"FWHM of horizontal direction at focus {gc_2.getv('FWHM_Y') * 1000000} (um)")
print(f"Substrate material : {gc_2.getv('Material')}")

print(f"Waveguide etch depth: {gc_2.getv('GC_etch') * 1000000000} (nm)")
print(f"Grating period (P): {gc_2.getv('GC_period') * 1000000000} (nm)")
print(f"Grating minimum duty cycle: {gc_2.getv('GC_DCmin')}")

# Display Grating Schema Image


def in_ipython():
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except ImportError:
        return False


schema_img = Image.open(PARENT_DIR_PATH / "img_001.jpg")

# Show image inside IPython / Jupyter

if in_ipython():
    from IPython.display import display

    display(schema_img)
# Show image using default image viewer
else:
    schema_img.show()

schema_img.close()

###############################################################################
# Exit the Solver
# ---------------
# Close FDTD projects and release AEDT.
#
gc_0.close()
gc_1.close()
gc_2.close()
m2d.save_project()
m2d.desktop_class.release_desktop()
# Wait 3 seconds to allow AEDT to shut down before cleaning the temporary directory.
time.sleep(3)
# Clean up
#
temp_folder.cleanup()
