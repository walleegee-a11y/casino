#################################################################################
# Compile the Design
#
# Recommended Options:
#
#     -scan
#     -gate_clock (-self_gating)
#     -retime
#     -spg
#
# Use compile_ultra as your starting point. For test-ready compile, include
# the -scan option with the first compile and any subsequent compiles.
#
# Use -gate_clock to insert clock-gating logic during optimization.  This
# is now the recommended methodology for clock gating.
#
# Use -self_gating option in addition to -gate_clock for potentially saving 
# additional dynamic power, in topographical mode only. Registers that are 
# not clock gated will be considered for XOR self gating.
# XOR self gating should be performed along with clock gating, using -gate_clock
# and -self_gating options. XOR self gates will be inserted only if there is 
# potential power saving without degrading the timing.
# An accurate switching activity annotation either by reading in a saif 
# file or through set_switching_activity command is recommended.
# You can use "set_self_gating_options" command to specify self-gating 
# options.
#
# Use -retime to enable adaptive retiming optimization for further timing benefit.
#
# Use the -spg option to enable Design Compiler Graphical physical guidance flow.
# The physical guidance flow improves QoR, area and timing correlation, and congestion.
# It also improves place_opt runtime in IC Compiler.
#
# Note: In addition to -spg option you can enable the support of via resistance for 
#       RC estimation to improve the timing correlation with IC Compiler by using the 
#       following setting:
#
#       set_app_var spg_enable_via_resistance_support true
#
# You can selectively enable or disable the congestion optimization on parts of 
# the design by using the set_congestion_optimization command.
# This option requires a license for Design Compiler Graphical.
#
# The constant propagation is enabled when boundary optimization is disabled. In 
# order to stop constant propagation you can do the following
#
# set_compile_directives -constant_propagation false <object_list>
#
# Note: Layer optimization is on by default in Design Compiler Graphical, to 
#       improve the the accuracy of certain net delay during optimization.
#       To disable the the automatic layer optimization you can use the 
#       -no_auto_layer_optimization option.
#
#################################################################################
## RM+ Variable and Command Settings before first compile_ultra
#################################################################################
# set scan option if DFT is enabled
set compile_cmd    "compile_ultra" ;# default
set compile_option "-gate_clock -no_seq_output_inversion" ;# default

if {[info exist ${env(syn_dc_ungroup)}] && !${env(syn_dc_ungroup)}} {
	lappend compile_option "-no_autoungroup -no_seq_output_inversion"
} 

if {${env(syn_dc_is_dft)} == 1} {
lappend scan_options [list "-scan" "-gate_clock" "-no_autoungroup" "-no_seq_output_inversion" "-timing_high_effort_script"]
}

if {${env(syn_dc_is_dft)} == 1} {
    set_scan_configuration -style multiplexed_flip_flop
    report_dft_configuration
    report_autofix_configuration
    eval compile_ultra $scan_options

} else {

}

#compile_ultra -gate_clock -no_autoungroup -no_seq_output_inversion -timing_high_effort_script
eval ${compile_cmd} ${compile_option}
GetDate compile

#TODO: need2test
# to avoid unexpected uniquify about HPDF sub BLKs
if { ${is_top} && ${env(syn_dc_is_flatten)} == 1} {
    set_app_var uniquify_naming_style "${top_design}_%s_%d"
    uniquify -force
}

change_names -rules verilog -hierarchy

#################################################################################
# Write Out Final Design and Reports
#
#        .ddc:   Recommended binary format used for subsequent Design Compiler sessions
#    Milkyway:   Recommended binary format for IC Compiler
#        .v  :   Verilog netlist for ASCII flow (Formality, PrimeTime, VCS)
#       .spef:   Topographical mode parasitics for PrimeTime
#        .sdf:   SDF backannotated topographical mode timing for PrimeTime
#        .sdc:   SDC constraints for ASCII flow
#
#################################################################################

#################################################################################
    source -echo -ver ${COMMON_SYN_DC}/sec_verilog_rule.tcl
    change_names -rules sec_verilog -verbose -hierarchy

    write -format verilog -hierarchy -output ${output_dir}/${top_design}.mapped.v
    write -format ddc     -hierarchy -output ${output_dir}/${top_design}.mapped.ddc

#TODO: syn_dc_insert_mv_cells.tcl
if { ${env(syn_dc_is_upf)} } {
	#################################################################################
	# read_UPF
	#################################################################################
    puts "1-Pass insert_mv_cells Flow Enabled !"
    puts "\${env(syn_dc_is_upf)} is Enabled."

    set upf_create_implicit_supply_sets true
    set auto_insert_level_shifters_on_clocks all
    set enable_ao_synthesis true

#   remove_attribute [get_lib_cells */ISOLOD4BWP20P90CPD] dont_use
    set upf ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.upf 
	#TODO: load_upf -strict_check true ${upf}
    redirect -tee -file ./logs/read_UPF.log {
		#source -e -v ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.upf
		source -e -v ${upf}

	}

    set_voltage 0.72 -object_list [get_supply_net VDD]
    set_voltage 0.72 -object_list [get_supply_net VDD_M]
    set_voltage 0.0  -object_list [get_supply_net VSS]

    check_mv_design -isolation -verbose > ./reports/${top_design}.mapped.pre_check_mv.rpt
    insert_mv_cells -isolation -verbose > ./reports/${top_design}.mapped.insert_mv_cells.rpt
    check_mv_design -isolation -verbose > ./reports/${top_design}.mapped.post_check_mv.rpt

    #################################################################################
    # Write out Design
    #################################################################################
    write -hier -format verilog -o ./outputs/${top_design}.mapped.iso.v

}

compile_ultra -gate_clock -incr -no_seq_output_inversion -timing_high_effort_script -no_autoungroup

if {${env(syn_dc_is_top)} == 1} {
    set_app_var uniquify_naming_style "${top_design}_%s_%d"
    uniquify -force
}

change_names -rules verilog -hierarchy
GetDate compile_incr
