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
.. _ref_fluent_mechanical_02-mechanical:

Thermo-mechanical assessment of representative exhaust manifold model
#####################################################################

MultiPhysics example: Thermo-Mechanical simulation on a representative exhuast manifold
model.

"""  # noqa: D400, D415

import os
from pathlib import Path

from ansys.mechanical.core import launch_mechanical
from ansys.mechanical.core.examples import download_file
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

###############################################################################
# Preparing the environment
# -------------------------
# This section is only necessary for workflow runs and docs generation. It checks
# the environment variables to determine which image to use for the mechanical service.
# If you are running this script outside of a workflow, you can ignore this section.
#

version = None
if "ANSYS_MECHANICAL_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_MECHANICAL_RELEASE"]
    version = int(image_tag.replace(".", ""))

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
mechanical = launch_mechanical(batch=False, cleanup_on_exit=False)
print(mechanical)


def display_image(image_name):
    plt.figure(figsize=(16, 9))
    plt.imshow(mpimg.imread(os.path.join(OUTPUT_DIR, image_name)))
    plt.xticks([])
    plt.yticks([])
    plt.axis("off")
    plt.show()


###############################################################################
# Input files needed for the simulation
# ---------------- --------------------
# Download the input files needed for the simulation.
#
geometry_path = download_file(
    "Exhaust_Manifold_Geometry.pmdb", "pyansys-workflow", "exhaust-manifold", "pymechanical"
)
material_path = download_file(
    "Nonlinear_Material.xml", "pyansys-workflow", "exhaust-manifold", "pymechanical"
)

# Files necessary for the thermal simulation from fluent analysis

temp_htc_data_high_path = os.path.join(OUTPUT_DIR, "htc_temp_mapping_HIGH_TEMP.csv")
temp_htc_data_med_path = os.path.join(OUTPUT_DIR, "htc_temp_mapping_MEDIUM_TEMP.csv")
temp_htc_data_low_path = os.path.join(OUTPUT_DIR, "htc_temp_mapping_LOW_TEMP.csv")

all_input_files = {
    "geometry_path": geometry_path,
    "material_path": material_path,
    "temp_htc_data_high_path": temp_htc_data_high_path,
    "temp_htc_data_med_path": temp_htc_data_med_path,
    "temp_htc_data_low_path": temp_htc_data_low_path,
}

# Upload to Mechanical Remote session server and get the file paths

project_directory = mechanical.project_directory
print(f"project directory = {project_directory}")
for input_file_name, input_file_path in all_input_files.items():

    # Upload the file to the project directory.
    mechanical.upload(file_name=input_file_path, file_location_destination=project_directory)

    # Build the path relative to project directory.
    base_name = os.path.basename(input_file_path)
    combined_path = os.path.join(project_directory, base_name)
    server_file_path = combined_path.replace("\\", "\\\\")
    mechanical.run_python_script(f"{input_file_name} = '{server_file_path}'")
    result = mechanical.run_python_script(f"{input_file_name}")
    print(f"path of {input_file_name} on server: {result}")


###############################################################################
# Configure graphics for image export
# -----------------------------------
#

mechanical.run_python_script(
    """
ExtAPI.Graphics.Camera.SetSpecificViewOrientation(
    Ansys.Mechanical.DataModel.Enums.ViewOrientationType.Iso
)
ExtAPI.Graphics.Camera.SetFit()
image_export_format = Ansys.Mechanical.DataModel.Enums.GraphicsImageExportFormat.PNG
settings_720p = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
settings_720p.Resolution = (
    Ansys.Mechanical.DataModel.Enums.GraphicsResolutionType.EnhancedResolution
)
settings_720p.Background = Ansys.Mechanical.DataModel.Enums.GraphicsBackgroundType.White
settings_720p.Width = 1280
settings_720p.Height = 720
settings_720p.CurrentGraphicsDisplay = False
"""
)

###############################################################################
# Import geometry
# ---------------
#


import os

geometry_import_group = Model.GeometryImportGroup
geometry_import = geometry_import_group.AddGeometryImport()
geometry_import_format = Ansys.Mechanical.DataModel.Enums.GeometryImportPreference.Format.Automatic
geometry_import_preferences = Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()
geometry_import_preferences.ProcessNamedSelections = True
geometry_import_preferences.NamedSelectionKey = ""
geometry_import_preferences.ProcessMaterialProperties = True
geometry_import_preferences.ProcessCoordinateSystems = True
geometry_import.Import(geometry_path, geometry_import_format, geometry_import_preferences)
project_directory = ExtAPI.DataModel.Project.ProjectDirectory
ExtAPI.Graphics.Camera.SetFit()
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "geometry.png"), image_export_format, settings_720p
)

mechanical.download(files=os.path.join(project_directory, "geometry.png"), target_dir=OUTPUT_DIR)
display_image("geometry.png")


###############################################################################
# Import material, assign it to the bodies and create Named Selections
# --------------------------------------------------------------------
#


materials = ExtAPI.DataModel.Project.Model.Materials
materials.Import(material_path)
materials.RefreshMaterials()

PRT1 = [x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "Geom-2\Geom-1\solid"][0]

# Assign it to the bodies
nmat = "1_HiSi_Model3_Exhaust Manifold updated"
PRT1.Material = nmat


# Select MKS units
ExtAPI.Application.ActiveUnitSystem = Ansys.ACT.Interfaces.Common.MechanicalUnitSystem.StandardMKS

# Store all main tree nodes as variables
GEOM = Model.Geometry
MAT_GRP = Model.Materials

# Create NS for Named Selection.

NS_GRP = ExtAPI.DataModel.Project.Model.NamedSelections
BRACKET_FIX_NS = [x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "bracket_fix"][0]
INTERFACE_SURFACE_NS = [
    x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "interface_surface"
][0]
EXHAUST_MANIFOLD_NS = [x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "exhaust_manifold"][
    0
]
TOP_BRACKET_SURFACE_NS = [
    x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "top_bracket_surface"
][0]
SPACERS_NS = [x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "spacers"][0]
EM_OUTER_SURFACE_NS = [x for x in ExtAPI.DataModel.Tree.AllObjects if x.Name == "em_outer_surface"][
    0
]

MESH = Model.Mesh
MESH.ElementSize = Quantity(0.004, "m")
MESH.UseAdaptiveSizing = False
MESH.MaximumSize = Quantity(0.004, "m")
MESH.ShapeChecking = 0
body_sizing = MESH.AddSizing()
selection = NS_GRP.Children[5]
body_sizing.Location = selection
body_sizing.ElementSize = Quantity(4e-3, "m")
# body_sizing.CaptureCurvature = True
# body_sizing.CurvatureNormalAngle = Quantity(0.31, "rad")
# body_sizing.LocalMinimumSize = Quantity(0.00025, "m")

Tree.Activate([MESH])
MESH.GenerateMesh()

# Export mesh image

ExtAPI.Graphics.Camera.SetFit()
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "mesh.png"), image_export_format, settings_720p
)

mechanical.download(files=os.path.join(project_directory, "mesh.png"), target_dir=OUTPUT_DIR)
display_image("mesh.png")

###############################################################################
# Add Transient Thermal Analysis and set up the analysis settings
# ---------------------------------------------------------------
#


Model.AddTransientThermalAnalysis()

# Store all main tree nodes as variables

TRANS_THERM = Model.Analyses[0]
TRANS_THERM_SOLN = TRANS_THERM.Solution
ANA_SETTINGS = TRANS_THERM.Children[1]

# Setup transient thermal analysis settings

# ANA_SETTINGS.AutomaticTimeStepping = AutomaticTimeStepping.On
ANA_SETTINGS.SolverType = SolverType.Direct
ANA_SETTINGS.NonLinearFormulation = NonLinearFormulationType.Full

ANA_SETTINGS.NumberOfSteps = 1
ANA_SETTINGS.SetStepEndTime(1, Quantity("720[s]"))
ANA_SETTINGS.NumberOfSteps = 14
analysis_step = (
    (1, Quantity("1e-3[s]")),
    (2, Quantity("2e-3[s]")),
    (3, Quantity("20[s]")),
    (4, Quantity("30[s]")),
    (5, Quantity("320[s]")),
    (6, Quantity("330[s]")),
    (7, Quantity("350[s]")),
    (8, Quantity("360[s]")),
    (9, Quantity("380[s]")),
    (10, Quantity("390[s]")),
    (11, Quantity("680[s]")),
    (12, Quantity("690[s]")),
    (13, Quantity("710[s]")),
    (14, Quantity("720[s]")),
)
for i, q in analysis_step:
    ANA_SETTINGS.SetStepEndTime(i, q)

# Applied External HTCs and Temperature data

External_Convection_Load_1 = TRANS_THERM.AddConvection()
selection = NS_GRP.Children[8]
External_Convection_Load_1.Location = selection

External_Convection_Load_1.FilmCoefficient.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_1.FilmCoefficient.Output.DiscreteValues = [
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
    Quantity("60[W m^-1 m^-1 K^-1]"),
]

External_Convection_Load_1.AmbientTemperature.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_1.AmbientTemperature.Output.DiscreteValues = [
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
    Quantity("473.15[K]"),
]


External_Convection_Load_2 = TRANS_THERM.AddConvection()
selection = NS_GRP.Children[7]
External_Convection_Load_2.Location = selection

External_Convection_Load_2.FilmCoefficient.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_2.FilmCoefficient.Output.DiscreteValues = [
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
    Quantity("20[W m^-1 m^-1 K^-1]"),
]

External_Convection_Load_2.AmbientTemperature.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_2.AmbientTemperature.Output.DiscreteValues = [
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
    Quantity("498.15[K]"),
]


External_Convection_Load_3 = TRANS_THERM.AddConvection()
selection = NS_GRP.Children[6]
External_Convection_Load_3.Location = selection

External_Convection_Load_3.FilmCoefficient.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_3.FilmCoefficient.Output.DiscreteValues = [
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
    Quantity("500[W m^-1 m^-1 K^-1]"),
]

External_Convection_Load_3.AmbientTemperature.Inputs[0].DiscreteValues = [
    Quantity("0[s]"),
    Quantity("1e-3[s]"),
    Quantity("2e-3[s]"),
    Quantity("20[s]"),
    Quantity("30[s]"),
    Quantity("320[s]"),
    Quantity("330[s]"),
    Quantity("350[s]"),
    Quantity("360[s]"),
    Quantity("380[s]"),
    Quantity("390[s]"),
    Quantity("680[s]"),
    Quantity("690[s]"),
    Quantity("710[s]"),
    Quantity("720[s]"),
]

External_Convection_Load_3.AmbientTemperature.Output.DiscreteValues = [
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
    Quantity("373.15[K]"),
]

group_list = [External_Convection_Load_1, External_Convection_Load_2, External_Convection_Load_3]
grouping_folder = Tree.Group(group_list)
tree_grouping_folder_70 = DataModel.GetObjectsByName("New Folder")


###############################################################################
# Use the ouput from Fluent to import the temperature and HTC data
# ---------------------------------------------------------------
#

# Import HTCs and Temperature data From Fluent run

Imported_Load_Group = TRANS_THERM.AddImportedLoadExternalData()
imported_load_group_61 = Imported_Load_Group
imported_convection_62 = imported_load_group_61.AddImportedConvection()

external_data_files = Ansys.Mechanical.ExternalData.ExternalDataFileCollection()
external_data_files.SaveFilesWithProject = False
external_data_file_1 = Ansys.Mechanical.ExternalData.ExternalDataFile()
external_data_files.Add(external_data_file_1)
external_data_file_1.Identifier = "File1"
external_data_file_1.Description = "High"
external_data_file_1.IsMainFile = True
external_data_file_1.FilePath = temp_htc_data_high_path
external_data_file_1.ImportSettings = (
    Ansys.Mechanical.ExternalData.ImportSettingsFactory.GetSettingsForFormat(
        MechanicalEnums.ExternalData.ImportFormat.Delimited
    )
)
import_settings = external_data_file_1.ImportSettings
import_settings.SkipRows = 1
import_settings.SkipFooter = 0
import_settings.Delimiter = ","
import_settings.AverageCornerNodesToMidsideNodes = False
import_settings.UseColumn(0, MechanicalEnums.ExternalData.VariableType.NodeId, "", "Node ID@A")
import_settings.UseColumn(
    1, MechanicalEnums.ExternalData.VariableType.XCoordinate, "m", "X Coordinate@B"
)
import_settings.UseColumn(
    2, MechanicalEnums.ExternalData.VariableType.YCoordinate, "m", "Y Coordinate@C"
)
import_settings.UseColumn(
    3, MechanicalEnums.ExternalData.VariableType.ZCoordinate, "m", "Z Coordinate@D"
)
import_settings.UseColumn(
    4, MechanicalEnums.ExternalData.VariableType.Temperature, "K", "Temperature@E"
)
import_settings.UseColumn(
    5,
    MechanicalEnums.ExternalData.VariableType.HeatTransferCoefficient,
    "W m^-2 K^-1",
    "Heat Transfer Coefficient@F",
)
external_data_file_2 = Ansys.Mechanical.ExternalData.ExternalDataFile()
external_data_files.Add(external_data_file_2)
external_data_file_2.Identifier = "File2"
external_data_file_2.Description = "Med"
external_data_file_2.IsMainFile = False
external_data_file_2.FilePath = temp_htc_data_med_path
external_data_file_2.ImportSettings = (
    Ansys.Mechanical.ExternalData.ImportSettingsFactory.GetSettingsForFormat(
        MechanicalEnums.ExternalData.ImportFormat.Delimited
    )
)
import_settings = external_data_file_2.ImportSettings
import_settings.SkipRows = 1
import_settings.SkipFooter = 0
import_settings.Delimiter = ","
import_settings.AverageCornerNodesToMidsideNodes = False
import_settings.UseColumn(0, MechanicalEnums.ExternalData.VariableType.NodeId, "", "Node ID@A")
import_settings.UseColumn(
    1, MechanicalEnums.ExternalData.VariableType.XCoordinate, "m", "X Coordinate@B"
)
import_settings.UseColumn(
    2, MechanicalEnums.ExternalData.VariableType.YCoordinate, "m", "Y Coordinate@C"
)
import_settings.UseColumn(
    3, MechanicalEnums.ExternalData.VariableType.ZCoordinate, "m", "Z Coordinate@D"
)
import_settings.UseColumn(
    4, MechanicalEnums.ExternalData.VariableType.Temperature, "K", "Temperature@E"
)
import_settings.UseColumn(
    5,
    MechanicalEnums.ExternalData.VariableType.HeatTransferCoefficient,
    "W m^-2 K^-1",
    "Heat Transfer Coefficient@F",
)
external_data_file_3 = Ansys.Mechanical.ExternalData.ExternalDataFile()
external_data_files.Add(external_data_file_3)
external_data_file_3.Identifier = "File3"
external_data_file_3.Description = "Low"
external_data_file_3.IsMainFile = False
external_data_file_3.FilePath = temp_htc_data_low_path
external_data_file_3.ImportSettings = (
    Ansys.Mechanical.ExternalData.ImportSettingsFactory.GetSettingsForFormat(
        MechanicalEnums.ExternalData.ImportFormat.Delimited
    )
)
import_settings = external_data_file_3.ImportSettings
import_settings.SkipRows = 1
import_settings.SkipFooter = 0
import_settings.Delimiter = ","
import_settings.AverageCornerNodesToMidsideNodes = False
import_settings.UseColumn(0, MechanicalEnums.ExternalData.VariableType.NodeId, "", "Node ID@A")
import_settings.UseColumn(
    1, MechanicalEnums.ExternalData.VariableType.XCoordinate, "m", "X Coordinate@B"
)
import_settings.UseColumn(
    2, MechanicalEnums.ExternalData.VariableType.YCoordinate, "m", "Y Coordinate@C"
)
import_settings.UseColumn(
    3, MechanicalEnums.ExternalData.VariableType.ZCoordinate, "m", "Z Coordinate@D"
)
import_settings.UseColumn(
    4, MechanicalEnums.ExternalData.VariableType.Temperature, "K", "Temperature@E"
)
import_settings.UseColumn(
    5,
    MechanicalEnums.ExternalData.VariableType.HeatTransferCoefficient,
    "W m^-2 K^-1",
    "Heat Transfer Coefficient@F",
)

imported_load_group_61.ImportExternalDataFiles(external_data_files)

table = imported_load_group_61.Children[0].GetTableByName("Film Coefficient")
numofsteps = 15
Film_Coeff = [
    "File1:Heat Transfer Coefficient@F",
    "File2:Heat Transfer Coefficient@F",
    "File3:Heat Transfer Coefficient@F",
]
Amb_Temp = ["File1:Temperature@E", "File2:Temperature@E", "File3:Temperature@E"]
Ana_time = [
    "0",
    "1e-3",
    "2e-3",
    "20",
    "30",
    "320",
    "330",
    "350",
    "360",
    "380",
    "390",
    "680",
    "690",
    "710",
    "720",
]

for i in range(numofsteps - 1):
    table.Add(None)

table[0][0] = Film_Coeff[2]
table[0][1] = Amb_Temp[2]
table[0][2] = Ana_time[0]

table[1][0] = Film_Coeff[2]
table[1][1] = Amb_Temp[2]
table[1][2] = Ana_time[1]

table[2][0] = Film_Coeff[2]
table[2][1] = Amb_Temp[2]
table[2][2] = Ana_time[2]

table[3][0] = Film_Coeff[2]
table[3][1] = Amb_Temp[2]
table[3][2] = Ana_time[3]

table[4][0] = Film_Coeff[0]
table[4][1] = Amb_Temp[0]
table[4][2] = Ana_time[4]

table[5][0] = Film_Coeff[0]
table[5][1] = Amb_Temp[0]
table[5][2] = Ana_time[5]

table[6][0] = Film_Coeff[1]
table[6][1] = Amb_Temp[1]
table[6][2] = Ana_time[6]

table[7][0] = Film_Coeff[1]
table[7][1] = Amb_Temp[1]
table[7][2] = Ana_time[7]

table[8][0] = Film_Coeff[2]
table[8][1] = Amb_Temp[2]
table[8][2] = Ana_time[8]

table[9][0] = Film_Coeff[2]
table[9][1] = Amb_Temp[2]
table[9][2] = Ana_time[9]

table[10][0] = Film_Coeff[0]
table[10][1] = Amb_Temp[0]
table[10][2] = Ana_time[10]

table[11][0] = Film_Coeff[0]
table[11][1] = Amb_Temp[0]
table[11][2] = Ana_time[11]

table[12][0] = Film_Coeff[1]
table[12][1] = Amb_Temp[1]
table[12][2] = Ana_time[12]

table[13][0] = Film_Coeff[1]
table[13][1] = Amb_Temp[1]
table[13][2] = Ana_time[13]

table[14][0] = Film_Coeff[2]
table[14][1] = Amb_Temp[2]
table[14][2] = Ana_time[14]

selection = NS_GRP.Children[4]
imported_convection_62.Location = selection
imported_load_id = imported_convection_62.ObjectId
imported_load = DataModel.GetObjectById(imported_load_id)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# imported_convection_62.InternalObject.ExternalLoadSteppingType = 1
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

imported_load.ImportLoad()

Tree.Activate([imported_load])
ExtAPI.Graphics.Camera.SetFit()
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "imported_temperature.png"), image_export_format, settings_720p
)

mechanical.download(
    files=os.path.join(project_directory, "imported_temperature.png"), target_dir=OUTPUT_DIR
)
if GRAPHICS_BOOL:
    display_image("imported_temperature.png")

###############################################################################
# Solve and post-process the results
# ----------------------------------
#

# Insert results objects

Temp = TRANS_THERM_SOLN.AddTemperature()
Temp.DisplayTime = Quantity("680 [s]")

# Run Solution: Transient Thermal Simulation

# TRANS_THERM_SOLN.Solve(True)
TRANS_THERM_SS = TRANS_THERM_SOLN.Status

# Export temperature image

Tree.Activate([Temp])
ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay = (
    Ansys.Mechanical.DataModel.MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe
)
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "temperature.png"), image_export_format, settings_720p
)

mechanical.download(files=os.path.join(project_directory, "temperature.png"), target_dir=OUTPUT_DIR)
if GRAPHICS_BOOL:
    display_image("temperature.png")


###############################################################################
# Setup Structural Analysis
# -------------------------
#

Model.AddStaticStructuralAnalysis()

# Define analysis settings

# Setup static structural analysis settings
STAT_STRUC = Model.Analyses[1]
STAT_STRUC_SOLN = STAT_STRUC.Solution
STAT_STRUC_ANA_SETTING = STAT_STRUC.Children[0]

STAT_STRUC_ANA_SETTING.NumberOfSteps = 1
STAT_STRUC_ANA_SETTING.SetStepEndTime(1, Quantity("720[s]"))
STAT_STRUC_ANA_SETTING.NumberOfSteps = 14

analysis_step = (
    (1, Quantity("1e-3[s]")),
    (2, Quantity("2e-3[s]")),
    (3, Quantity("20[s]")),
    (4, Quantity("30[s]")),
    (5, Quantity("320[s]")),
    (6, Quantity("330[s]")),
    (7, Quantity("350[s]")),
    (8, Quantity("360[s]")),
    (9, Quantity("380[s]")),
    (10, Quantity("390[s]")),
    (11, Quantity("680[s]")),
    (12, Quantity("690[s]")),
    (13, Quantity("710[s]")),
    (14, Quantity("720[s]")),
)
for i, q in analysis_step:
    STAT_STRUC_ANA_SETTING.SetStepEndTime(i, q)
STAT_STRUC_ANA_SETTING.Activate()


# Add Imported Body Temperature load from Transient Thermal Run

STAT_STRUC.ImportLoad(Model.Analyses[0])
imported_load = DataModel.GetObjectsByName("Imported Body Temperature")[0]

table = imported_load.GetTableByName("Source Time")
numofsteps = 14
nCol = 2
Ana_time = [
    "1e-3",
    "2e-3",
    "20",
    "30",
    "320",
    "330",
    "350",
    "360",
    "380",
    "390",
    "680",
    "690",
    "710",
    "720",
]

for i in range(numofsteps - 1):
    table.Add(None)

for i in range(numofsteps):
    for j in range(nCol):
        table[i][j] = Ana_time[i]

imported_load.ImportLoad()

# Apply Fixed Support Condition

Fixed_Support = STAT_STRUC.AddFixedSupport()
selection = NS_GRP.Children[3]
Fixed_Support.Location = selection

###############################################################################
# Sovle and post-process the results
# ----------------------------------
#

SOLN = STAT_STRUC.Solution

TOT_DEF1 = SOLN.AddTotalDeformation()
TOT_DEF1.DisplayTime = Quantity("680 [s]")

EQV_STRS1 = SOLN.AddEquivalentStress()
EQV_STRS1.DisplayTime = Quantity("680 [s]")

EQV_PLAS_STRN1 = SOLN.AddEquivalentPlasticStrain()
EQV_PLAS_STRN1.DisplayTime = Quantity("680 [s]")

THERM_STRN1 = SOLN.AddThermalStrain()
THERM_STRN1.DisplayTime = Quantity("680 [s]")

# Solve Nonlinear Static Simulation

# SOLN.Solve(True)
STAT_STRUC_SS = SOLN.Status

# Export results images

Tree.Activate([TOT_DEF1])
ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay = (
    Ansys.Mechanical.DataModel.MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe
)
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "deformation.png"), image_export_format, settings_720p
)

Tree.Activate([EQV_STRS1])
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "stress.png"), image_export_format, settings_720p
)

Tree.Activate([EQV_PLAS_STRN1])
ExtAPI.Graphics.ExportImage(
    os.path.join(project_directory, "plastic_strain.png"), image_export_format, settings_720p
)

mechanical.download(files=os.path.join(project_directory, "deformation.png"), target_dir=OUTPUT_DIR)
mechanical.download(files=os.path.join(project_directory, "stress.png"), target_dir=OUTPUT_DIR)
mechanical.download(
    files=os.path.join(project_directory, "plastic_strain.png"), target_dir=OUTPUT_DIR
)

# Display the resilts
if GRAPHICS_BOOL:
    display_image("deformation.png")
    display_image("stress.png")
    display_image("plastic_strain.png")

###############################################################################
# Close the Mechanical
# --------------------
#
mechanical.exit()
