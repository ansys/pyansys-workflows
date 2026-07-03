# /// script
# requires-python = "==3.12"
# dependencies = [
#     "ansys-optislang-core>0.7.0",
#     "pyaedt[all]>1.1.0"
# ]
# ///
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
import os
import pathlib
import sys
import tempfile
import time

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map as concurrent_map

from ansys.aedt.core import Hfss
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


# -

# ## Define constants.
#
# **Take note:** Jupyters execution model does not work well with multiprocessing.
# When executing from within Jupyter, please set `MAX_PARALLEL_SOLVE_PROCESSES = 1`, 
# otherwise the process will fail.
# When executed outside of Jupyter, `MAX_PARALLEL_SOLVE_PROCESSES` can be increased,
# as long as `NUM_CORES_PER_JOB * MAX_PARALLEL_SOLVE_PROCESSES` does not exceed the
# number of available cores.

AEDT_VERSION = "2026.1"
NUM_CORES_PER_PROCESS = 2
NG_MODE = True # HFSS jobs run non-graphically (headless) to support parallel execution.
MAX_PARALLEL_SOLVE_PROCESSES = 3
FORCE_SEQUENTIAL_SOLVE = False   # Set to True to force sequential execution even outside of Jupyter, for testing and debugging.
AEDT_WORKING_DIRNAME = "pyaedt_workingdir"
SOLVE_MODE = "HFSS"  # Set to "DUMMY" to run without an HFSS license, for testing purposes.


# ## Define HFSS solver function
#
# The ``solve_hfss()`` function creates and solves a dipole antenna model in HFSS
# for a given set of design parameters, exports the return loss to a CSV file,
# and returns the result as a NumPy array.
# Each call runs in its own HFSS desktop instance and releases it when done.


def solve_hfss(working_dir, l_dipole, wire_rad, port_gap):
    project_name = os.path.join(working_dir, "dipole.aedt")
    hfss = Hfss(
        version=AEDT_VERSION,
        non_graphical=NG_MODE,
        project=project_name,
        new_desktop=True,
        solution_type="Modal",
    )

    hfss["l_dipole"] = f"{l_dipole}cm"
    hfss["wire_rad"] = f"{wire_rad}mm"
    hfss["port_gap"] = f"{port_gap}mm"

    component_name = "Dipole_Antenna_DM"
    freq_range = ["1GHz", "2GHz"]
    center_freq = "1.5GHz"
    freq_step = "0.5GHz"

    component_fn = hfss.components3d[component_name]
    comp_params = hfss.get_component_variables(component_name)
    comp_params["dipole_length"] = "l_dipole"
    comp_params["wire_rad"] = "wire_rad"
    comp_params["port_gap"] = "port_gap"
    hfss.modeler.insert_3d_component(component_fn, geometry_parameters=comp_params)

    hfss.create_open_region(frequency=center_freq)

    setup_name = "MySetup"
    setup = hfss.create_setup(
        name=setup_name,
        MultipleAdaptiveFreqsSetup=freq_range,
        MaximumPasses=2,
    )
    setup.add_sweep(
        name="DiscreteSweep",
        sweep_type="Discrete",
        RangeStart=freq_range[0],
        RangeEnd=freq_range[1],
        RangeStep=freq_step,
        SaveFields=True,
    )
    interp_sweep = setup.add_sweep(
        name="InterpolatingSweep",
        sweep_type="Interpolating",
        RangeStart=freq_range[0],
        RangeEnd=freq_range[1],
        SaveFields=False,
    )

    hfss.analyze_setup(setup_name, use_auto_settings=True, cores=NUM_CORES_PER_PROCESS)
    hfss.create_scattering(plot="Return Loss", sweep=interp_sweep.name)
    hfss.post.export_report_to_file(working_dir, "Return Loss", ".csv")

    hfss.save_project()
    hfss.release_desktop(close_projects=True, close_desktop=True)

    data = np.loadtxt(os.path.join(working_dir, "Return Loss.csv"), delimiter=",", skiprows=1)
    return data

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


def call_solver(args):
    hid, working_dir, l_dipole, wire_rad, port_gap = args
    print(f"Solving design {hid} ...")
    result_data = solve_hfss(working_dir, l_dipole, wire_rad, port_gap)
    freq = result_data[:, -2].tolist()
    loss = result_data[:, -1].tolist()
    return_loss = get_signal_value_format(freq, loss)
    freq_min = float(freq[np.argmin(loss)])
    print(f"Solving design {hid} ... done.")
    # return {"freq_min": freq_min}
    return {"return_loss": return_loss, "freq_min": freq_min, "amplitude_min": min(loss)}


def call_solver_dummy(args):
    hid, working_dir, l_dipole, wire_rad, port_gap = args
    print(f"Solving design {hid} ...")
    freq = np.linspace(0, 3, 301).tolist()

    def notch_return_loss(f, f0, Q):
        num = (f**2 - f0**2)**2
        den = num + (f * f0 / Q)**2
        s11 = math.sqrt(num / den)
        return 20 * math.log10(s11)

    try:
        loss = [notch_return_loss(f, l_dipole/10+port_gap/5+wire_rad/5, (port_gap+wire_rad)/4) for f in freq]
    except Exception as e:
        print(f"Error in call_solver_dummy: {e}")
        return {"return_loss": None, "freq_min": None, "amplitude_min": None}

    return_loss = get_signal_value_format(freq, loss)
    freq_min = float(freq[np.argmin(loss)])
    print(f"Solving design {hid} ... done.")
    # return {"freq_min": freq_min}
    return {"return_loss": return_loss, "freq_min": freq_min, "amplitude_min": min(loss)}


# ## Define parallel compute function
#
# ``compute_designs()`` receives a list of design points from the ProxySolver,
# dispatches them to the solver in parallel using ``multiprocessing.Pool``,
# and returns the collected responses.


def get_parameter_value(design, parameter_name):
    return design.parameters[design.parameters_names.index(parameter_name)].value


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
            get_parameter_value(design, "l_dipole"),
            get_parameter_value(design, "wire_rad"),
            get_parameter_value(design, "port_gap"),
        ))

    if SOLVE_MODE == "HFSS":
        solve = call_solver
    elif SOLVE_MODE == "DUMMY":
        solve = call_solver_dummy
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
    num_designs_max = 20

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

    osl = Optislang(
        project_path=str(WORKING_DIR / osl_project_name),
        )
    osl.application.save()
    osl.dispose()
    osl = Optislang(
        project_path=str(WORKING_DIR / osl_project_name),
        batch=NG_MODE,
        )

    add_stdout_handler(osl.log)
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
