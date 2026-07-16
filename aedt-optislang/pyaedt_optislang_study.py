# /// script
# requires-python = "==3.12"
# dependencies = [
#     "ansys-optislang-core==1.5.0",
#     "pyaedt[all]==1.1.0"
# ]
# ///
# Copyright (C) 2024 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

# # Parametric AMOP design study with optiSLang ProxySolver and PyAEDT
# This example shows how to combine PyAEDT and pyOptiSLang to run a parametric
# AMOP study on a dipole antenna in HFSS. optiSLang's ProxySolver node
# is used to process the designs. Parallel design evaluations are managed via
# process_map. The AMOP system automatically creates a MOP, which is then used
# in a subsequent MOP-Solver based optimization system.
#
# ## Ways to run this script:
# * Open as a Jupytext notebook (requires installation of jupyter & jupytext).
# * Run with `uv run pyaedt_optislang_study.py` (requires installation of uv).
# * Create a virtual environment and install requirements from requirements file,
#   then run this script.
#
# ## Software requirements:
# - Ansys optiSLang version 2026 R1 or later.
# - Ansys Electronics Desktop version 2026 R1 or later.
#
# ## Python package requirements:
# - pyaedt[all] version 1.1.0 or later.
# - ansys-optislang-core version 1.5.0 or later.
# - Optional: jupyter & jupytext (to run within Jupyter lab as jupytext notebook)
#
# ## Keywords:
# * AEDT
# * HFSS
# * optiSLang
# * Parametric design study
# * ProxySolver
# * AMOP

# # Import the required packages.

# +
import pathlib
import tempfile
import time

from ansys.optislang.core import Optislang
import ansys.optislang.core.node_types as node_types
from ansys.optislang.core.nodes import DesignFlow
from ansys.optislang.core.project_parametric import (
    ComparisonType,
    Design,
    DesignVariable,
    ObjectiveCriterion,
    OptimizationParameter,
    Response,
    ResponseValueType,
)

from ansys.optislang.parametric.design_study import ParametricDesignStudyManager
from ansys.optislang.parametric.design_study_templates import (
    GeneralAlgorithmSettings,
    GeneralAlgorithmTemplate,
    OptimizationOnMOPTemplate,
    ProxySolverNodeSettings,
)
import dipole_antenna
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map as concurrent_map

# -

# ## Define constants.
#
# **Take note:** Jupyters execution model does not work well with multiprocessing.
# Therefore, a fallback is implemented further below to force sequential execution
# when executed as jupytext notebook.
#
# When executed outside of Jupyter, `MAX_PARALLEL_SOLVE_PROCESSES` can be increased.
# In that case please make sure the `NUM_CORES_PER_JOB * MAX_PARALLEL_SOLVE_PROCESSES`
# does not exceed the number of available cores.
# `NUM_CORES_PER_JOB` is defined in file `dipole_antenna.py`.
#

NG_MODE = True  # True: Exceute optiSLang in batch mode. False: Execute optiSLang with GUI.
MAX_PARALLEL_SOLVE_PROCESSES = 3  # Maximum number of parallel solve processes.
FORCE_SEQUENTIAL_SOLVE = (
    False  # Set to True to force sequential execution (for testing and debugging).
)
AEDT_WORKING_DIRNAME = "pyaedt_workingdir"  # Name of working directory to store the AEDT projects.
SOLVE_MODE = "DUMMY"  # "HFSS": Solve HFSS antenna model. "DUMMY": Run an analytical dummy model
# (for testing purposes).
SOLVE_TIMEOUT = 300  # Timeout for the solve process in [s]. If the solve process exceeds this
# time, it will be aborted.


# ## Define conversion facilities
#
# Define functions for conversion:
# * `get_legacy_signal_value_format` and `get_signal_value_format` are used to convert signal
#   data to the convention used by pyOptislang.
# * `get_parameter_values` returns parameter values of a design as dictionary.
# * `get_responses_as_design_variables` converts a dictionary of responses to a list of
#   DesignVariables.


def get_legacy_signal_value_format(abscissa, channel_data):
    """
    Convert to the following legacy signal format, which is supported by optiSLang's current
    ProxySolver implementation:

    Parameters:
        - freq: list of frequencies (abscissa)
        - loss: list of return loss values (channel data)
    Returns:
        dict: Legacy signal format compatible with optiSLang's ProxySolver.
        {
            "kind" : "signal",
            "matrix" : "[1,100](((0,0),(0.431848,0),(0.762402,0),(0.921527,0), ...
            "vector" : "[100]((0,0),(0.10101,0),(0.20202,0),(0.30303,0), ....
        }
        where the value pairs in () represent the real and the imaginary part of the signal,
        respectively. The "matrix" field contains the full 2D array of signal data, while the
        "vector" field contains only the abscissa values (frequencies) for reference.
        The "kind" field indicates that this is a signal-type response, which allows optiSLang to
        interpret and process it correctly in the workflow.

    """
    if abscissa is None or channel_data is None:
        return None

    result = {
        "kind": "signal",
        "matrix": (
            f"[1,{len(abscissa)}](({','.join([f'({l.real},{l.imag})' for l in channel_data])}))"
        ),
        "vector": f"[{len(abscissa)}]({','.join([f'({f.real},{f.imag})' for f in abscissa])})",
    }

    return result


def get_signal_value_format(abscissa, *args):
    if abscissa is None:
        return None
    for arg in args:
        if arg is None:
            return None
    result = {
        "abscissa": abscissa,
        "channels": list(args),
        "num_channels": len(args),
        "num_entries": len(abscissa),
        "type": "signal",
    }
    return result


def get_parameter_values(design):
    parameter_values = {}
    for parameter in design.parameters:
        parameter_values[parameter.name] = parameter.value
    return parameter_values


def get_responses_as_design_variables(result):
    # We assume any tuple of structure tuple(list, list) to represent a signal
    # Try to convert it to signal format.
    r = {}
    for key, value in result.items():
        if (
            isinstance(value, tuple)
            and len(value) == 2
            and all([isinstance(v, list) for v in value])
        ):
            try:
                r[key] = get_signal_value_format(*value)
            except Exception as e:
                print(
                    f"Tried to parse value {value} of field {key} to signal"
                    " but failed. --> Skipping"
                )
        else:
            r[key] = value
    return [DesignVariable(name, value=value) for name, value in r.items()]


# ## Define helper functions
#
# Define helper functions:
# * `in_notebook` is used to determine if the script is executed as a jupytext notebook.
# * `sort_designs_by_id` returns a sorted list of designs.
# * `print_designs` prints a list of designs.
# * `get_pareto_designs` returns the pareto (optimal) designs of a list of designs.
#


def in_notebook():
    try:
        from IPython import get_ipython

        return get_ipython() is not None and "IPKernelApp" in get_ipython().config

    except Exception:
        return False


def sort_designs_by_id(designs):
    return sorted(designs, key=lambda obj: int(obj.id.split(".")[1]))  # Sort by design number


def print_designs(designs):
    sorted_result_designs = sort_designs_by_id(designs)
    for design in sorted_result_designs:
        p = [f"{p.name}={p.value:-1.2f}" for p in design.parameters]
        r = []
        for response in design.responses:
            if (
                isinstance(response.value, dict)
                and "type" in response.value
                and response.value["type"] == "signal"
            ):
                r.append(
                    f"{response.name}=signal"
                    f"[{response.value['num_entries']}:{response.value['num_channels']}]"
                )
            elif response.value is None:
                r.append(f"{response.name}=None")
            else:
                r.append(f"{response.name}={response.value:-1.2f}")

        if design.pareto_design is True:
            pareto_str = " *"
        else:
            pareto_str = ""
        print(f"{design.id:4}: {', '.join(p)} | {', '.join(r)}{pareto_str}")


def get_pareto_designs(designs):
    return [design for design in designs if design.pareto_design is True]


# ## Define parallel compute function
#
# ``compute_designs()`` receives a list of design points from the ProxySolver,
# dispatches them to the worker in parallel and returns the collected responses.


def compute_designs(designs):
    print(f"Calculate {len(designs)} designs: {', '.join([design.id for design in designs])}")
    all_designs_inputs = []
    aedt_working_dir = WORKING_DIR / AEDT_WORKING_DIRNAME
    aedt_working_dir.mkdir(parents=True, exist_ok=True)
    for design in designs:
        hid = design.id
        design_temp_folder = tempfile.mkdtemp(dir=str(aedt_working_dir), prefix="pyaedt.")
        all_designs_inputs.append(
            (
                hid,
                design_temp_folder,
                get_parameter_values(design),
                SOLVE_TIMEOUT,
            )
        )

    if SOLVE_MODE == "HFSS":
        worker = dipole_antenna.hfss_worker
    elif SOLVE_MODE == "DUMMY":
        worker = dipole_antenna.dummy_worker
    else:
        raise KeyError(f"Unknown SOLVE_MODE: {SOLVE_MODE}")

    if in_notebook() or FORCE_SEQUENTIAL_SOLVE:
        # Run sequentially in Jupyter to avoid multiprocessing issues.
        print(
            "Running in notebook environment -> Ignoring MAX_PARALLEL_SOLVE_PROCESSES "
            "and running processes in sequence"
        )
        all_designs_responses = []
        for design_args in tqdm(all_designs_inputs, desc="Solving designs"):
            all_designs_responses.append(worker(design_args))
    else:
        all_designs_responses = concurrent_map(
            worker, all_designs_inputs, max_workers=MAX_PARALLEL_SOLVE_PROCESSES
        )

    solved_designs = []
    for design, response in zip(all_designs_inputs, all_designs_responses):
        solved_designs.append(
            Design(
                design_id=design[0],
                responses=get_responses_as_design_variables(response),
            )
        )

    print(f"Return {len(solved_designs)} designs")
    return solved_designs


# ## Prepare run
#
# * Create a temporary directory where data can be stored.
# * Define parameter and response definition
# * Define total number of designs to execute `num_designs_max`

# +
# Create temporary working dir
temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")
WORKING_DIR = pathlib.Path(temp_folder.name)
print(f"WORKING DIR: {WORKING_DIR}")

# The optiSLang project file (``pyoptislang_example_proxy_solver.opf``) is created
# on the fly by optiSLang when the ``Optislang`` instance is initialized.
osl_project_name = "pyoptislang_example_proxy_solver.opf"

# The dipole antenna geometry is parameterized by three variables:
# * l_dipole
# * wire_rad
# * port_gap
parameters_as_dict = {
    "l_dipole": {"reference_value": 10.2, "lower_bound": 9.0, "upper_bound": 12.0},
    "wire_rad": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
    "port_gap": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
}

# There are three responses expected.
# Signal responses:
# * return_loss
# Scalar responses:
# * freq_min
# * amplitude_min
responses_as_dict = {
    "return_loss": {
        "reference_value": get_legacy_signal_value_format([0, 1, 2], [0, -20, -10]),
        "type": "signal",
    },
    "freq_min": {
        "reference_value": 1.0,
        "type": "scalar",
    },
    "amplitude_min": {
        "reference_value": -10.0,
        "type": "scalar",
    },
}
# Maximum number of (HFSS or DUMMY) designs to compute in the AMOP system.
# If Target CoP is met earlier, AMOP may run less than the defined number of designs.
num_designs_max = 30

# AMOP parameter definition
parameters_objects = []
for parameter_name, parameter_data in parameters_as_dict.items():
    parameters_objects.append(
        OptimizationParameter(
            name=parameter_name,
            reference_value=parameter_data["reference_value"],
            range=(parameter_data["lower_bound"], parameter_data["upper_bound"]),
        )
    )


# For the AMOP system, we include all responses including the full return loss signal, so we
# can check if the return_loss signal is valid.
amop_responses_objects = []
for response_name, response_data in responses_as_dict.items():
    amop_responses_objects.append(
        Response(
            name=response_name,
            reference_value=response_data["reference_value"],
            reference_value_type=ResponseValueType.from_str(response_data["type"]),
        )
    )

# For optimization, we are only interested in the scalar responses, not the full return loss signal.
optimization_responses_objects = []
for response_name in ["freq_min", "amplitude_min"]:
    response_data = responses_as_dict[response_name]
    optimization_responses_objects.append(
        Response(
            name=response_name,
            reference_value=response_data["reference_value"],
            reference_value_type=ResponseValueType.from_str(response_data["type"]),
        )
    )
# -

# ## Initialize the optiSLang session
# Create optiSLang project named `osl_project_name` and create
#   * AMOP system with
#     * ProxySolver node
# and load the parameter/response schema.
#
# We are using the `GeneralAlgorithmTemplate` and `ParametricDesignStudyManager`
# convenience classes to create the AMOP workflow.
# The template automatically creates the required system and nodes and configures
# the ProxySolver to use `compute_designs()` as its callback function for design evaluation.


# +
# For initializing the project and saving it we create a short batch
# optiSLang session.
osl = Optislang(
    project_path=str(WORKING_DIR / osl_project_name),
    batch=True,
)
osl.application.save()
osl.dispose()
time.sleep(10)

# Now we reopen this new project in either batch or GUI mode, depending
# on definition of NG_MODE.
osl = Optislang(
    project_path=str(WORKING_DIR / osl_project_name),
    loglevel="INFO",
    log_process_stdout=True,  # log oSL messages to STDOUT
    log_process_stderr=True,  # log oSL error messages to STDERR
    batch=NG_MODE,
)

solver_settings = ProxySolverNodeSettings(callback=compute_designs, multi_design_launch_num=-1)

# Number of designs in an AMOP system
algorithm_settings = GeneralAlgorithmSettings(
    {
        "AMopSettings": {
            "min_cop": 0.9999,
            # "num_discretization_adaption" : 70,
            # "num_discretization_initial" : 50,
            # "num_discretization_initial": math.floor(num_designs_max/2),
            # "num_discretization_adaption": int(num_designs_max/2),
            "num_designs_max": num_designs_max,
            # "max_iteration": 3,
        }
    }
)
"""
# In case of a regular Sensitivity system, the number of designs is controlled as follows
algorithm_settings = GeneralAlgorithmSettings(
    {"AlgorithmSettings": {"num_discretization": num_designs_max}}
)
"""

amop_template = GeneralAlgorithmTemplate(
    parameters=parameters_objects,
    responses=amop_responses_objects,
    criteria=[],
    algorithm_type=node_types.AMOP,
    algorithm_settings=algorithm_settings,
    solver_type=node_types.ProxySolver,
    solver_settings=solver_settings,
)

design_study_manager = ParametricDesignStudyManager(
    optislang_instance=osl,
)
amop_study = design_study_manager.create_design_study(template=amop_template)
design_study_manager.save()
# -


# ## Run the parametric study
# Start the optiSLang workflow without blocking. Poll the ProxySolver for pending
# design batches, dispatch them to HFSS via ``compute_designs()``, and return the
# responses until all design points have been evaluated.

# +
amop_study.execute()
design_study_manager.save()
time.sleep(5)

print("AMOP result designs:")
print_designs(amop_study.get_result_designs())
print("AMOP design study done!")
# -

# ## Create MOP-based optimization system
# As a next step, an optimization system is created that uses the trained MOP
# as its surrogate model for design evaluation.
#
# We define the target frequency and maximum number of generations to be
# evaluated in the optimization system.
#
# We are using the `OptimizationOnMOPTemplate` and `ParametricDesignStudyManager`
# convenience classes to automatically create the optimization as well as the validation systems.

# +
# Define the target frequency
target_frequency = 1.35  # GHz

# Define number of generations to be used for the genetic algorithm
max_num_generations = 10

# Define the optimization criteria to minimize the squared difference between the resonance
# frequency and the target frequency.
criteria = [
    ObjectiveCriterion(
        "obj_freq_min", expression=f"(freq_min-{target_frequency})^2", criterion=ComparisonType.MIN
    )
]

# Get the AMOP system object we created in the previous step
amop_system = amop_study.managed_instances[0].instance

# Create a nature inspired optimization algorithm system that uses the trained MOP as its
# surrogate model for design evaluation.
optimizer_settings = GeneralAlgorithmSettings(
    {
        "OptimizerSettings": {
            "settings": {
                "MaxGenerations": max_num_generations,
            }
        }
    }
)
optimization_node_type = node_types.NOA2
optimization_template = OptimizationOnMOPTemplate(
    optimizer_name="Optimization",
    optimizer_type=optimization_node_type,
    parameters=parameters_objects,
    criteria=criteria,
    responses=optimization_responses_objects,
    mop_predecessor=amop_system,
    callback=compute_designs,
)

optimization_study = design_study_manager.create_design_study(optimization_template)

# Find the optimization system
for managed_instance in optimization_study.managed_instances:
    instance = managed_instance.instance
    if instance.type == optimization_node_type:
        optimization_system = instance
# Deactivate Auto save and set .omdb file update to "at end" to decrease run-time
optimization_system.set_property("AutoSaveMode", "no_auto_save")
optimization_system.set_property("UpdateResultFile", "at_end")
# Execute the optimization
optimization_study.execute()
# Save the project
design_study_manager.save()
print(f"Optimization design study done! Status: {optimization_study.get_status()}")
# -


# ## Display results

# +
print("MOP-based optimization designs:")
optimization_result_designs = optimization_study.get_result_designs()[
    1:
]  # Skip the first design, this is the validation design
print_designs(optimization_result_designs)

# Get the validated design result
validated_design = optimization_study.get_result_designs()[
    0
]  # The first design is the validated design
# Alternatively, the validated design can be obtained from the validation system, which is the
# last system in the optimization study.
# validation_system = optimization_study.get_last_parametric_system()
# validation_result_designs = validation_system.design_manager.get_designs()

# Get best design results
pareto_designs = get_pareto_designs(optimization_result_designs)
best_design = pareto_designs[0]
freq_min = best_design.responses[best_design.responses_names.index("freq_min")].value
amplitude_min = best_design.responses[best_design.responses_names.index("amplitude_min")].value
# Get validated design results
validated_design = pareto_designs[0]
freq_min_validated = validated_design.responses[
    validated_design.responses_names.index("freq_min")
].value
amplitude_min_validated = validated_design.responses[
    validated_design.responses_names.index("amplitude_min")
].value
print(f"Best design(s): {best_design.id}")
print(
    f"MOP-based optimization results: Resonance frequency: {freq_min:.3f}GHz,"
    f" Return loss: {amplitude_min:.2f}dB"
)
print(
    f"Validated results:              Resonance frequency: {freq_min_validated:.3f}GHz,"
    f" Return loss: {amplitude_min_validated:.2f}dB"
)

# Plot the resonance frequency over all designs
sorted_result_designs = sort_designs_by_id(optimization_result_designs)
freq_min_values = [
    design.responses[design.responses_names.index("freq_min")].value
    for design in sorted_result_designs
]
design_ids = [int(design.id.split(".")[1]) for design in sorted_result_designs]
plt.plot(design_ids, freq_min_values, marker=".")
# Highlight the best designs in red
plt.scatter(
    [int(p.id.split(".")[1]) for p in pareto_designs],
    [p.responses[p.responses_names.index("freq_min")].value for p in pareto_designs],
    c="None",
    edgecolor="red",
    zorder=5,
    label="Pareto designs",
)
plt.xlabel("Design ID")
plt.ylabel(f"Resonance frequency [GHz] (Target: {target_frequency}GHz)")
plt.grid(True)
plt.show()
# -

# ## Release optiSLang

design_study_manager.optislang.dispose()
time.sleep(5)  # Allow optiSLang to shut down before cleaning the temporary project folder.

# ## Clean up
# All project files are saved in the folder ``temp_folder.name``.
# If you've run this example as a Jupyter notebook, you can retrieve those
# project files. The following command will delete all temporary files, including the project
# folder.

try:
    temp_folder.cleanup()
except Exception as e:
    print(
        f"Tried to clean up temporary working directory path: {WORKING_DIR}"
        f"Could not complete cleanup: {e}\n"
    )
