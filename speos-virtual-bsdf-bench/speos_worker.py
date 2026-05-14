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
from concurrent.futures import ThreadPoolExecutor
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
        self._build(params)
    @Slot()
    def _preview(self):
        if self._VBB_Proj is not None:
            self._VBB_Proj.preview()
        else:
            raise RuntimeError("No simulation available for preview.")
    @Slot(speos_config)
    def speos_run(self):
        self._run()
    @Slot()
    def speos_cancel(self):
        try:
            if self._built is True and self._running is False: # if the simulation is built but not running, it means it is waiting to run, we can directly close the speos service without worrying about stopping the computation
                self._emit("Canceling simulation...")
                self._is_success = False
                self._speos.close()
                self._emit("Speos Service finished.")
                self.finished.emit(self._is_success)
                self._speos = None
                self._canceled = False
                self._VBB_Simu = None
                self._built = False
                self._running = False
            elif self._built is True and self._running is True: # if the simulation is built and running, we need to stop the computation first, then close the speos service in the finally block of _run function
                self._emit("Canceling simulation...")
                self._canceled = True
                self._request_stop_computation()
            else:
                self._emit("No running job to stop.")
        except Exception:
            pass
                
    def __init__(self):
        super().__init__()
        self._speos = None
        self._canceled = False
        self._VBB_Simu = None
        self._VBB_Proj = None
        self._is_success = False
        self.simupara = None
        self._built = False
        self._running = False
        self._stop_requested = False
        self._future = None
        self._executor = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._poll_run_future)
    #@Slot(object)
    
    
    def _emit(self, msg: str) -> None:
        self.progress.emit(msg)

    def _request_stop_computation(self):
        if self._VBB_Simu is None or self._stop_requested:
            return

        try:
            self._VBB_Simu.stop_computation()
            self._stop_requested = True
            self._emit("Stop command sent to SPEOS job.")
        except Exception:
            self._emit("Failed to send stop command to SPEOS job, will retry...")

    def _build(self, p: speos_config) -> None:
        self._canceled = False  # reset cancel flag
        self._built = False  # reset built flag
        self._is_success = False  # reset success flag
        self._stop_requested = False
        self.simupara = p  # store simulation parameters    
        try:
            # 1) read STL
            self._emit("Loading geometry...")
            mesh = pv.read(p.geo_path)
            mesh_center = mesh.center
            vertices = mesh.points
            vertex_normals = mesh.point_normals
            faces = mesh.faces.reshape((-1, 4))[:, 1:]

            # 2) init start SPEOS RPC
            self._emit("Starting SPEOS RPC...")
            if self.simupara.hostname == "localhost":
                try:
                    self._speos = launcher.launch_local_speos_rpc_server(
                        version=self.simupara.speos_version, port=self.simupara.grpc_port
                    )
                except:
                    raise RuntimeError("Can not launch local Speos RPC server.")
            else:
                try:
                    self._speos = launcher.launch_remote_speos(version=self.simupara.speos_version) # Fix in the future
                except:
                    raise RuntimeError("Can not launch remote Speos RPC server")

            # 3) build up Speos Project
            self._emit("Building Speos Project...")
            self._VBB_Proj = project.Project(speos=self._speos)
            root_part = self._VBB_Proj.create_root_part().commit()
            vbb_body = root_part.create_body(name="VBB_BODY").commit()
            '''
            vbb_body_face = (
                vbb_body.create_face(name="Face1")
                .set_vertices(vertices.flatten())
                .set_facets(faces.flatten())
                .set_normals(vertex_normals.flatten())
            )
            '''
            #After pyspeos 0.8.0
            vbb_body_face = vbb_body.create_face(name="Face1")
            vbb_body_face.vertices = vertices.flatten().tolist()
            vbb_body_face.facets = faces.flatten().tolist()
            vbb_body_face.normals = vertex_normals.flatten().tolist()
            vbb_body_face.commit()

            # 4) Optical properties
            self._emit("Setting Optical Properties...")
            op = self._VBB_Proj.create_optical_property(name="Material_1")
            if not self.simupara.roughness_only:
                if self.simupara.opaque:
                    op.set_volume_opaque()
                else:
                    #op.set_volume_library(self.simupara.vop_path)
                    op.set_volume_library().material_file_uri = self.simupara.vop_path

                if self.simupara.polished:
                    op.set_surface_opticalpolished()
                else:
                    #op.set_surface_library(self.simupara.sop_path)
                    op.set_surface_library().file_uri = self.simupara.sop_path

                if self.simupara.polished and self.simupara.opaque:
                    raise RuntimeError("Error: Both surface and volume cannot be set to polished and opaque.")
            else:
                op.set_volume_opaque()
                #op.set_surface_mirror(reflectance=100)
                op.set_surface_mirror().reflectance = 100

            #op.set_geometries(geometries=[vbb_body])
            op.geometries = [vbb_body]  # After pyspeos 0.8.0, set_geometries is deprecated, directly set geometries attribute
            try:
                op.commit()
            except:
                raise RuntimeError("Error: Unable to commit optical property. Please check the optical property settings.")

            # 5) Simulation Mode and Object
            self._emit("Setting Simulation Mode...")
            self._VBB_Simu = self._VBB_Proj.create_simulation(
                name="virtual_bsdf", feature_type=SimulationVirtualBSDF
            )

            if self.simupara.roughness_only: # Roughness only mode, no iridescence, no anisotropic, no BSDF180, only reflection
                if self.simupara.sampling_mode == "Adaptive sampling":
                    self._VBB_Simu.set_mode_roughness_only().set_adaptive().adaptive_uri = self.simupara.sampling_file
                elif self.simupara.sampling_mode == "Uniform":
                    self._VBB_Simu.set_mode_roughness_only().set_uniform().theta_sampling = self.simupara.theta_sampling
                else:
                    raise RuntimeError("Unexpected Unpolished Sampling Error.")
            else:
                self._VBB_Simu.set_mode_all_characteristics().is_bsdf180 = self.simupara.bsdf_180 #if it is BSDF depends on light incident, BSDF 180 is independent of iridescence and anisotropic, it can be set in any case.

                if self.simupara.iridescence: # if it is iridescence, then it must be isotropic
                    if self.simupara.sampling_mode == "Adaptive sampling":
                        self._VBB_Simu.set_mode_all_characteristics().set_iridescence().set_adaptive().adaptive_uri = self.simupara.sampling_file
                    elif self.simupara.sampling_mode == "Uniform":
                        self._VBB_Simu.set_mode_all_characteristics().set_iridescence().set_uniform().theta_sampling = self.simupara.theta_sampling 
                    else:
                        raise RuntimeError("Unexpected sampling mode.")
                else: # if it is not iridescence, it can be either anisotropic or isotropic
                    if self.simupara.anisotropic:
                        if self.simupara.sampling_mode == "Adaptive sampling":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_adaptive().adaptive_uri = self.simupara.sampling_file
                        elif self.simupara.sampling_mode == "Uniform":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().theta_sampling = self.simupara.theta_sampling
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().phi_sampling = self.simupara.phi_sampling
                            if self.simupara.symmetry == "none": # if it is none, no symmetry
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_none()
                            elif self.simupara.symmetry == "x": # if it is x, 0-180 plane symmetric
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_1_plane_symmetric()
                            elif self.simupara.symmetry == "xy": # if it is xy, 0-180 90-270 plane symmetric
                                self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_2_plane_symmetric()
                        else:
                            raise RuntimeError("Unexpected sampling mode.")
                    else: # if it is not anisotropic, it must be isotropic
                        if self.simupara.sampling_mode == "Adaptive sampling":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_adaptive().adaptive_uri = self.simupara.sampling_file
                        elif self.simupara.sampling_mode == "Uniform":
                            self._VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_uniform().theta_sampling = self.simupara.theta_sampling
                        else:
                            raise RuntimeError("Unexpected sampling mode.")

                self._VBB_Simu.set_mode_all_characteristics().reflection_and_transmission = self.simupara.sensor_RT # if sensor is reflection and transmission, it can be set in any case.
            
            try:
                self._VBB_Simu.commit()
            except:
                raise RuntimeError("VBB Mode Settings Error")
            
            # 6) sensor
            if self.simupara.sensor_auto:
                self._VBB_Simu.set_sensor_sampling_automatic()
            else:
                self._VBB_Simu.set_sensor_sampling_uniform().theta_sampling = self.simupara.sensor_theta_sample 
                self._VBB_Simu.set_sensor_sampling_uniform().phi_sampling = self.simupara.sensor_phi_sample
            
            try:
                self._VBB_Simu.commit()
            except:
                raise RuntimeError("VBB Sensor Settings Error")
            # 7) Optical propagation setting
            self._VBB_Simu.geom_distance_tolerance = self.simupara.GDT
            self._VBB_Simu.max_impact = self.simupara.max_suf_int
            if not self.simupara.weight:
                self._VBB_Simu.set_weight_none()
            else:
                #self._VBB_Simu.set_weight().set_minimum_energy_percentage(self.simupara.max_eng_pct/100)
                self._VBB_Simu.set_weight().minimum_energy_percentage = self.simupara.max_eng_pct/100
            # 8) other parameters
            self._VBB_Simu.integration_angle = float(self.simupara.integration_angle)
            self._VBB_Simu.analysis_x_ratio = float(self.simupara.x_ratio)
            self._VBB_Simu.analysis_y_ratio = float(self.simupara.y_ratio)
            self._VBB_Simu.set_wavelengths_range().start = int(self.simupara.wl_start)
            self._VBB_Simu.set_wavelengths_range().end = int(self.simupara.wl_end)
            self._VBB_Simu.set_wavelengths_range().sampling = int(self.simupara.wl_sampling)
            if self.simupara.ray_unit == "Megarays":
                self._VBB_Simu.stop_condition_ray_number = int(self.simupara.ray_value * 1e6)
            else:
                self._VBB_Simu.stop_condition_ray_number = int(self.simupara.ray_value * 1e9)
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
                raise RuntimeError("VBB Simulation Settings Error")

            # 9) calculating
            self._emit("Simulation built. Waiting to run...")
            self._built = True
  

        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self._is_success = False
            self._built = False

    def _run(self):
        try:
            if self._VBB_Simu is None:
                raise RuntimeError("No simulation available to run.")
            if self._running:
                return
            self._emit("Generating...")
            self._running = True
            self._canceled = False
            self._stop_requested = False
            self._executor = ThreadPoolExecutor(max_workers=1)
            self._future = self._executor.submit(self._VBB_Simu.compute_CPU, threads_number=self.simupara.threads_num)
            self._poll_timer.start()
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self._is_success = False
            self._finish_worker()

    @Slot()
    def _poll_run_future(self):
        if self._future is None:
            return

        if self._canceled:
            self._request_stop_computation()

        if not self._future.done():
            return

        self._poll_timer.stop()

        try:
            result_list = self._future.result()

            if self._canceled:
                raise RuntimeError("Simulation canceled by user.")

            self._emit("Getting Result...")
            copy_path_list_to_timestamp_dir(result_list, self.simupara.result_path, prefix="Result")
            self._emit("Simulation completed. Ending SPEOS service...")
            self._is_success = True
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self._is_success = False
        finally:
            self._finish_worker()

    def _finish_worker(self):
        try:
            if self._poll_timer.isActive():
                self._poll_timer.stop()
        except Exception:
            pass

        try:
            if self._executor is not None:
                self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        finally:
            self._executor = None
            self._future = None

        try:
            if self._speos is not None:
                self._speos.close()
                self._emit("Speos Service finished.")
        except Exception:
            pass

        self.finished.emit(self._is_success)
        self._speos = None
        self._canceled = False
        self._VBB_Simu = None
        self._built = False
        self._running = False
        self._stop_requested = False