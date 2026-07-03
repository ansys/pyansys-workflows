# /// script
# requires-python = "==3.12"
# dependencies = [
#     "ansys-optislang-core>0.7.0",
#     "pyaedt[all]>1.1.0"
# ]
# ///
# # Parametric AMOP design study with optiSLang ProxySolver and PyAEDT
#
# This example shows how to combine PyAEDT and pyOptiSLang to run a parametric
# AMOP study on a dipole antenna in HFSS. optiSLang's ProxySolver node
# is used to process the designs. Parallel design evaluations are managed via 
# process_map. The AMOP system automatically creates a MOP, which is then used
# in a subsequent MOP-Solver based optimization system.
#
# Ways to run this script:
# * Open as a Jupytext notebook (requires installation of Jupyter).
# * Run with `uv run pyaedt_optislang_study.py` (requires installation of uv).
# * Create a virtual environment and install requirements from requirements file, then run this script.
# 
# Software requirements:
# - Ansys optiSLang version 2026 R1 or later.
# - Ansys Electronics Desktop version 2026 R1 or later.
#
# Python package requirements:
# - ansys-aedt-core version 1.1.0 or later.
# - ansys-optislang-core version 0.7.0 or later.
#
# Keywords: **AEDT**, **HFSS**, **optiSLang**, **parametric**, **ProxySolver**, **AMOP**

# ## Perform imports and define constants
#
# Import the required packages.

# +
import logging
import math
import os
import pathlib
import sys
import tempfile
import time

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map as concurrent_map

from ansys.aedt.core import Hfss
from ansys.optislang.core import Optislang
import ansys.optislang.core.node_types as node_types
from ansys.optislang.core.nodes import DesignFlow
from ansys.optislang.core.project_parametric import (
    OptimizationParameter,
    Response,
    ResponseValueType,
    Design,
    DesignVariable,
    ObjectiveCriterion,
    ComparisonType,
)

# Convenience imports for building the optiSLang workflow graph.
from ansys.optislang.parametric.design_study import ParametricDesignStudyManager
from ansys.optislang.parametric.design_study_templates import (
    GeneralAlgorithmSettings,
    GeneralAlgorithmTemplate,
    OptimizationOnMOPTemplate,
    ProxySolverNodeSettings,
)


# -

# ## Define constants.
#
# **Take note:** Jupyters execution model does not work well with multiprocessing.
# When executing from within Jupyter, please set `MAX_PARALLEL_SOLVE_PROCESSES = 1`, 
# otherwise the process will fail.
# When executed outside of Jupyter, `MAX_PARALLEL_SOLVE_PROCESSES` can be increased,
# as long as `NUM_CORES_PER_JOB * MAX_PARALLEL_SOLVE_PROCESSES` does not exceed the
# number of available cores.

AEDT_VERSION = "2026.1"
NUM_CORES_PER_PROCESS = 2
NG_MODE = True # HFSS jobs run non-graphically (headless) to support parallel execution.
MAX_PARALLEL_SOLVE_PROCESSES = 3
FORCE_SEQUENTIAL_SOLVE = False   # Set to True to force sequential execution even outside of Jupyter, for testing and debugging.
AEDT_WORKING_DIRNAME = "pyaedt_workingdir"
SOLVE_MODE = "HFSS"  # Set to "DUMMY" to run without an HFSS license, for testing purposes.

MOP_CUSTOM_SETTINGS = {
    "competition_signal_model" : 
    {
        "header" : 0,
        "sequence" : 
        [
            {
                "First" : "number_of_folds",
                "Second" : 3
            },
            {
                "First" : "use_subspace_filtering",
                "Second" : True
            },
            {
                "First" : "models",
                "Second" : 
                [
                    {
                        "Config" : {},
                        "Display Name" : "Baseline",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "CreateBaseLineModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "VeryLow"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "nD",
                        "Short Name" : "Baseline",
                        "Used" : True,
                        "Version" : 1
                    },
                    {
                        "Config" : 
                        {
                            "max_num_shapes" : 
                            {
                                "Display Name" : "Maximum number of sub-space coefficients",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 50
                            },
                            "modeling_algo" : 
                            {
                                "Display Name" : "Sub-space modeling algorithm",
                                "Multiplicity" : "Singleton",
                                "Range" : [ "RBF", "Scalar MOP" ],
                                "Type" : "ModelingAlgoType",
                                "Value" : "Scalar MOP"
                            }
                        },
                        "Display Name" : "PCA-based Subspace Modeling",
                        "License" : False,
                        "License Capability" : "AI+",
                        "Name" : "CreateRSMModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : 
                                        {
                                            "Max" : 1.7976931348623157e+308,
                                            "Min" : 2.2250738585072014e-308
                                        },
                                        "Type" : "Real",
                                        "Value" : 2
                                    }
                                },
                                "Display Name" : "Coefficient factor",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "CoefficientFactorProperty",
                                "Version" : 1
                            },
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "High"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            },
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : 
                                        {
                                            "Max" : 1,
                                            "Min" : 0
                                        },
                                        "Type" : "Real",
                                        "Value" : 0.001
                                    }
                                },
                                "Display Name" : "Error tolerance parameter",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "DeltaErrorInputProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "Signal",
                        "Short Name" : "PCA-SM",
                        "Used" : True,
                        "Version" : 1
                    },
                    {
                        "Config" : 
                        {
                            "batchSize" : 
                            {
                                "Display Name" : "Batch size (0=No batch)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 0
                            },
                            "channelCrossCorrelation" : 
                            {
                                "Display Name" : "Channel cross-correlation",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "encodeMethodY" : 
                            {
                                "Display Name" : "Output compression method",
                                "Multiplicity" : "Singleton",
                                "Range" : [ "PCA", "AE (Beta)", "GAE (Beta)", "KPCA (Beta)" ],
                                "Type" : "String",
                                "Value" : "PCA"
                            },
                            "jobSubmitPattern" : 
                            {
                                "Display Name" : "Job submit pattern (Beta)",
                                "Multiplicity" : "Singleton",
                                "Range" : None,
                                "Type" : "String",
                                "Value" : "<jobscript> <arg1> <arg2> <arg3>"
                            },
                            "maxEpochs" : 
                            {
                                "Display Name" : "Maximum epochs",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 1000
                            },
                            "noisyData" : 
                            {
                                "Display Name" : "Noisy data",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "numberOfThreads" : 
                            {
                                "Display Name" : "Number of threads",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 2
                            },
                            "signalTransformation" : 
                            {
                                "Display Name" : "Signal transformation",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            }
                        },
                        "Display Name" : "Deep Infinite Mixture Gaussian Process (Signal)",
                        "ID" : "CreateDIMGPFieldModel",
                        "Interface Name" : "CreateDIMGPFieldModel",
                        "License" : False,
                        "License Capability" : "AI+",
                        "Name" : "CreateCustomModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "Custom"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "Signal",
                        "Short Name" : "DIMGP",
                        "Used" : False,
                        "Version" : 1
                    },
                    {
                        "Config" : 
                        {
                            "batchSize" : 
                            {
                                "Display Name" : "Batch size",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 32
                            },
                            "disableCV" : 
                            {
                                "Display Name" : "Disable Cross-validation",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "numEpochs" : 
                            {
                                "Display Name" : "Number of epochs",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 100
                            },
                            "numUnits" : 
                            {
                                "Display Name" : "Number of units",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 128
                            },
                            "seed" : 
                            {
                                "Display Name" : "Seed",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 7
                            }
                        },
                        "Display Name" : "LSTM Neural Network",
                        "ID" : "CreateLSTMNNModel",
                        "Interface Name" : "CreateLSTMNNModel",
                        "License" : False,
                        "License Capability" : "AI+",
                        "Name" : "CreateCustomModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "Custom"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "Signal",
                        "Short Name" : "LSTMNN",
                        "Used" : False,
                        "Version" : 1
                    },
                    {
                        "Config" : 
                        {
                            "applyOutputReduction" : 
                            {
                                "Display Name" : "Apply output reduction (Beta)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "batchSize" : 
                            {
                                "Display Name" : "Batch size",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 256
                            },
                            "disableCV" : 
                            {
                                "Display Name" : "Disable Cross-validation",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "numComponents" : 
                            {
                                "Display Name" : "Number of PCA components (Beta)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 50
                            },
                            "numEpochs" : 
                            {
                                "Display Name" : "Number of epochs",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 100
                            },
                            "numLayers" : 
                            {
                                "Display Name" : "Number of layers",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 6
                            },
                            "numNeurons" : 
                            {
                                "Display Name" : "Number of neurons",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 64
                            },
                            "seed" : 
                            {
                                "Display Name" : "Seed",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 7
                            }
                        },
                        "Display Name" : "Index Neural Network",
                        "ID" : "CreateIndexNNModel",
                        "Interface Name" : "CreateIndexNNModel",
                        "License" : False,
                        "License Capability" : "AI+",
                        "Name" : "CreateCustomModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "Custom"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "Signal",
                        "Short Name" : "IndexNN",
                        "Used" : True,
                        "Version" : 1
                    },
                    {
                        "Config" : 
                        {
                            "batchSize" : 
                            {
                                "Display Name" : "Batch size",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 32
                            },
                            "disableCV" : 
                            {
                                "Display Name" : "Disable cross-validation",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            },
                            "futureWindow" : 
                            {
                                "Display Name" : "Future window (0 for auto)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 0
                            },
                            "numEpochs" : 
                            {
                                "Display Name" : "Number of epochs",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 200
                            },
                            "numLayers" : 
                            {
                                "Display Name" : "Number of layers",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 10
                            },
                            "numNeurons" : 
                            {
                                "Display Name" : "Number of neurons",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 128
                            },
                            "pastWindow" : 
                            {
                                "Display Name" : "Past window (0 for auto)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 0
                            },
                            "seed" : 
                            {
                                "Display Name" : "Seed",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : 4294967295,
                                    "Min" : 0
                                },
                                "Type" : "UInteger",
                                "Value" : 7
                            },
                            "smartLayout" : 
                            {
                                "Display Name" : "Smart layout (Ignore hyperparameters)",
                                "Multiplicity" : "Singleton",
                                "Range" : 
                                {
                                    "Max" : True,
                                    "Min" : False
                                },
                                "Type" : "Boolean",
                                "Value" : False
                            }
                        },
                        "Display Name" : "Contextual Recursive Temporal Approximation",
                        "ID" : "CreateCortexModel",
                        "Interface Name" : "CreateCortexModel",
                        "License" : False,
                        "License Capability" : "AI+",
                        "Name" : "CreateCustomModel",
                        "Properties" : 
                        [
                            {
                                "Config" : 
                                {
                                    "value" : 
                                    {
                                        "Display Name" : "Value",
                                        "Multiplicity" : "Singleton",
                                        "Range" : [ "VeryLow", "Low", "Medium", "High", "VeryHigh", "Custom", "Undefined" ],
                                        "Type" : "ModelComplexity",
                                        "Value" : "Custom"
                                    }
                                },
                                "Display Name" : "Complexity",
                                "License" : False,
                                "License Capability" : "Pro",
                                "Name" : "ComplexityProperty",
                                "Version" : 1
                            }
                        ],
                        "Response Type" : "Signal",
                        "Short Name" : "Cortex",
                        "Used" : False,
                        "Version" : 1
                    }
                ]
            },
            {
                "First" : "quality_measures",
                "Second" : 
                [
                    {
                        "Config" : {},
                        "Display Name" : "Variance Averaged CoP",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "FCoPStationary",
                        "Version" : 1
                    },
                    {
                        "Config" : {},
                        "Display Name" : "Simple Averaged CoP",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "FCoPMean",
                        "Version" : 1
                    }
                ]
            },
            {
                "First" : "active_quality_measure_index",
                "Second" : 0
            },
            {
                "First" : "sensitivity_analyzers",
                "Second" : 
                [
                    {
                        "Config" : {},
                        "Display Name" : "No sensitivity Analysis",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "NoAnalyzer",
                        "Version" : 1
                    },
                    {
                        "Config" : {},
                        "Display Name" : "Sobol (Low)",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "FastSobolAnalyzer",
                        "Version" : 1
                    },
                    {
                        "Config" : {},
                        "Display Name" : "Sobol (High)",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "AccurateSobolAnalyzer",
                        "Version" : 1
                    },
                    {
                        "Config" : {},
                        "Display Name" : "Sobol (Auto)",
                        "License" : False,
                        "License Capability" : "Pro",
                        "Name" : "AutoSobolAnalyzer",
                        "Version" : 1
                    }
                ]
            },
            {
                "First" : "active_sensitivity_analyzer_index",
                "Second" : 3
            }
        ]
    },
    "custom_SoS" : 
    {
        "header" : 0,
        "sequence" : 
        [
            {
                "First" : "Maximum number of coefficients in Field-MOP",
                "Second" : 50
            },
            {
                "First" : "Use fast mode for Field-MOP creation",
                "Second" : 
                {
                    "bool" : False,
                    "kind" : 
                    {
                        "enum" : 
                        [
                            "uninitialized",
                            "bool",
                            "scalar",
                            "vector",
                            "matrix",
                            "signal",
                            "xydata"
                        ],
                        "value" : "bool"
                    }
                }
            },
            {
                "First" : "Create Random Field",
                "Second" : 
                {
                    "bool" : False,
                    "kind" : 
                    {
                        "enum" : 
                        [
                            "uninitialized",
                            "bool",
                            "scalar",
                            "vector",
                            "matrix",
                            "signal",
                            "xydata"
                        ],
                        "value" : "bool"
                    }
                }
            },
            {
                "First" : "Treat multiple signal channels cross-correlated",
                "Second" : 
                {
                    "bool" : True,
                    "kind" : 
                    {
                        "enum" : 
                        [
                            "uninitialized",
                            "bool",
                            "scalar",
                            "vector",
                            "matrix",
                            "signal",
                            "xydata"
                        ],
                        "value" : "bool"
                    }
                }
            },
            {
                "First" : "Minimum point-wise F-CoP for variable filtering [%]",
                "Second" : 5
            },
            {
                "First" : "Minimum average F-CoP for variable filtering [%]",
                "Second" : 1
            },
            {
                "First" : "Write algorithm messages to log file",
                "Second" : 
                {
                    "bool" : True,
                    "kind" : 
                    {
                        "enum" : 
                        [
                            "uninitialized",
                            "bool",
                            "scalar",
                            "vector",
                            "matrix",
                            "signal",
                            "xydata"
                        ],
                        "value" : "bool"
                    }
                }
            }
        ]
    },
    "dimgp_field_model" : 
    {
        "header" : 0,
        "sequence" : 
        [
            {
                "First" : "Maximum epochs",
                "Second" : 1000
            },
            {
                "First" : "Batch size (0=No batch)",
                "Second" : 0
            },
            {
                "First" : "Noisy data",
                "Second" : False
            },
            {
                "First" : "Basic_Settings",
                "Second" : True
            },
            {
                "First" : "encode_method_X",
                "Second" : 0
            },
            {
                "First" : "encode_method_Y",
                "Second" : 0
            },
            {
                "First" : "Job submit pattern (Beta)",
                "Second" : "<jobscript> <arg1> <arg2> <arg3>"
            },
            {
                "First" : "Signal_Transformation",
                "Second" : False
            },
            {
                "First" : "Channel_Cross_Correlation",
                "Second" : True
            },
            {
                "First" : "Number of threads",
                "Second" : 2
            }
        ]
    }
}


# ## Define HFSS solver function
#
# The ``solve_hfss()`` function creates and solves a dipole antenna model in HFSS
# for a given set of design parameters, exports the return loss to a CSV file,
# and returns the result as a NumPy array.
# Each call runs in its own HFSS desktop instance and releases it when done.
#
# > **Note:** This function must remain a module-level definition so that
# > ``multiprocessing.Pool`` can pickle it for parallel dispatch.


def solve_hfss(working_dir, l_dipole, wire_rad, port_gap):
    project_name = os.path.join(working_dir, "dipole.aedt")
    hfss = Hfss(
        version=AEDT_VERSION,
        non_graphical=NG_MODE,
        project=project_name,
        new_desktop=True,
        solution_type="Modal",
    )

    hfss["l_dipole"] = f"{l_dipole}cm"
    hfss["wire_rad"] = f"{wire_rad}mm"
    hfss["port_gap"] = f"{port_gap}mm"

    component_name = "Dipole_Antenna_DM"
    freq_range = ["1GHz", "2GHz"]
    center_freq = "1.5GHz"
    freq_step = "0.5GHz"

    component_fn = hfss.components3d[component_name]
    comp_params = hfss.get_component_variables(component_name)
    comp_params["dipole_length"] = "l_dipole"
    comp_params["wire_rad"] = "wire_rad"
    comp_params["port_gap"] = "port_gap"
    hfss.modeler.insert_3d_component(component_fn, geometry_parameters=comp_params)

    hfss.create_open_region(frequency=center_freq)

    setup_name = "MySetup"
    setup = hfss.create_setup(
        name=setup_name,
        MultipleAdaptiveFreqsSetup=freq_range,
        MaximumPasses=2,
    )
    setup.add_sweep(
        name="DiscreteSweep",
        sweep_type="Discrete",
        RangeStart=freq_range[0],
        RangeEnd=freq_range[1],
        RangeStep=freq_step,
        SaveFields=True,
    )
    interp_sweep = setup.add_sweep(
        name="InterpolatingSweep",
        sweep_type="Interpolating",
        RangeStart=freq_range[0],
        RangeEnd=freq_range[1],
        SaveFields=False,
    )

    hfss.analyze_setup(setup_name, use_auto_settings=True, cores=NUM_CORES_PER_PROCESS)
    hfss.create_scattering(plot="Return Loss", sweep=interp_sweep.name)
    hfss.post.export_report_to_file(working_dir, "Return Loss", ".csv")

    hfss.save_project()
    hfss.release_desktop(close_projects=True, close_desktop=True)

    data = np.loadtxt(os.path.join(working_dir, "Return Loss.csv"), delimiter=",", skiprows=1)
    return data

# ## Define solver wrappers
#
# ``call_solver()`` wraps ``solve_hfss()`` into the argument tuple format expected
# by ``multiprocessing.Pool.imap()``.
# ``call_solver_dummy()`` returns synthetic data and can be used to verify the
# workflow without an HFSS license (set ``SOLVE_MODE = "DUMMY"``).

def get_legacy_signal_value_format(abscissa, channel_data):
    """
    Convert to the following legacy signal format, which is supported by optiSLang's current ProxySolver implementation:

    Parameters:
        - freq: list of frequencies (abscissa)
        - loss: list of return loss values (channel data)
    Returns:
        dict: Legacy signal format compatible with optiSLang's ProxySolver.
        {
            "kind" : "signal",
            "matrix" : "[1,100](((0,0),(0.431848,0),(0.762402,0),(0.921527,0),(0.877561,0),(0.643542,0),(0.273608,0),(-0.149478,0),(-0.532816,0),(-0.793738,0),(-0.87761,0),(-0.769229,0),(-0.495453,0),(-0.118642,0),(0.27751,0),(0.606537,0),(0.79805,0),(0.812765,0),(0.65051,0),(0.349596,0),(-0.0221748,0),(-0.382755,0),(-0.653938,0),(-0.77829,0),(-0.731291,0),(-0.526094,0),(-0.210026,0),(0.146294,0),(0.464701,0),(0.676615,0),(0.737784,0),(0.637491,0),(0.400308,0),(0.08015,0),(-0.25195,0),(-0.52358,0),(-0.676717,0),(-0.680093,0),(-0.535541,0),(-0.277023,0),(0.0372977,0),(0.338125,0),(0.560281,0),(0.656811,0),(0.608878,0),(0.429381,0),(0.159598,0),(-0.140263,0),(-0.404491,0),(-0.576245,0),(-0.619765,0),(-0.527786,0),(-0.322627,0),(-0.0508354,0),(0.227354,0),(0.451344,0),(0.573363,0),(0.568627,0),(0.440337,0),(0.218503,0),(-0.0470388,0),(-0.297804,0),(-0.479523,0),(-0.553868,0),(-0.506513,0),(-0.349839,0),(-0.119785,0),(0.132373,0),(0.351429,0),(0.490323,0),(0.520228,0),(0.436508,0),(0.259314,0),(0.0287738,0),(-0.204074,0),(-0.388561,0),(-0.485404,0),(-0.475048,0),(-0.361581,0),(-0.17144,0),(0.0527191,0),(0.261576,0),(0.409981,0),(0.466703,0),(0.420979,0),(0.284506,0),(0.0885118,0),(-0.12337,0),(-0.304798,0),(-0.416847,0),(-0.436342,0),(-0.360631,0),(-0.207805,0),(-0.0124155,0),(0.182327,0),(0.33409,0),(0.410613,0),(0.396547,0),(0.296502,0),(0.133702,0)))",
            "vector" : "[100]((0,0),(0.10101,0),(0.20202,0),(0.30303,0),(0.40404,0),(0.505051,0),(0.606061,0),(0.707071,0),(0.808081,0),(0.909091,0),(1.0101,0),(1.11111,0),(1.21212,0),(1.31313,0),(1.41414,0),(1.51515,0),(1.61616,0),(1.71717,0),(1.81818,0),(1.91919,0),(2.0202,0),(2.12121,0),(2.22222,0),(2.32323,0),(2.42424,0),(2.52525,0),(2.62626,0),(2.72727,0),(2.82828,0),(2.92929,0),(3.0303,0),(3.13131,0),(3.23232,0),(3.33333,0),(3.43434,0),(3.53535,0),(3.63636,0),(3.73737,0),(3.83838,0),(3.93939,0),(4.0404,0),(4.14141,0),(4.24242,0),(4.34343,0),(4.44444,0),(4.54545,0),(4.64646,0),(4.74747,0),(4.84848,0),(4.94949,0),(5.05051,0),(5.15152,0),(5.25253,0),(5.35354,0),(5.45455,0),(5.55556,0),(5.65657,0),(5.75758,0),(5.85859,0),(5.9596,0),(6.06061,0),(6.16162,0),(6.26263,0),(6.36364,0),(6.46465,0),(6.56566,0),(6.66667,0),(6.76768,0),(6.86869,0),(6.9697,0),(7.07071,0),(7.17172,0),(7.27273,0),(7.37374,0),(7.47475,0),(7.57576,0),(7.67677,0),(7.77778,0),(7.87879,0),(7.9798,0),(8.08081,0),(8.18182,0),(8.28283,0),(8.38384,0),(8.48485,0),(8.58586,0),(8.68687,0),(8.78788,0),(8.88889,0),(8.9899,0),(9.09091,0),(9.19192,0),(9.29293,0),(9.39394,0),(9.49495,0),(9.59596,0),(9.69697,0),(9.79798,0),(9.89899,0),(10,0))"
        }
        where the value pairs in () represent the real and the imaginary part of the signal, respectively. The "matrix" field contains the full 2D array of signal data, while the "vector" field contains only the abscissa values (frequencies) for reference.
        If loss data is not complex, the imaginary part can be set to 0 as shown above. The "kind" field indicates that this is a signal-type response, which allows optiSLang to interpret and process it correctly in the workflow.

    """
    if abscissa is None or channel_data is None:
        return None

    result = {
        "kind" : "signal",
        "matrix": f"[1,{len(abscissa)}](({','.join([f'({l.real},{l.imag})' for l in channel_data])}))",
        "vector": f"[{len(abscissa)}]({','.join([f'({f.real},{f.imag})' for f in abscissa])})"
    }
        
    return result


def get_signal_value_format(abscissa, *args):
    if abscissa is None:
        return None
    for arg in args:
        if arg is None:
            return None
    result = {
        "abscissa": abscissa,
        "channels": list(args),
        "num_channels": len(args),
        "num_entries": len(abscissa),
        "type": "signal",
    }
    return result


def call_solver(args):
    hid, working_dir, l_dipole, wire_rad, port_gap = args
    print(f"Solving design {hid} ...")
    result_data = solve_hfss(working_dir, l_dipole, wire_rad, port_gap)
    freq = result_data[:, -2].tolist()
    loss = result_data[:, -1].tolist()
    return_loss = get_signal_value_format(freq, loss)
    freq_min = float(freq[np.argmin(loss)])
    print(f"Solving design {hid} ... done.")
    # return {"freq_min": freq_min}
    return {"return_loss": return_loss, "freq_min": freq_min, "amplitude_min": min(loss)}


def call_solver_dummy(args):
    hid, working_dir, l_dipole, wire_rad, port_gap = args
    print(f"Solving design {hid} ...")
    freq = np.linspace(0, 3, 301).tolist()

    def notch_return_loss(f, f0, Q):
        num = (f**2 - f0**2)**2
        den = num + (f * f0 / Q)**2
        s11 = math.sqrt(num / den)
        return 20 * math.log10(s11)

    try:
        loss = [notch_return_loss(f, l_dipole/10+port_gap/5+wire_rad/5, (port_gap+wire_rad)/4) for f in freq]
    except Exception as e:
        print(f"Error in call_solver_dummy: {e}")
        return {"return_loss": None, "freq_min": None, "amplitude_min": None}

    return_loss = get_signal_value_format(freq, loss)
    freq_min = float(freq[np.argmin(loss)])
    print(f"Solving design {hid} ... done.")
    # return {"freq_min": freq_min}
    return {"return_loss": return_loss, "freq_min": freq_min, "amplitude_min": min(loss)}


# ## Define parallel compute function
#
# ``compute_designs()`` receives a list of design points from the ProxySolver,
# dispatches them to the solver in parallel using ``multiprocessing.Pool``,
# and returns the collected responses.


def get_parameter_value(design, parameter_name):
    return design.parameters[design.parameters_names.index(parameter_name)].value


def in_notebook():
    try:
        from IPython import get_ipython
        return get_ipython() is not None and "IPKernelApp" in get_ipython().config
        
    except Exception:
        return False


def compute_designs(designs):
    print(f"Calculate {len(designs)} designs: {', '.join([design.id for design in designs])}")
    design_data = []
    aedt_working_dir = WORKING_DIR / AEDT_WORKING_DIRNAME
    aedt_working_dir.mkdir(parents=True, exist_ok=True)
    for design in designs:
        hid = design.id
        design_temp_folder = tempfile.mkdtemp(dir=str(aedt_working_dir), prefix="pyaedt.")
        design_data.append((
            hid,
            design_temp_folder,
            get_parameter_value(design, "l_dipole"),
            get_parameter_value(design, "wire_rad"),
            get_parameter_value(design, "port_gap"),
        ))

    if SOLVE_MODE == "HFSS":
        solve = call_solver
    elif SOLVE_MODE == "DUMMY":
        solve = call_solver_dummy
    else:
        raise KeyError(f"Unknown SOLVE_MODE: {SOLVE_MODE}")

    if in_notebook() or FORCE_SEQUENTIAL_SOLVE:
        # Run sequentially in Jupyter to avoid multiprocessing issues.
        print(
            "Running in notebook environment -> Ignoring MAX_PARALLEL_SOLVE_PROCESSES "
            "and running processes in sequence"
        )
        results = []
        for design_args in tqdm(design_data, desc="Solving designs"):
            result = solve(design_args)
            results.append(result)
    else:
        results = concurrent_map(solve, design_data, max_workers=MAX_PARALLEL_SOLVE_PROCESSES)


    result_design_list = []
    for design, result in zip(design_data, results):
        result_design_list.append(
            Design(
                design_id=design[0],
                responses=[
                    DesignVariable(name, value=value) for name, value in result.items()
                    ]
            )
        )

    print(f"Return {len(result_design_list)} designs")
    return result_design_list


# ## Define helper functions

def sort_designs_by_id(designs):
    return sorted(designs, key=lambda obj: int(obj.id.split(".")[1]))  # Sort by design number

def print_designs(designs):
    sorted_result_designs = sort_designs_by_id(designs)
    for design in sorted_result_designs:
        p = [f"{p.name}={p.value:-1.2f}" for p in design.parameters]
        r = []
        for response in design.responses:
            if isinstance(response.value, dict) and "type" in response.value and response.value["type"] == "signal":
                r.append(f"{response.name}=signal[{response.value['num_entries']}:{response.value['num_channels']}]")
            elif response.value is None:
                r.append(f"{response.name}=None")
            else:
                r.append(f"{response.name}={response.value:-1.2f}")

        if design.pareto_design is True:
            pareto_str = " *"
        else:
            pareto_str = ""
        print(f"{design.id:4}: {', '.join(p)} | {', '.join(r)}{pareto_str}")

def get_pareto_designs(designs):
    return [design for design in designs if design.pareto_design is True]


def add_stdout_handler(logger):
    # Create a StreamHandler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)

    # Optional: set level and formatter
    stdout_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)

    # Add it to the logger
    logger.addHandler(stdout_handler)


# ## Prepare run
#
# * Create a temporary directory where downloaded data or dumped data can be stored.
# * Define parameter and response definition
# * Define total number of designs to execute `num_designs_max`
#
# The below steps are wrapped in the main guard (`if __name__ == "__main__":)
# to ensure the process_map does not recursively spin up the same process again 
# and again.
# This is only necessary because we package everything in one file for the 
# sake of this example. As a best practice, it makes sense to refactor the 
# part executed by process_map into a separate file/module.

if __name__ == "__main__":
    # Create temporary working dir
    temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")
    WORKING_DIR = pathlib.Path(temp_folder.name)
    print(f"WORKING DIR: {WORKING_DIR}")

    # The optiSLang project file (``pyoptislang_example_proxy_solver.opf``) is created 
    # on the fly by optiSLang when the ``Optislang`` instance is initialized.
    osl_project_name = "pyoptislang_example_proxy_solver.opf"

    # The dipole antenna geometry is parameterized by three variables.
    # ``num_designs_max`` controls how many design points the sensitivity study evaluates.
    parameters_as_dict = {
        "l_dipole": {"reference_value": 10.2, "lower_bound": 9.0, "upper_bound": 12.0},
        "wire_rad": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
        "port_gap": {"reference_value": 1.0, "lower_bound": 0.8, "upper_bound": 1.2},
    }
    responses_as_dict = {
        "return_loss": {
            "reference_value": get_legacy_signal_value_format(
                    [0, 1, 2], [0, -20, -10]
                ),
            "type": "signal",
        },
        "freq_min": {
            "reference_value": 1.0,
            "type": "scalar",
        },
        "amplitude_min": {
            "reference_value": -10.0,
            "type": "scalar",
        },
    }
    num_designs_max = 2

    parameters_objects = []
    for parameter_name, parameter_data in parameters_as_dict.items():
        parameters_objects.append(
            OptimizationParameter(
                name=parameter_name,
                reference_value=parameter_data["reference_value"],
                range=(parameter_data["lower_bound"], parameter_data["upper_bound"]),
            )
        )
    amop_responses_objects = []
    # For the AMOP node, we include all responses including the full return loss signal, so we
    # can check if the return_loss signal is valid.
    for response_name in ["return_loss", "freq_min", "amplitude_min"]:
        response_data = responses_as_dict[response_name]
        amop_responses_objects.append(
            Response(
                name=response_name,
                reference_value=response_data["reference_value"],
                reference_value_type=ResponseValueType.from_str(response_data["type"])
                )
        )

    optimization_responses_objects = []
    # For optimization, we are only interested in the scalar responses, not the full return loss signal.
    for response_name in ["freq_min", "amplitude_min"]:
        response_data = responses_as_dict[response_name]
        optimization_responses_objects.append(
            Response(
                name=response_name,
                reference_value=response_data["reference_value"],
                reference_value_type=ResponseValueType.from_str(response_data["type"])
                )
        )

# ## Initialize the optiSLang session
# Create optiSLang project named `osl_project_name` and create
#   * Sensitivity system with ProxySolver node
#   * MOP node
# Load the parameter/response schema.
# ## Run the parametric study
# Start the optiSLang workflow without blocking. Poll the ProxySolver for pending
# design batches, dispatch them to HFSS via ``compute_designs()``, and return the
# responses until all design points have been evaluated.
# ## Convenience: Create the same workflow from a template
# As an alternative to the above cell, the entire workflow can be created from a 
# template in a single step, using the `GeneralAlgorithmTemplate` and 
# `ParametricDesignStudyManager` classes. The template internally creates the 
# same nodes and connections as above, and also configures the ProxySolver to 
# use `compute_designs()` as its callback function for design evaluation.


if __name__ == "__main__":

    osl = Optislang(
        project_path=str(WORKING_DIR / osl_project_name),
        )
    osl.application.save()
    osl.dispose()
    osl = Optislang(
        project_path=str(WORKING_DIR / osl_project_name),
        batch=NG_MODE,
        )

    add_stdout_handler(osl.log)
    solver_settings = ProxySolverNodeSettings(
        callback=compute_designs,
        multi_design_launch_num=-1
    )
    """
    # Number of designs in a Sensitivity sytem
    algorithm_settings = GeneralAlgorithmSettings(
        {"AlgorithmSettings": {"num_discretization": num_designs_max}}
    )
    """
    # Number of designs in an AMOP system
    algorithm_settings = GeneralAlgorithmSettings(
        {
            "AMopSettings": {
                "min_cop": 0.9999,
                # "num_discretization_adaption" : 70,
                # "num_discretization_initial" : 50,
                # "num_discretization_initial": math.floor(num_designs_max/2),
                #"num_discretization_adaption": int(num_designs_max/2),
                "num_designs_max": num_designs_max,
                # "max_iteration": 3,
            }
        }
    )

    amop_template = GeneralAlgorithmTemplate(
        parameters=parameters_objects,
        responses=amop_responses_objects,
        criteria=[],
        algorithm_type=node_types.AMOP,
        algorithm_settings=algorithm_settings,
        solver_type=node_types.ProxySolver,
        solver_settings=solver_settings
    )

    design_study_manager = ParametricDesignStudyManager(
        optislang_instance=osl,
        )
    amop_study = design_study_manager.create_design_study(template=amop_template)
    amop_study.execute()
    design_study_manager.save()
    time.sleep(5)

    print("AMOP result designs:")
    print_designs(amop_study.get_result_designs())

    print("AMOP design study done!")


# ## Add surrogate model (MOP)
# After all designs have been evaluated, append a **Metamodel of optimal prognosis
# (MOP)** node to the workflow and re-start the project to train the surrogate model
# on the collected results.
# - ``add_mop_node()`` appends a metamodel-of-optimal-prognosis (MOP) node and
#   connects it to the upstream sensitivity system.


"""
def add_mop_node(parent_system, predecessor_system):
    mop_node = parent_system.create_node(type_=node_types.Mop, name="MOP")
    predecessor_system.get_output_slots("OMDBPath")[0].connect_to(
        mop_node.get_input_slots("IMDBPath")[0]
    )
    predecessor_system.get_output_slots("OParameterManager")[0].connect_to(
        mop_node.get_input_slots("IParameterManager")[0]
    )
    mop_node.set_property("SettingsType", "mop_advanced_settings")
    mop_node.set_property("MOPCustomUsage", {"competition_signal_model": True})
    mop_node.set_property("MOPCustomSettings", MOP_CUSTOM_SETTINGS)
    return mop_node
"""

"""
if __name__ == "__main__":
    root_system = osl.application.project.root_system
    system = amop_study.get_last_parametric_system() # Get the system created from the template, which contains the ProxySolver node that executed the design evaluations.
    moptraining_node = add_mop_node(root_system, system)
    print("Added and connected MOP node.")
    
    print("Training MOP ...")
    time.sleep(5)
    system.set_property("ExecutionOptions", 1)

    osl.application.project.start()
    print("Training MOP ... done.")

    osl.application.save()
"""


# ## Create MOP-based optimization system
# As anext step, an optimization system is be created that uses the trained MOP
# as its surrogate model for design evaluation. 

if __name__ == "__main__":
    target_frequency = 1.35  # GHz
    criteria = [
        ObjectiveCriterion("obj_freq_min", expression=f"(freq_min-{target_frequency})^2", criterion=ComparisonType.MIN)
        ]

    amop_system = amop_study.managed_instances[0].instance # Get the system created from the template, which contains the ProxySolver node that executed the design evaluations.

    # Number of designs in an OCO system & deactivate additional MOP in OCO
    optimizer_settings = GeneralAlgorithmSettings(
        {
            "OptimizerSettings": {
                "settings": {
                    "MaxGenerations": 10,
                }
            }
        }
    )
    optimization_template = OptimizationOnMOPTemplate(
        optimizer_name="Optimization",
        optimizer_type=node_types.NOA2,
        parameters=parameters_objects,
        criteria=criteria,
        responses=optimization_responses_objects,
        mop_predecessor=amop_system,
        callback=compute_designs,
    )

    optimization_study = design_study_manager.create_design_study(optimization_template)
    optimization_study.execute()
    design_study_manager.save()

    print("Optimization result designs:")
    optimization_result_designs = optimization_study.get_result_designs()[1:] # Skip the first design, as it is a duplicate 
    print_designs(optimization_result_designs)
    print(f"Optimization design study done! Status: {optimization_study.get_status()}")

# ## Display results

if __name__ == "__main__":
    sorted_result_designs = sort_designs_by_id(optimization_result_designs)
    # Plot the resonance frequency over all designs
    freq_min_values = [design.responses[design.responses_names.index("freq_min")].value for design in sorted_result_designs]
    design_ids = [int(design.id.split(".")[1]) for design in sorted_result_designs]
    plt.plot(design_ids, freq_min_values, marker=".")
    # Highlight the best designs in red
    pareto_designs = get_pareto_designs(sorted_result_designs)
    plt.scatter(
        [int(p.id.split(".")[1]) for p in pareto_designs], 
        [p.responses[p.responses_names.index("freq_min")].value for p in pareto_designs],
        c="None",edgecolor="red", zorder=5, label="Pareto designs"
        )    
    plt.xlabel("Design ID")
    plt.ylabel(f"Resonance frequency [GHz] (Target: {target_frequency}GHz)")
    plt.grid(True)
    plt.show()

    print("Best designs:")
    print_designs(pareto_designs)
    for design in pareto_designs:
        freq_min = design.responses[design.responses_names.index("freq_min")].value
        amplitude_min = design.responses[design.responses_names.index("amplitude_min")].value

    """
    for design in result_designs:
        print(f"Design {design.id}:")
        for parameter in design.parameters:
            print(f"  Parameter {parameter.name}: {parameter.value}")
        for response in design.responses:
            print(f"  Response {response.name}: {response.value}")
    
    for response in all_responses:
        freq = response["responses"][0]["value"]["abscissa"]
        return_loss = response["responses"][0]["value"]["channels"][0]
        plt.plot(freq, return_loss, label=f"Design {response['hid']}")

    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Return loss [dB]")
    plt.grid(True)
    plt.legend()
    plt.show()
    """


# ## Release optiSLang

# +

if __name__ == "__main__":
    design_study_manager.optislang.dispose()
    time.sleep(3)  # Allow optiSLang to shut down before cleaning the temporary project folder.

# -

# ## Clean up
# All project files are saved in the folder ``temp_folder.name``.
# If you've run this example as a Jupyter notebook, you can retrieve those
# project files. The following command all temporary files, including the project folder.

if __name__ == "__main__":
    pass
    #temp_folder.cleanup()
