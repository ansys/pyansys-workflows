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
from __future__ import annotations
import shutil
import time
from pathlib import Path
#import Exception
class NoResultError(Exception):
    def __init__(self,ErrorInfo):
        super().__init__(self)
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorInro

def copy_path_list_to_timestamp_dir(
    data: tuple,
    dst_root: str | Path,
    *,
    prefix: str | None = None,
) -> Path:
    """
    Handles only one case:
    data is of type tuple[list[Result], list[Path]]

    Copies all files in the second element (list[Path]) into a newly created
    timestamp-named subdirectory under dst_root, to avoid name collisions.
    """

    # Extract list[Path] (second element of the tuple)

    # Normalize all paths to Path objects
    #if data is None:
    #    raise NoResultError("No result generated") 
    paths: list[Path] = [Path(data[0].path),Path(data[1].path)] # elements in data is a Result class


    # Create a unique timestamp-based subdirectory
    dst_root = Path(dst_root)

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    dir_name = f"{prefix + '_' if prefix else ''}{timestamp}"
    dst_dir = dst_root / dir_name
    dst_dir.mkdir(parents=True, exist_ok=False)

    # Copy files (only existing regular files)
    for p in paths:
        if p.is_file():
            shutil.copy2(p, dst_dir)
        else:
            print(f"[Skipped] File does not exist or is not a regular file: {p}")

    return dst_dir
