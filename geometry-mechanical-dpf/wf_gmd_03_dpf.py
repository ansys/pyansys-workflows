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
.. _ref_geometry_mech_dpf_03-dpf:

Post-processing
###############

This examples shows how dataprocessing framework can be used to extract results
and analyze them.

"""  # noqa: D400, D415
import os
from pathlib import Path

from ansys.dpf import core as dpf

# -- Parameters --
#
GRAPHICS_BOOL = False  # Set to True to display the graphics
OUTPUT_DIR = Path(Path(__file__).parent, "outputs")  # Output directory


# -- Finding necessary files for dpf --
#
def find_files(directory, extension):
    rst_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                rst_files.append(os.path.join(root, file))
    return rst_files


extension_to_find = ".rth"

# Mechanical poject directory
project_directory = os.path.join(OUTPUT_DIR, "pcb_Mech_Files")

steady_state_rth_file = find_files(
    os.path.join(project_directory, "SteadyStateThermal"), extension_to_find
)
transient_rth_file = find_files(
    os.path.join(project_directory, "TransientThermal"), extension_to_find
)

if steady_state_rth_file and transient_rth_file:
    print(f"Found {extension_to_find} files.")
else:
    print("No .rst files found.")

print(steady_state_rth_file)
print(transient_rth_file)

# -- DPF workflow --
#
# Result precision
decimal_precision = 6

# -- Steady state thermal results --
#
# Create model
steady_state_model = dpf.Model(steady_state_rth_file[0])
print(steady_state_model)

# Get temperature distribution
temp = steady_state_model.results.temperature.on_last_time_freq.eval()[0]

# Plot the temperature for ic-6
if GRAPHICS_BOOL:
    temp.plot()

# -- Transien thermal results --
#
# Create model
model = dpf.Model(transient_rth_file[0])
print(steady_state_model)

# Get temperature distribution
temp = model.results.temperature.on_last_time_freq.eval()[0]

# Plot the the temperature for ic-1
if GRAPHICS_BOOL:
    temp.plot()
