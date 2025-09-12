#!/bin/bash

# Required environment variables:
# -------------------------------
# - PYMAPDL_PORT: The port for the PyMAPDL service (e.g., 50052).
# - DPF_PORT: The port for the DPF service (e.g., 50055).

echo "::group:: Docker services" && docker ps && echo "::endgroup::"

echo "Waiting for the MAPDL service to be up..."
nc -v -z localhost "$PYMAPDL_PORT"

echo "::group:: ps aux Output" && ps aux && echo "::endgroup::"


echo "::group:: Waiting for the MAPDL port to be open..."
while ! nc -z localhost "$PYMAPDL_PORT"; do
    sleep 0.1
done
echo "::endgroup::"
echo "MAPDL service is up!"


echo "::group:: Waiting for the DPF port to be open..."
while ! nc -z localhost "$DPF_PORT"; do
    sleep 0.1
done
echo "::endgroup::"
echo "DPF service is up!"