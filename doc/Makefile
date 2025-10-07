# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -j auto
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build

# Check if vtk is installed - if so, uninstall and install vtk-osmesa
IS_VTK_INSTALLED := $(pip show vtk)
ifneq ($(IS_VTK_INSTALLED),)
	@echo "VTK is installed. Uninstalling vtk and installing vtk-osmesa"
	@pip uninstall -y vtk
	@pip install --index-url https://wheels.vtk.org vtk-osmesa==9.3.0
endif

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile


	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# Customized clean due to examples gallery
clean:
	rm -rf $(BUILDDIR)/*
	rm -rf $(SOURCEDIR)/sg_execution_times.rst
	find . -type d -name "api" -exec rm -rf {} +
	find . -type d -name "examples" -exec rm -rf {} +
