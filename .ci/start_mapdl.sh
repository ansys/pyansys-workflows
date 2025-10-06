#!/bin/bash
# This script is modified to start MAPDL directly inside a container (no Docker-in-Docker)
#
# Usage:
# ------
# This script is intended to be run in a CI/CD environment where we're already inside a MAPDL container.
#
# Required environment variables:
# -------------------------------
#
# - DISTRIBUTED_MODE: The mode of operation for MAPDL (e.g., "smp", "dmp").
# - DPF_PORT: The port for the DPF service (e.g., 50055).
# - INSTANCE_NAME: The name of the MAPDL instance (e.g., "MAPDL_0").
# - LICENSE_SERVER: The address of the license server (e.g., "123.123.123.123").
# - MAPDL_VERSION: The version of the MAPDL image to use (e.g., "v25.2-ubuntu-cicd").
# - PYMAPDL_DB_PORT: The port for the PyMAPDL database service (e.g., 50056).
# - PYMAPDL_PORT: The port for the PyMAPDL service (e.g., 50052).
#

export MAJOR MINOR VERSION

echo "MAPDL Instance name: $INSTANCE_NAME"
echo "MAPDL_VERSION: $MAPDL_VERSION"
echo "Running inside container - no Docker pull needed"

# Extract version from MAPDL_VERSION
MAJOR=$(echo "$MAPDL_VERSION" | head -c 3 | tail -c 2)
MINOR=$(echo "$MAPDL_VERSION" | head -c 5 | tail -c 1)

VERSION="$MAJOR$MINOR"
echo "MAPDL VERSION: $VERSION"

# Determine executable path based on image type
if [[ $MAPDL_VERSION == *"latest-ubuntu"* ]]; then
    echo "It is latest-ubuntu. Using 'ansys' script to launch"
    EXEC_PATH=ansys
    P_SCHEMA=/ansys_inc/ansys/ac4/schema

elif [[ $MAPDL_VERSION == *"ubuntu"* ]] ; then
    echo "It is an ubuntu based image"
    EXEC_PATH=/ansys_inc/v$VERSION/ansys/bin/mapdl
    P_SCHEMA=/ansys_inc/v$VERSION/ansys/ac4/schema

else
    echo "It is a CentOS based image"
    EXEC_PATH=/ansys_inc/ansys/bin/mapdl
    P_SCHEMA=/ansys_inc/ansys/ac4/schema
fi;

echo "EXEC_PATH: $EXEC_PATH"
echo "P_SCHEMA: $P_SCHEMA"

# Handle CICD version specifics
if [[ $MAPDL_VERSION == *"cicd"* ]] ; then
    echo "It is a CICD version"
    if [ "$RUN_DPF_SERVER" == "true" ]; then
        echo "RUN_DPF_SERVER is set to true, DPF will be available"
        export ANSYS_DPF_ACCEPT_LA=Y
    fi

    echo "DPF_PORT: $DPF_PORT"
    echo "PYMAPDL_DB_PORT: $PYMAPDL_DB_PORT"

    echo "Setting DISTRIBUTED_MODE to $DISTRIBUTED_MODE for CICD version"
else
    export PYMAPDL_DB_PORT=DPF_PORT
fi;

echo "EXEC_PATH: $EXEC_PATH"
echo "P_SCHEMA: $P_SCHEMA"

# Verify executable exists
if [ ! -f "$EXEC_PATH" ] && [ "$EXEC_PATH" != "ansys" ]; then
    echo "Executable not found at $EXEC_PATH, searching for alternatives..."

    # Try alternative paths
    ALTERNATIVE_PATHS=(
        "/ansys_inc/v$VERSION/ansys/bin/ansys$VERSION"
        "/ansys_inc/ansys/bin/mapdl"
        "/ansys_inc/ansys/bin/ansys$VERSION"
        "/opt/ansys_inc/v$VERSION/ansys/bin/mapdl"
    )

    for alt_path in "${ALTERNATIVE_PATHS[@]}"; do
        if [ -f "$alt_path" ]; then
            EXEC_PATH="$alt_path"
            echo "Found alternative executable: $EXEC_PATH"
            break
        fi
    done

    # If still not found, try which command
    if [ ! -f "$EXEC_PATH" ]; then
        if command -v "ansys$VERSION" >/dev/null 2>&1; then
            EXEC_PATH="ansys$VERSION"
            echo "Using system command: $EXEC_PATH"
        else
            echo "ERROR: Could not find MAPDL executable"
            echo "Searched paths:"
            printf '%s\n' "${ALTERNATIVE_PATHS[@]}"
            exit 1
        fi
    fi
fi

# Set environment variables for MAPDL
export ANSYS_LOCK="OFF"
export I_MPI_SHM_LMT=shm
export VERSION=$VERSION
export P_SCHEMA=$P_SCHEMA

# Allow MPI to run as root (required for container environments)
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

echo "Starting MAPDL directly in container..."
echo "Environment variables:"
echo "  ANSYS_LOCK: $ANSYS_LOCK"
echo "  I_MPI_SHM_LMT: $I_MPI_SHM_LMT"
echo "  DISTRIBUTED_MODE: $DISTRIBUTED_MODE"
echo "  OMPI_ALLOW_RUN_AS_ROOT: $OMPI_ALLOW_RUN_AS_ROOT"
echo "  OMPI_ALLOW_RUN_AS_ROOT_CONFIRM: $OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"

# Start MAPDL using the entrypoint logic directly
echo "Starting MAPDL with: $EXEC_PATH -grpc -port $PYMAPDL_PORT -$DISTRIBUTED_MODE"

# Checking PYMAPDL is free
netstat -tulpn | grep :$PYMAPDL_PORT || echo "Port $PYMAPDL_PORT is free"

# Create the log file
touch "${INSTANCE_NAME}.log"

# Start MAPDL in background
nohup $EXEC_PATH -grpc -port $PYMAPDL_PORT -$DISTRIBUTED_MODE -np 2 > "${INSTANCE_NAME}.log" 2>&1 &
MAPDL_PID=$!

echo "MAPDL started with PID: $MAPDL_PID"

# Wait for MAPDL to be ready (similar to original script)
echo "Waiting for MAPDL to start..."
timeout 60 bash -c "
    while ! grep -q 'Server listening on' '${INSTANCE_NAME}.log' 2>/dev/null; do
        if ! kill -0 $MAPDL_PID 2>/dev/null; then
            echo 'ERROR: MAPDL process died'
            exit 1
        fi
        sleep 1
    done
"

if [ $? -eq 0 ]; then
    echo "MAPDL is ready!"
else
    echo "ERROR: MAPDL failed to start or timed out"
    echo "Content of ${INSTANCE_NAME}.log:"
    cat "${INSTANCE_NAME}.log"
    exit 1
fi

echo "Content of ${INSTANCE_NAME}.log:"
cat "${INSTANCE_NAME}.log"

echo "MAPDL_PID=$MAPDL_PID"