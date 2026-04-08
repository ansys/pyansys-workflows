This version is tested with Speos RPC 2025R2 SP4, 
PySpeos (ansys-speos-core) version 0.7.2,
and PyAnsys Geometry (ansys-geometry-core) version 0.15.1.

This tool is meant only for demonstration purposes. 
It can be used as a starting point or reference for larger custom projects.

This tool utilizes the ansys geometry interface for CAD import, which can be 
installed from the ansys universal installer or as a part of the Discovery installation.
More information can be found here:
https://geometry.docs.pyansys.com/version/0.6/getting_started/faq.html#how-is-the-ansys-geometry-service-installed

Alternatively, if a Spaceclaim or Discovery license is available, the geometry services of those tools can be implemented
instead of the ansys geometry service (by changing the "mode" flag of launch_modeler(mode=))
