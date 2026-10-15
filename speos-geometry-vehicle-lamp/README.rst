Speos vehicle lamp lit appearance workflow
==========================================

This workflow demonstrates how to import vehicle lamp CAD data, build a Speos project, and
compute the lit appearance of the lamp using PyAnsys. The CAD file is imported and tessellated
using PyAnsys Geometry, and PySpeos builds the Speos project from it. Materials, sensors, and
sources are defined by user-supplied Excel libraries and by the object names in the CAD model.
A direct simulation of the lamp and an inverse simulation of the ambient light are run on the
GPU, and their XMP results are merged into one lit-appearance result.

This workflow is meant only for demonstration purposes. It can be used as a starting point or
reference for larger custom projects.

Requirements
------------

This version is tested with Speos RPC 2026 R1 SP2, PySpeos (``ansys-speos-core``) 0.9.0, and
PyAnsys Geometry (``ansys-geometry-core``) 0.15.2. The workflow runs on Windows only. Install the
Python dependencies with:

.. code:: bash

    pip install -r requirements.txt

The workflow uses the Ansys Geometry Service for CAD import. It is installed with the Ansys
Universal Installer or as part of the Discovery installation. For more information, see the
`PyAnsys Geometry documentation <https://geometry.docs.pyansys.com/>`_.

If a SpaceClaim or Discovery license is available, you can use the geometry services of those
products instead by changing the ``mode`` argument of ``launch_modeler()``.

Running the workflow
--------------------

From this folder, start the graphical interface:

.. code:: bash

    python main_gui.py

The material, source, and sensor settings files are filled in by default from the ``SpeosModel``
folder when they exist. To run the workflow:

#. Select the CAD file. The sample model is ``SpeosModel/Rearlamp_Simulation.stp``.
#. Review the material, source, and sensor settings files, and the material library in
   ``Library/MaterialsLibrary.xlsx``.
#. Click **Import/Initialize** to import the CAD data and build the Speos project.
#. Click **Preview** to inspect the project.
#. Click **Run Direct Simulation** and **Run Inverse Simulation**.
#. Click **Merge Results** to combine both results into a single XMP file.

The scripts are organized as follows:

- ``main_gui.py``: graphical interface.
- ``PySpeos_LitAppearance_Demo.py``: CAD import, Speos project creation, simulation, and result
  merging.
- ``logger.py``: log output in the interface.
- ``plot_helper.py``: interactive face picker.
