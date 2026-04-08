This example tool imports a CAD body into a pre-defined speos scene (.speos file), 
loads a user-specified camera model into the scene, and runs an inverse simulation.

The tool utilizes ansys-geometry-core for the CAD import and tessellation.
It utilizes ansys-speos-core for loading the pre-defined .speos scenario model, 
and building and running the optical simulation.
It also utilizes the speos labs APIs for loading results.

The intended use case for this demo is for automotive vehicle camera simulation within a
specified test scenario, such as FMVSS or a lab test scene. Test scenario(s) can be pre-defined
once in the Speos UI, and then re-used by this tool, bypassing Speos UI usage after distribution.

The camera parameters are defined by an optdistortion file (currently only V1 is supported), and by 
specifying necessary optical settings such as EFL, transmission, sensor size, camera position, etc.
All camera settings are specified by a JSON file.

This version is tested with Speos RPC 2025R2 SP4, 
PySpeos (ansys-speos-core) version 0.7.2,
and PyAnsys Geometry (ansys-geometry-core) version 0.15.1.

This tool is meant only for demonstration purposes. 
It can be used as a starting point or reference for larger custom projects.