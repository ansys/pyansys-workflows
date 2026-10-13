Speos vehicle camera simulation workflow
========================================

This workflow demonstrates how to simulate a vehicle camera in a Speos test scenario using
PyAnsys. A CAD body is imported and tessellated using PyAnsys Geometry, and added to a
pre-defined Speos scenario (.speos file) using PySpeos. A camera model is then loaded into the
scene, and an inverse simulation is run on the GPU. The result is opened in the XMP viewer.

The intended use case is automotive vehicle camera simulation within a specified test scenario,
such as FMVSS or a lab test scene. Test scenarios can be defined once in the Speos UI and then
reused by this tool, so the Speos UI is not needed after distribution.

The camera parameters are defined by an optdistortion file (currently only V1 is supported)
and by optical settings such as EFL, transmission, sensor size, and camera position. All camera
settings are specified in a JSON file.

This workflow is meant only for demonstration purposes. It can be used as a starting point or
reference for larger custom projects.

Requirements
------------

This workflow runs on Windows only and was tested with SPEOS RPC and Geometry Service backend
versions 2026R1, and with PySpeos (``ansys-speos-core``) 0.9.1 and
PyAnsys Geometry (``ansys-geometry-core``) 0.17.2. Install the Python dependencies with:

.. code:: bash

    pip install -r requirements.txt

The workflow uses the Ansys Geometry Service for CAD import. It is installed with the Ansys
Universal Installer or as part of the Discovery installation. For more information, see the
`PyAnsys Geometry documentation <https://geometry.docs.pyansys.com/>`_.

If a SpaceClaim or Discovery license is available, you can use the geometry services of those
products instead by changing the ``mode`` argument of ``launch_modeler()``.

The Geometry Service uses port 50051. The Speos RPC server is launched on port 50098 so that
the two do not conflict.

Input data
----------

The ``simulation_data`` folder contains the inputs:

- ``scenario``: one folder per test scenario, each with a .speos file.
- ``camera``: one folder per camera model, each with a ``Camera_Sensor.json`` file and the
  distortion, transmittance, and spectrum files that it references.
- ``cad``: the material used for the imported CAD bodies.
- ``Pyspeos_Simulation_Results``: the output folder for simulation results.

Running the workflow
--------------------

Start the graphical interface from any folder:

.. code:: bash

    python main_gui.py

To run the workflow:

#. Optionally select a CAD file, and click **Import CAD and Tessellate**.
#. Select a test scenario and a camera model.
#. Click **Load Scenario** to build the Speos project.
#. Click **Load Camera Sensor** to add the selected camera to the scene.
#. Click **Preview Simulation** to inspect the project.
#. Click **Run Simulation**, and then **Open Results** to view the XMP result.

The scripts are organized as follows:

- ``main_gui.py``: graphical interface.
- ``CameraSimulation_PySpeos_Demo.py``: CAD import, scenario and camera loading, and simulation.
