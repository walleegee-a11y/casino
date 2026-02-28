#################################################################################
# Read in the RTL Design
#
# Read in the RTL source files or read in the elaborated design (.ddc).
#################################################################################
define_design_lib WORK -path ./WORK

if {$env(syn_dc_design_format) == "rtl"} {
    set common_rtl_path "${DB_PATH}/vers/${db_ver}/design/$env(syn_dc_design_format)/common"
    set psu_top_rtl_path "${DB_PATH}/vers/${db_ver}/design/$env(syn_dc_design_format)/${top_design}"
    analyze -format verilog -vcs "-f ${DB_PATH}/vers/${db_ver}/design/$env(syn_dc_design_format)/${top_design}/${top_design}.${env(syn_dc_design_format)}_list.f"

    #elaborate -architecture verilog ${top_design}
    elaborate ${top_design}

    # Write outputs in DDC and Verilog formats
    write -hierarchy -format ddc -output ${output_dir}/${top_design}.elab.ddc
    write -hierarchy -format verilog -output ${output_dir}/${top_design}.elab.v
} elseif {$env(syn_dc_design_format) == "ddc"} {
    # Read DDC files and write Verilog output
    read_ddc ""
    write -hierarchy -format verilog -output ${output_dir}/${top_design}.elab.v
} elseif {$env(syn_dc_design_format) == "NET"} {
    # Read netlist files in Verilog format
    read_verilog "" 
} else {
    puts "error: Check design format '$env(syn_dc_design_format)'. Supported formats are 'rtl', 'ddc', and 'NET'."
}

GetDate read_design
#### set units #
current_design ${top_design}

link > ${report_dir}/${top_design}.link

GetDate link

#################################################################################
# read_sdc
#################################################################################
set sdc "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.sdc"
if {[file exists $sdc]} {
    puts "RM-Info: Sourcing script file: $sdc\n"
    source -echo -verbose $sdc
} else {
    puts "error: sdc file not found at: $sdc. Please ensure the file exists in the DB_PATH."
}

#################################################################################
# user_setting dont touch/use
#################################################################################
if {[file exists [which ${RUN_PATH}/syn_dc/$env(syn_dc_user_dont_use)]]} {
    source -echo -verbose ${RUN_PATH}/syn_dc/$env(syn_dc_user_dont_use)
} else {
    puts "Info: \"user_dont_use file\" does not exist."
}

if {[file exist [which ${RUN_PATH}/syn_dc/$env(syn_dc_user_dont_touch)]] } {
  source -echo -verbose ${RUN_PATH}/syn_dc/$env(syn_dc_user_dont_touch)
} else {
	puts "Info: \"user_dont_touch file\" no exist." 
}

### clock gating ###
# user setup please >> set_clock_gating_check -setup 0.1

set ports_clock_root [filter_collection [get_attribute [get_clocks] sources] object_class==port]
group_path -name REGOUT -to [all_outputs] 
group_path -name REGIN -from [remove_from_collection [all_inputs] ${ports_clock_root}] 
group_path -name FEEDTHROUGH -from [remove_from_collection [all_inputs] ${ports_clock_root}] -to [all_outputs]

#################################################################################
# driving_cell
#################################################################################
source -echo -verbose ${COMMON_SYN_DC}/driving_cell.tcl


#################################################################################
# Apply Additional Optimization Constraints
#################################################################################
# Prevent assignment statements in the Verilog netlist.
set_fix_multiple_port_nets -all -buffer_constants

#################################################################################
# operating_conditions
#################################################################################
#    set_operating_conditions -max ${WST_TIV_RVT_CON} -max_library ${PRIM_RVT_WST_TIV_NAME}

#set_max_area 0

# Set the maximum transition value on the design
set max_transition         ""
#set_max_transition $max_transition ${top_design}

# Load all outputs with suitable capacitance
#if {![regexp {top|flatten} ${is_top}]} {
if {${env(syn_dc_is_top)} != 1} {
	set output_load   0.02
} else {
	set output_load	   10
}
set_load ${output_load} [all_outputs]

set max_fanout         32
#set_max_fanout $max_fanout ${top_design}

#################################################################################
# timing derate
#################################################################################
foreach mem_list [get_attribute [get_cells -hier * -filter "is_memory_cell == true"] ref_name] {
	if {[sizeof_collection [get_cells -quiet -hierarchical -filter "ref_name =~ ${mem_list}* && is_hierarchical==false"]] > 0} {
		set_timing_derate -cell_check -late 0.75 [get_cells -quiet -hierarchical -filter "ref_name =~ ${mem_list}* && is_hierarchical==false"]
		set_timing_derate -cell_delay -late 0.75 [get_cells -quiet -hierarchical -filter "ref_name =~ ${mem_list}* && is_hierarchical==false"]
	}
}

set_auto_disable_drc_nets -clock true

#################################################################################
# Check for Design Problems 
#################################################################################
# Check the current design for consistency
check_design -summary
check_design -multiple_designs > ${report_dir}/${top_design}.check_design.rpt

