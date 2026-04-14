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
# worker.py
from __future__ import annotations
from typing import Optional
from dataclasses import asdict
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable, QTimer
import pyvista as pv
import traceback
#from threading import Thread
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FuturesTimeoutError
from ansys.speos.core import project,launcher,speos
from ansys.speos.core.simulation import SimulationVirtualBSDF
from setup_data import speos_config
from toolfunction import copy_path_list_to_timestamp_dir
class sim_worker(QObject):
    
    progress = Signal(str)         # Progress message
    error = Signal(str)            # Failed with error message
    finished = Signal(bool)      # Finished, with success flag

    @Slot(speos_config)
    def speos_start(self, params: speos_config):
        """collect params from Ui then run。"""
        self._run(params)

    @Slot()
    def speos_cancel(self):
        try:
            self._canceled = True
            self._emit("Cancel request received...")
            # Attempt to stop the running job
            
            if self._VBB_Simu is not None and hasattr(self._VBB_Simu, "job_link") and self._VBB_Simu.job_link is not None:
                self._emit("Stop command sent to SPEOS job.")
                #self._VBB_Simu.job_link.stop()
            else:
                self._emit("No running job to stop.")
            
        except Exception as e:
            pass

    def __init__(self):
        super().__init__()
        self._speos = None
        self._canceled = False
        self._VBB_Simu = None
        self._is_success = False
    #@Slot(object)
    def _run(self, p: speos_config):
        self._canceled = False  # reset cancel flag
        try:
            # 1) read STL
            self._emit("Loading geometry...")
            mesh = pv.read(p.geo_path)
            mesh_center = mesh.center
            vertices = mesh.points
            vertex_normals = mesh.point_normals
            faces = mesh.faces.reshape((-1, 4))[:, 1:]
            self._check_cancel()

            # 2) init start SPEOS RPC
            self._emit("Starting SPEOS RPC...")
            if p.hostname == "localhost":
                try:
                    self._speos = launcher.launch_local_speos_rpc_server(
                        version=p.speos_version, port=p.grpc_port
                    )
                except:
                    raise RuntimeError("Can not launch local Speos RPC server.")
            else:
                try:
                    self._speos = launcher.launch_remote_speos(version=p.speos_version) # Fix in the future
                except:
                    raise RuntimeError("Can not launch remote Speos RPC server")
            self._check_cancel()

            # 3) build up Speos Project
            self._emit("Building Speos Project...")
            VBB_Proj = project.Project(speos=self._speos)
            root_part = VBB_Proj.create_root_part().commit()
            vbb_body = root_part.create_body(name="VBB_BODY").commit()
            vbb_body_face = (
                vbb_body.create_face(name="Face1")
                .set_vertices(vertices.flatten())
                .set_facets(faces.flatten())
                .set_normals(vertex_normals.flatten())
            )
            vbb_body_face.commit()

            # 4) Optical properties
            self._emit("Setting Optical Properties...")
            op = VBB_Proj.create_optical_property(name="Material_1")
            if not p.roughness_only:
                if p.opaque:
                    op.set_volume_opaque()
                else:
                    op.set_volume_library(p.vop_path)

                if p.polished:
                    op.set_surface_opticalpolished()
                else:
                    op.set_surface_library(p.sop_path)

                if p.polished and p.opaque:
                    raise RuntimeError("Error: Both surface and volume cannot be set to polished and opaque.")
            else:
                op.set_volume_opaque()
                op.set_surface_mirror(reflectance=100)

            op.set_geometries(geometries=[vbb_body])
            try:
                op.commit()
            except:
                raise RuntimeError("Error: Unable to commit optical property. Please check the optical property settings.")

            # 5) Simulation Mode and Object
            self._emit("Setting Simulation Mode...")
            self._VBB_Simu = VBB_Proj.create_simulation(
                name="virtual_bsdf", feature_type=SimulationVirtualBSDF
            )

            if p.roughness_only:
                if p.sampling_mode == "Adaptive sampling":
                    self._VBB_Simu.set_mode_roughness_only().set_adaptive().adaptive_uri = p.sampling_file
                elif p.sampling_mode == "Uniform":
                    self._VBB_Simu.set_mode_roughness_only().set_uniform().theta_sampling = p.theta_sampling
                else:
                    raise RuntimeError("Unexpected Unpolished Sampling Error.")
            else:
                self._VBB_Simu.set_mode_all_characteristics().is_bsdf180 = p.bsdf_180

                if p.iridescence:
                    if p.sampling_mode == "Adaptive sampling":
                        self._VBB_Simu.set_mode_all_characteristics().set_iridescence().set_adaptive().adaptive_uri = p.sampling_file
                    elif p.sampling_mode == "Uniform":
                        self._VBB_Simu.set_mode_all_characteristics().set_iridescence().set_uniform().theta_sampling = p.theta_sampling 
                    else:
                        raise RuntimeError("Unexpected sampling mode.")
                else:
                    if p.anisotropic:
                        if p.sampling_mode == "Adaptive sampling":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_adaptive().adaptive_uri = p.sampling_file
                        elif p.sampling_mode == "Uniform":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().theta_sampling = p.theta_sampling
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().phi_sampling = p.phi_sampling
                            if p.symmetry == "none":
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_none()
                            elif p.symmetry == "x":
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_1_plane_symmetric()
                            elif p.symmetry == "xy":
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_2_plane_symmetric()
                        else:
                            raise RuntimeError("Unexpected sampling mode.")
                    else:
                        if p.sampling_mode == "Adaptive sampling":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_adaptive().adaptive_uri = p.sampling_file
                        elif p.sampling_mode == "Uniform":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_uniform().theta_sampling = p.theta_sampling
                        else:
                            raise RuntimeError("Unexpected sampling mode.")

                self._VBB_Simu.set_mode_all_characteristics().reflection_and_transmission = p.sensor_RT

            # 6) sensor
            if p.sensor_auto:
                self._VBB_Simu.set_sensor_sampling_automatic()
            else:
                self._VBB_Simu.set_sensor_sampling_uniform().theta_sampling = p.sensor_theta_sample 
                self._VBB_Simu.set_sensor_sampling_uniform().phi_sampling = p.sensor_phi_sample


            # 7) other parameters
            self._VBB_Simu.integration_angle = float(p.integration_angle)
            self._VBB_Simu.analysis_x_ratio = float(p.x_ratio)
            self._VBB_Simu.analysis_y_ratio = float(p.y_ratio)
            self._VBB_Simu.set_wavelengths_range().start = int(p.wl_start)
            self._VBB_Simu.set_wavelengths_range().end = int(p.wl_end)
            self._VBB_Simu.set_wavelengths_range().sampling = int(p.wl_sampling)
            if p.ray_unit == "Megarays":
                self._VBB_Simu.stop_condition_ray_number = int(p.ray_value * 1e6)
            else:
                self._VBB_Simu.stop_condition_ray_number = int(p.ray_value * 1e9)
            self._VBB_Simu.axis_system = [
                mesh_center[0], mesh_center[1], 0.0, #几何体中心的问题
#                0.0, 0.0, 0.0,
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0,
            ]
            try:
                self._VBB_Simu.commit()
            except:
                raise RuntimeError("Something wrong during Simulation Settings")

            self._check_cancel()
            # 8) calculating
            self._emit("Generating...")
            """ Need to check and improve cancel function here
            with ThreadPoolExecutor(max_workers=1) as executor:   # 应该行得通
                future = executor.submit(self._VBB_Simu.compute_CPU)
                #while not future.done():
                    #self._check_cancel()
                #result_list = future.result()  # blocking call
                
                while True:
                    try:
                        result_list = future.result(timeout=1)
                        break
                    except FuturesTimeoutError:          
                        if self._canceled and self._VBB_Simu is not None and hasattr(self._VBB_Simu, "job_link") and self._VBB_Simu.job_link is not None:
                            #self._VBB_Simu.job_link.stop()
                            print("checking cancel inside loop...")
                            t = t+1
                            print(t)
                            raise RuntimeError("Simulation canceled by user.")
                        continue
            """
            
            result_list = self._VBB_Simu.compute_CPU(threads_number=p.threads_num)   # blocking call, executed in thread
            self._check_cancel()

            # 9) Copy result
            self._emit("Getting Result...")
            copy_path_list_to_timestamp_dir(result_list, p.result_path, prefix="Result") 
            self._emit("Simulation completed. Ending SPEOS service...")
            self._is_success = True
            #self.finished.emit(True)
        #except NoResultError:
        #    tb = traceback.format_exc()
        #    self.error.emit(f"{e}\n{tb}")
        #    self.finished.emit(False)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self._is_success = False
            #self.finished.emit(False)
        finally:
            try:
                if self._speos is not None:
                    self._speos.close()
                    self._emit("Speos Service finished.")
                    self.finished.emit(self._is_success)
                    self._speos = None
                    self._canceled = False
                    self._VBB_Simu = None
            except Exception:
                pass

    def _emit(self, msg: str):
        self.progress.emit(msg)

    def _check_cancel(self):
        if self._canceled:
            raise RuntimeError("Simulation canceled by user.")
