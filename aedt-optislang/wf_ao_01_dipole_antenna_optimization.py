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

"""
.. _ref_wf_ao_01_dipole_antenna_optimization:

Dipole antenna optimization with AEDT and optiSLang
####################################################

This example shows how to combine PyAEDT and pyOptiSLang to run a parametric
AMOP study on a dipole antenna in HFSS. optiSLang's ProxySolver node is used to
process the designs. Parallel design evaluations are managed via ``process_map``.
The AMOP system automatically creates a MOP, which is then used in a subsequent
MOP-Solver based optimization system as well as a validation system.

Problem description
-------------------

The dipole antenna geometry is parameterized by three variables (``l_dipole``,
``wire_rad``, ``port_gap``). An AMOP study explores the parameter space and builds
a Meta-Model of Optimal Prognosis (MOP). The MOP is then used for a fast
surrogate-model based optimization targeting a desired resonance frequency.

The workflow includes the following steps:

- Definition of parameters and response definitions.
- optiSLang project creation and AMOP workflow setup.
- Parallel design evaluations via HFSS or an analytical dummy solver.
- MOP-based optimization and validation.
- Display of convergence results.

"""  # noqa: D400, D415

# Perform required imports
# ------------------------

from functools import partial
import math
from multiprocessing import Process, Queue, freeze_support
import os
import pathlib
from pathlib import Path
import tempfile
import time

from ansys.aedt.core import Hfss
from ansys.optislang.core import Optislang
import ansys.optislang.core.node_types as node_types
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
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map as concurrent_map

# sphinx_gallery_start_ignore
# Check if the __file__ variable is defined. If not, set it.
# This is a workaround to run the script in Sphinx-Gallery.
if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_ao_01_dipole_antenna_optimization.py")
# sphinx_gallery_end_ignore

###############################################################################
# Define constants
# ----------------
# The following constants control the script execution. You can modify these
# to suit your needs.
#
# - ``AEDT_VERSION``: AEDT version to use.
# - ``NUM_CORES_PER_PROCESS``: Number of cores to use for each HFSS process.
# - ``NG_MODE``: Run optiSLang in batch (``True``) or GUI (``False``) mode.
# - ``MAX_PARALLEL_SOLVE_PROCESSES``: Maximum number of parallel solve processes.
# - ``SOLVE_MODE``: ``"HFSS"`` to solve the HFSS antenna model, or ``"DUMMY"``
#   to run an analytical dummy model (useful for testing).
# - ``SOLVE_TIMEOUT``: Timeout in seconds for each solve process.

AEDT_VERSION = "2026.1"
"""AEDT version to use."""

NUM_CORES_PER_PROCESS = 2
"""Number of cores to use for each HFSS process."""

NG_MODE = True
"""Run optiSLang in batch mode (``True``) or with GUI (``False``)."""

MAX_PARALLEL_SOLVE_PROCESSES = 3
"""Maximum number of parallel solve processes."""

FORCE_SEQUENTIAL_SOLVE = False
"""Set to ``True`` to force sequential execution (for testing and debugging)."""

AEDT_WORKING_DIRNAME = "pyaedt_workingdir"
"""Name of working directory to store the AEDT projects."""

SOLVE_MODE = "DUMMY"
"""Solve mode: ``"HFSS"`` solves the HFSS antenna model; ``"DUMMY"`` runs an analytical model."""

SOLVE_TIMEOUT = 300
"""Timeout for the solve process in seconds. The process is aborted if this is exceeded."""

NUM_DESIGNS_MAX = 30
"""Maximum number of designs to compute in the AMOP system."""

TARGET_FREQUENCY = 1.35
"""Target resonance frequency in GHz for the MOP-based optimization."""

MAX_NUM_GENERATIONS = 10
"""Maximum number of generations for the genetic optimization algorithm."""

PROJECT_INITIALIZATION_DELAY_SECONDS = 10
"""Delay after creating the optiSLang project before reopening it."""

POST_STUDY_SAVE_DELAY_SECONDS = 5
"""Delay after study execution or shutdown to let optiSLang flush project state."""

###############################################################################
# Define HFSS solve functions
# ---------------------------
# The following functions create and run an HFSS simulation for the dipole
# antenna. ``hfss_solve`` sets up the project, runs the analysis, and returns
# the return loss data. ``hfss_task`` wraps ``hfss_solve`` for use with
# multiprocessing. ``hfss_worker`` dispatches tasks with timeout handling.


def hfss_solve(working_dir, parameter_values):
    """
    Create a new HFSS project, set up the dipole antenna design, run the simulation,
    and export the return loss data to a CSV file.

    Parameters
    ----------
    working_dir : str
        Directory where the HFSS project and output files are saved.
    parameter_values : dict
        Dictionary containing the dipole antenna parameter values:

        - ``l_dipole`` (float): Length of the dipole antenna in cm.
        - ``wire_rad`` (float): Radius of the wire in mm.
        - ``port_gap`` (float): Gap of the port in mm.

    Returns
    -------
    dict
        Dictionary with the return loss data, the frequency at minimum return
        loss, and the minimum return loss amplitude.
    """
    project_filepath = Path(working_dir) / "dipole.aedt"
    hfss = Hfss(
        version=AEDT_VERSION,
        non_graphical=NG_MODE,
        project=project_filepath,
        new_desktop=True,
        solution_type="Modal",
    )

    hfss["l_dipole"] = f"{parameter_values['l_dipole']}cm"
    hfss["wire_rad"] = f"{parameter_values['wire_rad']}mm"
    hfss["port_gap"] = f"{parameter_values['port_gap']}mm"

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

    data = np.loadtxt(Path(working_dir) / "Return Loss.csv", delimiter=",", skiprows=1)
    freq = data[:, -2].tolist()
    loss = data[:, -1].tolist()
    freq_min = float(freq[np.argmin(loss)])
    return {"return_loss": (freq, loss), "freq_min": freq_min, "amplitude_min": min(loss)}


def hfss_task(working_dir, parameter_values, q):
    """
    Target function for the multiprocessing ``Process`` wrapping ``hfss_solve``.

    Parameters
    ----------
    working_dir : str
        Directory where the HFSS project and output files are saved.
    parameter_values : dict
        Dictionary containing the dipole antenna parameter values.
    q : multiprocessing.Queue
        Queue into which the result is placed.
    """
    result_data = hfss_solve(working_dir, parameter_values)
    q.put(result_data)


def hfss_worker(args):
    """
    Worker function called by each process for the HFSS solver.

    It unpacks the arguments, calls ``hfss_task`` inside a subprocess, and
    handles timeout and termination if the process exceeds the time limit.

    Parameters
    ----------
    args : tuple
        Tuple containing:

        - ``hid`` (str): Unique identifier for the design being solved.
        - ``working_dir`` (str): Directory for HFSS project and output files.
        - ``parameters`` (dict): Dipole antenna parameter values.
        - ``timeout`` (int): Maximum time in seconds before termination.

    Returns
    -------
    dict
        Dictionary with return loss data, minimum frequency, and minimum amplitude.
    """
    hid, working_dir, parameters, timeout = args
    print(f"Solving design {hid} ...")
    q = Queue()
    p = Process(target=hfss_task, args=(working_dir, parameters, q))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        print(f"Terminating task {p} after it exceeded the {timeout}s timeout.")
        result_data = {}
    else:
        result_data = q.get()
        print(f"Solving design {hid} ... done.")
    return result_data


###############################################################################
# Define dummy solve functions
# ----------------------------
# The following functions simulate the HFSS solver with an analytical dummy
# model. They are useful for testing the workflow without a license.
# ``dummy_solve`` generates a synthetic return loss curve. ``dummy_task`` and
# ``dummy_worker`` mirror the structure of the HFSS equivalents.


def dummy_solve(working_dir, parameter_values):
    """
    Simulate the HFSS solver using an analytical dummy model without running HFSS.

    Generates a synthetic return loss curve based on the input parameters.

    Parameters
    ----------
    working_dir : str
        Directory where output files would be saved (unused in this dummy function).
    parameter_values : dict
        Dictionary containing the dipole antenna parameter values.

    Returns
    -------
    dict
        Dictionary with synthetic return loss data, minimum frequency, and minimum amplitude.
    """
    l_dipole, wire_rad, port_gap = (
        parameter_values["l_dipole"],
        parameter_values["wire_rad"],
        parameter_values["port_gap"],
    )
    freq = np.linspace(0, 3, 301).tolist()

    def notch_return_loss(f, f0, Q):
        num = (f**2 - f0**2) ** 2
        den = num + (f * f0 / Q) ** 2
        s11 = math.sqrt(num / den)
        return 20 * math.log10(s11)

    try:
        loss = [
            notch_return_loss(
                f, l_dipole / 10 + port_gap / 5 + wire_rad / 5, (port_gap + wire_rad) / 4
            )
            for f in freq
        ]
    except Exception as e:
        print(f"Error in call_solver_dummy: {e}")
        return {"return_loss": None, "freq_min": None, "amplitude_min": None}

    freq_min = float(freq[np.argmin(loss)])
    return {"return_loss": (freq, loss), "freq_min": freq_min, "amplitude_min": min(loss)}


def dummy_task(working_dir, parameter_values, q):
    """
    Target function for the multiprocessing ``Process`` wrapping ``dummy_solve``.

    Parameters
    ----------
    working_dir : str
        Directory where output files would be saved (unused in this dummy function).
    parameter_values : dict
        Dictionary containing the dipole antenna parameter values.
    q : multiprocessing.Queue
        Queue into which the result is placed.
    """
    result_data = dummy_solve(working_dir, parameter_values)
    q.put(result_data)


def dummy_worker(args):
    """
    Worker function called by each process for the dummy solver.

    It unpacks the arguments, calls ``dummy_task`` inside a subprocess, and
    handles timeout and termination if the process exceeds the time limit.

    Parameters
    ----------
    args : tuple
        Tuple containing:

        - ``hid`` (str): Unique identifier for the design being solved.
        - ``working_dir`` (str): Directory for output files.
        - ``parameters`` (dict): Dipole antenna parameter values.
        - ``timeout`` (int): Maximum time in seconds before termination.

    Returns
    -------
    dict
        Dictionary with return loss data, minimum frequency, and minimum amplitude.
    """
    hid, working_dir, parameters, timeout = args
    print(f"Solving design {hid} ...")
    q = Queue()
    p = Process(target=dummy_task, args=(working_dir, parameters, q))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        print(f"Task {p} exceeded {timeout}s")
        result_data = {}
    else:
        result_data = q.get()
        print(f"Solving design {hid} ... done.")
    return result_data


###############################################################################
# Define conversion facilities
# ----------------------------
# The following functions convert signal data and design information to
# the conventions used by pyOptiSLang:
#
# - ``get_legacy_signal_value_format``: Converts signal data to the legacy
#   signal format used by the ProxySolver.
# - ``get_signal_value_format``: Converts signal data to the standard signal
#   format.
# - ``get_parameter_values``: Returns parameter values of a design as a
#   dictionary.
# - ``get_responses_as_design_variables``: Converts a response dictionary to
#   a list of ``DesignVariable`` objects.


def get_legacy_signal_value_format(abscissa, channel_data):
    """
    Convert signal data to the legacy signal format used by optiSLang's ProxySolver.

    Parameters
    ----------
    abscissa : list
        List of abscissa values (for example, frequencies).
    channel_data : list
        List of channel data values (for example, return loss values).

    Returns
    -------
    dict or None
        Dictionary in the legacy signal format, or ``None`` if either input is ``None``.
        The dictionary has the following keys:

        - ``"kind"``: Always ``"signal"``.
        - ``"matrix"``: Full 2D array of signal data as a string.
        - ``"vector"``: Abscissa values as a string.
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
    """
    Convert signal data to the standard signal format used by pyOptiSLang.

    Parameters
    ----------
    abscissa : list or None
        List of abscissa values. Returns ``None`` if this is ``None``.
    *args : list
        One or more channel data lists.

    Returns
    -------
    dict or None
        Dictionary with keys ``"abscissa"``, ``"channels"``, ``"num_channels"``,
        ``"num_entries"``, and ``"type"``, or ``None`` if any input is ``None``.
    """
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
    """
    Return the parameter values of a design as a dictionary.

    Parameters
    ----------
    design : ansys.optislang.core.project_parametric.Design
        Design object.

    Returns
    -------
    dict
        Dictionary mapping parameter names to their values.
    """
    parameter_values = {}
    for parameter in design.parameters:
        parameter_values[parameter.name] = parameter.value
    return parameter_values


def get_responses_as_design_variables(result):
    """
    Convert a response dictionary to a list of ``DesignVariable`` objects.

    Any value that is a tuple of two lists is assumed to represent a signal and
    is converted to signal format.

    Parameters
    ----------
    result : dict
        Dictionary of response names to values.

    Returns
    -------
    list of ansys.optislang.core.project_parametric.DesignVariable
        List of design variables.
    """
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
                print(e)
        else:
            r[key] = value
    return [DesignVariable(name, value=value) for name, value in r.items()]


###############################################################################
# Define helper functions
# -----------------------
# The following helper functions support design inspection and display:
#
# - ``in_notebook``: Determines if the script runs as a Jupytext notebook.
# - ``sort_designs_by_id``: Returns a sorted list of designs.
# - ``print_designs``: Prints a list of designs with their parameters and
#   responses.
# - ``get_pareto_designs``: Returns the Pareto-optimal designs.


def in_notebook():
    """
    Determine if the script is executed as a Jupytext notebook.

    Returns
    -------
    bool
        ``True`` if running inside a Jupyter kernel, ``False`` otherwise.
    """
    try:
        from IPython import get_ipython

        return get_ipython() is not None and "IPKernelApp" in get_ipython().config

    except Exception:
        return False


def sort_designs_by_id(designs):
    """
    Return a list of designs sorted by their numeric design ID.

    Parameters
    ----------
    designs : list
        List of design objects.

    Returns
    -------
    list
        Sorted list of designs.
    """
    return sorted(designs, key=lambda obj: int(obj.id.split(".")[1]))


def print_designs(designs):
    """
    Print a list of designs with their parameters and responses.

    Parameters
    ----------
    designs : list
        List of design objects.
    """
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
    """
    Return the Pareto-optimal designs from a list of designs.

    Parameters
    ----------
    designs : list
        List of design objects.

    Returns
    -------
    list
        List of designs for which ``pareto_design`` is ``True``.
    """
    return [design for design in designs if design.pareto_design is True]


###############################################################################
# Define parallel compute function
# ---------------------------------
# ``compute_designs`` receives a list of design points from the ProxySolver,
# dispatches them to the worker in parallel, and returns the collected responses.


def compute_designs(designs, working_dir):
    """
    Evaluate a batch of design points and return the collected responses.

    This function is used as the callback for the optiSLang ProxySolver. It
    dispatches design evaluations to the HFSS or dummy worker (depending on
    ``SOLVE_MODE``) and collects the results.

    Parameters
    ----------
    designs : list
        List of design objects from the ProxySolver.
    working_dir : pathlib.Path
        Base temporary directory where per-design AEDT working folders are created.

    Returns
    -------
    list
        List of ``Design`` objects with populated response values.
    """
    if working_dir is None:
        raise RuntimeError("working_dir must not be None when compute_designs is invoked.")

    print(f"Calculate {len(designs)} designs: {', '.join([design.id for design in designs])}")
    all_designs_inputs = []
    aedt_working_dir = working_dir / AEDT_WORKING_DIRNAME
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
        worker = hfss_worker
    elif SOLVE_MODE == "DUMMY":
        worker = dummy_worker
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


###############################################################################
# Prepare the run
# ---------------
# Create a temporary working directory, define the parameter and response
# schema, and set the maximum number of designs.


def main():
    """Run the AEDT and optiSLang optimization workflow."""
    # Create temporary working dir
    temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")
    working_dir = pathlib.Path(temp_folder.name)
    print(f"WORKING DIR: {working_dir}")

    # The optiSLang project file is created on the fly when the ``Optislang``
    # instance is initialized.
    osl_project_name = "pyoptislang_example_proxy_solver.opf"

    # The dipole antenna geometry is parameterized by three variables:
    # ``l_dipole``, ``wire_rad``, and ``port_gap``.
    parameters_as_dict = {
        "l_dipole": {"reference_value": 10.2, "lower_bound": 9.0, "upper_bound": 12.0},
        "wire_rad": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
        "port_gap": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
    }

    # There are three expected responses:
    #
    # Signal responses: ``return_loss``
    #
    # Scalar responses: ``freq_min``, ``amplitude_min``
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
    # If the target CoP is met earlier, AMOP may evaluate fewer designs.
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

    # For the AMOP system, include all responses (including the full return loss
    # signal) to verify that the signal response is valid.
    amop_responses_objects = []
    for response_name, response_data in responses_as_dict.items():
        amop_responses_objects.append(
            Response(
                name=response_name,
                reference_value=response_data["reference_value"],
                reference_value_type=ResponseValueType.from_str(response_data["type"]),
            )
        )

    # For optimization, only the scalar responses are relevant.
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

    ###############################################################################
    # Initialize the optiSLang session
    # --------------------------------
    # Create the optiSLang project and set up an AMOP system with a ProxySolver
    # node. Load the parameter and response schema.
    #
    # The ``GeneralAlgorithmTemplate`` and ``ParametricDesignStudyManager``
    # convenience classes create the AMOP workflow and configure the ProxySolver
    # to use ``compute_designs`` as its callback for design evaluation.

    # For initializing the project and saving it we create a short batch
    # optiSLang session.
    osl = Optislang(
        project_path=str(working_dir / osl_project_name),
        batch=True,
    )
    osl.application.save()
    osl.dispose()
    time.sleep(PROJECT_INITIALIZATION_DELAY_SECONDS)

    # Reopen the project in batch or GUI mode, depending on ``NG_MODE``.
    osl = Optislang(
        project_path=str(working_dir / osl_project_name),
        loglevel="INFO",
        log_process_stdout=True,
        log_process_stderr=True,
        batch=NG_MODE,
    )

    compute_designs_callback = partial(compute_designs, working_dir=working_dir)
    solver_settings = ProxySolverNodeSettings(
        callback=compute_designs_callback, multi_design_launch_num=-1
    )

    # Number of designs in an AMOP system
    algorithm_settings = GeneralAlgorithmSettings(
        {
            "AMopSettings": {
                "min_cop": 0.9999,
                "num_designs_max": NUM_DESIGNS_MAX,
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
        solver_settings=solver_settings,
    )

    design_study_manager = ParametricDesignStudyManager(
        optislang_instance=osl,
    )
    amop_study = design_study_manager.create_design_study(template=amop_template)
    design_study_manager.save()

    ###############################################################################
    # Run the parametric study
    # ------------------------
    # Start the optiSLang workflow. The ProxySolver polls for pending design
    # batches and dispatches them to HFSS (or the dummy solver) via
    # ``compute_designs`` until all design points have been evaluated.

    amop_study.execute()
    design_study_manager.save()
    time.sleep(POST_STUDY_SAVE_DELAY_SECONDS)

    print("AMOP result designs:")
    print_designs(amop_study.get_result_designs())
    print("AMOP design study done!")

    ###############################################################################
    # Create MOP-based optimization system
    # -------------------------------------
    # Create an optimization system that uses the trained MOP as its surrogate
    # model. Define the target frequency and the maximum number of generations.
    #
    # The ``OptimizationOnMOPTemplate`` and ``ParametricDesignStudyManager``
    # classes automatically create the optimization and validation systems.

    # Define the target frequency
    # Define the optimization criteria to minimize the squared difference between
    # the resonance frequency and the target frequency.
    criteria = [
        ObjectiveCriterion(
            "obj_freq_min",
            expression=f"(freq_min-{TARGET_FREQUENCY})^2",
            criterion=ComparisonType.MIN,
        )
    ]

    # Get the AMOP system object created in the previous step.
    amop_system = amop_study.managed_instances[0].instance

    # Create a nature-inspired optimization algorithm system using the trained MOP
    # as its surrogate model.
    optimizer_settings = GeneralAlgorithmSettings(
        {
            "OptimizerSettings": {
                "settings": {
                    "MaxGenerations": MAX_NUM_GENERATIONS,
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
        callback=compute_designs_callback,
    )

    optimization_study = design_study_manager.create_design_study(optimization_template)

    # Find the optimization system
    for managed_instance in optimization_study.managed_instances:
        instance = managed_instance.instance
        if instance.type == optimization_node_type:
            optimization_system = instance
    # Deactivate auto-save and set ``.omdb`` file update to "at end" to reduce run time.
    optimization_system.set_property("AutoSaveMode", "no_auto_save")
    optimization_system.set_property("UpdateResultFile", "at_end")
    # Execute the optimization
    optimization_study.execute()
    # Save the project
    design_study_manager.save()
    print(f"Optimization design study done! Status: {optimization_study.get_status()}")

    ###############################################################################
    # Display results
    # ---------------
    # Print the MOP-based optimization results and the validated design values.
    # Plot the resonance frequency convergence over all optimization designs,
    # highlighting the Pareto-optimal designs.

    print("MOP-based optimization designs:")
    optimization_result_designs = optimization_study.get_result_designs()[
        1:
    ]  # Skip the first design; it is the validation design.
    print_designs(optimization_result_designs)

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
    plt.ylabel(f"Resonance frequency [GHz] (Target: {TARGET_FREQUENCY}GHz)")
    plt.grid(True)
    plt.show()

    ###############################################################################
    # Release optiSLang
    # -----------------
    # Dispose the optiSLang instance.

    design_study_manager.optislang.dispose()
    time.sleep(
        POST_STUDY_SAVE_DELAY_SECONDS
    )  # Allow optiSLang to shut down before cleaning the temporary project folder.

    ###############################################################################
    # Clean up
    # --------
    # All project files are saved in the temporary folder. The following command
    # deletes all temporary files, including the project folder.

    try:
        temp_folder.cleanup()
    except Exception as e:
        print(
            f"Tried to clean up temporary working directory path: {working_dir}\n"
            f"Could not complete cleanup: {e}\n"
        )


if __name__ == "__main__":
    freeze_support()
    main()
