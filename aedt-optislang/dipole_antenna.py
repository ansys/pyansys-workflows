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

import math
from multiprocessing import Process, Queue
from pathlib import Path

from ansys.aedt.core import Hfss
import numpy as np

AEDT_VERSION = "2026.1"  # AEDT version to use
NUM_CORES_PER_PROCESS = 2  # number of cores to use for each HFSS process
NG_MODE = True  # True: Run AEDT in non-graphical mode, False: Run AEDT with GUI.

# Define HFSS solve functions


def hfss_solve(working_dir, parameter_values):
    """
    This function creates a new HFSS project, sets up the dipole antenna design with the given parameters,
    runs the simulation, and exports the return loss data to a CSV file.

    Parameters:
    working_dir (str): The directory where the HFSS project and output files will be saved.
    parameter_values (dict): A dictionary containing the values for the dipole antenna parameters:
        - l_dipole (float): Length of the dipole antenna in cm.
        - wire_rad (float): Radius of the wire in mm.
        - port_gap (float): Gap of the port in mm.

    Returns:
    dict: A dictionary containing the return loss data, the frequency at which the return loss is minimum, and the minimum amplitude of the return loss.
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
    This function is the target of the multiprocessing Process.
    It wraps around the hfss_solve function and puts the result in a Queue.

    Parameters:
        working_dir (str): The directory where the HFSS project and output files will be saved.
        parameter_values (dict): A dictionary containing the values for the dipole antenna parameters.
        q (Queue): A multiprocessing Queue to put the result into.

    Returns:
        None: (The result is put into the Queue.)
    """
    result_data = hfss_solve(working_dir, parameter_values)
    q.put(result_data)


def hfss_worker(args):
    """
    We define a worker function that will be called by each process.
    It takes a tuple of arguments, unpacks them, and calls the hfss_task function.
    It also handles the timeout and termination of the process if it exceeds the specified time limit.

    Parameters:
    args (tuple): A tuple containing the following elements:
        - hid (str): The unique identifier for the design being solved.
        - working_dir (str): The directory where the HFSS project and output files will be saved.
        - parameters (dict): A dictionary containing the values for the dipole antenna parameters.
        - timeout (int): The maximum time in seconds to allow the process to run before terminating it.
    Returns:
        dict: A dictionary containing the return loss data, the frequency at which the return loss is minimum, and the minimum amplitude of the return loss.
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
        print(f"Terminating task {p} due to exceeded timeout span {timeout}s.")
        result_data = {}
    else:
        result_data = q.get()
        print(f"Solving design {hid} ... done.")
    return result_data


# Define DUMMY solve functions


def dummy_solve(working_dir, parameter_values):
    """
    This function simulates the behavior of the hfss_solve function without actually running HFSS.
    It generates a synthetic return loss curve based on the input parameters.

    Parameters:
        working_dir (str): The directory where the HFSS project and output files would be saved (not used in this dummy function).
        parameter_values (dict): A dictionary containing the values for the dipole antenna parameters.

    Returns:
        dict: A dictionary containing the return loss data, the frequency at which the return loss is minimum, and the minimum amplitude of the return loss.
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
    This function is the target of the multiprocessing Process for the dummy solver.
    It wraps around the dummy_solve function and puts the result in a Queue.

    Parameters:
        working_dir (str): The directory where the HFSS project and output files would be saved (not used in this dummy function).
        parameter_values (dict): A dictionary containing the values for the dipole antenna parameters.
        q (Queue): A multiprocessing Queue to put the result into.

    Returns:
        None: (The result is put into the Queue.)
    """
    result_data = dummy_solve(working_dir, parameter_values)
    q.put(result_data)


def dummy_worker(args):
    """We define a worker function that will be called by each process.
    It takes a tuple of arguments, unpacks them, and calls the hfss_task function.
    It also handles the timeout and termination of the process if it exceeds the specified time limit.

    Parameters:
        args (tuple): A tuple containing the following elements:
         - hid (str): The unique identifier for the design being solved.
         - working_dir (str): The directory where the HFSS project and output files will be saved.
         - parameters (dict): A dictionary containing the values for the dipole antenna parameters.
         - timeout (int): The maximum time in seconds to allow the process to run before terminating it.
     Returns:
         dict: A dictionary containing the return loss data, the frequency at which the return loss is minimum, and the minimum amplitude of the return loss.
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
