sh date
sh touch STA_PT_START

###############################################
#- Environment variables
###############################################
regexp {[A-Z]-(\d+\.\d+)} $sh_product_version match PT_VERSION
source -echo -verbose $env(RUN_COMMON_PATH)/globals/pi/get_pi_vars.tcl

set mode       [lindex [split [pwd] "/"] end-1]
set corner     [lindex [split [pwd] "/"] end]

#- from ${corner}
set p_corner  [lindex [split ${corner} _] 0]
set v_corner  [lindex [split ${corner} _] 1]
set t_corner  [lindex [split ${corner} _] 2]
set rc_corner [lindex [split ${corner} _] 3]
set setup_corner [lindex [split ${corner} _] 4]

set pvt_corner ${p_corner}_${v_corner}_${t_corner}

if { ${setup_corner} != "" } {
    set spef_cond  ${t_corner}_${rc_corner}_${setup_corner}
} else {
    set spef_cond  ${t_corner}_${rc_corner}
}

    if { [string match "ss*p125c*" ${corner}] } { set op_cond WCG1 } \
elseif { [string match "ss*m40c*"  ${corner}] } { set op_cond WCG2 } \
elseif { [string match "ff*m40c*"  ${corner}] } { set op_cond BCG1 } \
elseif { [string match "ff*p125c*" ${corner}] } { set op_cond BCG2 } \
elseif { [string match "*tt*"      ${corner}] } { set op_cond TT } \
else   { echo "ERROR : Need to check corner, ${corner}" ; exit 1 }

echo "# kill -9 [pid] \;# run_path : ./$mode/$corner" >> ../../sta_pid.list

###############################################
#- ovars.tcl
###############################################
source -echo -verbose ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

if { [file exist ${RUN_PATH}/sta_pt/sta_pt_teco.tcl] } {
	source -echo -verbose ${RUN_PATH}/sta_pt/sta_pt_teco.tcl
}

###############################################
#- set_app_var
###############################################
set_app_var report_default_significant_digits 4
set_app_var timing_report_unconstrained_paths true
set_app_var link_keep_unconnected_cells true
# set_app_var timing_early_launch_at_borrowing_latches false
set_app_var auto_wire_load_selection false

if { [file exist ${RUN_COMMON_STA_PT}/set_user_variables.tcl] } {
	redirect -tee ./logs/user_variables.tcl {
		source -echo -verbose ${RUN_COMMON_STA_PT}/set_user_variables.tcl
	}
}

if { ${pre_post} == "post" } {
    #TSMC 22nm aocvm
    #set_pt_variables -post -aocvm -ccs
    suppress_message RC-203
    
    #set_si_options -static_noise true
    set_app_var si_xtalk_double_switching_mode clock_network
    set_app_var si_enable_analysis true
   
    #TSMC Recomanded
    set_app_var delay_calc_waveform_analysis_mode full_design
    
    #SBOCV Options
    #set_app_var timing_aocvm_enable_analysis true
    #set_app_var timing_aocvm_analysis_mode combined_launch_capture_depth
    
    # Bi-directional Pad Feedback Path STA
    set_app_var timing_disable_internal_inout_net_arcs false

    # reporting the X-y coordinates
    set_app_var read_parasitics_load_locations true
}

# timing_slew_threshold_scaling_for_max_transition_compatibility has been made obsolete starting with the S-2021.06 release of PrimeTime and is no longer supported. (PT-008)
if { !($PT_VERSION >= 2021.06) } {
    set_app_var timing_slew_threshold_scaling_for_max_transition_compatibility true
}


###############################################
# lib setup
###############################################
source -echo -verbose ${RUN_COMMON_STA_PT}/lib_setup.tcl

# read design
if { ${pre_post} == "pre" } {
    # RTL
    # TODO: syn run_ver?
    if { [regexp rtl- ${design_ver}] } {
        # DC
        if { [regexp dc- ${run_ver}] } {
            set NETLIST ${RUN_PATH}/syn_dc/results/${top_design}.incr.v

        # DCG
        } elseif { [regexp dcg- ${run_ver}] } {
            set NETLIST ${RUN_PATH}/syn_dc/results/${top_design}.incr.v

        } else {
            echo "ERROR : The netlist for performing STA is parsed based on ${run_ver}"
            echo "        ${run_ver} should indicate whether the synthesis was done with \"dc\" or \"dcg\"."
            echo "        ex) 01_dc_for_gen_def"
            echo "        ex) 02_dcg_def_v01"
            sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
            sh chmod +s :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
            exit 1
        }

    # TODO: netlist name?
    } elseif { [regexp net- ${design_ver}] } {
        set NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v
        if { $ovars(sta_pt,is_flatten) == 1 } {
            if { [info exist ovars(sta_pt,sub_block_list)] && $ovars(sta_pt,sub_block_list) != "" } {
                set sub_block_list $ovars(sta_pt,sub_block_list)
            } else {
                set sub_block_list [lminus $all_blks $top_design]
            }
            foreach sub_block $sub_block_list {
                lappend NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${sub_block}.v
            }
        }
    } else {
        echo "ERROR : need2chk ${design_ver}"
        sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
        sh chmod +s :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
        exit 1
    }

} elseif { ${pre_post} == "post" } {

    # Top netlist
    set NETLIST ${PD_OUT_PATH}/netlist/${top_design}.v

    # Sub-block setting
    set need_subblocks 0
    if { $ovars(sta_pt,is_flatten) == 1 } {
        set need_subblocks 1
    }

    if { $need_subblocks } {
        if { [info exist ovars(sta_pt,sub_block_list)] && $ovars(sta_pt,sub_block_list) != "" } {
            set sub_block_list $ovars(sta_pt,sub_block_list)
        } else {
            set sub_block_list [lminus $all_blks $top_design]
        }
        foreach sub_block $sub_block_list {
            lappend NETLIST ${OUTFEED_PATH}/${sub_block}/pd___${db_ver}/$ovars(sta_pt,sub_block_version,${sub_block})/netlist/${sub_block}.v
        }
    }
}

if { $NETLIST != ""} {
	sh rm -f ./NET_SPEF_INFO
	foreach net $NETLIST {
		echo "NETLIST : ${net}" >> ./NET_SPEF_INFO
		echo "read_verilog ${net}"
		read_verilog ${net}
	}
} else {
    echo "ERROR : NO NETLIST - ${NETLIST}"
    sh touch :ABNORMAL_ERROR_NO_NETLIST
	sh chmod +s :ABNORMAL_ERROR_NO_NETLIST
    exit 1
}

###############################################
# link design
###############################################
current_design ${top_design}
link > ./logs/link.log

sh touch READ_DESIGN_DONE

###############################################
# read parasitics
###############################################
#TODO: flatten STA
if { ${pre_post} == "post" } {
    set SPEF ${PD_OUT_PATH}/spef/${top_design}.spef.${spef_cond}.gz

    if { [file exists ${SPEF}] } {
        echo "INFO : SPEF - ${SPEF}"
        echo "SPEF    : ${SPEF}" >> ./NET_SPEF_INFO
        read_parasitics -keep_capacitive_coupling ${SPEF}
    } else {
        echo "Error : NO SPEF - ${SPEF}"
        sh touch :ABNORMAL_ERROR_SPEF
        sh chmod +s :ABNORMAL_ERROR_SPEF
        exit 1
    }

    # Flatten -> sub-block SPEF setting
    if { $ovars(sta_pt,is_flatten) == 1 } {
        if { [file exists $ovars(sta_pt,sub_block_location_file)] } {
            set Line_num 0
            set fin [open $ovars(sta_pt,sub_block_location_file) r]

            while { [gets $fin line] >= 0 } {
                incr Line_num
                if { [string trim $line] eq "" || [string match "#*" [string trim $line]] } {
                    continue
                }

                lassign $line sub_module sub_path sub_x_coordinate sub_y_coordinate sub_orientation

                foreach sub_block $sub_block_list {
                    if { $sub_block == $sub_module } {
                        set sub_SPEF ${OUTFEED_PATH}/${sub_block}/pd___${db_ver}/$ovars(sta_pt,sub_block_version,${sub_block})/spef/${sub_block}.spef.${spef_cond}.gz
                        # mm -> nm (?: 251.0 -> 251000.0)
                        set sub_x_coordinate [expr {$sub_x_coordinate * 1000.0}]
                        set sub_y_coordinate [expr {$sub_y_coordinate * 1000.0}]

                        set sub_orientation [string toupper $sub_orientation]
                        if { [regexp {^M?([XY])?R?(0|90|180|270)?$} $sub_orientation -> flip rotate] } {
                            if { $flip eq "" } {
                                set sub_flip none
                            } else {
                                # X/Y -> x/y
                                set sub_flip [string tolower $flip]
                            }

                            if { $rotate eq "" || $rotate eq "0" } {
                                set sub_rotate none
                            } else {
                                set sub_rotate $rotate
                            }
                        } else {
                            puts "Error: Invalid orientation \"$sub_orientation\" for submodule \"$sub_module\", R0 will be assumed"
                            puts "       Check Line $Line_num: $ovars(sta_pt,sub_block_location_file)"
                            set sub_flip none
                            set sub_rotate none
                        }

                        echo "SPEF    : ${sub_SPEF}" >> ./NET_SPEF_INFO
                        puts "INFO : read_parasitics -keep_capacitive_coupling $sub_SPEF -path $sub_path -x_offset $sub_x_coordinate -y_offset $sub_y_coordinate -axis_flip flip_${sub_flip} -rotation rotate_${sub_rotate}"
                        read_parasitics -keep_capacitive_coupling $sub_SPEF -path $sub_path -x_offset $sub_x_coordinate -y_offset $sub_y_coordinate -axis_flip flip_${sub_flip} -rotation rotate_${sub_rotate}
                    }
                }
            }

            close $fin
            unset Line_num
        } else {
            echo "Error : NO SUB BLOCK LOCATION FILE - $ovars(sta_pt,sub_block_location_file)"
            sh touch :ABNORMAL_ERROR_SUB_BLOCK_LOCATION_FILE
            sh chmod +s :ABNORMAL_ERROR_SUB_BLOCK_LOCATION_FILE
            exit 1
        }
    }
}

###############################################
# read_sdc
###############################################
if { ${pre_post} == "pre" } {
    if { $ovars(sta_pt,is_flatten) == 1 } {
        #set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}_full.${mode}.sdc"
        set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.${mode}.sdc"
    } else {
        set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.${mode}.sdc"
    }

} elseif { ${pre_post} == "post" } {
    if { $ovars(sta_pt,is_flatten) == 1 } {
        # - ${pi_ver} must be made unique
        # set SDC [glob -nocomplain -types f ${PRJ_HOME}/outfeeds/${top_design}/pi___*/${pi_ver}/sdc/${top_design}.${mode}.sdc]
        #set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}_full.${mode}.sdc"
        set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.${mode}.sdc"
    } else {
        set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.${mode}.sdc"
    }
}

if { [file exists ${SDC}] } {
    echo "INFO : SDC - ${SDC}"
    source -echo -verbose ${SDC} > ./logs/read_constraint.log
} else {
    echo "ERROR : NO SDC - ${SDC}"
    sh touch :ABNORMAL_ERROR_SDC
    sh chmod +s :ABNORMAL_ERROR_SDC
    exit 1
}

sh touch READ_SDC_DONE

# TODO: MBIST @FUNC -> merge SDC as misn?
#if { [file exist $MBIST_SDC] } {
#    redirect -tee -append {
#        echo "INFO : SOURCE .. $MBIST_SDC"
#        source -echo -verbose $MBIST_SDC
#    }
#}

if { ${pre_post} == "pre" } {
	# treat high fanout net as ideal
    set max_fanout 32
    source -echo -verbose ${RUN_COMMON_STA_PT}/HFN.tcl > ./HFN.log

	# remove boundary condition
    set port_nets [get_nets -of_object [get_ports *]]
    foreach_in_collection each_net $port_nets {
           set_load       0 [get_nets $each_net]
           set_resistance 0 [get_nets $each_net]

    }

} elseif { ${pre_post} == "post" } {
    if { [regexp _setup ${corner}] } {
        set_false_path -hold -from [all_clocks]

    } elseif { [regexp _hold ${corner}] } {
        set_false_path -setup -from [all_clocks]

    }
	remove_ideal_network [all_inputs]
	remove_ideal_network [get_pins * -h]
	remove_clock_transition [all_clocks]
    remove_clock_latency [all_clocks]
    set_propagated_clock [all_clocks]
}

###############################################
# set ocv margin & clock uncertainty
###############################################
if { ${pre_post} == "pre" } {
    # Setup Uncertainty @pre
    #  -> setup_uncertainty = 0.05 * $period + $setup_extra_margin
    set setup_extra_margin 0.00
    source ${RUN_COMMON_STA_PT}/gen_setup_uncertainty.pre_sta.tcl
    gen_setup_uncertainty setup_uncertainty.pre_sta.scr
    source -echo -verbose ./setup_uncertainty.pre_sta.scr

} elseif { ${pre_post} == "post" } {
	# Apply OCV Derate
	reset_timing_derate

    if { [file exist ${RUN_COMMON_STA_PT}/tech/aocv_setup.22eHVG_7T.tcl]} {
         source -echo -verbose ${RUN_COMMON_STA_PT}/tech/aocv_setup.22eHVG_7T.tcl

    } else {
        echo "ERROR : Need to check OCV margin, ${corner}"
        exit 1
    }

    # Setup Uncertainty @POST
    #  -> setup_uncertainty = 0.03 * $period + $setup_extra_margin
    # PLL Jitter + 50 ps (Sign-off Criteria for 0.8V Operation)
    set setup_extra_margin [expr 0.05 + $ovars(sta_pt,extra_setup_uncert)]
    source ${RUN_COMMON_STA_PT}/gen_setup_uncertainty.post_sta.tcl
    gen_setup_uncertainty setup_uncertainty.scr
    source -echo -verbose ./setup_uncertainty.scr

    # Hold Uncertainty @POST
    # BCG : 35ps / WCG : 80ps (Sign-off Criteria for 0.8V Operation)
	if { [regexp BCG $op_cond] } {
	    set_clock_uncertainty -hold [expr 0.035 + $ovars(sta_pt,extra_hold_uncert)] [all_clocks]

	} elseif { [regexp WCG $op_cond] } {
	    set_clock_uncertainty -hold [expr 0.080 + $ovars(sta_pt,extra_hold_uncert)] [all_clocks]

	} elseif { [string match -nocase "*tt*" ${corner}] } {
	    set_clock_uncertainty -hold [expr 0.010 + $ovars(sta_pt,extra_hold_uncert)] [all_clocks]

	}
}

###############################################
#TODO: Pre-Source
###############################################
set ovars(sta_pt,pre_source) "${RUN_COMMON_STA_PT}/pre_source.tcl"
if { [info exist ${ovars(sta_pt,pre_source)}] && [file exists ${ovars(sta_pt,pre_source)}] } {
    redirect -tee pre_source.log { source -echo -verbose ${ovars(sta_pt,pre_source)} }
    echo "INFO : PRE_ECO - /mnt/data/prjs/RDP180XP/pi/post/sta/${top_design}/${SYN_VERSION}.${PD_RUN_VERSION}/pre_source_eco/${ECO_VERSION}.tcl"
}


#################################
#- update_timing
#################################
#- set group_path
set clock_ports [get_ports -filter "is_clock_network"]
group_path -name IN2REG  -from [remove_from_collection [all_input] $clock_ports]
group_path -name REG2OUT -to [all_outputs]
group_path -name IN2OUT  -from [remove_from_collection [all_inputs] $clock_ports] -to [all_outputs]

#- update_timing
update_timing -full > ./reports/update_timing.rpt
sh touch UPDATE_TIMING_DONE

sh date

#- save_session
save_session session.${mode}_${corner}
sh touch SAVE_SESSION_DONE
sh date

#- write_sdc
if { ${pre_post} == "pre" } {
    write_sdc -nos ./sdc/${top_design}.${mode}.sdc
}

#################################
#- Reports
#################################
report_clock -nos > ./reports/clocks.rpt
check_timing -verbose -include {signal_level clock_crossing} > ./reports/check_timing.rpt
report_case_analysis -nosplit > ./reports/case_analysis.rpt
report_analysis_coverage -nos -status_details {untested violated} -sort_by slack \
    -check_type {setup hold recovery removal min_period clock_gating_setup clock_gating_hold out_setup out_hold} \
    -exclude_untested {constant_disabled mode_disabled user_disabled no_paths false_paths} > ./reports/analysis_coverage.rpt

#- check Vth & GC
source ${RUN_COMMON_STA_PT}/report_Vth.tcl
vth_rpt > ./reports/cell_vth.rpt

source ${RUN_COMMON_STA_PT}/report_cell_usage.tcl

#- check_clock_tree_cells
source ${RUN_COMMON_STA_PT}/check_clock_tree_cells.tbc
check_clock_tree_cells -verbose
#file delete chk_clk_tree.cell_usage chk_clk_tree.cell_usage.sort_by_ref_name

if { ${pre_post} == "post" } {
	source ${RUN_COMMON_STA_PT}/report_unanno_net_analysis.tcl
	report_annotated_parasitics -list_not_annotated -max 1000000 > ./reports/pt_unannotated_net.log
	report_unanno_net_analysis ./reports/pt_unannotated_net.log > ./reports/summary_unannotated_net.rpt

	#- Check OCV
	report_timing_derate -incr -sig 4 > ./reports/report_timing_derate_check_OCV.rpt
}

#set CTS_CELL_TYPE "_lvt"
#source ${RUN_COMMON_STA_PT}/clock_network_check.tcl
#clock_network_check $CTS_CELL_TYPE

report_constraint -nos -sig 4 -all_violators                               > ./reports/all_violators.rpt
report_constraint -nos -sig 4 -all_violators -max_delay -recovery          > ./reports/all_violators.max_delay.rpt
report_constraint -nos -sig 4 -all_violators -min_delay -removal           > ./reports/all_violators.min_delay.rpt
report_constraint -nos -sig 4 -all_violators -max_delay -recovery -verbose > ./reports/all_violators.max_delay.rpt.verbose
report_constraint -nos -sig 4 -all_violators -min_delay -removal  -verbose > ./reports/all_violators.min_delay.rpt.verbose
report_constraint -nos -sig 4 -all_violators -max_transition               > ./reports/all_violators.max_transition.rpt
report_constraint -nos -sig 4 -all_violators -max_capacitance              > ./reports/all_violators.max_capacitance.rpt
report_constraint -nos -sig 4 -all_violators -min_pulse_width              > ./reports/all_violators.min_pulse.rpt 
report_constraint -nos -sig 4 -all_violators -min_period                   > ./reports/all_violators.min_period.rpt

report_global_timing > ./reports/global_timing.rpt
report_global_timing -delay_type max -separate_all_groups > ./reports/global_timing.max.all_grps.rpt
report_global_timing -delay_type min -separate_all_groups > ./reports/global_timing.min.all_grps.rpt

if { [file exist ./reports/all_violators.min_period.rpt] } {
	set fin [open ./reports/all_violators.min_period.rpt r]
	while { [gets $fin line] >= 0 } {
		if { [regexp "VIOLATED" $line] } {
			sh touch :VIOLATION_min_period
			sh chmod +s :VIOLATION_min_period
		}
	}
	close $fin
}

if { ${pre_post} == "post" } {
    #- Check clock delta delay
    source ${RUN_COMMON_STA_PT}/report_clk_net_delta_delay.tcl
    report_clk_net_delta_delay > ./reports/shielding_check_${mode}_${corner}.rpt

    #- Check noise
    check_noise -nos -verbose > ./reports/check_noise.rpt
    update_noise > ./reports/update_noise.rpt
    report_noise -nos -all_violators -sig 3 > ./reports/gnoise_viols_${corner}.rpt

	#- PBA Report
	report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba)                               > ./reports/all_violators.$ovars(sta_pt,pba).rpt
	report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -max_delay -recovery          > ./reports/all_violators.max_delay.$ovars(sta_pt,pba).rpt
	report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -min_delay -removal           > ./reports/all_violators.min_delay.$ovars(sta_pt,pba).rpt
	report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -max_delay -recovery -verbose > ./reports/all_violators.max_delay.$ovars(sta_pt,pba).rpt.verbose
	report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -min_delay -removal  -verbose > ./reports/all_violators.min_delay.$ovars(sta_pt,pba).rpt.verbose

    report_global_timing -pba_mode $ovars(sta_pt,pba) > ./reports/global_timing.$ovars(sta_pt,pba).rpt
	report_global_timing -pba_mode $ovars(sta_pt,pba) -delay_type max -separate_all_groups > ./reports/global_timing.all_grps.$ovars(sta_pt,pba).max.rpt
	report_global_timing -pba_mode $ovars(sta_pt,pba) -delay_type min -separate_all_groups > ./reports/global_timing.all_grps.$ovars(sta_pt,pba).min.rpt

}

sh touch REPORT_DONE

#- MTTV report
source ${RUN_COMMON_STA_PT}/mttv.tcl
mttv ./reports/all_violators.max_transition.rpt ./reports/mttv_${mode}_${corner}.rpt

source -echo -verbose ${RUN_COMMON_STA_PT}/mttv_check.22eHVG_7T.tcl

###############################################
#- Project Check
###############################################
#- data skew report
# 6714 source -echo -verbose ${RUN_COMMON_STA_PT}/prj/data_skew_rpt.tcl


###############################################
#- write_sdf
###############################################
if { ${pre_post} == "post" && $ovars(sta_pt,gen_sdf) } {
	reset_timing_derate
	update_timing -full

	file mkdir ./SDF
    write_sdf -version 3.0 -compress gzip \
		-exclude checkpins -context verilog -input_port_nets -significant 3 \
		-no_edge -no_edge_merging timing_checks -include {SETUPHOLD RECREM } \
		./SDF/${top_design}.${mode}_${corner}.sdf
}


#- Write hack_sdf
if { ${pre_post} == "post" && $ovars(sta_pt,hack_sdf) } {
    reset_timing_derate
	update_timing -full

	file mkdir ./HSDF
    write_sdf -version 3.0 -compress gzip \
		-exclude checkpins -context verilog -input_port_nets -significant 3 \
		-no_edge -no_edge_merging timing_checks -include {SETUPHOLD RECREM } \
        -mask_violations both \
		./HSDF/${top_design}.${mode}_${corner}_hacked.sdf
}


###############################################
#- Generate timing window file
###############################################
if { ${pre_post} == "post" } {
		if { [regexp ff_0p88v_m40c_cmin ${corner}] || [regexp ss_0p72v_p125c_cmax ${corner}] } {
			source ${RUN_COMMON_STA_PT}/pt2timing.tcl
            if {${mode} == "bist"} {
			    set ADS_ALLOWED_PCT_OF_NON_CLOCKED_REGISTERS 90
            } else {
                set ADS_ALLOWED_PCT_OF_NON_CLOCKED_REGISTERS 20
            }
			set rc_slew_lower_threshold_pct_rise 30.00
			set rc_slew_upper_threshold_pct_rise 70.00
			set rc_slew_lower_threshold_pct_fall 30.00
			set rc_slew_upper_threshold_pct_fall 70.00
			getSTA * -noexit
			file rename -force ${top_design}.timing ${top_design}.${corner}.${mode}.timing
#			if { ![file exist ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file] } {
#				file mkdir ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file
#			}
#			file copy -force ${top_design}.${corner}.${mode}.timing ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file

		}
}

sh touch STA_PT_DONE
exit
