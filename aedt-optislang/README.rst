AEDT and optiSLang
==================

This workflow demonstrates how to combine PyAEDT and pyOptiSLang to run a parametric
AMOP (Adaptive Meta-model of Optimal Prognosis) study on a dipole antenna in HFSS.
optiSLang's ProxySolver node is used to process the designs. Parallel design evaluations
are managed via ``process_map``. The AMOP system automatically creates a MOP (Meta-Model
of Optimal Prognosis), which is then used in a subsequent MOP-Solver based optimization
system as well as a validation system.
