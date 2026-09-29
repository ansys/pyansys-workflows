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

log_widget = None
tk_master = None


def init_logger(master, widget):
    global tk_master, log_widget
    tk_master = master
    log_widget = widget


def log_message(msg):
    if log_widget is None:
        return
    log_widget.config(state="normal")
    log_widget.insert("end", msg + "\n")
    log_widget.config(state="disabled")
    log_widget.see("end")
    log_widget.update_idletasks()


def log_progress_inline(percent):
    if log_widget is None:
        return

    bar_len = 40
    filled = int(bar_len * percent / 100)
    bar = "#" * filled + "-" * (bar_len - filled)
    text = f"[{bar}] {percent:.1f}%"

    log_widget.config(state="normal")

    # delete previous progress line
    log_widget.delete("end-2l", "end-1l")
    log_widget.insert("end", text + "\n")

    log_widget.config(state="disabled")
    log_widget.see("end")
    log_widget.update_idletasks()


def force_update():
    if tk_master:
        tk_master.update()
