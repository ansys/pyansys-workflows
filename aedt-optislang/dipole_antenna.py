from ansys.aedt.core import Hfss
import math
from multiprocessing import Process, Queue
import numpy as np
from pathlib import Path
import time

AEDT_VERSION = "2026.1"
NUM_CORES_PER_PROCESS = 2
NG_MODE = True

# ## Define HFSS solver function
#
# The ``solve_hfss()`` function creates and solves a dipole antenna model in HFSS
# for a given set of design parameters, exports the return loss to a CSV file,
# and returns the result as a NumPy array.
# Each call runs in its own HFSS desktop instance and releases it when done.


def hfss_solve(working_dir, parameter_values):
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

    data = np.loadtxt(Path(working_dir)/ "Return Loss.csv", delimiter=",", skiprows=1)
    freq = data[:, -2].tolist()
    loss = data[:, -1].tolist()
    freq_min = float(freq[np.argmin(loss)])
    return {"return_loss": (freq, loss), "freq_min": freq_min, "amplitude_min": min(loss)}


def hfss_task(working_dir, parameter_values, q):
    """This function is the target of the multiprocessing Process. 
       It wraps around the hfss_solve function and puts the result in a Queue."""
    result_data = hfss_solve(working_dir, parameter_values)
    q.put(result_data)


def hfss_worker(args):
    """We define a worker function that will be called by each process. 
       It takes a tuple of arguments, unpacks them, and calls the hfss_task function.
       It also handles the timeout and termination of the process if it exceeds the specified time limit."""
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


def dummy_solve(working_dir, parameter_values):
    l_dipole, wire_rad, port_gap = parameter_values["l_dipole"], parameter_values["wire_rad"], parameter_values["port_gap"]
    freq = np.linspace(0, 3, 301).tolist()

    def notch_return_loss(f, f0, Q):
        num = (f**2 - f0**2)**2
        den = num + (f * f0 / Q)**2
        s11 = math.sqrt(num / den)
        return 20 * math.log10(s11)

    try:
        time.sleep(20)
        loss = [notch_return_loss(f, l_dipole/10+port_gap/5+wire_rad/5, (port_gap+wire_rad)/4) for f in freq]
    except Exception as e:
        print(f"Error in call_solver_dummy: {e}")
        return {"return_loss": None, "freq_min": None, "amplitude_min": None}

    nreq_min = float(freq[np.argmin(loss)])
    return {"return_loss": (freq, loss), "freq_min": freq_min, "amplitude_min": min(loss)}


def dummy_task(working_dir, parameter_values, q):
    result_data = dummy_solve(working_dir, parameter_values)
    q.put(result_data)


def dummy_worker(args):
    """We define a worker function that will be called by each process. 
       It takes a tuple of arguments, unpacks them, and calls the hfss_task function.
       It also handles the timeout and termination of the process if it exceeds the specified time limit."""
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
