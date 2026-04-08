import os
import numpy as np
import pandas as pd
import time
import shutil
import win32com.client
from comtypes.client import CreateObject
import progressbar
import logger
from logger import log_message

import plot_helper

from ansys.geometry.core import launch_modeler
from ansys.geometry.core.designer.component import Component
from ansys.geometry.core.misc.options import ImportOptions, TessellationOptions

from ansys.speos.core.opt_prop import OptProp
from ansys.speos.core import project, launcher, Body, Face, Part
from ansys.speos.core.sensor import SensorRadiance
from ansys.speos.core.source import SourceAmbientNaturalLight, SourceSurface, SourceLuminaire
from ansys.speos.core.simulation import SimulationDirect, SimulationInverse
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.workflow import open_result
from ansys.speos.core.kernel.job import ProtoJob


def import_cad(speos_session="", cad_data_filepath="", material_settings_filepath="", sensor_settings_filepath="", source_settings_filepath=""):
    """imports the CAD data into the Speos session"""
    
    ### error handling on input data

    def load_settings(fn):
        """loads in the material library data from xlsx file"""
        df = pd.read_excel(fn, header=0)
        return df

    def load_cad_part(fn):
        """loads cad file using geometry modeler"""
        time0 = time.time()
        log_message('')
        log_message('importing: ' + fn)
        modeler_import_options = ImportOptions(
            cleanup_bodies=False,
            import_coordinate_systems=True,
            import_curves=False,
            import_hidden_components_and_geometry=False,
            import_names= True,
            import_planes=False,
            import_points=False,
            )
        modeler_design = modeler.open_file(file_path=fn, import_options=modeler_import_options) # returns ansys.geometry.core Design
        time1 = time.time()
        log_message('CAD import duration: ' + str(time1-time0))
        return modeler_design

    def tesselate_body(modeler_body, parent_subcomp, speos_body_name):
        """
        tesselates modeler body object, and commits to speos project
        note: the demonstrated architecture tessellates body-by-body, but 
        it could be done face-by-face to allow for application of face properties
        """
        watertight_tessellation = True
        if modeler_body.is_surface:
            watertight_tessellation = False
        fine_mesh_substr = ["HEX", "Lightguide"] # hacky hard-code for optical designs; ideally mesh settings would be defined in materials XLSX, or UI
        if any(sub in speos_body_name for sub in fine_mesh_substr):
            log_message(f"fine mesh on body: {speos_body_name}")
            tessellation_options = TessellationOptions(
                surface_deviation=0.000001, #1 um
                angle_deviation=1,
                max_aspect_ratio=0,
                max_edge_length=0.001, #1 mm
                watertight=watertight_tessellation
            )
        else:
            tessellation_options = TessellationOptions(
                surface_deviation=0.0001, #10 um
                angle_deviation=1,
                max_aspect_ratio=0,
                max_edge_length=0.01, # 10 mm
                watertight=watertight_tessellation
            )

        if type(modeler_body) == Component: 
            #sub-components are tessellated body-by-body; this should never be accessed
            mesh = modeler_body.tessellate(tess_options=tessellation_options)
        else:
            mesh = modeler_body.tessellate(include_edges=False, include_faces=True, merge=True, tess_options=tessellation_options)
            
        # if merge=False, need to loop through blocks
        ### EXAMPLE PSEUDO-CODE ###
        #for block in mesh:
        #    facets = block.faces[np.mod(np.arange(mesh.faces.size),4)!=0] # remove every 4th entry (that is the number of vertices for the facet; for pyspeos it is always n=3)
        #    vertices = 1000*block.points.flatten()
        #    vertex_normals = block.point_normals.flatten()
        
        #if merge=True, the entire body is one block
        facets = mesh.faces[np.mod(np.arange(mesh.faces.size),4)!=0] # remove every 4th entry (that is the number of vertices for the facet; for pyspeos it is always n=3)
        vertices = 1000*mesh.points.flatten()
        vertex_normals = mesh.point_normals.flatten()
        
        # Create a pyspeos body
        speos_body = parent_subcomp.create_body(name=speos_body_name).commit()
        
        # generate geometry as a single face, populated with meshed facet data
        speos_face = speos_body.create_face(name=f"{speos_body_name}_face")
        speos_face.set_vertices(vertices)
        speos_face.set_facets(facets)
        speos_face.set_normals(vertex_normals)
        speos_face.commit()
        
        return speos_body

    def format_name(obj, avoid_slash=False):
        """retrieve body/subcomponent name, and format into library convention"""
        name = obj.name
        while obj.parent_component.parent_component != None:
            if avoid_slash:
                name = obj.parent_component.name + "_" + name
            else:
                name = obj.parent_component.name + "/" + name
            obj = obj.parent_component
        return name

    def create_materials(p, material_data):
        """create a new pyspeos material, based on imported material library data"""
        library_data_dir, fname = os.path.split(library_data_filepath)
        optical_property = p.create_optical_property(material_data['Material_Name'].item())
        
        # check VOP type
        match material_data['VOP'].item():
            case 'Opaque':
                optical_property.set_volume_opaque()
            case 'Optic':
                # only currently support index of refraction
                index_of_refraction = material_data['VOP_Index'].item()
                optical_property.set_volume_optic(index=index_of_refraction, absorption=0, constringence=None)
        
            case 'Library':
                # set the material volume data path (speos .material file)
                vop_data_path = library_data_dir + "\\Library_Data\\VOP\\" + material_data['VOP_File'].item()
                if not os.path.exists(vop_data_path):
                    log_message("\nError in Material Library, on material '" + material_data['Material_Name'].item() + "'")
                    log_message("material data file path not found (" + vop_data_path + ")")
                    log_message("reverting to mirror\n")
                optical_property.set_volume_library(vop_data_path)

        # check SOP type
        match material_data['SOP'].item():
            case 'Mirror':
                # don't allow on transparent VOP
                if material_data['VOP'].item() != 'Opaque':
                    log_message("Error in Material Library, on material '" + material_data['Material_Name'].item() + "'\nmirror SOP on non-opaque VOP")
                    log_message("unable to set VOP")
                    optical_property.set_volume_opaque()
                reflectance = index_of_refraction = material_data['SOP_Reflectance'].item()
                optical_property.set_surface_mirror(reflectance)
            case 'OpticalPolished':
                # don't allow on opaque VOP
                if material_data['VOP'].item() == 'Opaque':
                    log_message("Error in Material Library, on material '" + material_data['Material_Name'].item() + "'\noptical polish SOP on opaque VOP")
                    log_message("unable to set VOP")
                    optical_property.set_volume_optic(index=1.0, absorption=0, constringence=None)
                optical_property.set_surface_opticalpolished()
            case 'Library':
                # need some intricate error handling here
                sop_data_path = library_data_dir + "\\Library_Data\\SOP\\" + material_data['SOP_File'].item()
                # check file existance
                if not os.path.exists(sop_data_path):
                    log_message("\nError in Material Library, on material '" + material_data['Material_Name'].item() + "'")
                    log_message("material data file path not found (" + sop_data_path + ")")
                    log_message("reverting to mirror\n")
                optical_property.set_surface_library(sop_data_path)
        
        return optical_property

    def create_sensor(p, cs, sensor_data):
        """create a radiance sensor in pyspeos project, using the data from the dataframe cs"""
        sensor_name = format_name(cs, avoid_slash=True)
        sensor = p.create_sensor(name=sensor_name, feature_type=SensorRadiance)
        sensor.set_type_colorimetric()
        sensor.set_layer_type_source()

        # set the orientation and position
        o = cs.frame.origin
        dx = cs.frame.direction_x
        dy = cs.frame.direction_y
        dz = cs.frame.direction_z
        sensor_axis = [1e3*o.x.magnitude, 1e3*o.y.magnitude, 1e3*o.z.magnitude] # convert units to mm
        sensor_axis.extend([dx.x, dx.y, dx.z])
        sensor_axis.extend([dy.x, dy.y, dy.z])
        sensor_axis.extend([dz.x, dz.y, dz.z])
        sensor.set_axis_system(sensor_axis)
        sensor.set_integration_angle(2)

        # set the other data from the sensor library
        sensor.set_focal(sensor_data['EFL'].item())
        dim = sensor.set_dimensions()
        dim.set_x_start(sensor_data['X_Start'].item())
        dim.set_x_end(sensor_data['X_End'].item())
        dim.set_x_sampling(sensor_data['X_Samp'].item())
        dim.set_y_start(sensor_data['Y_Start'].item())
        dim.set_y_end(sensor_data['Y_End'].item())
        dim.set_y_sampling(sensor_data['Y_Samp'].item())

        # commit
        sensor.commit()
        sensor_names_record.append(sensor_name)
        return
     
    def create_source_luminaire(p, cs, this_source_data):
        # create the surface source
        source_name = this_source_data['Source_Name'].item()
        this_source = p.create_source(name=source_name, feature_type=SourceLuminaire)
        
        # get library path
        library_data_dir, fname = os.path.split(library_data_filepath)
        ies_data_path = library_data_dir + "\\Library_Data\\Source\\" + this_source_data['Ies_File'].item()
        spectrum_data_path = library_data_dir + "\\Library_Data\\Source\\" + this_source_data['Spectrum_File'].item()

        this_source.set_intensity_file_uri(ies_data_path)
        this_source.set_flux_luminous(this_source_data['Flux_Luminous'].item())
        spectrum = this_source.set_spectrum()
        spectrum.set_library(spectrum_data_path)
        # set orientation and position from cs
        o = cs.frame.origin
        dx = -1 * cs.frame.direction_x
        dy = cs.frame.direction_y
        dz = cs.frame.direction_z
        source_axis = [1e3*o.x.magnitude, 1e3*o.y.magnitude, 1e3*o.z.magnitude] # convert units to mm
        source_axis.extend([dx.x, dx.y, dx.z])
        source_axis.extend([dy.x, dy.y, dy.z])
        source_axis.extend([dz.x, dz.y, dz.z])
        this_source.set_axis_system(source_axis)
        this_source.commit()
        source_names_record.append(source_name)
        return 
            
    def create_source_surface(p, modeler_design):
        """search speos structure tree to help generate user-supplied sources from library data"""
        #features = p.find(name=".*", name_regex=True)
        #for feat in features:
        #    log_message(str(type(feat)) + " : name=" + feat._name)
        library_data_dir, fname = os.path.split(library_data_filepath)
        for index, row in source_settings_data.iterrows():
            if row["Type"] != "Surface":
                continue
                #define_surface_source(p, row, modeler_design)
            feature = p.find(name=row["Parent_Name"], name_regex=True, feature_type=Part)
            if len(feature) > 1:
                log_message("error: multiple bodies found with body name specified for source <" + row["Body_Name"] + ">")
                continue
            if feature == []:
                log_message("error: no body found with body name specified for source <" + row["Body_Name"] + ">")
                continue
            feature = feature[0]
            faces = p.find(name=row["Parent_Name"]+"/.*", name_regex=True, feature_type=Face)
            
            # create the surface source
            this_source = p.create_source(name=row["Source_Name"], feature_type=SourceSurface)
            
            if row["Entire_Body"]:
                geoms = []
                for f in faces:
                    geoms.append((f.geo_path, bool(row["Reverse_Normal"])))
                this_source.set_exitance_constant(geometries=geoms)
            else:
                log_message("\nWARNING: face selection for surface source not currently supported\nface picker may lock up due to tkinter/pyvista interoperability issue\n")
            ######## UNDER CONSTRUCTION ########
                # re-tessellate the body in order to allow face-selection in GUI
                faces_blocks = []
                # easier for now to retrieve the geometry itself
                geom_body = get_body_from_path(modeler_design, row["Body_Name"])
                for f in geom_body.faces:
                    faces_blocks.append(f.tessellate())
                selected_face = plot_helper.plot_picker(faces_blocks, geom_body.faces)
                this_source.set_exitance_constant(geometries=[(selected_face.geo_path, row["Reverse_Normal"])])
            
            this_source.set_flux_luminous(row["Flux_Luminous"])
            spectrum_filepath = library_data_dir + "\\Library_Data\\Source\\" + row['Spectrum_File']
            this_source.set_spectrum().set_library(spectrum_filepath)
            this_source.commit()
            source_names_record.append(row["Source_Name"])
            
        return
    
    def create_source_ambient(p):
        """create a uniform ambient source"""
        source_name = "source_ambient"
        if source_name in source_names_record:
            source_name += "_1"
        source_ambient = p.create_source(name=source_name, feature_type=SourceAmbientNaturalLight)
        source_ambient.set_sun_automatic().year = 2025
        source_ambient.set_sun_automatic().month = 4
        source_ambient.set_sun_automatic().day = 1
        source_ambient.set_sun_automatic().hour = 7
        source_ambient.set_sun_automatic().minute = 30
        source_ambient.set_sun_automatic().longitude = 10
        source_ambient.set_sun_automatic().latitude = 45
        source_ambient.set_sun_automatic().time_zone = "CST"
        source_ambient.commit()
        source_names_record.append(source_name)
        return source_name

    def create_inverse_simulation(p, sensors, sources):
        # === create the speos simulation object ===
        sim_name = "inversesim_ambient"
        sim = p.create_simulation(name=sim_name, feature_type=SimulationInverse)
        sim.set_sensor_paths(sensors)
        sim.set_source_paths(sources)

        # define the other settings
        sim.set_dispersion(True)
        sim.set_stop_condition_passes_number(50)
        sim.set_stop_condition_duration(10000)
        sim.commit()
        return sim

    def create_direct_simulation(p, sensors, sources):
        # === create the speos simulation object ===
        sim_name = "directsim_lamp_lit"
        sim = p.create_simulation(name=sim_name, feature_type=SimulationDirect)
        sim.set_sensor_paths(sensors)
        sim.set_source_paths(sources)

        # define the other settings
        sim.set_dispersion(True)
        sim.set_stop_condition_rays_number(None) # hard-coded number of rays
        sim.set_stop_condition_duration(180)
        sim.commit()
        return sim  

    def retrieve_design_data(p, modeler_comp, speos_comp, tessellate_all_material):
        """recursive cs, body, and subcomponent search"""

        # first, retrieve all the bodies in this (sub)component
        for body in modeler_comp.bodies:
            # get the body name, with material library naming convention
            this_body_name = format_name(body)
            log_message(this_body_name)

            # if we have designated material data, we need to tessellate the body and apply material
            if (tessellate_all_material) or (this_body_name in material_settings_data['Body_Name'].values):
                log_message("\t-->tessellating body")
                # deal with duplicate object names
                if this_body_name in obj_names_record:
                    obj_names_record[this_body_name] += 1
                else:
                    obj_names_record[this_body_name] = 1
                speos_body_name = body.name + "." + str(obj_names_record[this_body_name])    
                
                # tesselate body and commit to speos project
                speos_body = tesselate_body(body, speos_comp, speos_body_name) 

                # apply material to new speos body
                if tessellate_all_material:
                    this_material_name = tessellate_all_material
                else:
                    this_material_name = material_settings_data[material_settings_data['Body_Name'] == this_body_name]['Material_Name'].item()
                log_message(f"\t-->applying material: {this_material_name}")
                apply_materials(p, speos_body, this_material_name)

        # then, retrieve all the coordinate systems in this (sub)compoment
        for cs in modeler_comp.coordinate_systems:
            # check if the cs is used for sensors
            this_cs_name = format_name(cs)
            if this_cs_name in sensor_settings_data['CS_Name'].values:
                # a sensor is requested for this CS; create the sensor
                this_sensor_data = sensor_settings_data[sensor_settings_data['CS_Name'] == this_cs_name]
                this_sensor_name = create_sensor(p, cs, this_sensor_data)

            # check if the cs is used for sources
            elif this_cs_name in source_settings_data['Parent_Name'].values:
                this_source_data = source_settings_data[source_settings_data['Parent_Name'] == this_cs_name]
                create_source_luminaire(p, cs, this_source_data)
            else:
                pass

        # recursively search subcomponents in this (sub)component
        for modeler_subcomp in modeler_comp.components:
            # create speos subcomponent
            speos_subcomp = speos_comp.create_sub_part(name=modeler_subcomp.name)
            speos_subcomp.set_axis_system(axis_system=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])

            #if list(modeler_subcomp.get_world_transform().flat) != list(np.identity(4).flat):
            #    #not necessary to check, since the mesh data is in global coordinates
            #    log_message("Warning: subcomponent <" + modeler_subcomp.name + "> position/orientation was not correctly imported")
            #    log_message(modeler_subcomp.get_world_transform())
            #    axis = list(modeler_subcomp.get_world_transform().flat)
            #    speos_axis = [1e3*axis[12], 1e3*axis[13], 1e3*axis[14], 1, 0, 0, 0, 1, 0, 0, 0, 1]
                #speos_subcomp.set_axis_system(axis_system=speos_axis)
                
            speos_subcomp.commit()

            # check if we need to tessellate the entire subcomp tree
            this_subcomp_name = format_name(modeler_subcomp)
            log_message(this_subcomp_name)
            if this_subcomp_name in material_settings_data['Body_Name'].values:
                log_message(f"     tessellating all bodies in subcomponent {this_subcomp_name}")
                this_material_name = material_settings_data[material_settings_data['Body_Name'] == this_subcomp_name]['Material_Name'].item()
                retrieve_design_data(p, modeler_subcomp, speos_subcomp, this_material_name) 
            else:
                retrieve_design_data(p, modeler_subcomp, speos_subcomp, tessellate_all_material=False)
            
    def apply_materials(p, speos_body, material_name):
        """apply material settings to a speos body"""
        
        # check that the requested material exists in the library
        if material_name not in material_library_data['Material_Name'].values:
            log_message("error: material <"+ material_name + "> specified for body <" + speos_body._name + "> \nin materials settings xlsx was not found in materials library xlsx\n")

        # check if the material already exists in pyspeos project
        optical_property = p.find(name=material_name, feature_type=OptProp)
        if optical_property:
            if len(optical_property) > 1:
                log_message("warning: found multiple instances of optical property <" + material_name + "in pyspeos scene>")
            
            optical_property = optical_property[0]
            
            # apply to geometries; append the list of geometries using this optical property
            geometries_list = optical_property.get("geometries")['geo_paths'] #[optical_property._material_instance.geometries]
            georef_list = [GeoRef.from_native_link(geometries_list[i]) for i in range(0,len(geometries_list))]
            georef_list.append(speos_body)
            optical_property.set_geometries(geometries=georef_list)

        else:
            # grab the material data entry from the library
            material_data = material_library_data[material_library_data['Material_Name'] == material_name]
            # create optical property from library data
            optical_property = create_materials(p, material_data)
            # apply to  geometries
            optical_property.set_geometries(geometries=[speos_body])

        optical_property.commit()
        return

    def get_body_from_path(model, hierarchy_path: str):
        """
        Retrieve a Body from a hierarchical path string.

        Parameters
        ----------
        model : ansys.geometry.core.model.Model
            Loaded geometry model.
        hierarchy_path : str
            Path in the form "PartA/PartB/PartC/BodyName".

        Returns
        -------
        ansys.geometry.core.designer.body.Body

        Raises
        ------
        KeyError
            If any part or the body is not found.
        """
        tokens = [t for t in hierarchy_path.split("/") if t]
        if len(tokens) < 2:
            raise ValueError("Path must include at least one part and a body name")

        *subcomp_names, body_name = tokens

        subcomp = model
        for subcomp_name in subcomp_names:
            matches = [c for c in subcomp.components if c.name == subcomp_name]
            if not matches:
                raise KeyError(f"Component '{subcomp_name}' not found under '{subcomp.name}'")
            subcomp = matches[0]

        matches = [b for b in subcomp.bodies if b.name == body_name]
        if not matches:
            raise KeyError(f"Body '{body_name}' not found in component '{subcomp.name}'")

        return matches[0]
 

    ### Launch CAD and PySpeos tools, if necessary
    global modeler
    if speos_session.built.get():
        log_message("Re-building Speos Model")
        modeler = speos_session.modeler
        pyspeos = speos_session.speos
    else:
        log_message("Building Speos Model")
        log_message("Launching Geometry Service...")
        #modeler = launch_modeler(mode="spaceclaim", hidden=True) # mode="discovery", mode="geometry_service"
        modeler = launch_modeler(mode="geometry_service", version="261")#, version="261")
        log_message("Launching SPEOS RPC server...")
        # check your port by running C:\Program Files\ANSYS Inc\vXXX\Optical Products\SPEOS_RPC\SpeosRPC_Server.exe
        #pyspeos = launcher.launch_local_speos_rpc_server(version="252", port=50098) 
        pyspeos = launcher.launch_local_speos_rpc_server(port=50051) #version="252" 
    
    ### Create new pyspeos project
    p = project.Project(speos=pyspeos)
    root_part = p.create_root_part()
    root_part.commit()

    ### Import the material library data
    global library_data_filepath
    library_data_filepath = os.getcwd() + "\\Library\\MaterialsLibrary.xlsx"
    material_library_data = load_settings(library_data_filepath)

    ### Import the settings data
    global project_folder
    project_folder = os.getcwd() + "\\SpeosModel"
    material_settings_data = load_settings(material_settings_filepath)
    sensor_settings_data = load_settings(sensor_settings_filepath)
    source_settings_data = load_settings(source_settings_filepath)

    ### Import the CAD and Tessellate
    global obj_names_record 
    global sensor_names_record
    global source_names_record
    obj_names_record = dict()
    sensor_names_record = []
    source_names_record = []

    # load in the CAD part
    modeler_design = load_cad_part(cad_data_filepath)

    # look for all the bodies, coordinates, and sub-components (recursive search)
    retrieve_design_data(p, modeler_comp=modeler_design, speos_comp=root_part, tessellate_all_material=False)

    ### Set up remaining Speos simulation items
    # create remaining sources (we've only created the luminaires during the retrieve_design_data step)
    create_source_surface(p, modeler_design)

    # create the direct simulation
    sim_direct = create_direct_simulation(p, sensor_names_record, source_names_record)

    # create inverse simulation, with ambient source 
    source_ambient = create_source_ambient(p)
    sim_inverse = create_inverse_simulation(p, sensor_names_record, [source_ambient])

    return [pyspeos, modeler, p, sim_direct, sim_inverse]


def run_simulation(sim, p):
    """runs the speos simulation, retrieves the results, and opens in XMP viewer"""
    #sim_result = sim.compute_GPU()
    ### LAUNCH SIMULATION AS PROTOJOB ###
    sim._job.job_type = ProtoJob.Type.GPU
    sim.job_link = p.client.jobs().create(message=sim._job)
    sim.job_link.start()
    #simulation.job_link.get_progress_status()

    ### MONITOR STATUS ###
    job_state_res = sim.job_link.get_state()
    while (
        job_state_res.state != ProtoJob.State.FINISHED
        and job_state_res.state != ProtoJob.State.STOPPED
        and job_state_res.state != ProtoJob.State.IN_ERROR
    ):
        time.sleep(1)
        job_state_res = sim.job_link.get_state()
        
        progress = 100 * sim.job_link.get_progress_status().progress
        logger.log_progress_inline(progress)
        logger.force_update()

    try:
        results = sim.job_link.get_results()
    except:
        time.sleep(1)
        results = sim.job_link.get_results()

    ### retrieve the results 
    xmp_path = results.results[0].path
    #sensor_name = sim.get("sensor_paths")[0].split(":")[0]
    #xmp_path = open_result._find_correct_result(simulation_feature=sim, result_name=sensor_name+".xmp")

    # transfer results to project folder
    out_folder = project_folder + "\\SPEOS Output Files\\Pyspeos_Simulation_Results"
    if not os.path.isdir(out_folder):
        os.mkdir(out_folder)
    
    # add simulation name to out path
    sim_name = sim._name
    out_folder = out_folder + "\\" + sim_name
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
    #shutil.rmtree(os.path.dirname(xmp_path))
    try:
        sim.job_link.delete()
    except:
        time.sleep(1)
        sim.job_link.delete()

    # open the result in an XMP viewer window
    xmp_path = out_folder + "\\" + os.path.basename(xmp_path)
    xmpviewer = CreateObject("XMPViewer.Application")
    xmpviewer.OpenFile(xmp_path)
    xmpviewer.Show(1)

    log_message('results saved to\n' + os.path.dirname(out_folder) + '\n')
    return xmp_path


def merge_results(xmp_paths):
    ### Manage Inputs 
    outfile = project_folder + "\\SPEOS Output Files\\Pyspeos_Simulation_Results\\XmpUnionResult.xmp"
    if os.path.isfile(outfile):
        os.remove(outfile)

    #photometric calc instance creation
    vpLab = win32com.client.Dispatch("VPLab.Application")
    vpLab.FileSource1(xmp_paths[0])
    vpLab.FileSource2(xmp_paths[1])
    vpLab.FileResult(outfile)
    vpLab.Operation("MapUnion")
    vpLab.Process

    # Close VPLab
    pid=vpLab.GetPID
    cmd = 'taskkill /PID ' + str(pid) + ' /F'
    os.system(cmd)
    
    # show the result
    xmpviewer = CreateObject("XMPViewer.Application")
    xmpviewer.OpenFile(outfile)
    xmpviewer.Show(1)
 
    return outfile
