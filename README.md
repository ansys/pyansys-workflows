# PyAnsys workflows

This repository holds examples of how to use PyAnsys to automate Ansys simulations.

Table of contents:
- [Introduction](#introduction)
- [Available workflows](#available-workflows)
- [How to run the workflows](#how-to-run-the-workflows)
- [Ansys versions supported](#ansys-versions-supported)
- [Contributing](#contributing)

## Introduction

As PyAnsys grows in adoption, we want to provide users with examples of how to use the ecosystem libraries
to automate Ansys simulations. This repository contains workflows that demonstrate how to use PyAnsys to
automate different parts of the simulation process, such as geometry creation, meshing, simulation setup and post-processing.

## Available workflows

Within this repository, users can find multiphysics examples that demonstrate how to use PyAnsys
to automate Ansys simulations. The workflows are organized by folders, each containing Python scripts
for every part of the simulation process. The available workflows are:

- [Geometry and meshing](./geometry-mesh): this workflow demonstrates how to create a geometry and mesh
  it using PyAnsys. The geometry is a simple CAD structure. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For meshing: Ansys PRIME Server

- [Geometry, meshing and fluids simulation](./geometry-mesh-fluent): this workflow demonstrates how to
  create a geometry, mesh it, and run a fluid simulation using PyAnsys. The geometry generated is a NACA
  airfoil, which is prepared for a fluid simulation. The exported CAD file is then consumed by Ansys Fluent
  to run a compressible flow simulation over the airfoil. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For meshing: Ansys Fluent Meshing
    - For simulation: Ansys Fluent Solver
- [Geometry, mechanical and post-processing](./geometry-mechanical-dpf): this workflow demonstrates how to
  create a printed circuit board (PCB) geometry, mesh, run steady state and transient thermal analysis,
  and post-process using DPF. The geometry generated is a simple PCB with multiple chips.
  The exported CAD file (PMDB format) is then imported inside Ansys Mechanical
  to run a steady-state thermal analysis followed by transient analysis.
  All temperature results in different chips are displayed using DPF. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For simulation: Ansys Mechanical
    - For post-procesing: Ansys Data Processing Framework

## How to run the workflows

All workflows are structured in the same way, with a Python script for each part of the simulation process.
To run the workflows, users need to have Ansys installed on their machine. The setup process is the following:

1. Download the repository to your local machine:
    ```bash
    git clone https://github.com/ansys-internal/pyansys-workflows.git
    ```

2. Navigate to the desired workflow folder:
    ```bash
    # For example...
    cd pyansys-workflows/geometry-mesh
    ```

3. Create a virtual environment and install the required packages:
    ```bash
    python -m venv .venv

    # On Linux / MacOS
    source venv/bin/activate

    # On Windows
    .venv\Scripts\activate
    ```

4. Depending on the Ansys version you have installed, select the appropriate requirements file to install:
    - For Ansys 2024 R1:
        ```bash
        pip install -r requirements_24.1.txt
        ```

    - For Ansys 2024 R2:
        ```bash
        pip install -r requirements_24.2.txt
        ```

5. Run the Python scripts in the expected order. For example, to run the geometry and meshing workflow:
    ```bash
    python 01_geometry.py
    python 02_mesh.py
    ```

    The scripts will generate the geometry and mesh files in the `outputs` folder. This behavior is consistent
    across all workflows.

## Ansys versions supported

The workflows in this repository are tested with the following Ansys releases:

- Ansys 2024 R1
- Ansys 2024 R2

Each workflow is ran on our CI/CD pipelines to ensure compatibility with the supported Ansys versions.

## Contributing

This repository is open for contributions. If you have a workflow that you would like to share with the community,
please open a pull request with the new content. The workflow should be organized in a similar way to the existing
ones, with Python scripts for each part of the simulation process.
