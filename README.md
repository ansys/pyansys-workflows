# PyAnsys workflows

This repository holds examples of how to use PyAnsys to automate Ansys simulations.

## Introduction

As PyAnsys grows in adoption, we want to provide users with examples of how to use the ecosystem libraries
to automate Ansys simulations. This repository contains workflows that demonstrate how to use PyAnsys to
automate different parts of the simulation process, such as geometry creation, meshing, simulation setup and post-processing.

## Available workflows

Within this repository, users can find multiphysics examples that demonstrate how to use PyAnsys
to automate Ansys simulations. The workflows are organized by folders, each containing Python scripts
for every part of the simulation process. The available workflows are:

- [Geometry and meshing](https://github.com/ansys/pyansys-workflows/tree/main//geometry-mesh): this workflow demonstrates how to create a geometry and mesh
  it using PyAnsys. The geometry is a simple CAD structure. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For meshing: Ansys PRIME Server

- [Geometry, meshing and fluids simulation](https://github.com/ansys/pyansys-workflows/tree/main/geometry-mesh-fluent): this workflow demonstrates how to
  create a geometry, mesh it, and run a fluid simulation using PyAnsys. The geometry generated is a NACA
  airfoil, which is prepared for a fluid simulation. The exported CAD file is then consumed by Ansys Fluent
  to run a compressible flow simulation over the airfoil. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For meshing: Ansys Fluent Meshing
    - For simulation: Ansys Fluent Solver

- [Geometry, mechanical and post-processing](https://github.com/ansys/pyansys-workflows/tree/main/geometry-mechanical-dpf): this workflow demonstrates how to
  create a printed circuit board (PCB) geometry, mesh, run steady state and transient thermal analysis,
  and post-process using DPF. The geometry generated is a simple PCB with multiple chips.
  The exported CAD file (PMDB format) is then imported inside Ansys Mechanical
  to run a steady-state thermal analysis followed by transient analysis.
  All temperature results in different chips are displayed using DPF. The involved Ansys products are:
    - For geometry: Ansys SpaceClaim / Ansys Discovery / Ansys Geometry Service
    - For simulation: Ansys Mechanical
    - For post-procesing: Ansys Data Processing Framework

- [Fluent and mechanical analysis](https://github.com/ansys/pyansys-workflows/tree/main/fluent-mechanical): this workflow demonstrates how to perform a Conjugate Heat Transfer (CHT) analysis for an exhaust manifold to simulate heat transfer between solid and fluid domains, calculate heat transfer coefficients (HTCs) and temperature distribution, and export results for thermo-mechanical analysis. The thermo-mechanical assessment is then performed to evaluate the exhaust manifold's performance under thermal cycling, aiding in design optimization for durability
  The involved Ansys products are:
    - For fluids analysis: Ansys Fluent
    - For thermal analysis: Ansys Mechanical

- [Speos and optiSLang robustness analysis](https://github.com/ansys/pyansys-workflows/tree/main/speos-optislang): this workflow performs a robustness
   study to evaluate how variations in LED source power and position influence lightguide performance using PySpeos and PyOptiSLang. The analysis quantifies performance
   through key metrics such as RMS contrast, average luminance, and the number of failed regulations.
  The involved Ansys products are:
    - For optical analysis: Ansys Speos
    - For robustness analysis: Ansys optiSLang

- [Maxwell2D and Lumerical ion trap modelling](https://github.com/ansys/pyansys-workflows/tree/main/maxwell2d-lumerical): this workflow
  is fully automated and models a chip-based ion trap that incorporates optical antennas with surface electrodes.
  Ansys Maxwell computes the electrostatic response of a three-rail surface electrode design, while Ansys Lumerical retrieves the data
  from Maxwell to optimize the grating coupler design that operates as an optical antenna for tightly focused laser beams.
  For additional information, see this article:
    https://optics.ansys.com/hc/en-us/articles/20715978394131-Integrated-Ion-Traps-using-Surface-Electrodes-and-Grating-Couplers
  where multiple grating couplers can provide a platform for more complex field distributions and optical force calculation
  over various nano-objects.

## How to run the workflows

All workflows are structured in the same way, with a Python script for each part of the simulation process.
To run the workflows, users need to have Ansys installed on their machine. The setup process is the following:

1. Download the repository to your local machine:
    ```bash
    git clone https://github.com/ansys/pyansys-workflows.git
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
    python wf_gm_01_geometry.py
    python wf_gm_02_mesh.py
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
