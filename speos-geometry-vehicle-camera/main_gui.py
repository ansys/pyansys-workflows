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
Tkinter GUI for the vehicle camera PySpeos simulation demo.

This tool relies on a pre-generated test scenario/environment (provided as a .speos file),
and can optionally import additional CAD components into the test scene.
The camera data (position/orientation, distortion, etc.) is provided in a separate JSON file.

Provision of this resource is intended for demonstration purposes only.

Author: Zach Derocher

To do:

- dynamic materials selection
- support multiple CAD imports
- optionally read camera axis from cad coordinate system
- add logging directly in the GUI
- add preview/result directly in the GUI

"""

import gc
import glob
import os
import tkinter as tk
from tkinter import filedialog

import CameraSimulation_PySpeos_Demo
from CameraSimulation_PySpeos_Demo import BASE_DIR

master = tk.Tk()
master.title("PySpeos Simulation Utility")
master.geometry("800x500")
color_wheat = "#fff4b3"
color_green = "#d3fbc5"


class pyspeos_sim:
    """Hold the modeler, PySpeos project, simulation, and build status shared across the GUI."""

    def __init__(self):
        self.built = tk.BooleanVar()
        self.built.set(False)
        self.speos = ""
        self.modeler = ""
        self.cad_mesh_cache = ""
        self.coordinates_cache = ""
        self.project = ""
        self.sim = ""
        self.xmp_result_path = ""


def exit_program():
    """Release the PySpeos and mesh objects, and close the GUI."""
    # drop PyVista meshes now to avoid __del__ errors during interpreter shutdown
    my_pyspeos_sim.cad_mesh_cache = ""
    my_pyspeos_sim.project = ""
    my_pyspeos_sim.sim = ""
    gc.collect()
    master.destroy()


def import_cad():
    """Import the CAD data and tessellate it for use in the PySpeos simulation."""
    print("importing CAD data and tessellating...")
    cad_import_result = CameraSimulation_PySpeos_Demo.import_cad_part(
        cad_data_path=master.cad_path.get(), pyspeos_simulation=my_pyspeos_sim
    )
    my_pyspeos_sim.cad_mesh_cache = cad_import_result[0]
    my_pyspeos_sim.coordinates_cache = cad_import_result[1]
    my_pyspeos_sim.modeler = cad_import_result[2]

    my_pyspeos_sim.built.set(False)  # force rebuild of speos project to apply the new CAD data
    b_import_cad.configure(bg=color_green)

    print("CAD import and tessellation complete\n")


def build_simulation():
    """Connect to Speos and build the PySpeos project from the selected scenario."""
    print("building pyspeos project...")
    build_result = CameraSimulation_PySpeos_Demo.build_camera_simulation(
        test_environment=master.scenario.get(), pyspeos_simulation=my_pyspeos_sim
    )
    my_pyspeos_sim.speos = build_result[0]
    my_pyspeos_sim.project = build_result[1]
    my_pyspeos_sim.sim = build_result[2]

    my_pyspeos_sim.built.set(True)
    b_build.configure(bg=color_green)
    b_import_camera.configure(bg=color_wheat)
    b_run.configure(bg=color_wheat)
    print("pyspeos project build complete\n")


def import_camera():
    """Load the selected camera model into the PySpeos project."""
    print("loading camera sensor data into pyspeos model...")
    CameraSimulation_PySpeos_Demo.import_camera_sensor(
        pyspeos_simulation=my_pyspeos_sim, camera_model=master.camera.get()
    )
    b_import_camera.configure(bg=color_green)
    b_run.configure(bg=color_wheat)
    print("camera sensor import complete\n")


def preview_simulation():
    """Open the PySpeos preview window."""
    print("launching pyspeos preview window...")
    my_pyspeos_sim.project.preview()


def run_simulation():
    """Run the camera simulation with the current PySpeos model."""
    print("running pyspeos simulation....")
    result_path = CameraSimulation_PySpeos_Demo.run_camera_simulation(my_pyspeos_sim)
    my_pyspeos_sim.xmp_result_path = result_path
    print(f"simulation run complete\nresults saved to: {result_path}\n")
    b_run.config(bg=color_green)
    b_show.config(state="normal")


def show_results():
    """Open the latest simulation result in the XMP viewer."""
    # find the xmp file in the results path
    xmp_files = glob.glob(my_pyspeos_sim.xmp_result_path + "/*.xmp")
    if not xmp_files:
        print(
            "error: no .xmp file found in simulation results path\n"
            + my_pyspeos_sim.xmp_result_path
            + "\n\n"
        )
        return
    xmp_path = xmp_files[0]

    print(f"displaying results for: {xmp_path}")
    CameraSimulation_PySpeos_Demo.show_sim_results(xmp_path)


def browse_cad():
    """
    Select a CAD file through a file dialog.

    From PyAnsys Geometry, the latest supported file types for import are:
    ___
    Format and latest supported version
        * AutoCAD 2024
        * CATIA V5 2024
        * CATIA V6 2024
        * Creo Parametric 11
        * IGES 5.3
        * Inventor 2025
        * JT 10.10
        * NX 2412
        * Rhino 8
        * Solid Edge 2025
        * SOLIDWORKS 2025
        * STEP AP242
    """

    allowed_filetypes = [
        ("STEP File", ["*.stp", "*.step"]),
        ("CATIA part", ["*.CATPart", ".CATProduct"]),
        ("All Files", "*.*"),
    ]
    selected_path = filedialog.askopenfilename(
        parent=master, initialdir=BASE_DIR, title="Select a CAD file", filetypes=allowed_filetypes
    )

    if selected_path:
        master.cad_path.set(selected_path)


def sim_built_updated():
    """Enable or reset the buttons when the build status changes."""
    # only allow preview/run if the model has been built
    if my_pyspeos_sim.built.get():
        b_preview.config(state="normal")
        b_run.config(state="normal")
        b_import_camera.config(state="normal")
    else:
        b_preview.config(state="disabled")
        b_run.config(state="disabled")
        b_import_camera.config(state="disabled")
        b_show.config(state="disabled")
        b_build.config(bg=color_wheat)
        b_import_camera.configure(bg=color_wheat)
        b_run.config(bg=color_wheat)


def scenario_entry_updated():
    """Reset the build, camera, run, and result buttons after the scenario changes."""
    b_build.configure(bg=color_wheat)
    b_import_camera.configure(bg=color_wheat)
    b_run.configure(bg=color_wheat)
    b_show.config(state="disabled")


def camera_entry_updated():
    """Reset the camera, run, and result buttons after the camera model changes."""
    b_import_camera.configure(bg=color_wheat)
    b_run.configure(bg=color_wheat)
    b_show.config(state="disabled")


# create the class to hold our pyspeos project
if "my_pyspeos_sim" not in globals():
    my_pyspeos_sim = pyspeos_sim()

# CAD file path entry components
lb_cad = tk.Label(master, text="CAD File:")
lb_cad.place(relx=0.15, rely=0.2, anchor=tk.E)
master.cad_path = tk.StringVar()
tb_cad = tk.Entry(master, textvariable=master.cad_path)
tb_cad.place(relx=0.18, rely=0.2, width=480, anchor=tk.W)
tb_cad.insert(0, "")
b_browse_cad = tk.Button(master, text="Browse", width=10, height=1, command=browse_cad)
b_browse_cad.place(relx=0.85, rely=0.2, anchor=tk.CENTER)

# Speos environment entry components
lb_speos = tk.Label(master, text="Test Scenario:")
lb_speos.place(relx=0.15, rely=0.3, anchor=tk.E)
scenario_dir = os.path.join(BASE_DIR, "simulation_data", "scenario")
scenarios = os.listdir(scenario_dir)
master.scenario = tk.StringVar()
cb_scenario = tk.OptionMenu(master, master.scenario, *scenarios)
cb_scenario.place(relx=0.18, rely=0.3, anchor=tk.W)
master.scenario.set(scenarios[0])

# Speos camera entry components
lb_speos = tk.Label(master, text="Camera Model:")
lb_speos.place(relx=0.15, rely=0.4, anchor=tk.E)
camera_dir = os.path.join(BASE_DIR, "simulation_data", "camera")
cameras = os.listdir(camera_dir)
master.camera = tk.StringVar()
cb_camera = tk.OptionMenu(master, master.camera, *cameras)
cb_camera.place(relx=0.18, rely=0.4, anchor=tk.W)
master.camera.set(cameras[0])

# button creation
row1_y = 0.7
row2_y = 0.85
w = 150
h = 50
b_import_cad = tk.Button(
    master, text="Import CAD\nand Tessellate", activeforeground="red", command=lambda: import_cad()
)
b_import_cad.place(relx=0.2, rely=row1_y, width=w, height=h, anchor=tk.CENTER)
b_import_cad.configure(bg=color_wheat)

b_build = tk.Button(
    master, text="Load Scenario", activeforeground="red", command=lambda: build_simulation()
)
b_build.place(relx=0.4, rely=row1_y, width=w, height=h, anchor=tk.CENTER)
b_build.configure(bg=color_wheat)

b_import_camera = tk.Button(
    master, text="Load Camera\nSensor", activeforeground="red", command=lambda: import_camera()
)
b_import_camera.config(state="disabled")
b_import_camera.place(relx=0.6, rely=row1_y, width=w, height=h, anchor=tk.CENTER)
b_import_camera.configure(bg=color_wheat)

b_preview = tk.Button(
    master, text="Preview\nSimulation", activeforeground="red", command=lambda: preview_simulation()
)
b_preview.config(state="disabled")
b_preview.place(relx=0.6, rely=row2_y, width=w, height=h, anchor=tk.CENTER)

b_run = tk.Button(
    master, text="Run Simulation", activeforeground="red", command=lambda: run_simulation()
)
b_run.config(state="disabled")
b_run.place(relx=0.8, rely=row1_y, width=w, height=h, anchor=tk.CENTER)
b_run.configure(bg=color_wheat)

b_show = tk.Button(
    master, text="Open Results", activeforeground="red", command=lambda: show_results()
)
b_show.config(state="disabled")
b_show.place(relx=0.8, rely=row2_y, width=w, height=h, anchor=tk.CENTER)

b_exit = tk.Button(master, text="Exit", command=exit_program)
b_exit.place(relx=0.2, rely=row2_y, width=w, height=h, anchor=tk.CENTER)

# trace the build status
my_pyspeos_sim.built.trace_add("write", lambda *args: sim_built_updated())
master.scenario.trace_add("write", lambda *args: scenario_entry_updated())
master.camera.trace_add("write", lambda *args: camera_entry_updated())

# run the same cleanup when the window is closed with the title-bar button
master.protocol("WM_DELETE_WINDOW", exit_program)

master.mainloop()
