
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

# params.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class speos_config:
    #Simulation
    roughness_only: bool
    #all_property: bool
    iridescence:bool
    #non_iridesense:bool
    anisotropic:bool
    bsdf_180:bool
    wl_start: float
    wl_end: float
    wl_sampling: int
    ray_unit: str               # "Megarays" or "Gigarays"
    ray_value: float
    threads_num: int           # 线程数
    #home_path:Optional[str]
    result_path:Optional[str]
    hostname: str           # "localhost" or 远端主机名
    grpc_port: int
    speos_version: str
    #Geometry
    opaque: bool
    polished: bool 
    geo_path: Optional[str]
    vop_path: Optional[str]
    sop_path: Optional[str]
    x_ratio: float
    y_ratio:float
    #Source
    sampling_mode: str          # "Adaptive sampling" / "Uniform"
    sampling_file: Optional[str]
    theta_sampling: int
    phi_sampling: int
    symmetry: str               # "none" / "x" / "xy"
    #Sensor
    sensor_RT: bool
    sensor_auto: bool
    sensor_theta_sample: int
    sensor_phi_sample: int
    integration_angle: float