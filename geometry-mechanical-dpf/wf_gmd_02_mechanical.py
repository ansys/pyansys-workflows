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
.. _ref_geometry_mech_dpf_02-mechanical:

Mechanical - Thermal analysis
#############################

This examples shows meshing and performing of steady-state and transient thermal analysis.
These analyses are used to study the resulting temperatures caused by the heat developed in chips.

"""  # noqa: D400, D415

import os
from pathlib import Path

import ansys.mechanical.core as mech
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

# Check env vars to see which image to launch
#
# --- ONLY FOR WORKFLOW RUNS ---
version = None
if "ANSYS_MECHANICAL_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_MECHANICAL_RELEASE"]
    version = int(image_tag.replace(".", ""))

# -- Start PyMechanical app --
#
app = mech.App(version=version)
globals().update(mech.global_variables(app, True))
print(app)

# -- Parameters --
#
GRAPHICS_BOOL = False  # Set to True to display the graphics
OUTPUT_DIR = Path(Path(__file__).parent, "outputs")  # Output directory


def display_image(image_name):
    plt.figure(figsize=(16, 9))
    plt.imshow(mpimg.imread(os.path.join(OUTPUT_DIR, image_name)))
    plt.xticks([])
    plt.yticks([])
    plt.axis("off")
    plt.show()


# -- Configure graphics for image export --
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

# -- Import geometry --
#
# Import geometry
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

# -- Setup steady steate and transient analysis --
#
steady = Model.AddSteadyStateThermalAnalysis()
transient = Model.AddTransientThermalAnalysis()

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

# -- Meshing --
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

# -- Analysis --
#
# Steady state thermal analysis setup
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
initial_condition = steady_solution.Children[0]
initial_condition.InitialTemperature = InitialTemperatureType.NonUniform
initial_condition.InitialEnvironment = steady

transient_analysis_settings = transient.AnalysisSettings
transient_analysis_settings.StepEndTime = Quantity(200, "sec")

internal_heat_generation2 = transient.AddInternalHeatGeneration()

ic1 = [i for i in NSall if i.Name == "ic-1"][0]
internal_heat_generation2.Location = ic1
internal_heat_generation2.Magnitude.Output.SetDiscreteValue(0, Quantity(5e7, "W m^-1 m^-1 m^-1"))

# -- Add result objects for post processing --
#
transient_solution = transient.Solution
transient_temperature_result = transient_solution.AddTemperature()
temperature_probe1 = transient_solution.AddTemperatureProbe()
temperature_probe1.GeometryLocation = ic6
temperature_probe2 = transient_solution.AddTemperatureProbe()
temperature_probe2.GeometryLocation = ic1

# -- Solve --
#
transient_solution.Solve(True)

# -- Save files and close Mechanical --
#
# Mechanical file (mechdb) contains results for each analysis
app.save(os.path.join(OUTPUT_DIR, "pcb.mechdb"))
project_directory = ExtAPI.DataModel.Project.ProjectDirectory
app.exit()
