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
.. _ref_speops-optislang-01-light-guide-robustness-study:

Evaluating robustness of exterior lightguide
############################################

In this example, we use Speos and optiSLang to analyze the robustness of a prismatic light
guide and quantify the failure rate due to production tolerances in an automated way.
We will understand which tolerances lead to regulation fails for the automotive
Day-Time-Running lights and which tolerances must be improved to increase the optical
performance. Additionally, we will evaluate the scattering of the homogeneity (RMS-contrast)
and the lit appearance (average luminance) to see what the worst design looks like due to
tolerances.

"""  # noqa: D400, D415

import os
import pathlib
import time

from ansys.optislang.core import Optislang
import ansys.optislang.core.node_types as node_types
from ansys.optislang.core.nodes import DesignFlow
from ansys.optislang.core.project_parametric import (
    ComparisonType,
    ConstraintCriterion,
    DistributionType,
    ObjectiveCriterion,
    StochasticParameter,
)
import ansys.speos.core as core
from ansys.speos.core import Body, Project
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.source import SourceSurface
from comtypes.client import CreateObject
import numpy as np

###############################################################################
# Parameters for the script
# -------------------------
# The following parameters are used to control the script execution. You can
# modify these parameters to suit your needs.
#

MAXIMUM_NUMBER_SIMULATIONS: int = 200
"""Maximum number of simulations for the robustness analysis."""

PARAMETERS: list[dict] = [
    {
        "name": "LED_delta_x",
        "value": 0.0,
        "distribution_type": "NORMAL",
        "distribution_parameters": [0, 0.25],  # mean value, standard deviation
    },
    {
        "name": "LED_delta_y",
        "value": 0.0,
        "distribution_type": "NORMAL",
        "distribution_parameters": [0, 0.25],  # mean value, standard deviation
    },
    {
        "name": "LED_delta_z",
        "value": 0.0,
        "distribution_type": "NORMAL",
        "distribution_parameters": [0, 0.25],  # mean value, standard deviation
    },
    {
        "name": "Flux",
        "value": 200.0,
        "distribution_type": "TRUNCATEDNORMAL",
        "distribution_parameters": [
            300,
            45,
            200,
            400,
        ],  # mean value, standard deviation, lower bound, upper bound
    },
]
"""Input parameters and their statistical distributions."""

RESPONSES: list[dict] = [
    {"name": "RMS_contrast", "value": 1.0},
    {"name": "Average", "value": 120.0},
    {"name": "Number_of_rules_limited_passed", "value": 0.0},
    {"name": "Number_of_rules_failed", "value": 0.0},
]
"""Expected responses in the robustness analysis."""

CRITERIA: list[dict] = [
    {"name": "RMS_contrast", "type": "constraint", "limit": 0.2, "target": "<="},
    {"name": "Average", "type": "constraint", "limit": 160000, "target": ">="},
    {
        "name": "Number_of_rules_limited_passed",
        "type": "constraint",
        "limit": 2,
        "target": "<=",
    },
    {"name": "Number_of_rules_failed", "type": "constraint", "limit": 0, "target": "<="},
]
"""Evaluation criteria for the robustness analysis."""

VARIATION_ANALYSIS_BOUNDARIES = {
    "maximum_number_simulations": MAXIMUM_NUMBER_SIMULATIONS,
    "parameters": PARAMETERS,
    "responses": RESPONSES,
    "criteria": CRITERIA,
}
"""Variation analysis boundaries for the robustness study."""

###############################################################################
# Define functions
# ----------------
# The following functions are defined to perform various tasks in the
# robustness analysis workflow, such as cleaning databases, displacing faces and bodies,
# opening results, changing source positions and powers, running Speos simulations,
# and creating the optiSLang workflow.


def clean_all_dbs(speos_client: core.kernel.client.SpeosClient):
    """
    Clean the database info loaded inside a client.

    Parameters
    ----------
    speos_client: core.SpeosClient

    Returns
    -------

    """
    for item in (
        speos_client.jobs().list()
        + speos_client.scenes().list()
        + speos_client.simulation_templates().list()
        + speos_client.sensor_templates().list()
        + speos_client.source_templates().list()
        + speos_client.intensity_templates().list()
        + speos_client.spectrums().list()
        + speos_client.vop_templates().list()
        + speos_client.sop_templates().list()
        + speos_client.parts().list()
        + speos_client.bodies().list()
        + speos_client.faces().list()
    ):
        item.delete()


def displace_face(edit_face, face_name, xyz=[0, 0, 0]):
    """
    Move a face in a translational direction defined by a provided vector xyz.

    Parameters
    ----------
    edit_face: ansys.speos.core.face.Face
    face_name: str
        geo_path of face
    xyz: tuple
        A tuple with 3 elements defining a vector defined by xyz

    Returns
    -------

    """
    temp_face_vertices = edit_face._face.vertices
    temp_face_vertices = np.array(temp_face_vertices).reshape((-1, 3))
    new_face_vertices = [np.add(item, xyz) for item in temp_face_vertices]
    new_face_vertices = np.array(new_face_vertices).reshape((1, -1)).tolist()[0]

    edit_face.set_vertices(new_face_vertices)
    edit_face.commit()


def displace_body(project, body_name, xyz=[1, 0, 0]):
    """
    Move a body in a translational direction defined by a provided vector xyz.

    Parameters
    ----------
    project: script.Project
    body_name: str
        geo_path of a body
    xyz: tuple
        A tuple with 3 elements defining a vector defined by xyz

    Returns
    -------

    """
    print(body_name)
    edit_body = project.find(name=body_name, name_regex=True, feature_type=Body)[0]
    faces = edit_body._geom_features
    for face in faces:
        face_name = face._name
        displace_face(face, face_name="/".join([body_name, face_name]), xyz=xyz)


def open_result(file):
    """
    Open result file and extract results.

    Parameters
    ----------
    file: str
        file directory

    Returns
    -------
    dict
        a dictionary with results

    """
    dpf_instance = CreateObject("XMPViewer.Application")
    dpf_instance.OpenFile(file)
    temp_dir = os.getenv("TEMP")
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    if "radiance" in file.lower():
        dpf_instance.ImportTemplate(
            os.path.join(os.path.abspath(""), "Lightguide.speos", "DRL_Upper-only.VE-measure.xml"),
            1,
            1,
            0,
        )
        export_dir = os.path.join(temp_dir, "lg_robustness_result.txt")
        dpf_instance.MeasuresExportTXT(export_dir)
        file = open(export_dir)
        content = file.readlines()
        RMS_content = content[10]
        Average_content = content[11]
        res = {
            "RMS_contrast": float(
                RMS_content[RMS_content.find("\tValue=") + 7 : RMS_content.find(r"ValueUnit=")]
            ),
            "Average": float(
                Average_content[
                    Average_content.find("\tValue=") + 7 : Average_content.find(r"ValueUnit=")
                ]
            ),
        }
        return res
    else:
        dpf_instance.ImportTemplate(
            os.path.join(os.path.abspath(""), "Lightguide.speos", "ECE_R87_DRL_WithoutLines.xml"),
            1,
            1,
            0,
        )
        export_dir = os.path.join(temp_dir, f"lg_robustness_result.txt")
        dpf_instance.MeasuresExportTXT(export_dir)
        limited_passed_count = 0
        failed_count = 0
        passed_count = 0
        with open(export_dir) as result_file:
            for line in result_file:
                if "RuleStatus" in line:
                    if "(specification failed)" in line:
                        limited_passed_count += 1
                    elif "(passed)" in line:
                        passed_count += 1
                    elif "(failed)" in line:
                        failed_count += 1
                    else:
                        print("Rules status is unknown.")

        res = {
            "Number_of_rules_limited_passed": limited_passed_count,
            "Number_of_rules_failed": failed_count,
        }
        return res


def change_surface_source_position(project, sources, source_position_dict):
    """
    change the position of surface where surface source is linked.

    Parameters
    ----------
    project: script.Project
        project in which source will be modified.
    sources: script.Source
        sources inside the project.
    source_position_dict: dict
        A dictionary within which position information is saved.

    Returns
    -------

    """
    for source in sources:
        source_name = source.get(key="name")
        source_geo_path = source.get(key="geo_path")[0]
        source_linked_body = source_geo_path["geo_path"].split("/")[0]
        if source_name in source_position_dict:
            displace_body(
                project,
                "/".join([source_linked_body]),
                source_position_dict[source_name],
            )


def change_source_power(sources, source_power_dict):
    """
    Change the power of surface where surface source is linked.

    Parameters
    ----------
    sources: script.Source
        sources inside the project.
    source_power_dict: dict
        A dictionary within which source power information is saved.

    Returns
    -------

    """
    for source in sources:
        source_name = source.get(key="name")
        if source_name in source_power_dict:
            source.set_flux_luminous(value=source_power_dict[source_name])
            source.commit()


def speos_simulation(hid, speos, parameters):
    """
    Run speos simulation with given source parameters to be changed.

    Parameters
    ----------
    hid: str
        string that contains the design id
    speos: core.Speos
    parameters: dict
        dictionary includes parameters to be used for each design iteration

    Returns
    -------

    """
    new_parameter_values = {p["name"]: p["value"] for p in parameters}

    clean_all_dbs(speos.client)
    script_folder = pathlib.Path(__file__).resolve().parent
    speos_file = script_folder / "Lightguide.speos" / "Lightguide.speos"
    project = Project(speos=speos, path=str(speos_file))
    # project.preview()

    # Update of the light source power
    sources = project.find(name=".*", name_regex=True, feature_type=SourceSurface)
    new_sources_power = {
        "Surface.1:6015": new_parameter_values.get("Flux"),
        "Surface.2:30": new_parameter_values.get("Flux"),
    }

    change_source_power(sources, new_sources_power)

    # Update of the source position
    new_source_displacement = {
        "Surface.1:6015": [
            new_parameter_values.get("LED_delta_x"),
            new_parameter_values.get("LED_delta_y"),
            new_parameter_values.get("LED_delta_z"),
        ],
        "Surface.2:30": [
            new_parameter_values.get("LED_delta_x"),
            new_parameter_values.get("LED_delta_y"),
            new_parameter_values.get("LED_delta_z"),
        ],
    }
    change_surface_source_position(project, sources, new_source_displacement)
    # project.preview()

    # execution of the Speos simulation
    sim = project.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sim.set_stop_condition_rays_number(2000000).commit()
    res = sim.compute_CPU()

    # Result extraction
    xmp_files = [item.path for item in res if ".xmp" in item.path]
    response = {}
    result_design = {}
    for xmp in xmp_files:
        response.update(open_result(xmp))
    result_design.update(
        hid=hid,
        responses=[
            {"name": "RMS_contrast", "value": response.get("RMS_contrast")},
            {"name": "Average", "value": response.get("Average")},
            {
                "name": "Number_of_rules_limited_passed",
                "value": response.get("Number_of_rules_limited_passed"),
            },
            {"name": "Number_of_rules_failed", "value": response.get("Number_of_rules_failed")},
        ],
    )
    result_print = str("Design " + result_design["hid"]) + ": "
    for i in range(0, len(result_design["responses"])):
        result_print += (
            str(result_design["responses"][i]["name"])
            + " = "
            + str(result_design["responses"][i]["value"])
            + " | "
        )
    print(result_print)
    return result_design


def get_executable(version):
    """Returns the optiSLang executable for given version.

    Parameters
    ----------
    version : int
        optiSLang version, e.g. 251

    Returns
    -------
    pathlib.Path
        Executable path.
    """
    if os.getenv(f"AWP_ROOT{version}"):
        awp_root = os.getenv(f"AWP_ROOT{version}")
        osl_com = pathlib.Path(awp_root) / "optiSLang" / "optislang.com"
    else:
        raise Exception(f"optiSLang installation not found. Please install optiSLang v{version}.")
    return osl_com


def create_workflow(osl, user_input_json):
    """
    This function creates the robustness workflow
    with a proxy node and register parameters and responses.

    Parameters
    ----------
    osl: ansys.optislang.core
        Ansys optiSLang instance
    user_input_json: dict
        dictionary with optimization boundaries as json

    Returns
    -------
    ansys.optislang.core.nodes
        optiSLang Optimization system and proxy solver node.
    """
    # create system
    root_system = osl.application.project.root_system
    robustness_system = root_system.create_node(type_=node_types.Robustness, name="Robustness")

    # create node
    proxy_solver_node = robustness_system.create_node(
        type_=node_types.ProxySolver, name="Proxy Solver", design_flow=DesignFlow.RECEIVE_SEND
    )
    mop_node = root_system.create_node(type_=node_types.Mop, name="MOP")

    # connect system with MOP node
    robustness_system_out = robustness_system.get_output_slots(name="OMDBPath")[0]
    mop_node_in = mop_node.get_input_slots(name="IMDBPath")[0]
    robustness_system_out.connect_to(mop_node_in)

    # register parameter and responses
    proxy_solver_node.load(user_input_json)
    proxy_solver_node.register_locations_as_parameter()
    proxy_solver_node.register_locations_as_response()

    # adjust parameter ranges
    for parameter in user_input_json.get("parameters"):
        robustness_system.parameter_manager.modify_parameter(
            StochasticParameter(
                name=parameter.get("name"),
                reference_value=parameter.get("value"),
                distribution_type=getattr(DistributionType, parameter.get("distribution_type")),
                distribution_parameters=parameter.get("distribution_parameters"),
            )
        )

    # robustness system settings
    robustness_settings = robustness_system.get_property("AlgorithmSettings")
    robustness_settings["num_discretization"] = user_input_json.get("maximum_number_simulations")
    robustness_system.set_property("AlgorithmSettings", robustness_settings)

    # proxy node settings
    multi_design_launch_num = 30  # set -1 to solve all designs simultaneously
    proxy_solver_node.set_property("MultiDesignLaunchNum", multi_design_launch_num)
    proxy_solver_node.set_property("ForwardHPCLicenseContextEnvironment", True)

    return robustness_system, proxy_solver_node


def criteria_definition(system, load_json):
    """
    This functions defines the robustness criteria in optiSLang based on user input
    Parameters
    ----------
    system: ansys.optislang.core.nodes
        optiSLang Optimization system
    load_json: dict
        dictionary with optimization boundaries as json

    Returns
    -------

    """
    for crit in load_json.get("criteria"):
        crit_name = crit.get("name")
        if crit.get("type") == "objective":
            if crit.get("target") == "MIN":
                comparison_type_obj = ComparisonType.MIN
            elif crit.get("target") == "MAX":
                comparison_type_obj = ComparisonType.MAX
            else:
                raise Exception("objective type not defined")

            system.criteria_manager.add_criterion(
                ObjectiveCriterion(
                    name=f"obj_{crit_name}", expression=crit_name, criterion=comparison_type_obj
                )
            )

        if crit.get("type") == "constraint":
            if crit.get("target") == "<=":
                comparison_type_constr = ComparisonType.LESSEQUAL
            elif crit.get("target") == ">=":
                comparison_type_constr = ComparisonType.GREATEREQUAL
            else:
                raise Exception("Constraint type not well defined")
            system.criteria_manager.add_criterion(
                ConstraintCriterion(
                    name=f"constr_{crit_name}",
                    expression=crit_name,
                    criterion=comparison_type_constr,
                    limit_expression=str(crit.get("limit")),
                )
            )


def calculate(designs):
    """
    This function evaluated the outputs based on the given designs parameters.
    Parameters
    ----------
    designs: list
        A list of designs to be evaluated. For each design the parameter values are defined

    Returns
    -------
    list
        A list of evaluated designs with the corresponding outputs.
    """
    # create speos instance
    from ansys.speos.core import launcher

    speos = launcher.launch_local_speos_rpc_server(version="252")

    # speos = core.Speos(host="localhost", port=50098)

    # run speos simulation
    result_design_list = []

    # testing
    design = designs[0]
    hid = design["hid"]
    parameters = design["parameters"]
    result_design = speos_simulation(hid, speos, parameters)
    exit()
    # for design in designs:
    #     hid = design["hid"]
    #     parameters = design["parameters"]

    #     result_design = speos_simulation(hid, speos, parameters)
    #     result_design_list.append(result_design)

    # close speos instance
    speos.client.close()
    return result_design_list


def get_design_values(osl):
    """

    Parameters
    ----------
    osl: ansys.optislang.core
        Ansys optiSLang instance

    Returns
    -------
    list of dict:
        A list of dictionaries containing the all design information for each design.
    """
    project_tree = osl.osl_server.get_full_project_tree()
    project_actors = project_tree["projects"][0]["system"]
    algorithmsystem_uid = project_actors["nodes"][0]["uid"]
    actor_info = osl.osl_server.get_actor_status_info(
        algorithmsystem_uid, 0, include_design_values=True
    )

    return actor_info


def get_design_quality_values(osl):
    """
    This function calculates the probability of failure for each response.
    osl: ansys.optislang.core
        Ansys optiSLang instance

    Returns
    -------
    real
        The probability of failure for the response as well as the number of feasible designs.
    """
    list_design_information = get_design_values(osl)

    rms_contrast_count_failed = 0
    average_count_failed = 0
    rules_specification_count_failed = 0
    rules_count_failed = 0
    feasible_designs = 0

    for design_status in list_design_information.get("design_status"):
        if design_status.get("feasible"):
            feasible_designs += 1

    response_names = list_design_information.get("designs").get("response_names")
    designs = list_design_information.get("designs").get("values")

    for design_values in designs:
        response_values = design_values.get("response_values")
        responses = {name: value for name, value in zip(response_names, response_values)}

        if responses.get("RMS_contrast") > 0.2:
            rms_contrast_count_failed += 1
        if responses.get("Average") < 160000.0:
            average_count_failed += 1
        if responses.get("Number_of_rules_limited_passed") > 2.0:
            rules_specification_count_failed += 1
        if responses.get("Number_of_rules_failed") > 0.0:
            rules_count_failed += 1

    return (
        rms_contrast_count_failed / len(designs) * 100,
        average_count_failed / len(designs) * 100,
        rules_specification_count_failed / len(designs) * 100,
        rules_count_failed / len(designs) * 100,
        feasible_designs,
    )


###############################################################################
# Main script execution
# ---------------------

# optiSLang Project creation and workflow setup
osl_executable = get_executable(252)
my_osl = Optislang(
    executable=osl_executable,
    ini_timeout=60,
    port=50099,
    # loglevel="DEBUG"
)
print(f"Using optiSLang version {my_osl.osl_version_string}")

# Create workflow
parametric_system, proxy_node = create_workflow(my_osl, VARIATION_ANALYSIS_BOUNDARIES)

# Create criteria definition
criteria_definition(parametric_system, VARIATION_ANALYSIS_BOUNDARIES)

# Save project
temp_dir = pathlib.Path(os.getenv("TEMP"))
project_name = "_proxy_solver_workflow.opf"
# my_osl.application.save_as(temp_dir / project_name)  # uncomment to save the project

# optiSLang project execution
my_osl.application.project.start(wait_for_finished=False)
print("Variation Analysis: started.")

# Run Robustness analysis and loop until get_status()
# returns "Processing done" for the root system
while not my_osl.project.root_system.get_status() == "Processing done":
    design_list = proxy_node.get_designs()
    if len(design_list):
        responses_dict = calculate(design_list)
        proxy_node.set_designs(responses_dict)
    time.sleep(1)

# Run MOP node
my_osl.application.project.start(wait_for_finished=True)
print("Variation Analysis: Done!")

# Get quality values
(
    rms_contrast_fail_prob,
    average_fail_prob,
    specification_rules_fail_prob,
    national_rules_fail_prob,
    num_feasible_designs,
) = get_design_quality_values(my_osl)

print(f'{"*" * 25} SUMMARY {"*" * 25}')
print(f"Probability of failure for RMS contrast: {round(rms_contrast_fail_prob, 1)} %")
print(f"Probability of failure for Average: {round(average_fail_prob, 1)} %")
print(
    f"Probability of failure for fulfillment national rules: {round(national_rules_fail_prob, 1)} %"
)
print(
    "Probability of failure for fulfillment specification rules: "
    f"{round(specification_rules_fail_prob, 1)} %\n"
)
print(
    f"{num_feasible_designs} out of {VARIATION_ANALYSIS_BOUNDARIES['maximum_number_simulations']} "
    "designs are feasible."
)
print("*" * 50)

# Close optiSLang
my_osl.dispose()
print("OSL Project finished.")
