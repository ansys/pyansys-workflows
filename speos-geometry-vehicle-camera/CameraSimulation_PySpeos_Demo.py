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
Build and run a vehicle camera simulation in a Speos scenario using PySpeos.

CAD bodies are imported and tessellated through the Ansys Geometry Service, then added to a
pre-defined .speos test scenario. A camera sensor defined by a JSON file is loaded into the
scene, and an inverse simulation is run on the GPU. The result is opened in the XMP viewer.

"""  # noqa: D400, D415

import datetime
import glob
import json
import os
from pathlib import Path
import shutil
import time

from ansys.geometry.core import launch_modeler
from ansys.geometry.core.misc.options import ImportOptions, TessellationOptions
from ansys.speos.core import launcher, project, sensor, simulation
from ansys.speos.core.kernel.job import ProtoJob
from comtypes.client import CreateObject
import numpy as np
import progressbar

BASE_DIR = Path(__file__).resolve().parent  # folder containing simulation_data


def import_cad_part(cad_data_path="", pyspeos_simulation=""):
    """
    Import a CAD file and tessellate its bodies using PyAnsys Geometry.

    This function is set up for a single part, but can be expanded to handle assemblies.

    Parameters
    ----------
    cad_data_path : str
        Path to the CAD file. If empty, nothing is imported.
    pyspeos_simulation : pyspeos_sim
        Session that holds an existing modeler, which is reused when available.

    Returns
    -------
    tuple
        The cached ``(body, mesh)`` pairs, the coordinate systems, and the modeler.

    """
    if not cad_data_path:
        return [], [], pyspeos_simulation.modeler

    ### Launch pyansys-geometry, if necessary
    if pyspeos_simulation.modeler:
        modeler = pyspeos_simulation.modeler
    else:
        print("Launching Geometry Service...")
        # modeler = launch_modeler(mode="spaceclaim", hidden=True)
        modeler = launch_modeler(mode="geometry_service")

    time0 = time.time()
    print("")
    print("importing: " + cad_data_path)
    modeler_import_options = ImportOptions(
        cleanup_bodies=True,
        import_coordinate_systems=True,
        import_curves=True,
        import_hidden_components_and_geometry=False,
        import_names=True,
        import_planes=True,
        import_points=True,
        import_as_lightweight=False,
    )
    modeler_design = modeler.open_file(
        file_path=cad_data_path, import_options=modeler_import_options
    )
    print("CAD import duration: " + str(time.time() - time0))

    # mesh all bodies in the geometry
    cad_mesh_cache = []
    all_bodies = modeler_design.get_all_bodies()

    tessellation_options = TessellationOptions(
        surface_deviation=0.001,  # 0.1 mm
        angle_deviation=1,
        max_aspect_ratio=0,
        max_edge_length=0.1,  # 100 mm
        watertight=False,
    )

    for body in all_bodies:
        body_mesh = body.tessellate(merge=True, tess_options=tessellation_options)
        # cache the meshes to re-apply materials or the .speos scene without re-tessellating
        cad_mesh_cache.append((body, body_mesh))

    # retrieve coordinate systems as well
    # note: a recursive component search is necessary for the general case
    coordinate_systems = []
    for cs in modeler_design.coordinate_systems:
        if cs.name.startswith("_PyspeosLamp"):
            coordinate_systems.append(cs)

    return cad_mesh_cache, coordinate_systems, modeler


def create_source_luminaire():
    """Create a luminaire source from source data and a coordinate system (not implemented)."""
    # to do
    return


def build_camera_simulation(test_environment="", pyspeos_simulation=""):
    """
    Load a test scenario into a PySpeos project and add the imported CAD bodies.

    Parameters
    ----------
    test_environment : str
        Name of the scenario folder under ``simulation_data/scenario``. Defaults to
        ``Rear_Camera_Scene``.
    pyspeos_simulation : pyspeos_sim
        Session that holds the cached CAD meshes and any running Speos RPC server.

    Returns
    -------
    list
        The Speos RPC server, the project, and the inverse simulation. Returns None if no
        .speos file is found in the scenario folder.

    """
    ### Manage Inputs
    # need error handling here
    if test_environment == "":
        test_environment = "Rear_Camera_Scene"
    model_data_path = os.path.join(BASE_DIR, "simulation_data", "scenario", test_environment)
    files = glob.glob(f"{model_data_path}/{'*.speos'}")
    if not files:
        print("error: invalid speos scenario; no .speos file found\n" + model_data_path + "\n\n")
        return
    model_data_path = files[0]

    # need error handling and UI support
    material_data_path = os.path.join(
        BASE_DIR, "simulation_data", "cad", "OrangeTranslucent.scattering"
    )

    ### Launch CAD and PySpeos tools, if necessary
    if pyspeos_simulation.built.get():
        speos = pyspeos_simulation.speos
    else:
        print("Launching SPEOS RPC server...")
        # check the port by running SpeosRPC_Server.exe in the Optical Products\SPEOS_RPC folder
        # speos = launcher.launch_local_speos_rpc_server(version="252", port=50098)
        speos = launcher.launch_local_speos_rpc_server(port=50098)

    ### Load test environment
    # load .speos file (containing test env scene and ambient source) into new pyspeos project
    p = project.Project(speos=speos, path=str(model_data_path))
    root_part = p.create_root_part()
    root_part.commit()

    def create_speos_body(modeler_body, mesh):
        """Create a PySpeos body with a single face from a tessellated modeler body."""
        # Create a pyspeos body
        speos_body = root_part.create_body(name=modeler_body.name).commit()

        # retrieve the mesh data, and prepare for pyspeos
        facets = mesh.faces[
            np.mod(np.arange(mesh.faces.size), 4) != 0
        ]  # remove every 4th entry (the facet vertex count; always 3 for pyspeos)
        vertices = 1000 * mesh.points.flatten()
        vertex_normals = mesh.point_normals.flatten()

        # generate geometry as a single face, populated with meshed facet data
        speos_face = speos_body.create_face(name=f"{modeler_body.name}_face")
        speos_face.vertices = vertices.tolist()
        speos_face.facets = facets.tolist()
        speos_face.normals = vertex_normals.tolist()
        speos_face.commit()

        return speos_body

    def apply_materials(speos_body):
        """Apply a clear volume and the translucent surface material to a PySpeos body."""
        # apply material properties to the body
        # the material data path is stored in material_data_path
        optical_property_name = speos_body._name + "_material"
        optical_property_geometries = [speos_body]

        # create the optical property
        optical_property = p.create_optical_property(optical_property_name)
        optical_vop = optical_property.set_volume_optic()  # clear volume (allow transparency)
        optical_vop.index = 1.0
        optical_vop.absorption = 0
        optical_vop.constringence = None
        optical_property.set_surface_library().file_uri = material_data_path  # translucent surface

        # apply the geometries
        optical_property.geometries = optical_property_geometries

        # commit optical properties
        optical_property.commit()

        return

    ### bring the geometry into pyspeos, and apply materials
    for body, body_mesh in pyspeos_simulation.cad_mesh_cache:
        # create the pyspeos geometry and apply materials
        speos_body = create_speos_body(body, body_mesh)
        apply_materials(speos_body)

    ### Setup the simulation
    sim = p.find(name=".*", name_regex=True, feature_type=simulation.SimulationInverse)[0]

    # define the other settings
    sim.stop_condition_passes_number = 50  # hard-coded number of cycles for now
    sim.stop_condition_duration = 1000000
    sim.commit()

    return [speos, p, sim]


def import_camera_sensor(pyspeos_simulation="", camera_model=""):
    """
    Load a camera model into the PySpeos project and point the simulation at it.

    Parameters
    ----------
    pyspeos_simulation : pyspeos_sim
        Session that holds the project and simulation.
    camera_model : str
        Name of the camera folder under ``simulation_data/camera``. The folder must contain
        a ``Camera_Sensor.json`` file.

    """
    if pyspeos_simulation.project:
        p = pyspeos_simulation.project
    else:
        print("error: no pyspeos project found; cannot import camera sensor")
        return

    # remove previous sensor from model
    prev_sensors = []
    try:
        for sensor_prev in p.find("", name_regex=True, feature_type=sensor.SensorRadiance):
            prev_sensors.append(sensor_prev)
    except:
        pass
    try:
        for sensor_prev in p.find("", name_regex=True, feature_type=sensor.SensorCamera):
            prev_sensors.append(sensor_prev)
    except:
        pass

    # retrieve the camera data from the JSON file
    camera_dir = os.path.join(BASE_DIR, "simulation_data", "camera", camera_model) + "/"
    camera_json_path = camera_dir + "Camera_Sensor.json"
    with open(camera_json_path, "r") as file:
        camera_data = json.load(file)

    # prepare pyspeos camera inputs
    distortion_file_uri = str(camera_dir + camera_data["distortion_file"])
    transmittance_file_uri = str(camera_dir + camera_data["transmittance_file"])
    red_spectrum_file_uri = str(camera_dir + camera_data["spectrum_red_file"])
    green_spectrum_file_uri = str(camera_dir + camera_data["spectrum_green_file"])
    blue_spectrum_file_uri = str(camera_dir + camera_data["spectrum_blue_file"])
    camera_axis_system = camera_data.get("axis", [])
    origin = camera_axis_system["origin"]
    direction_x = camera_axis_system["x_direction"] / np.linalg.norm(
        camera_axis_system["x_direction"]
    )
    direction_y = camera_axis_system["y_direction"] / np.linalg.norm(
        camera_axis_system["y_direction"]
    )
    direction_z = np.cross(direction_x, direction_y) / np.linalg.norm(
        np.cross(direction_x, direction_y)
    )  # calculate z direction based on x and y to ensure orthogonality

    direction_y_orthonorm = np.cross(direction_z, direction_x) / np.linalg.norm(
        np.cross(direction_z, direction_x)
    )  # recalculate y direction to ensure orthogonality with the new z
    if (
        direction_y_orthonorm.dot(direction_y) < 0.9999
    ):  # warn if recalculating y changed it significantly
        print(
            "warning: provided camera axis directions are not orthogonal; recalculating y "
            "based on x and z changed it significantly. Please verify the camera axis data in "
            "the JSON file."
        )
    direction_y = direction_y_orthonorm

    camera_axis = origin + direction_x.tolist() + direction_y.tolist() + direction_z.tolist()

    # create camera sensor object in speos model
    uid = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sensor_name = "Camera_Sensor__" + uid
    camera_sensor_obj = p.create_sensor(name=sensor_name, feature_type=sensor.SensorCamera)

    # Set distortion file
    camera_sensor_obj.distortion_file_uri = distortion_file_uri

    # set camera intrinsic/extrinsic parameters
    camera_sensor_obj.axis_system = camera_axis
    camera_sensor_obj.focal_length = camera_data["efl"]
    camera_sensor_obj.imager_distance = camera_data["efl"]  # set equal to efl
    camera_sensor_obj.f_number = camera_data["fno"]
    camera_sensor_obj.horz_pixel = camera_data["pix_x"]
    camera_sensor_obj.vert_pixel = camera_data["pix_y"]
    camera_sensor_obj.width = camera_data["size_x"]
    camera_sensor_obj.height = camera_data["size_y"]

    # photometric settings
    photometric = camera_sensor_obj.set_mode_photometric()
    photometric.transmittance_file_uri = transmittance_file_uri

    # color settings
    color = photometric.set_mode_color()
    color.red_spectrum_file_uri = red_spectrum_file_uri
    color.green_spectrum_file_uri = green_spectrum_file_uri
    color.blue_spectrum_file_uri = blue_spectrum_file_uri

    # commit changes to the project
    camera_sensor_obj.commit()

    # update the sensor path in the simulation to point to the new camera sensor
    sim = pyspeos_simulation.sim
    sim.sensor_paths = [sensor_name]
    sim.commit()

    # delete old sensors from the pyspeos model
    for sensor_prev in prev_sensors:
        sensor_prev.delete()

    return


def run_camera_simulation(pyspeos_simulation=""):
    """
    Run the simulation on the GPU and copy the results to the project results folder.

    Parameters
    ----------
    pyspeos_simulation : pyspeos_sim
        Session that holds the project and simulation.

    Returns
    -------
    str
        Path to the folder that contains the result files.

    """
    p = pyspeos_simulation.project
    sim = pyspeos_simulation.sim

    ### LAUNCH SIMULATION AS PROTOJOB ###
    sim._job.job_type = ProtoJob.Type.GPU
    sim.job_link = p.client.jobs().create(message=sim._job)
    sim.job_link.start()
    # simulation.job_link.get_progress_status()

    ### MONITOR STATUS ###
    bar = progressbar.ProgressBar(
        maxval=100, widgets=[progressbar.Bar("=", "[", "]"), " ", progressbar.Percentage()]
    )
    bar.start()
    job_state_res = sim.job_link.get_state()
    while (
        job_state_res.state != ProtoJob.State.FINISHED
        and job_state_res.state != ProtoJob.State.STOPPED
        and job_state_res.state != ProtoJob.State.IN_ERROR
    ):
        time.sleep(1)  # status update interval
        job_state_res = sim.job_link.get_state()  # check simulation status
        # print(sim.job_link.get_progress_status()) # simuation progress, estimated time remaining
        bar.update(100 * sim.job_link.get_progress_status().progress)

    try:
        sim_result = sim.job_link.get_results()
    except:
        time.sleep(1)
        sim_result = sim.job_link.get_results()

    ### retrieve the results
    xmp_path = sim_result.results[0].path

    # transfer results to project folder
    out_folder = os.path.join(BASE_DIR, "simulation_data", "Pyspeos_Simulation_Results") + "/"
    if not os.path.isdir(out_folder):
        os.mkdir(out_folder)

    # add simulation name to out path
    sim_name = sim._name
    out_folder = (
        out_folder + "/" + sim_name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    if not os.path.isdir(out_folder):
        # create the output folder
        os.mkdir(out_folder)
    else:
        # clear the output folder
        for item in os.listdir(out_folder):
            item_path = os.path.join(out_folder, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)

    # Move all data files from xmp_path to out_folder, overwriting existing files
    for filename in os.listdir(os.path.dirname(xmp_path)):
        full_file_name = os.path.join(os.path.dirname(xmp_path), filename)
        if os.path.isfile(full_file_name):
            shutil.copy2(full_file_name, out_folder)  # overwrite existing files
    shutil.rmtree(os.path.dirname(xmp_path))

    # open the result in an XMP viewer window
    xmp_path = out_folder + "\\" + os.path.basename(xmp_path)

    return os.path.dirname(xmp_path)


def show_sim_results(xmp_path=""):
    """
    Open a simulation result in the XMP viewer.

    Parameters
    ----------
    xmp_path : str
        Path to the XMP result file.

    """

    # open the result in an XMP viewer window
    xmpviewer = CreateObject("XMPViewer.Application")
    xmpviewer.OpenFile(xmp_path)
    xmpviewer.Show(1)

    return
