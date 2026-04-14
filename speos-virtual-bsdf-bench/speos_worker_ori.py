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
This is an backlog of SPEOS worker implementation.
"""
# worker.py
from __future__ import annotations
from typing import Optional
from dataclasses import asdict
from PySide6.QtCore import QObject, Signal, Slot, QStandardPaths
import pyvista as pv
import traceback
from ansys.speos.core import project,launcher,speos
from ansys.speos.core.simulation import SimulationVirtualBSDF
from setup_data import speos_config
from toolfunction import copy_path_list_to_timestamp_dir
class sim_worker(QObject):
    
    progress = Signal(str)         # 若能获得进度（server stream 或循环）
    error = Signal(str)            # 失败文本
    finished = Signal(bool)      # 成功完成，附带返回信息（如结果路径等）

    @Slot(speos_config)
    def speos_start(self, params: speos_config):
        """collect params from Ui then run。"""
        self._run(params)
    @Slot()
    def speos_cancel(self):
        """recieve UI cancel request。"""
        self._canceled = True
        self._emit("Cancel request received...")
        try:
            if self._speos is not None:
                self._speos.close()  # 若 compute_CPU 可被打断，将尽快返回
                print("toggled cancel")
            else:
                self._emit("No Job running...")
        except Exception:
            pass
    
    def __init__(self):
        super().__init__()
        self._speos = None
        self._canceled = False
    @Slot(object)
    def _run(self, p: speos_config):
        try:
            # 1) read STL
            self._emit("Loading geometry...")
            import pyvista as pv
            mesh = pv.read(p.geo_path)
            mesh_center = mesh.center
            vertices = mesh.points
            vertex_normals = mesh.point_normals
            faces = mesh.faces.reshape((-1, 4))[:, 1:]
            #self._check_cancel()

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
                    self._speos = launcher.launch_remote_speos(version=p.speos_version)
                except:
                    raise RuntimeError("Can not launch remote Speos RPC server")
            #self._check_cancel()

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
            self._check_cancel()

            # 5) Simulation Mode and Object
            self._emit("Setting Simulation Mode...")
            VBB_Simu = VBB_Proj.create_simulation(
                name="virtual_bsdf", feature_type=SimulationVirtualBSDF
            )

            if p.roughness_only:
                if p.sampling_mode == "Adaptive sampling":
                    VBB_Simu.set_mode_roughness_only().set_adaptive().adaptive_uri = p.sampling_file
                elif p.sampling_mode == "Uniform":
                    VBB_Simu.set_mode_roughness_only().set_uniform().theta_sampling = p.theta_sampling
                else:
                    raise RuntimeError("Unexpected Unpolished Sampling Error.")
            else:
                VBB_Simu.set_mode_all_characteristics().is_bsdf180 = p.bsdf_180

                if p.iridescence:
                    if p.sampling_mode == "Adaptive sampling":
                        VBB_Simu.set_mode_all_characteristics().set_iridescence().set_adaptive().adaptive_uri = p.sampling_file
                    elif p.sampling_mode == "Uniform":
                        VBB_Simu.set_mode_all_characteristics().set_iridescence().set_uniform().theta_sampling = p.theta_sampling 
                    else:
                        raise RuntimeError("Unexpected sampling mode.")
                else:
                    if p.anisotropic:
                        if p.sampling_mode == "Adaptive sampling":
                            VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_adaptive().adaptive_uri = p.sampling_file
                        elif p.sampling_mode == "Uniform":
                            VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().theta_sampling = p.theta_sampling
                            VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().phi_sampling = p.phi_sampling
                            if p.symmetry == "none":
                                VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_none()
                            elif p.symmetry == "x":
                                VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_1_plane_symmetric()
                            else:
                                VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_uniform().set_symmetric_2_plane_symmetric()
                        else:
                            raise RuntimeError("Unexpected sampling mode.")
                    else:
                        if p.sampling_mode == "Adaptive sampling":
                            VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_adaptive().adaptive_uri = p.sampling_file
                        elif p.sampling_mode == "Uniform":
                            VBB_Simu.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_uniform().theta_sampling = p.theta_sampling
                        else:
                            raise RuntimeError("Unexpected sampling mode.")

                VBB_Simu.set_mode_all_characteristics().reflection_and_transmission = p.sensor_RT

            # 6) sensor
            if p.sensor_auto:
                VBB_Simu.set_sensor_sampling_automatic()
            else:
                VBB_Simu.set_sensor_sampling_uniform().theta_sampling = p.sensor_theta_sample 
                VBB_Simu.set_sensor_sampling_uniform().phi_sampling = p.sensor_phi_sample


            # 7) other parameters
            VBB_Simu.integration_angle = float(p.integration_angle)
            VBB_Simu.analysis_x_ratio = float(p.x_ratio)
            VBB_Simu.analysis_y_ratio = float(p.y_ratio)
            VBB_Simu.set_wavelengths_range().start = int(p.wl_start)
            VBB_Simu.set_wavelengths_range().end = int(p.wl_end)
            VBB_Simu.set_wavelengths_range().sampling = int(p.wl_sampling)
            if p.ray_unit == "Megarays":
                VBB_Simu.stop_condition_ray_number = int(p.ray_value * 1e6)
            else:
                VBB_Simu.stop_condition_ray_number = int(p.ray_value * 1e9)
            VBB_Simu.axis_system = [
                mesh_center[0], mesh_center[1], 0.0,
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0,
            ]
            VBB_Simu.threads_number = int(p.threads_num)
            try:
                VBB_Simu.commit()
            except:
                raise RuntimeError("Something wrong during Simulation Settings")

            self._check_cancel()

            # 8) calculating
            self._emit("Generating...")
            result_list = VBB_Simu.compute_CPU()   # 阻塞调用，在线程内执行
            self._check_cancel()

            # 9) 复制结果
            self._emit("Getting Result...")
            copy_path_list_to_timestamp_dir(result_list, p.result_path, prefix="Result")
            #homepath: str = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
            #src = os.path.join(homepath, r"AppData/Local/Temp/jobs")
            #out_dir = p.result_dir
            #dst_path = copy_latest_subdir_overwrite(src, out_dir, ignore_names={}, follow_symlinks=False)

            self._emit("Simulation completed.")
            self.finished.emit(True)

        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self.finished.emit(False)
        finally:
            try:
                if self._speos is not None:
                    self._speos.close()
                    self._emit("Simulation finished.")
            except Exception:
                pass

    def _emit(self, msg: str):
        self.progress.emit(msg)

    def _check_cancel(self):
        if self._canceled:
            raise RuntimeError("Simulation canceled by user.")
