# Copyright (C) 2024 - 2025 ANSYS, Inc. and/or its affiliates.
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
.. _ref_geometry_mech_dpf_02-mechanical:

Mechanical - Thermal analysis
#############################

This examples performs meshing, steady-state and transient thermal analysis of PCB.
Objective of this example is to study or examine resulting temperatures caused by
the heat developed in chips.

"""  # noqa: D400, D415

import os
from pathlib import Path

import ansys.mechanical.core as mech
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gmd_02_mechanical.py")
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
# Start a PyMechanical app
# ------------------------
#
app = mech.App()
app.update_globals(globals())
print(app)


def display_image(image_name):
    plt.figure(figsize=(16, 9))
    plt.imshow(mpimg.imread(os.path.join(OUTPUT_DIR, image_name)))
    plt.xticks([])
    plt.yticks([])
    plt.axis("off")
    plt.show()


###############################################################################
# Configure graphics for image export
# -----------------------------------
#
ExtAPI.Graphics.Camera.SetSpecificViewOrientation(ViewOrientationType.Iso)
ExtAPI.Graphics.Camera.SetFit()
image_export_format = GraphicsImageExportFormat.PNG
settings_720p = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
settings_720p.Resolution = GraphicsResolutionType.EnhancedResolution
settings_720p.Background = GraphicsBackgroundType.White
settings_720p.Width = 1280
settings_720p.Height = 720
settings_720p.CurrentGraphicsDisplay = False


###############################################################################
# Import geometry
# ---------------
# Import geometry which is generated with pyansys-geometry
#
geometry_path = Path(OUTPUT_DIR, "pcb.pmdb")
geometry_import_group = Model.GeometryImportGroup
geometry_import = geometry_import_group.AddGeometryImport()
geometry_import_format = Ansys.Mechanical.DataModel.Enums.GeometryImportPreference.Format.Automatic
geometry_import_preferences = Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()
geometry_import_preferences.ProcessNamedSelections = True
geometry_import.Import(str(geometry_path), geometry_import_format, geometry_import_preferences)

# Plot geometry
if GRAPHICS_BOOL:
    app.plot()


###############################################################################
# Create named selections
# -----------------------
#

ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardMKS

# Create named selection for all bodies
bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)
body_ids = [bd.GetGeoBody().Id for bd in bodies]
selection = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
selection.Ids = body_ids
ns1 = Model.AddNamedSelection()
ns1.Name = "all_bodies"
ns1.Location = selection

# Create named selection for all except substrate
substrate_id = [bd.GetGeoBody().Id for bd in bodies if bd.Name.endswith("substrate")]
except_substrate_id = list(set(body_ids) - set(substrate_id))

selection = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
selection.Ids = except_substrate_id
ns2 = Model.AddNamedSelection()
ns2.Name = "all_except_board"
ns2.Location = selection

###############################################################################
# Meshing
# -------
#
mesh = Model.Mesh
mesh.GenerateMesh()

# Export mesh image
ExtAPI.Graphics.Camera.SetFit()
ExtAPI.Graphics.ExportImage(
    os.path.join(OUTPUT_DIR, "mesh.png"), image_export_format, settings_720p
)

# Display the mesh
if GRAPHICS_BOOL:
    display_image("mesh.png")


###############################################################################
# Analysis
# --------
# Setup steady state thermal analysis

steady = Model.AddSteadyStateThermalAnalysis()
transient = Model.AddTransientThermalAnalysis()

internal_heat_generation = steady.AddInternalHeatGeneration()
NSall = ExtAPI.DataModel.Project.Model.NamedSelections.GetChildren[
    Ansys.ACT.Automation.Mechanical.NamedSelection
](True)
ic6 = [i for i in NSall if i.Name == "ic-6"][0]
internal_heat_generation.Location = ic6
internal_heat_generation.Magnitude.Output.SetDiscreteValue(0, Quantity(5e7, "W m^-1 m^-1 m^-1"))

all_bodies = [i for i in NSall if i.Name == "all_bodies"][0]
convection = steady.AddConvection()
convection.Location = all_bodies
convection.FilmCoefficient.Output.DiscreteValues = [Quantity("5[W m^-2 C^-1]")]

steady_solution = steady.Solution
temperature_result = steady_solution.AddTemperature()
steady_solution.Solve(True)

# Transient analysis setup
initial_condition = transient.InitialConditions[0]
initial_condition.InitialTemperature = InitialTemperatureType.NonUniform
initial_condition.InitialEnvironment = steady

transient_analysis_settings = transient.AnalysisSettings
transient_analysis_settings.StepEndTime = Quantity(200, "sec")

internal_heat_generation2 = transient.AddInternalHeatGeneration()

ic1 = [i for i in NSall if i.Name == "ic-1"][0]
internal_heat_generation2.Location = ic1
internal_heat_generation2.Magnitude.Output.SetDiscreteValue(0, Quantity(5e7, "W m^-1 m^-1 m^-1"))

###############################################################################
# Add result objects
# ------------------
#
transient_solution = transient.Solution
transient_temperature_result = transient_solution.AddTemperature()
temperature_probe1 = transient_solution.AddTemperatureProbe()
temperature_probe1.GeometryLocation = ic6
temperature_probe2 = transient_solution.AddTemperatureProbe()
temperature_probe2.GeometryLocation = ic1

###############################################################################
# Solve
# -----
#
transient_solution.Solve(True)

# TODO :Remove once completed
# Export mesh image
Tree.Activate([transient_temperature_result])
ExtAPI.Graphics.Camera.SetFit()
ExtAPI.Graphics.ExportImage(
    os.path.join(OUTPUT_DIR, "temperature.png"), image_export_format, settings_720p
)

###############################################################################
# Save files and close Mechanical
# -------------------------------
# Mechanical file (mechdb) contains results for each analysis
#
app.save(os.path.join(OUTPUT_DIR, "pcb.mechdb"))
print(f"Mechanical file saved to: {OUTPUT_DIR / 'pcb.mechdb'}")
app.close()
