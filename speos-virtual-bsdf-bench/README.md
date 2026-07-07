# Speos Virtual BSDF Bench (VBB)

Speos Virtual BSDF Bench is a desktop GUI tool for configuring and running Virtual BSDF simulations with PyAnsys Speos.
It provides a workflow to:

- Load geometry (STL) or an existing SPEOS LightBox scene.
- Configure material and simulation modes.
- Build, preview, run, and cancel simulation jobs.
- Export simulation results into timestamped output folders.

## Requirements

### System Requirements

- OS: Windows (recommended and currently validated environment).
- Python: 3.10+
- Ansys Speos installation compatible with your selected RPC version.
- Valid Speos license and local RPC availability.

### Python Dependencies

Project dependencies are defined in `pyproject.toml`:

- `ansys-speos-core>=0.9.0`
- `pyside6>=6.11.1`
- `pyvista>=0.47.3`

Development dependency:

- `pyinstaller>=6.20.0`

## Core Features

- Graphical configuration for Virtual BSDF simulation settings.
- Multiple simulation modes:
	- Roughness only
	- All characteristics
	- Iridescent / non-iridescent
	- Anisotropic / isotropic
	- BSDF 180 option
- Source sampling:
	- Uniform sampling
	- Adaptive sampling from file
- Sensor options:
	- Automatic sampling
	- Custom theta/phi sampling
	- Reflection only or reflection + transmission
- Geometry input options:
	- Direct STL geometry import
	- SPEOS LightBox loading
- Job control:
	- Build simulation
	- Preview project
	- Run simulation
	- Cancel running simulation
- Output management:
	- Result files are copied into a timestamped folder under the selected destination path.

## Installation

### Option 1: Using `uv` (recommended)

```powershell
uv sync
```

### Option 2: Using `pip`

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## How to Run

From the project root:

```powershell
python main.py
```

This opens the VBB GUI.

## Usage Guide

1. Open the tool.
2. In the Simulation tab, configure:
	 - mode (roughness/all properties)
	 - wavelength range and sampling
	 - ray count and unit
	 - thread count
	 - output folder
	 - SPEOS RPC settings (version and port)
3. In the Geometry tab, choose one input flow:
	 - STL + optical properties, or
	 - LightBox file
4. Configure Source and Sensor sampling settings.
5. Click **Build** to prepare the simulation.
6. (Optional) Click **Preview** to inspect the built project.
7. Click **Run** to execute the simulation.
8. If needed, click **Stop** to cancel.
9. Check the selected output folder for a new timestamped result directory.

## Notes

- The tool currently uses `localhost` for SPEOS RPC in the main UI flow.
- Ensure the configured SPEOS version and port match your local environment.
- If build/run fails, check input paths (geometry/material/sampling files) and RPC availability.

## Packaging (Optional)

If you need a standalone executable for internal use, use PyInstaller with the provided spec files (for example `main.spec`).

Example:

```powershell
uv run pyinstaller main.spec
```

## Project Structure (Key Files)

- `main.py`: GUI entry point and user interactions.
- `speos_worker.py`: Background worker for build/run/cancel workflow.
- `setup_data.py`: Dataclass for simulation configuration payload.
- `toolfunction.py`: Result copy utilities.
- `vbbui_designer.py`: Generated Qt UI bindings.

## License

This project includes MIT-licensed source headers in core files.
