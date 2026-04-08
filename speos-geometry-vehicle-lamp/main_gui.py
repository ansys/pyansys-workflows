# This tool imports CAD data and runs a Speos ray tracing simulation.
# Optical material data is applied based on body names, according to a user-specified library (xlsx).
# Sensors are specified by coordinate axes by name, and use a user-specified library (xlsx).
# Sources are specified by object name, and settings are determined by a user-specified library (xlsx).
# 
# Provision of this resource is intended for demonstration purposes only.
#
# Zach Derocher


import tkinter as tk
from tkinter import filedialog
import PySpeos_LitAppearance_Demo
import os
import logger
from logger import log_message


master = tk.Tk()
master.title("PySpeos Simulation Utility")
master.geometry("1200x800")
color_wheat ="#fff4b3"
color_green = "#d3fbc5"

class pyspeos_sim():
    # holds the pyspeos object and some metadata
    def __init__(self):
        self.built = tk.BooleanVar()
        self.built.set(False)
        self.direct_run_complete = tk.BooleanVar()
        self.direct_run_complete.set(False)
        self.inverse_run_complete = tk.BooleanVar()
        self.inverse_run_complete.set(False)
        self.speos = ''
        self.modeler = ''
        self.project = ''
        self.sim_direct = ''
        self.sim_direct_xmp_path = ''
        self.sim_inverse = ''
        self.sim_inverse_xmp_path = ''

def buttonpress_exit():
    # terminates the gui
    master.destroy()

def buttonpress_import_cad(speos_session, cad_data_filepath, material_settings_filepath, sensor_settings_filepath, source_settings_filepath):
    # generates the pyspeos connection and model

    # build model
    build_result = PySpeos_LitAppearance_Demo.import_cad(
        speos_session=speos_session, 
        cad_data_filepath=cad_data_filepath.get(), 
        material_settings_filepath=material_settings_filepath.get(), 
        sensor_settings_filepath=sensor_settings_filepath.get(), 
        source_settings_filepath=source_settings_filepath.get())
    speos_session.speos = build_result[0]
    speos_session.modeler = build_result[1]
    speos_session.project = build_result[2]
    speos_session.sim_direct = build_result[3]
    speos_session.sim_inverse = build_result[4]

    log_message("pyspeos project build complete\n")
    speos_session.built.set(True)

def buttonpress_preview_simulation(speos_session):
    # pop-up window of pyspeos preview
    speos_session.project.preview()

def buttonpress_run_direct_simulation(speos_session):
    log_message("running direct simulation on GPU...")
    logger.log_message("")
    # run the simulation with the current pyspeos model
    result_path = PySpeos_LitAppearance_Demo.run_simulation(speos_session.sim_direct, speos_session.project)
    speos_session.sim_direct_xmp_path = result_path
    speos_session.direct_run_complete.set(True)

def buttonpress_run_inverse_simulation(speos_session):
    log_message("running inverse simulation on GPU...")
    logger.log_message("")
    # run the simulation with the current pyspeos model
    result_path = PySpeos_LitAppearance_Demo.run_simulation(speos_session.sim_inverse, speos_session.project)
    speos_session.sim_inverse_xmp_path = result_path
    speos_session.inverse_run_complete.set(True)

def buttonpress_merge_results(xmp_paths):
    # merges the inverse and direct results
    results_path = PySpeos_LitAppearance_Demo.merge_results(xmp_paths)

def buttonpress_browse_cad():
    """
    from py-ansys-geometry the latest supported file types for import are:
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

    allowed_filetypes = [("STEP File", ["*.stp", "*.step"]), 
                         ("CATIA part", ["*.CATPart", ".CATProduct"]),
                         ("All Files", "*.*")
                         ]
    selected_path = filedialog.askopenfilename(
        parent=master, 
        initialdir= os.getcwd(), 
        title='Select a CAD file',
        filetypes=allowed_filetypes)
    
    if selected_path:
        master.cad_path.set(selected_path)

def buttonpress_browse_xlsx(target_var, text):
    allowed_filetypes = [("Excel File", "*.xlsx"),
                         ("All Files", "*.*")
                         ]
    selected_path = filedialog.askopenfilename(
        parent=master, 
        initialdir= os.getcwd(), 
        title=f'Select an excel file describing material properties for {text} settings',
        filetypes=allowed_filetypes)
    
    if selected_path:
        target_var.set(selected_path)
      
def update_buttons(speos_session, button_preview, button_run_direct, button_run_inverse, button_merge):
    # only allow preview/run if the model has been built
    if speos_session.built.get():  
        button_preview.config(state="normal")
        button_run_direct.config(state="normal")
        button_run_inverse.config(state="normal")
    else:
        button_preview.config(state="disabled")
        button_run_direct.config(state="disabled")
        button_run_inverse.config(state="disabled")
    # only allow merge if both results have been computed
    if speos_session.direct_run_complete.get() and speos_session.inverse_run_complete.get():
        button_merge.config(state="normal")
    else:
        button_merge.config(state="disabled")

def main():
    # create the class to hold our pyspeos project
    if 'speos_session' not in globals():
        speos_session = pyspeos_sim()

    # CAD file path entry components
    rely_cad = 0.15
    lb_cad = tk.Label(master, text="CAD File:")
    lb_cad.place(relx=0.15, rely=rely_cad, anchor=tk.E)
    master.cad_path = tk.StringVar()
    tb_cad = tk.Entry(master, textvariable=master.cad_path)
    tb_cad.place(relx=0.18, rely=rely_cad, width=800, anchor=tk.W)
    b_browse_cad = tk.Button(master, text = "Browse", width=10, height=1, command=buttonpress_browse_cad)
    b_browse_cad.place(relx=0.9, rely=rely_cad, anchor=tk.CENTER)

    # MATERIAL file path entry components
    rely_material = 0.2
    lb_material = tk.Label(master, text="Material Settings:")
    lb_material.place(relx=0.15, rely=rely_material, anchor=tk.E)
    master.material_path = tk.StringVar()
    tb_material = tk.Entry(master, textvariable=master.material_path)
    tb_material.place(relx=0.18, rely=rely_material, width=800, anchor=tk.W)
    # initialize for convenience, if possible
    material_data_path_init = f"{os.getcwd()}\SpeosModel\Settings_Material.xlsx"
    if os.path.isfile(material_data_path_init):
        master.material_path.set(material_data_path_init)
    else:
        master.material_path.set("")   # or leave blank / set fallback
    b_browse_material = tk.Button(master, text = "Browse", width=10, height=1, command= lambda: buttonpress_browse_xlsx(master.material_path, text='material'))
    b_browse_material.place(relx=0.9, rely=rely_material, anchor=tk.CENTER)

    # SOURCES file path entry components
    rely_source = 0.25
    lb_source = tk.Label(master, text="Source Settings:")
    lb_source.place(relx=0.15, rely=rely_source, anchor=tk.E)
    master.source_path = tk.StringVar()
    tb_source = tk.Entry(master, textvariable=master.source_path)
    tb_source.place(relx=0.18, rely=rely_source, width=800, anchor=tk.W)
    # initialize for convenience, if possible
    source_data_path_init = f"{os.getcwd()}\SpeosModel\Settings_Source.xlsx"
    if os.path.isfile(source_data_path_init):
        master.source_path.set(source_data_path_init)
    else:
        master.source_path.set("")   # or leave blank / set fallback
    b_browse_source = tk.Button(master, text = "Browse", width=10, height=1, command= lambda: buttonpress_browse_xlsx(master.source_path, text='source'))
    b_browse_source.place(relx=0.9, rely=rely_source, anchor=tk.CENTER)

    # SENSORS file path entry components
    rely_sensor = 0.3
    lb_sensors = tk.Label(master, text="Sensor Settings:")
    lb_sensors.place(relx=0.15, rely=rely_sensor, anchor=tk.E)
    master.sensor_path = tk.StringVar()
    tb_sensor = tk.Entry(master, textvariable=master.sensor_path)
    tb_sensor.place(relx=0.18, rely=rely_sensor, width=800, anchor=tk.W)
    # initialize for convenience, if possible
    sensor_data_path_init = f"{os.getcwd()}\SpeosModel\Settings_Sensor.xlsx"
    if os.path.isfile(sensor_data_path_init):
        master.sensor_path.set(sensor_data_path_init)
    else:
        master.sensor_path.set("")   # or leave blank / set fallback
    b_browse_sensor = tk.Button(master, text = "Browse", width=10, height=1, command= lambda: buttonpress_browse_xlsx(master.sensor_path, text='sensor'))
    b_browse_sensor.place(relx=0.9, rely=rely_sensor, anchor=tk.CENTER)


    # button creation
    rely_buttons = 0.4
    button_import = tk.Button(master, text="Import/\nInitialize", activeforeground="red", command= lambda: buttonpress_import_cad(
        speos_session=speos_session,
        cad_data_filepath=master.cad_path, 
        material_settings_filepath=master.material_path,
        source_settings_filepath=master.source_path,
        sensor_settings_filepath=master.sensor_path))
    button_import.place(relx=0.125, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    button_preview = tk.Button(master, text="Preview", activeforeground="red", command= lambda: buttonpress_preview_simulation(speos_session=speos_session))
    button_preview.config(state="disabled")
    button_preview.place(relx=0.275, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    button_run_direct = tk.Button(master, text="Run Direct\nSimulation", activeforeground="red", command= lambda: buttonpress_run_direct_simulation(speos_session))
    button_run_direct.config(state="disabled")
    button_run_direct.place(relx=0.425, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    button_run_inverse = tk.Button(master, text="Run Inverse\nSimulation", activeforeground="red", command= lambda: buttonpress_run_inverse_simulation(speos_session))
    button_run_inverse.config(state="disabled")
    button_run_inverse.place(relx=0.575, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    button_merge = tk.Button(master, text="Merge Results", activeforeground="red", command= lambda: buttonpress_merge_results([speos_session.sim_direct_xmp_path, speos_session.sim_inverse_xmp_path]))
    button_merge.config(state="disabled")
    button_merge.place(relx=0.725, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    button_exit = tk.Button(master, text="Exit", activeforeground="red", command=buttonpress_exit)
    button_exit.place(relx=0.875, rely=rely_buttons, width=150, height=50, anchor=tk.CENTER)

    # Log creation 
    log_widget = tk.Text(master, height=20, width=100, state='disabled')
    log_widget.place(relx=0.5, rely=0.725, anchor=tk.CENTER)
    
    # Register with logger
    logger.init_logger(master, log_widget)

    # trace the build status
    speos_session.built.trace_add("write", lambda *args:update_buttons(speos_session, button_preview, button_run_direct, button_run_inverse, button_merge))
    speos_session.direct_run_complete.trace_add("write", lambda *args:update_buttons(speos_session, button_preview, button_run_direct, button_run_inverse, button_merge))
    speos_session.inverse_run_complete.trace_add("write", lambda *args:update_buttons(speos_session, button_preview, button_run_direct, button_run_inverse, button_merge))

    
    master.mainloop()

if __name__ == "__main__":
    main()
