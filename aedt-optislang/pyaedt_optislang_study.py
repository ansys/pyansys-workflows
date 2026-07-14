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

# +
# # Parametric AMOP design study with optiSLang ProxySolver and PyAEDT
#
# This example shows how to combine PyAEDT and pyOptiSLang to run a parametric
# AMOP study on a dipole antenna in HFSS. optiSLang's ProxySolver node
# is used to process the designs. Parallel design evaluations are managed via 
# process_map. The AMOP system automatically creates a MOP, which is then used
# in a subsequent MOP-Solver based optimization system.
#
# Ways to run this script:
# * Open as a Jupytext notebook (requires installation of Jupyter).
# * Run with `uv run pyaedt_optislang_study.py` (requires installation of uv).
# * Create a virtual environment and install requirements from requirements file, then run this script.
# 
# Software requirements:
# - Ansys optiSLang version 2026 R1 or later.
# - Ansys Electronics Desktop version 2026 R1 or later.
#
# Python package requirements:
# - ansys-aedt-core version 1.1.0 or later.
# - ansys-optislang-core version 0.7.0 or later.
#
# Keywords: **AEDT**, **HFSS**, **optiSLang**, **parametric**, **ProxySolver**, **AMOP**

# ## Perform imports and define constants
#
# Import the required packages.

# +
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pathlib
import sys
import tempfile
import time
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map as concurrent_map

from ansys.optislang.core import Optislang
import ansys.optislang.core.node_types as node_types
from ansys.optislang.core.nodes import DesignFlow
from ansys.optislang.core.project_parametric import (
    OptimizationParameter,
    Response,
    ResponseValueType,
    Design,
    DesignVariable,
    ObjectiveCriterion,
    ComparisonType,
)

# Convenience imports for building the optiSLang workflow graph.
from ansys.optislang.parametric.design_study import ParametricDesignStudyManager
from ansys.optislang.parametric.design_study_templates import (
    GeneralAlgorithmSettings,
    GeneralAlgorithmTemplate,
    OptimizationOnMOPTemplate,
    ProxySolverNodeSettings,
)

import dipole_antenna


# -

# ## Define constants.
#
# **Take note:** Jupyters execution model does not work well with multiprocessing.
# When executing from within Jupyter, please set `MAX_PARALLEL_SOLVE_PROCESSES = 1`, 
# otherwise the process will fail.
# When executed outside of Jupyter, `MAX_PARALLEL_SOLVE_PROCESSES` can be increased,
# as long as `NUM_CORES_PER_JOB * MAX_PARALLEL_SOLVE_PROCESSES` does not exceed the
# number of available cores.

NG_MODE = True # Controls whether optiSLang should be executed in batch mode or with GUI.
MAX_PARALLEL_SOLVE_PROCESSES = 3
FORCE_SEQUENTIAL_SOLVE = False   # Set to True to force sequential execution even outside of Jupyter, for testing and debugging.
AEDT_WORKING_DIRNAME = "pyaedt_workingdir"
SOLVE_MODE = "HFSS"  # Set to "DUMMY" to run without an HFSS license, for testing purposes.
SOLVE_TIMEOUT = 300



# ## Define solver wrappers
#
# ``call_solver()`` wraps ``solve_hfss()`` into the argument tuple format expected
# by ``multiprocessing.Pool.imap()``.
# ``call_solver_dummy()`` returns synthetic data and can be used to verify the
# workflow without an HFSS license (set ``SOLVE_MODE = "DUMMY"``).

def get_legacy_signal_value_format(abscissa, channel_data):
    """
    Convert to the following legacy signal format, which is supported by optiSLang's current ProxySolver implementation:

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
        where the value pairs in () represent the real and the imaginary part of the signal, respectively. 
        The "matrix" field contains the full 2D array of signal data, while the "vector" field contains 
        only the abscissa values (frequencies) for reference.
        If loss data is not complex, the imaginary part can be set to 0 as shown above. 
        The "kind" field indicates that this is a signal-type response, which allows optiSLang to interpret and process 
        it correctly in the workflow.

    """
    if abscissa is None or channel_data is None:
        return None

    result = {
        "kind" : "signal",
        "matrix": f"[1,{len(abscissa)}](({','.join([f'({l.real},{l.imag})' for l in channel_data])}))",
        "vector": f"[{len(abscissa)}]({','.join([f'({f.real},{f.imag})' for f in abscissa])})"
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


# ## Define parallel compute function
#
# ``compute_designs()`` receives a list of design points from the ProxySolver,
# dispatches them to the solver in parallel using ``multiprocessing.Pool``,
# and returns the collected responses.


def get_parameter_values(design):
    parameter_values = {}
    for parameter in design.parameters:
        parameter_values[parameter.name] = parameter.value
    return parameter_values


def in_notebook():
    try:
        from IPython import get_ipython
        return get_ipython() is not None and "IPKernelApp" in get_ipython().config
        
    except Exception:
        return False


def compute_designs(designs):
    print(f"Calculate {len(designs)} designs: {', '.join([design.id for design in designs])}")
    design_data = []
    aedt_working_dir = WORKING_DIR / AEDT_WORKING_DIRNAME
    aedt_working_dir.mkdir(parents=True, exist_ok=True)
    for design in designs:
        hid = design.id
        design_temp_folder = tempfile.mkdtemp(dir=str(aedt_working_dir), prefix="pyaedt.")
        design_data.append((
            hid,
            design_temp_folder,
            get_parameter_values(design),
            SOLVE_TIMEOUT,
        ))

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
        results = []
        for design_args in tqdm(design_data, desc="Solving designs"):
            result = solve(design_args)
            results.append(result)
    else:
        results = concurrent_map(solve, design_data, max_workers=MAX_PARALLEL_SOLVE_PROCESSES)


    result_design_list = []
    for design, result in zip(design_data, results):
        result_design_list.append(
            Design(
                design_id=design[0],
                responses=[
                    DesignVariable(name, value=value) for name, value in result.items()
                    ]
            )
        )

    print(f"Return {len(result_design_list)} designs")
    return result_design_list


# ## Define helper functions

def sort_designs_by_id(designs):
    return sorted(designs, key=lambda obj: int(obj.id.split(".")[1]))  # Sort by design number


def print_designs(designs):
    sorted_result_designs = sort_designs_by_id(designs)
    for design in sorted_result_designs:
        p = [f"{p.name}={p.value:-1.2f}" for p in design.parameters]
        r = []
        for response in design.responses:
            if isinstance(response.value, dict) and "type" in response.value and response.value["type"] == "signal":
                r.append(f"{response.name}=signal[{response.value['num_entries']}:{response.value['num_channels']}]")
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


def add_stdout_handler(logger):
    # Create a StreamHandler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)

    # Optional: set level and formatter
    stdout_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)

    # Add it to the logger
    logger.addHandler(stdout_handler)


# ## Prepare run
#
# * Create a temporary directory where downloaded data or dumped data can be stored.
# * Define parameter and response definition
# * Define total number of designs to execute `num_designs_max`
#
# The below steps are wrapped in the main guard (`if __name__ == "__main__":)
# to ensure the process_map does not recursively spin up the same process again 
# and again.
# This is only necessary because we package everything in one file for the 
# sake of this example. As a best practice, it makes sense to refactor the 
# part executed by process_map into a separate file/module.

if __name__ == "__main__":
    # Create temporary working dir
    temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")
    WORKING_DIR = pathlib.Path(temp_folder.name)
    print(f"WORKING DIR: {WORKING_DIR}")

    # The optiSLang project file (``pyoptislang_example_proxy_solver.opf``) is created 
    # on the fly by optiSLang when the ``Optislang`` instance is initialized.
    osl_project_name = "pyoptislang_example_proxy_solver.opf"

    # The dipole antenna geometry is parameterized by three variables.
    # ``num_designs_max`` controls how many design points the sensitivity study evaluates.
    parameters_as_dict = {
        "l_dipole": {"reference_value": 10.2, "lower_bound": 9.0, "upper_bound": 12.0},
        "wire_rad": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
        "port_gap": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
    }
    responses_as_dict = {
        "return_loss": {
            "reference_value": get_legacy_signal_value_format(
                    [0, 1, 2], [0, -20, -10]
                ),
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
    num_designs_max = 30

    parameters_objects = []
    for parameter_name, parameter_data in parameters_as_dict.items():
        parameters_objects.append(
            OptimizationParameter(
                name=parameter_name,
                reference_value=parameter_data["reference_value"],
                range=(parameter_data["lower_bound"], parameter_data["upper_bound"]),
            )
        )
    amop_responses_objects = []
    # For the AMOP node, we include all responses including the full return loss signal, so we
    # can check if the return_loss signal is valid.
    for response_name in ["return_loss", "freq_min", "amplitude_min"]:
        response_data = responses_as_dict[response_name]
        amop_responses_objects.append(
            Response(
                name=response_name,
                reference_value=response_data["reference_value"],
                reference_value_type=ResponseValueType.from_str(response_data["type"])
                )
        )

    optimization_responses_objects = []
    # For optimization, we are only interested in the scalar responses, not the full return loss signal.
    for response_name in ["freq_min", "amplitude_min"]:
        response_data = responses_as_dict[response_name]
        optimization_responses_objects.append(
            Response(
                name=response_name,
                reference_value=response_data["reference_value"],
                reference_value_type=ResponseValueType.from_str(response_data["type"])
                )
        )

# ## Initialize the optiSLang session
# Create optiSLang project named `osl_project_name` and create
#   * Sensitivity system with ProxySolver node
#   * MOP node
# Load the parameter/response schema.
# ## Run the parametric study
# Start the optiSLang workflow without blocking. Poll the ProxySolver for pending
# design batches, dispatch them to HFSS via ``compute_designs()``, and return the
# responses until all design points have been evaluated.
# ## Convenience: Create the same workflow from a template
# As an alternative to the above cell, the entire workflow can be created from a 
# template in a single step, using the `GeneralAlgorithmTemplate` and 
# `ParametricDesignStudyManager` classes. The template internally creates the 
# same nodes and connections as above, and also configures the ProxySolver to 
# use `compute_designs()` as its callback function for design evaluation.


if __name__ == "__main__":

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
        log_process_stdout=True, # log oSL messages to STDOUT
        log_process_stderr=True, # log oSL error messages to STDERR
        batch=NG_MODE,
        )

    solver_settings = ProxySolverNodeSettings(
        callback=compute_designs,
        multi_design_launch_num=-1
    )
    """
    # Number of designs in a Sensitivity sytem
    algorithm_settings = GeneralAlgorithmSettings(
        {"AlgorithmSettings": {"num_discretization": num_designs_max}}
    )
    """
    # Number of designs in an AMOP system
    algorithm_settings = GeneralAlgorithmSettings(
        {
            "AMopSettings": {
                "min_cop": 0.9999,
                # "num_discretization_adaption" : 70,
                # "num_discretization_initial" : 50,
                # "num_discretization_initial": math.floor(num_designs_max/2),
                #"num_discretization_adaption": int(num_designs_max/2),
                "num_designs_max": num_designs_max,
                # "max_iteration": 3,
            }
        }
    )

    amop_template = GeneralAlgorithmTemplate(
        parameters=parameters_objects,
        responses=amop_responses_objects,
        criteria=[],
        algorithm_type=node_types.AMOP,
        algorithm_settings=algorithm_settings,
        solver_type=node_types.ProxySolver,
        solver_settings=solver_settings
    )

    design_study_manager = ParametricDesignStudyManager(
        optislang_instance=osl,
        )
    amop_study = design_study_manager.create_design_study(template=amop_template)
    amop_study.execute()
    design_study_manager.save()
    time.sleep(5)

    print("AMOP result designs:")
    print_designs(amop_study.get_result_designs())
    print("AMOP design study done!")


# ## Create MOP-based optimization system
# As anext step, an optimization system is be created that uses the trained MOP
# as its surrogate model for design evaluation. 

if __name__ == "__main__":
    # Define the target frequency
    target_frequency = 1.35  # GHz
    # Define the optimization criteria to minimize the squared difference between the resonance frequency and the target frequency.
    criteria = [
        ObjectiveCriterion("obj_freq_min", expression=f"(freq_min-{target_frequency})^2", criterion=ComparisonType.MIN)
        ]

    # Get the AMOP system object we created in the previous step
    amop_system = amop_study.managed_instances[0].instance 

    # Create a nature inspired optimization algorithm system that uses the trained MOP as its surrogate model for design evaluation.
    optimizer_settings = GeneralAlgorithmSettings(
        {
            "OptimizerSettings": {
                "settings": {
                    "MaxGenerations": 10,
                }
            }
        }
    )
    optimization_template = OptimizationOnMOPTemplate(
        optimizer_name="Optimization",
        optimizer_type=node_types.NOA2,
        parameters=parameters_objects,
        criteria=criteria,
        responses=optimization_responses_objects,
        mop_predecessor=amop_system,
        callback=compute_designs,
    )

    optimization_study = design_study_manager.create_design_study(optimization_template)
    optimization_study.execute()
    design_study_manager.save()

    print("Optimization result designs:")
    optimization_result_designs = optimization_study.get_result_designs()[1:] # Skip the first design, as it is a duplicate 
    print_designs(optimization_result_designs)
    print(f"Optimization design study done! Status: {optimization_study.get_status()}")

# ## Display results

if __name__ == "__main__":
    sorted_result_designs = sort_designs_by_id(optimization_result_designs)
    # Plot the resonance frequency over all designs
    freq_min_values = [design.responses[design.responses_names.index("freq_min")].value for design in sorted_result_designs]
    design_ids = [int(design.id.split(".")[1]) for design in sorted_result_designs]
    plt.plot(design_ids, freq_min_values, marker=".")
    # Highlight the best designs in red
    pareto_designs = get_pareto_designs(sorted_result_designs)
    plt.scatter(
        [int(p.id.split(".")[1]) for p in pareto_designs], 
        [p.responses[p.responses_names.index("freq_min")].value for p in pareto_designs],
        c="None",edgecolor="red", zorder=5, label="Pareto designs"
        )    
    plt.xlabel("Design ID")
    plt.ylabel(f"Resonance frequency [GHz] (Target: {target_frequency}GHz)")
    plt.grid(True)
    plt.show()

    print("Best designs:")
    print_designs(pareto_designs)
    for design in pareto_designs:
        freq_min = design.responses[design.responses_names.index("freq_min")].value
        amplitude_min = design.responses[design.responses_names.index("amplitude_min")].value


# ## Release optiSLang

# +

if __name__ == "__main__":
    design_study_manager.optislang.dispose()
    time.sleep(3)  # Allow optiSLang to shut down before cleaning the temporary project folder.

# -

# ## Clean up
# All project files are saved in the folder ``temp_folder.name``.
# If you've run this example as a Jupyter notebook, you can retrieve those
# project files. The following command all temporary files, including the project folder.

if __name__ == "__main__":
    temp_folder.cleanup()
