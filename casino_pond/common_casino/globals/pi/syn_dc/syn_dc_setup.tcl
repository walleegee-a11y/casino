#########################################################################################
# Tech_lib
##########################################################################################
##- from ${corner}
#set p_corner  [lindex [split ${corner} _] 0]
#set v_corner  [lindex [split ${corner} _] 1]
#set t_corner  [lindex [split ${corner} _] 2]
#set rc_corner [lindex [split ${corner} _] 3]
set corner $env(default_pvt)
#
## UMC
#    if { [string match "ss*p125c*" ${corner}] } { set op_cond WCG1 } \
#elseif { [string match "ss*m40c*"  ${corner}] } { set op_cond WCG2 } \
#elseif { [string match "ff*m40c*"  ${corner}] } { set op_cond BCG1 } \
#elseif { [string match "ff*p125c*" ${corner}] } { set op_cond BCG2 } \
#elseif { [string match "*tt*"      ${corner}] } { set op_cond TT } \
#else   { echo "ERROR : Need to check corner, ${corner}" ; #exit }

set std_cnt "0"
set mem_cnt "0"
set ip_cnt  "0"
set io_cnt  "0"

## - Source STD, MEM, IO_IP db_setup.tcl
source -e -v ${COMMON_SYN_DC}/lib_setup.tcl

echo "std_cnt : $std_cnt"
echo "mem_cnt : $mem_cnt"
echo "ip_cnt  : $ip_cnt"
echo "io_cnt  : $io_cnt"

#pre sta
#if { [string match "*_dc_*" ${run_ver}] || (${stage} == "vclp") } {
#    set link_library 	[concat * \
#								$LINK_ONLY_DB \
#							]
#	} else {
#        echo "ERROR : Check link_library $\{run_ver\}"
#	}
#}

## 0811 To use 'same techlib wtih another step' in dcg step
if { [string match "*rtl-*_dk-*_tag-*" ${ws}] } {
	set link_db_files     ${link_library}  
	set target_db_files   $env(syn_dc_target_library)
	set pvt_corner        ${corner}
	puts "link_db_files   : ${link_library}"
	puts "target_db_files : $env(syn_dc_target_library)"
}

puts "RM-Info: Running script [info script]\n"

set_app_var sh_new_variable_message false

set verilogout_no_tri "true"

# Ensure the program is dc_shell and set options(Original script version uses read_LSF)
if {[info exists synopsys_program_name] && $synopsys_program_name == "dc_shell"} {
    # Set multicore options
    set_host_options -max_cores 4
    puts "## info - default core : set_host_options -max_cores 4"
    
    # Change alib_library_analysis_path to point to a central cache of analyzed libraries
    # to save runtime and disk space.  The following setting only reflects the
    # default value and should be changed to a central location for best results.
    # Set analyzed library cache path
    set_app_var alib_library_analysis_path .

    # Add any additional Design Compiler variables below
}

#################################################################################
# Library Setup
#
# This section is designed to work with the settings from common_setup.tcl
# without any additional modification.
#################################################################################

#taeblue 1129 set_app_var target_library ${TARGET_LIBRARY_FILES}

set_app_var synthetic_library dw_foundation.sldb

set_app_var link_library "* $link_library $synthetic_library"
#set_app_var link_library "* $ADDITIONAL_LINK_LIB_FILES_MEM $synthetic_library"
 
## - project_setup.tcl if {[file exists [which ${LIBRARY_DONT_USE_FILE}]]} {
## - project_setup.tcl     puts "RM-Info: Sourcing script file [which ${LIBRARY_DONT_USE_FILE}]\n"
## - project_setup.tcl     source -echo -verbose ${LIBRARY_DONT_USE_FILE}
## - project_setup.tcl }


puts "RM-Info: Completed script [info script]\n"

#################################################################################
# 65nm => Zero WLM
#################################################################################
if {[shell_is_in_topographical_mode]} {
    echo "Variable auto_wire_load_selection is not supported in DC Topographical mode and will be ignored"
} else {
    set auto_wire_load_selection "true"
    
    # 130 nm
    # set auto_wire_load_selection "true"
    # set_wire_load_mode enclosed
    # set_wire_load_selection_group -library ${PRIM_WST_NAME} ${WIRE_LOAD_TYPE}
    
    # 90nm ~ 65nm : ZERO-WLM Style -> Margin : 45 % Clock Period 
    # set auto_wire_load_selection "false"
}

#################################################################################
# variables
#################################################################################
set WIRE_LOAD_TYPE       NORMAL
set WIRE_LOAD_VALUE      none

#-------------------------------------------------------
# To turn off only hierarchical phase optimization, 
# set the environment variable 
# compile_disable_hierarchical_inverter_opt to TRUE. 
# This will prevent the compile command from changing the
# phase of hierarchical port signals. 
# Other boundary_optimizations will still be attempted.
#-------------------------------------------------------
set compile_disable_hierarchical_inverter_opt true

#-------------------------------------------------------
# Remove constant registers (prevent Formality error)
#-------------------------------------------------------
#jsj 210830 set compile_seqmap_propagate_constants false
#jsj 210830 set compile_delete_unloaded_sequential_cells false

# set hdlin_preserve_sequential true

set compile_seqmap_synchronous_extraction "true"

#-------------------------------------------------------
# To disable Automatic  shift-register  identification (A-2007.12-SP3)
#-------------------------------------------------------
set compile_seqmap_identify_shift_registers true 
set compile_seqmap_identify_shift_registers_with_synchronous_logic false

#-------------------------------------------------------
# Preserving original port connection for sub modules
#-------------------------------------------------------
set compile_preserve_subdesign_interfaces true

#-------------------------------------------------------
# Detecting multiple drive nets with error serverity level
#-------------------------------------------------------
set check_design_allow_unknown_wired_logic_type false

#-------------------------------------------------------
# Allowing multiple clocks per register
#-------------------------------------------------------
set timing_enable_multiple_clocks_per_reg true

#-------------------------------------------------------
# Disable sequential output inversion
#-------------------------------------------------------
set compile_seqmap_enable_output_inversion false

# propagate logic 0/1 also even when there is no set_case_analysis
set case_analysis_with_logic_constants true

set compile_seqmap_no_scan_cell "true"

set compile_ultra_ungroup_small_hierarchies false

# Enable the support of via resistance for RC estimation to improve the timing 
# correlation with IC Compiler
set_app_var spg_enable_via_resistance_support true

#-------------------------------------------------------
# This option affects whether or not escaped characters are
# created when translating the HDL.
#-------------------------------------------------------
set with_brackets  1
    
if {$with_brackets == 1} {
    set bus_naming_style {%s[%d]}
    set bus_dimension_separator_style {][}
} else {
    set bus_naming_style "%s_%d"
    set bus_dimension_separator_style "_"
}

#-------------------------------------------------------
# suppress error
#-------------------------------------------------------
set suppress_errors WL-40


#-------------------------------------------------------
# Enable RTL DRC
#-------------------------------------------------------
set hdlin_enable_rtldrc_info     FALSE
set hdlin_enable_presto          TRUE

#-------------------------------------------------------
# for multi-dimensional array & 64-bit compile
#-------------------------------------------------------
set hdlin_enable_presto_for_vhdl true

#-------------------------------------------------------
# for parameterized modules
#-------------------------------------------------------
set hdlin_auto_save_templates true

#-------------------------------------------------------
# for complex logic : ELAB-2008
#-------------------------------------------------------
# set hdlin_infer_complex_set_reset TRUE

#-------------------------------------------------------
# Parmeter digit conversion 
#-------------------------------------------------------
#  set ::template_parameter_style %d

#-------------------------------------------------------
# DC-Ultra dw ungroup envirionment
#-------------------------------------------------------
  set compile_ultra_ungroup_dw false

#-------------------------------------------------------
# global envirionment
#-------------------------------------------------------
get_license DC-Ultra-opt
get_license DesignWare
get_license HDL-Compiler
get_license VHDL-Compiler

#-------------------------------------------------------
# set intermediate file directory
#-------------------------------------------------------
set cache_read  ./synopsys_cache
set cache_write ./synopsys_cache

#-------------------------------------------------------
# set verilog out unconnected pin 
# < must be modify when new ddc file split > lkj
#-------------------------------------------------------
set cur_dir [pwd]
# 230306 LSH
# set DESIGN         [lindex [split [lindex [split $cur_dir "/"] 6] "."] 1]

set verilogout_show_unconnected_pins true



####################################
# copy syn varable in dc_main.tcl
####################################
#Env.
set collection_result_display_limit 10000000
set hdlin_shorten_long_module_name true
set hdlin_module_name_limit 120

# Clock gating setup
set pwr_hdlc_split_cg_cells true  
set hdlin_no_group_register true
# recognize all clock_gating opportunities
set hdlin_infer_complex_enable true

#################################################################################
#for formality.
#################################################################################
if {[string match {*AIXV_NVP_coretile*} ${cur_dir}] != 1} { 
	set_app_var simplified_verification_mode true
}

#-------------------------------------------------------
# source procs
#-------------------------------------------------------
source ${COMMON_SYN_DC}/procs_util.tcl
set enable_page_mode false

################################################################################
# You can enable inference of multibit registers from the buses defined in the RTL.
# The replacement of single-bit cells with multibit library cells occurs during execution 
# of the compile_ultra command. This variable has to be set before reading the RTL
#
# set_app_var hdlin_infer_multibit default_all
#################################################################################
set report_dir		 "reports"
set output_dir		 "outputs"

#### Runtime check ####
set step 	"synthesis"

#################################################################################
#For library setup
#################################################################################
if {[file exists $env(syn_dc_library_dont_use_pre_compile_list)]} {
    puts "RM-Info: Sourcing script file: $env(syn_dc_library_dont_use_pre_compile_list)\n"
    source -echo -verbose $env(syn_dc_library_dont_use_pre_compile_list)
} else {
    puts "Info: \"library_dont_use_pre_compile_list\" does not exist."
}

#################################################################################
#For formality.
#################################################################################

# 221208 move to global.tcl
#if {[string match {*AIXV_NVP_coretile*} ${cur_dir}] != 1} { 
#	set_app_var simplified_verification_mode true
#}

#################################################################################
# Setup for Formality Verification
#################################################################################
set_svf ${output_dir}/${top_design}.mapped.svf

#############################################################################
# Clock Gating Setup
#############################################################################
# insert dummy clock_gating cells
#--set power_cg_always_enabled_registers true
#
set target_library {}
foreach lib_path [split $env(syn_dc_target_library) " "] {
    set full_path "${DB_PATH}/vers/${db_ver}/std/db/$env(pi_default_pvt)/$lib_path"
    if {[lsearch -exact $target_library $full_path] == -1} {
        lappend target_library $full_path
    }
}

foreach lib_path $target_library {
    puts $lib_path
}

set_clock_gating_style -sequential_cell latch \
                       -control_point before \
                       -control_signal scan_enable \
                       -max_fanout 32 \
                       -minimum_bitwidth 5 \
   		               -num_stages 1 \
                       -positive_edge_logic integrated:$env(syn_dc_ckg_positive)
					   #-negative_edge_logic integrated:$CKG_NEGATIVE_CELL_NAM
