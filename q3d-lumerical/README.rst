Q3D and Lumerical
========================

Surface electrodes adjacent to grating couplers render an integrated ion trap.
This workflow uses Ansys Q3D to model surface electrodes and Ansys Lumerical to model grating couplers. Using the boundary element method, the Q3D CG solver evaluates the ion trap height. The workflow then passes the coordinates of the ion trap to an optimization
algorithm to define the optimal two-dimensional grating coupler design, which focuses the laser
beam at the ion trap height.This is 3D-BEM version of the example: https://workflows.docs.pyansys.com/examples/maxwell2d-lumerical/wf_ml_01_ion_trap_modelling.html

This `article <https://optics.ansys.com/hc/en-us/articles/20715978394131-Integrated-Ion-Traps-using-Surface-Electrodes-and-Grating-Couplers>`_ describes the workflow in details.


