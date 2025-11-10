#################################################################################
# Check & Report Input Files for DC
#################################################################################
set current_time [clock format [clock seconds] -format %y%m%d_%H%M]
set file_out [open ./check_input_${current_time}.txt w]
set input_list [list \
    ${env(syn_dc_design_format)} \
    ${sdc} \
    ${upf} \
    ${env(syn_dc_user_dont_use)} \
    ${env(syn_dc_user_dont_touch)} \
    USER_OPTION_FILE \
    USER_OPTION_B4_COMPILE \
    USER_OPTION_B4_INCR \
    USER_REPORT_FILE \
   ]

foreach input ${input_list} {
  if {[file exists [set  ${input}]]} {
	puts ${file_out} [format "%-25s %s %-1s %-1s" $input (exist) : [set  $input]]
  } else {
	puts ${file_out} [format "%-25s %s %-1s %-1s" $input (no_ex) : [set  $input]]
  }
}

close $file_out
unset current_time

#################################################################################
# rename_design & Write out Design 
#################################################################################
source -echo -ver ${COMMON_SYN_DC}/sec_verilog_rule.tcl
change_names -rules sec_verilog -verbose -hierarchy

	#X330 if {[string match {*17.AIXV_CORE_ucx*} $cur_dir]} {
	#X330 	set postfix_name "AIXV_CORE_ucx"
	#X330 	rename_design * -postfix _$postfix_name
	#X330 	rename_design [current_design] $top_design
 	#X330 } elseif {[string match {*16.AIXV_CORE_lcx*} $cur_dir]} {
	#X330 	set postfix_name "AIXV_CORE_lcx"
	#X330 	rename_design * -postfix _$postfix_name
	#X330 	rename_design [current_design] $top_design
	#X330 }
	#X330 ################

write -format verilog -hierarchy -output ${output_dir}/${top_design}.mapped_incr.v
write -format ddc     -hierarchy -output ${output_dir}/${top_design}.mapped_incr.ddc

# Write and close SVF file and make it available for immediate use
set_svf -off

write_sdc -nosplit ${output_dir}/${top_design}.mapped.sdc

if {(${top_design} == "psu_top") && [file exists [which ${upf}]]} {
    save_upf "./outputs/${top_design}.upf"
}

#################################################################################
# Generate Final Reports
#################################################################################
    report_qor > ${report_dir}/${top_design}.mapped.qor.rpt
    
    report_timing -transition_time -nets -attributes -nosplit > ${report_dir}/${top_design}.mapped.timing.rpt
    
    report_area -nosplit > ${report_dir}/${top_design}.mapped.area.rpt

    report_area -designware  > ${report_dir}/${top_design}.mapped.designware_area.rpt
#   report_resources -hierarchy > ${report_dir}/${top_design}.mapped.final_resources.rpt
    report_clock_gating -nosplit > ${report_dir}/${top_design}.mapped.clock_gating.rpt

    report_constraint -all_violators -nosplit -significant_digits 5           > ${report_dir}/${top_design}.mapped.report_constraint_wst
    #report_constraint -all_violators -verbose -nosplit -significant_digits 5  > ${report_dir}/${top_design}.mapped.report_constraint_wst_verbose
 
### USER_Modified Start
redirect -file ./logs/vth_cnt_area.log {source -e -v ${COMMON_SYN_DC}/vth_cnt_area.syn.tcl}
### USER_Modified End

	redirect ${report_dir}/check_port_macro_list {
		echo "TOTAL PORT NUMBER : [sizeof_collection [get_port]]"
		foreach_in_collection port_temp [get_port] {
			echo [get_object_name $port_temp]
		}
		echo "\n\n-------------------------------------------------------------------------------------------------------------"
		echo "-------------------------------------------------------------------------------------------------------------\n\n"
		echo "TOTAL MACRO NUMBER : [sizeof_collection [get_cell -h -f " ( is_macro_cell==true ) || ( pad_cell == true )"]]"
		set macro_list [get_object_name [get_cell -h -f "( is_macro_cell==true ) || ( pad_cell == true ) "]]
		foreach macro_temp $macro_list {
			set macro_temp_ref_name [get_attribute [get_cell $macro_temp] ref_name]
			echo [format "%-20s %s"  $macro_temp [get_attribute [get_cell $macro_temp] ref_name]]
		}
    }

    # Create a QoR snapshot of timing, physical, constraints, clock, power data, and routing on 
    # active scenarios and stores it in the location  specified  by  the icc_snapshot_storage_location 
    # variable. 
    

    
    # Uncomment the next line to report all the multibit registers and the banking ratio in the design
    # redirect ${report_dir}/${top_design}.multibit.banking.rpt {report_multibit_banking -nosplit }
    
    # Use SAIF file for power analysis
    # set current_scenario_saved [current_scenario]
    # foreach scenario [all_active_scenarios] {
    #   current_scenario ${scenario}
    #   read_saif -auto_map_names -input ${top_design}.${scenario}.saif -instance < DESIGN_INSTANCE > -verbose
    # }
    # current_scenario ${current_scenario_saved}
    
    report_power -nosplit > ${report_dir}/${top_design}.mapped.power.rpt
    report_clock_gating -nosplit > ${report_dir}/${top_design}.mapped.clock_gating.rpt
    
    # Uncomment the next line if you include the -self_gating to the compile_ultra command
    # to report the XOR Self Gating information.
    # report_self_gating  -nosplit > ${report_dir}/${top_design}.mapped.self_gating.rpt
    
    # Uncomment the next line to reports the number, area, and  percentage  of cells 
    # for each threshold voltage group in the design.
    # report_threshold_voltage_group -nosplit > ${report_dir}/${top_design}.mapped.threshold.voltage.group.rpt
    
# write user reports
if {([info exist USER_REPORT_FILE] == 1) && [file exist [which ${USER_REPORT_FILE}]] } {
	source -e -v ${USER_REPORT_FILE}
}

#################################################################################
# Write out Milkyway Design for Top-Down Flow
#
# This should be the last step in the script
#################################################################################

#sh touch ../pass/syn.pass
GetDate DC_done
GetTotalRunTime Total_RunTime
#################################################################################
# Quit
#################################################################################
#exit
