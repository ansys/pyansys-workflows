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

import time

import pyvista as pv
from pyvista.plotting.opts import PickerType
from pyvistaqt import BackgroundPlotter


def plot_picker(faces_blocks, faces):
    selected_face_id = {"value": None}

    def add_block(block, face):
        if isinstance(block, pv.MultiBlock):
            for sub in block:
                add_block(sub, face)
        else:
            block.field_data["id"] = face.id
            pl.add_mesh(block)

    def pick_callback(picked):
        if picked is None:
            return

        for name in ["selection", "selection-label", "face-highlight"]:
            try:
                pl.remove_actor(name, reset_camera=False)
            except:
                pass

        boundary = picked.extract_feature_edges(
            boundary_edges=True,
            feature_edges=False,
            manifold_edges=False,
        )
        pl.add_mesh(boundary, color="magenta", name="selection", pickable=False)

        pl.add_mesh(
            picked.copy(),
            color="orange",
            opacity=0.5,
            name="face-highlight",
            pickable=False,
        )

        try:
            fid = picked.field_data["id"]
            selected_face_id["value"] = fid
            text = f"Face ID: {fid}"
        except Exception:
            text = "Cannot extract info"

        pt = pl.picked_point
        pl.add_point_labels(
            [pt],
            [text],
            name="selection-label",
            always_visible=True,
            point_size=10,
            render_points_as_spheres=True,
        )

    def confirm_selection():
        pl.close()

    pv.global_theme.color_cycler = "default"

    # IMPORTANT CHANGE
    pl = BackgroundPlotter(show=True)

    for block, face in zip(faces_blocks, faces):
        add_block(block, face)

    pl.enable_mesh_picking(
        picker=PickerType.HARDWARE,
        show=False,
        callback=pick_callback,
    )

    pl.add_key_event("Return", confirm_selection)
    pl.add_key_event("KP_Enter", confirm_selection)

    # WAIT until the window closes
    while pl.app_window is not None and pl.app_window.isVisible():
        time.sleep(0.05)

    return selected_face_id["value"]
