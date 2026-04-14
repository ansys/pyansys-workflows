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
from concurrent.futures import ThreadPoolExecutor
import pyvista as pv
from ansys.speos.core import Project, launcher
from ansys.speos.core.simulation import SimulationVirtualBSDF
from ansys.speos.core.bsdf import AnisotropicBSDF
from threading import Thread
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FuturesTimeoutError
import time
# load the geometry scanned
t0 = time.time()
mesh = pv.read(r"C:\Py_Projects\VBB\9054 k24\9054 k24\9054.stl")
mesh_center = mesh.center
vertices = mesh.points
vertex_normals = mesh.point_normals
faces = mesh.faces.reshape((-1, 4))[:, 1:]

# initiate an empty pySpeos project
speos = launcher.launch_local_speos_rpc_server("252", 50098)
p = Project(speos=speos)

# create geometry inside pySpeos project
root_part = p.create_root_part().commit()
vbb_body = root_part.create_body(name="MT_11000").commit()
vbb_body_face = (
    vbb_body.create_face(name="Face1")
    .set_vertices(vertices.flatten())
    .set_facets(faces.flatten())
    .set_normals(vertex_normals.flatten())
)
vbb_body_face.commit()
#p.preview(viz_args={"opacity": 0.7})
# assign material to geometry
op = p.create_optical_property(name="Material_1")
op.set_volume_optic(index=1.49)
op.set_surface_opticalpolished()
#op.set_surface_mirror(reflectance=100)
op.set_geometries(geometries=[vbb_body])
op.commit()

# create and run a virtual bsdf bench simulation
vbb = p.create_simulation(name="virtual_bsdf", feature_type=SimulationVirtualBSDF)
vbb.integration_angle = 2
vbb.set_sensor_sampling_automatic()
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().theta_sampling = 13
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().phi_sampling = 2
vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_2_plane_symmetric()
#vbb.set_sensor_sampling_uniform()
vbb.stop_condition_ray_number = 100000
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
vbb.threads_number = 16
t = 0
vbb.commit()
with ThreadPoolExecutor(max_workers=1) as executor:   #这个地方还要改
    future = executor.submit(vbb.compute_CPU)
                #while not future.done():
                    #self._check_cancel()
                #result_list = future.result()  # blocking call
                
    while True:
        try:
            result_list = future.result(timeout=5)
            break
        except FuturesTimeoutError:
            if vbb is not None:          
                print(vbb.job_link.get_progress_status().progress)
            #print(t)
            continue
            
#print(vbb.job_link.get_progress_status().progress)
#compute_thread = Thread(target=vbb.compute_CPU)
#compute_thread.start()

#time.sleep(30)
#vbb.job_link.stop()
#compute_thread.join()
#results = vbb.compute_CPU()
#print(results)

speos.close()
t1 = time.time()
print(t1-t0)
