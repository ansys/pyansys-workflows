# # Maxwell3D - Simplified IonTrap Modelling
#
# Description:
#
# First step of a multi-tool workflow: Maxwell 2D model to identify electric field node in Ion Trap
# 1. Set up the Q3D Parametric Model
# 2. Identify the Electric Field Node Point for Each Design Point
# 3. Export the NOde Coordinates for the subsequent Lumerical Step
#
# Keywords: **Ion Trap**, **Q3D CG Solver**

# ## Perform imports and define constants
#
# Perform required imports.

import os,sys
import tempfile
import time

sys.path.append("C:\\Program Files\\Lumerical\\v251\\api\\python\\")
sys.path.append(os.path.dirname(__file__)) #Current directory
my_path = r"D:/2025/17_IonTrap/PyAnsys_GC/"
my_node_filename = "Q3DNodePositionTable.tab"
my_node_filename_lum = "legend.txt"

import ansys.aedt.core
import lumapi

# Define constants.

AEDT_VERSION = "2025.2"
NUM_CORES = 4
NG_MODE = False  # Open AEDT UI when it is launched.

# ## Create temporary directory
#

temp_folder = tempfile.TemporaryDirectory(suffix=".ansys")

# ## Launch AEDT and application
#

project_name = os.path.join(temp_folder.name, "IonTrapQ3D.aedt")
q3d = ansys.aedt.core.Q3d(
    project=project_name,
    design="01_Q3D_IonTrap_3rails",
    version=AEDT_VERSION,
    non_graphical=NG_MODE,
    new_desktop=True
)
q3d.modeler.model_units = "um"

# ## Preprocess
#
# Initialize dictionaries for design variables

geom_params = {
    "div": str(73/41),
    "w_rf": "41um",
    "w_dc": "41um*div",
    "w_cut": "4um",
    "metal_thickness": "1um",
    "offset_glass": "50um",
    "glass_thickness": "10um",
    "x_dummy": "2um",
    "y_dummy": "300um",
    "Z_length": "300um"
}

# Define variables from dictionaries

for k, v in geom_params.items():
    q3d[k] = v

# Create Design Geometry

dc = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["-w_dc/2" ,"-metal_thickness/2" ,"0"],
    sizes=["w_dc", "metal_thickness"],
    name="DC",
    material="aluminum"
)
#dc.color = (0, 0, 255)  # rgb

gnd = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["-(w_dc/2+w_cut+w_rf+offset_glass)" ,"-(metal_thickness/2+glass_thickness)" ,"0"],
    sizes=["2*(w_dc/2+w_cut+w_rf+offset_glass)", "-metal_thickness"],
    name="gnd",
    material="aluminum"
)

rf = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["-(w_dc/2+w_cut+w_rf)" ,"-metal_thickness/2" ,"0"],
    sizes=["w_rf", "metal_thickness"],
    name="RF",
    material="aluminum"
)

sub_glass = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["-(w_dc/2+w_cut+w_rf+offset_glass)" ,"-metal_thickness/2" ,"0"],
    sizes=["2*(w_dc/2+w_cut+w_rf+offset_glass)", "-glass_thickness"],
    name="substrate_glass",
    material="glass"
)

ins = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["-(w_dc/2+w_cut)" ,"-metal_thickness/2" ,"0"],
    sizes=["w_cut", "metal_thickness"],
    name="ins",
    material="vacuum"
)

# Create dummy objects for mesh, center_line for Post Processing and Region

dummy = q3d.modeler.create_rectangle(
    orientation = "XY",
    origin=["0" ,"metal_thickness/2" ,"0"],
    sizes=["-x_dummy", "y_dummy"],
    name="dummy",
    material="vacuum"
)

# Extrude in z-direction

q3d.modeler.sweep_along_vector(assignment=q3d.modeler._get_model_objects(),sweep_vector=[0,0,"Z_length"], draft_angle=0, draft_type='Round')
center_line_length = 300*1e-6 #300 um
center_line_length_str = str(center_line_length*1e6) #in um
mid_center_line_length_str = str(0.5*center_line_length*1e6) #in um
center_line = q3d.modeler.create_polyline(points=[["0","metal_thickness/2",str(mid_center_line_length_str)+"um"],
                                                  ["0","metal_thickness/2+"+center_line_length_str+"um",str(mid_center_line_length_str)+"um"]],
                                          name='center_line')

# Define Excitations

q3d.auto_identify_nets()

# Define Mesh Settings

q3d.mesh.assign_initial_mesh(method = "AnsoftClassic")
#q3d.mesh.assign_length_mesh(assignment=center_line.id, maximum_length=1e-7, maximum_elements=None,name="center_line_0.1um")
#q3d.mesh.assign_length_mesh(assignment=dummy.name, maximum_length=2e-6, maximum_elements=1e6, name="dummy_2um")
#q3d.mesh.assign_length_mesh(assignment=ins.id, maximum_length=8e-7, inside_selection=False, maximum_elements=1e6, name="ins_0.8um")
#q3d.mesh.assign_length_mesh(assignment=[dc.id, rf.id], maximum_length=5e-6, inside_selection=False, maximum_elements=1e6,name="dc_5um")
#q3d.mesh.assign_length_mesh(assignment=gnd.id, maximum_length=1e-5, inside_selection=False, maximum_elements=1e6, name="gnd_10um")

# Duplicate structures and assignments to complete the model

q3d.modeler.duplicate_and_mirror(assignment= [rf.id,dummy.id,ins.id],
        origin = ["0","0","0"],
        vector = ["-1","0","0"],
        duplicate_assignment=True)

# Create, validate, and analyze setup

setup_name = "MySetupAuto"
setup1 = q3d.create_setup(props={"Name":setup_name,"AdaptiveFreq": "1Hz","SaveFields":True})
setup1.ac_rl_enabled = False
setup1.dc_enabled = False
setup1.update()
q3d.validate_simple()
q3d.analyze_setup(name=setup_name, use_auto_settings=False, cores=NUM_CORES)

#  Create parametric sweep

# keeping w_rf constant, we recompute the w_dc values from the desired ratios w_rf/w_dc

div_sweep_start=1.4
div_sweep_stop=2
sweep = q3d.parametrics.add(
    variable="div",
    start_point=div_sweep_start,
    end_point = div_sweep_stop,
    step = 0.2,
    variation_type="LinearStep",
    name="w_dc_sweep"
)
add_points= [1,1.3]
[sweep.add_variation(
	sweep_variable="div",
	start_point=p,
	variation_type="SingleValue"
) for p in add_points]
sweep["SaveFields"] = True
sweep.analyze(cores=NUM_CORES)

#

# ## Postprocess
#
# Create the Ey expression in the PyAEDT Advanced Field Calculator
#Due to the symmetric nature of this specific geometry, the electric field node will be located along the center line
#The electric field node is the point where the Ey will be zero and can be found directly by Maxwell post processing features

# edit sources to scale the solution for the actual assigned potentials
sources_cg = {"DC": ("0V", "0deg"), "gnd": ("0V", "0deg"),"RF": ("1V", "0deg"),"RF_1":("1V", "0deg")}
q3d.edit_sources(sources_cg)

# evaluate the E- filed on the control line and export nodal points
line_name = "Line1"
q3d.insert_em_field_line(assignment="center_line",points=1000,name = line_name)
my_plots = q3d.post.create_report(expressions="re(EY)",primary_sweep_variable="NormalizedDistance",report_category="Static EM Fields",plot_type="Rectangular Plot",context=line_name,plot_name ="my_plot")
my_plots.edit_x_axis_scaling(min_scale="0.01", max_scale="1")
my_plots.update_trace_in_report(my_plots.get_solution_data().expressions,variations={"div": ["All"]}, context=line_name)
my_plots.add_cartesian_y_marker("0")
my_plots.add_trace_characteristics("XAtYVal", arguments=["0"], solution_range=["Full", "0.01", "1.0"])
my_plots.edit_general_settings(use_scientific_notation=True)
my_plots.export_table_to_file(my_plots.plot_name,my_path+"//"+my_node_filename, "Legend")

# ## Release AEDT

q3d.save_project()
q3d.release_desktop()

# ## Edit the outputted file to be read in by Lumerical - units in um
new_line=[]
with open(my_path+my_node_filename, "r", encoding='utf-8') as f:
    lines = f.readlines()
new_line.append(lines[0])
for line in lines[1:]:
    new_line.append(line.split('\t')[0])
    node_pos_um = (center_line_length - float(line.split('\t')[1].lstrip()))*1e6 #um
    new_line.append('\n'+str(node_pos_um)+'\n')
with open(my_path+my_node_filename_lum, "w", encoding='utf-8') as f:
    for line in new_line:
        f.write(line)

# ## Start the Lumerical Process

GC0 = lumapi.FDTD(my_path+"GC_Opt.lsf") # run the first script: Build geometry & Run optimization
Gc1 = lumapi.FDTD(my_path+"Readata.lsf")
print('Optimize for the Nodal point located',str(Gc1.getv('T5')),'um, above the linearly apodized grating coupler')
Gc2 = lumapi.FDTD(my_path+"Testsim_Intensity_best_solution") # Run the optimized design
Gc2.save(my_path+"GC_farfields_calc")
Gc2.run()
Gc2.feval(my_path+"GC_farfield.lsf") # run the second script for calculating plots
print('Target focal distance of output laser beam, (um) :',str(Gc2.getv('Mselect')*1000000))
print('Actual focal distance for the optimised geometry, (um)  :',str(Gc2.getv('Mactual')*1000000))
print('Relative error:',str(Gc2.getv('RelVal')*100),'(%)')
print('FWHM of vertical direction at focus, (um) ',str(Gc2.getv('FWHM_X')*1000000))
print('FWHM of horizontal direction at focus, (um) ',str(Gc2.getv('FWHM_Y')*1000000))
print('Substrate material :',str(Gc2.getv('Material')))

print('Waveguide etch depth, (nm) ',str(Gc2.getv('GC_etch')*1000000000))
print('Grating period (P), (nm) ',str(Gc2.getv('GC_period')*1000000000))
print('Grating minimum duty cycle:',str(Gc2.getv('GC_DCmin')))

# Wait 3 seconds to allow AEDT to shut down before cleaning the temporary directory.
time.sleep(3)

# ## Clean up
#

temp_folder.cleanup()
