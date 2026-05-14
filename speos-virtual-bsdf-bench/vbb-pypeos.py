# Copyright (C) 2024 - 2026 ANSYS, Inc. and/or its affiliates.
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
This is only an simple test project
"""
import pyvista as pv
from ansys.speos.core import Project, launcher
from ansys.speos.core.simulation import SimulationVirtualBSDF
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import threading
from ansys.geometry.core import launch_modeler
from ansys.geometry.core.designer.component import Component
from ansys.geometry.core.misc.options import ImportOptions, TessellationOptions


def run_vbb_with_timeout(vbb, threads_number: int, timeout_seconds: float):
    """Run VBB computation and request stop when timeout is reached."""
    stop_event = threading.Event()
    stop_requested = False
    use_timeout = timeout_seconds >= 0

    def request_stop():
        stop_event.set()

    timer = None
    if use_timeout:
        timer = threading.Timer(timeout_seconds, request_stop)
        timer.start()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(vbb.compute_CPU, threads_number=threads_number)

            if not use_timeout:
                return future.result()

            while True:
                try:
                    result = future.result(timeout=0.5)
                    if stop_requested:
                        raise TimeoutError(f"VBB computation exceeded {timeout_seconds} seconds and was stopped.")
                    return result
                except FuturesTimeoutError:
                    if stop_event.is_set() and not stop_requested:
                        print(f"Timeout reached after {timeout_seconds} seconds, stopping computation...")
                        vbb.stop_computation()
                        stop_requested = True
    finally:
        if timer is not None:
            timer.cancel()

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
    
modeler = launch_modeler(mode="geometry_service", version="261")

# load the geometry scanned
mesh = pv.read(r"C:\Py_Projects\VBB\9054 k24\9054 k24\9054.stl")
mesh_center = mesh.center
vertices = mesh.points
vertex_normals = mesh.point_normals
faces = mesh.faces.reshape((-1, 4))[:, 1:]

# initiate an empty pySpeos project
speos = launcher.launch_local_speos_rpc_server("261", 50098)
p = Project(speos=speos)

# create geometry inside pySpeos project
root_part = p.create_root_part().commit()
vbb_body = root_part.create_body(name="MT_11000").commit()
'''
vbb_body_face = (
    vbb_body.create_face(name="Face1")
    .set_vertices(vertices.flatten())
    .set_facets(faces.flatten())
    .set_normals(vertex_normals.flatten())
)
'''
vbb_body_face = vbb_body.create_face(name="Face1")
vbb_body_face.vertices = vertices.flatten().tolist()
vbb_body_face.facets = faces.flatten().tolist()
vbb_body_face.normals = vertex_normals.flatten().tolist()
vbb_body_face.commit()
#p.preview(viz_args={"opacity": 0.7})
# assign material to geometry
op = p.create_optical_property(name="Material_1")
op.set_volume_optic().index = 1.5
op.set_surface_opticalpolished()
#op.set_surface_mirror(reflectance=100)
op.geometries = [vbb_body] #？？？
op.commit()

# create and run a virtual bsdf bench simulation
vbb = p.create_simulation(name="virtual_bsdf", feature_type=SimulationVirtualBSDF)
vbb.integration_angle = 2
vbb.set_sensor_sampling_automatic()
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().theta_sampling = 5
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().phi_sampling = 2
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_2_plane_symmetric()
#vbb.set_sensor_sampling_uniform()
vbb.stop_condition_ray_number = 1000000
vbb.analysis_x_ratio = 50
vbb.analysis_y_ratio = 50
vbb.axis_system = [
    mesh_center[0],
    mesh_center[1],
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
]  # change the coordinate VBSDF to body center
vbb.commit()

try:
    results = run_vbb_with_timeout(vbb, threads_number=16, timeout_seconds=-1)
    print(results)
except TimeoutError as exc:
    print(exc)
finally:
    speos.close()
