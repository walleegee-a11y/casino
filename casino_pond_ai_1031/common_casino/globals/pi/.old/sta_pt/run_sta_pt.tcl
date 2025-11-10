sh date
sh touch STA_PT_START

sh mkdir -p logs
sh mkdir -p reports
sh mkdir -p sdc

###############################################
#- Environment Variables
###############################################
regexp {[A-Z]-(\d+\.\d+)} $sh_product_version match PT_VERSION

#- from [pwd]
#    0 1   2    3    4       5                  6          7                           8    9                                   10     11   12
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_dc_init-00_PD_RUN-fe00_te00_pv00/sta_pt/func/ss_0p72v_m40c_cmax_setup
set prj_name   [lindex [split [pwd] "/"] end-8]
set top_design [lindex [split [pwd] "/"] end-6]
set ws         [lindex [split [pwd] "/"] end-5]
set run_ver    [lindex [split [pwd] "/"] end-3]
set stage      [lindex [split [pwd] "/"] end-2]
set mode       [lindex [split [pwd] "/"] end-1]
set corner     [lindex [split [pwd] "/"] end]


#- from ${ws}
regexp {^([^_]+)___(.*)$} $ws match role db_ver
set design_ver  [lindex [split ${db_ver} _] 0] ;# rtl-0.0
set dk_ver      [lindex [split ${db_ver} _] 1] ;# dk-0.0
set dk_ver_tag  [lindex [split ${db_ver} _] 2] ;# tag-0.0

#- from ${run_ver}
set pi_ver      [lindex [split ${run_ver} -] 0] ;# < 00_dc_init >
set pd_ver      [lindex [split ${run_ver} -] 1] ;# < 00_PD_RUN >
set eco_num     [lindex [split ${run_ver} -] 2] ;# < fe00_te00_pv00 >

    if { ${eco_num} == "" }                      { set pre_post "pre" } \
elseif {[string match "fe*_te*_pv*" ${eco_num}]} { set pre_post "post" } \
else   { echo "ERROR : Need to check run_ver, ${run_ver}" ; exit }

#- from ${corner}
set p_corner  [lindex [split ${corner} _] 0]
set v_corner  [lindex [split ${corner} _] 1]
set t_corner  [lindex [split ${corner} _] 2]
set rc_corner [lindex [split ${corner} _] 3]

set pvt_corner ${p_corner}_${v_corner}_${t_corner}
set spef_cond  ${t_corner}_${rc_corner}

    if { [string match "ss*p125c*" ${corner}] } { set op_cond WCG1 } \
elseif { [string match "ss*m40c*"  ${corner}] } { set op_cond WCG2 } \
elseif { [string match "ff*m40c*"  ${corner}] } { set op_cond BCG1 } \
elseif { [string match "ff*p125c*" ${corner}] } { set op_cond BCG2 } \
elseif { [string match "*tt*"      ${corner}] } { set op_cond TT } \
else   { echo "ERROR : Need to check corner, ${corner}" ; exit }

#- Design Variables
set top_name       ${prj_name}
set all_blks       $env(all_blks)

#- PATH setup
#set PRJ_HOME        "$env(prj_base)/${prj_name}"
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
set RUN_DIR     [regsub {/sta.*} [pwd] ""]

set DB_PATH           "${PRJ_HOME}/db"
set OUTFEED_PATH      "${PRJ_HOME}/outfeeds"
set PI_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
set PD_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
set PD_DONE_FILE      "${PD_OUT_PATH}/SMC.done"

set COMMON_PATH       "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
set RUN_COMMON_PATH   "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
set COMMON_STA_PT     "${COMMON_PATH}/globals/pi/sta_pt"
set RUN_COMMON_STA_PT "${RUN_COMMON_PATH}/globals/pi/sta_pt"


###############################################
#- ovars.tcl
###############################################
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

if { [file exist ${RUN_DIR}/sta_pt/sta_pt_teco.tcl] } {
    source -e -v ${RUN_DIR}/sta_pt/sta_pt_teco.tcl
}

###############################################
#- set_app_var
###############################################
set_app_var report_default_significant_digits 4
set_app_var timing_report_unconstrained_paths true
# set_app_var link_keep_unconnected_cells true
# set_app_var timing_early_launch_at_borrowing_latches false

if { [file exist ${COMMON_STA_PT}/set_user_variables.tcl] } {
    redirect -tee ./logs/user_variables.tcl {
        source -e -v ${COMMON_STA_PT}/set_user_variables.tcl
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

if { $PT_VERSION >= 2021.06 } {
    # timing_slew_threshold_scaling_for_max_transition_compatibility has been made obsolete starting with the S-2021.06 release of PrimeTime and is no longer supported. (PT-008)
} else {
    set_app_var timing_slew_threshold_scaling_for_max_transition_compatibility true
}


###############################################
# lib setup
###############################################
source -e -v ${COMMON_STA_PT}/lib_setup.tcl

# read design
if { ${pre_post} == "pre" } {
#    TODO: flatten STA
#    if { [string match dsc_decode $top_design] } {
#        if { [llength $ASSEM_SUBS] > 0 } {
#            foreach obj $ASSEM_SUBS {
#                set SUB_NET /${DB_PATH}/vers/$ws/design/v/${ASSEM_SUBS}_syn.v
#                if { [file exist $SUB_NET] } {
#                    echo "INFO : SUB_NET - ${SUB_NET}"
#                    read_verilog ${SUB_NET}
#                } else {
#                    echo "ERROR : NO NETLIST - ${SUB_NET}"
#                    sh touch :ABNORMAL_ERROR_NETLIST
#                    exit
#                }
#            }
#        }
#    }

    # RTL
    # TODO: syn run_ver?
    if { [regexp rtl- ${design_ver}] } {
        # DC
        if { [regexp -nocase dc ${run_ver}] && ![regexp -nocase dcg ${run_ver}] } {
            set NETLIST ${RUN_DIR}/syn_dc/results/${top_design}.incr.v

        # DCG
        } elseif { [regexp -nocase dcg ${run_ver}] } {
            set NETLIST ${RUN_DIR}/syn_dc/results/${top_design}.incr.v

        } else {
            echo "ERROR : The netlist for performing STA is parsed based on $\{run_ver\}"
            echo "        $\{run_ver\} should indicate whether the synthesis was done with \"dc\" or \"dcg\"."
            echo "        ex) 01_dc_for_gen_def"
            echo "        ex) 02_dcg_def_v01"
            sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
            exit

        }

    # TODO: netlist name?
    } elseif { [regexp dc- ${design_ver}] } {
        set NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v

    } elseif { [regexp dcg- ${design_ver}] } {
        set NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v
    
    } else {
        echo "ERROR : need2chk $\{design_ver\}"
        sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
        exit

    }

} elseif { ${pre_post} == "post" } {
    set NETLIST ${PD_OUT_PATH}/netlist/${top_design}.v
}

if { [file exist ${NETLIST}] } {
    echo "info : net - ${NETLIST}"
    echo "NETLIST : ${NETLIST}" > net_spef_info
    read_verilog ${NETLIST}

} else {
    echo "ERROR : NO NETLIST - ${NETLIST}"
    sh touch :ABNORMAL_ERROR_NO_NETLIST
    exit

}

# link design
current_design ${top_design}
link > ./logs/link.log

# read parasitics
if { ${pre_post} == "post" } {
    set SPEF ${PD_OUT_PATH}/spef/${top_design}.spef.${spef_cond}.gz
    if { [file exist ${SPEF}] } {
        echo "INFO : SPEF - ${SPEF}"
        echo "SPEF    : ${SPEF}" >> NET_SPEF_INFO
        read_parasitics -keep_capacitive_coupling ${SPEF}
    } else {
        echo "Error : NO SPEF - ${SPEF}"
        sh touch :ABNORMAL_ERROR_SPEF
        exit
    }
}

# TODO: Pre-Source
# if { ${pre_post} == "post" } {
#     if { [file exists /mnt/data/prjs/RDP180XP/pi/post/sta/${top_design}/${SYN_VERSION}.${PD_RUN_VERSION}/pre_source_eco/${ECO_VERSION}.tcl] } {
#         source -e -v /mnt/data/prjs/RDP180XP/pi/post/sta/${top_design}/${SYN_VERSION}.${PD_RUN_VERSION}/pre_source_eco/${ECO_VERSION}.tcl > pre_source_${ECO_VERSION}.log
#         echo "INFO : PRE_ECO - /mnt/data/prjs/RDP180XP/pi/post/sta/${top_design}/${SYN_VERSION}.${PD_RUN_VERSION}/pre_source_eco/${ECO_VERSION}.tcl"
#     }
# }

# TODO: case- design_ver/pre_post
# read_sdc
set SDC "${DB_PATH}/vers/${db_ver}/design/sdc/${top_design}.sdc"
if { [file exist ${SDC}] } {
    redirect -tee ./logs/read_constraint.log {
        echo "INFO : SDC - ${SDC}"
        source -e -v ${SDC}
    }
} else {
    echo "ERROR : NO SDC - ${SDC}"
    sh touch :ABNORMAL_ERROR_SDC
    exit
}

# TODO: MBIST @FUNC -> merge SDC as misn?
#if { [file exist $MBIST_SDC] } {
#    redirect -tee -append {
#        echo "INFO : SOURCE .. $MBIST_SDC"
#        source -e -v $MBIST_SDC
#    }
#}

if { ${pre_post} == "pre" } {
    # treat high fanout net as ideal
    set max_fanout 32
    source -e -v ${COMMON_STA_PT}/HFN.tcl > ./HFN.log

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

#################################
# set ocv margin & clock uncertainty
#################################
if { ${pre_post} == "pre" } {
    # Setup Uncertainty @pre
    #  -> setup_uncertainty = 0.05 * $period + $setup_extra_margin
    set setup_extra_margin 0.00
    source ${COMMON_STA_PT}/gen_setup_uncertainty.pre_sta.tcl
    gen_setup_uncertainty setup_uncertainty.pre_sta.scr
    source -e -v ./setup_uncertainty.pre_sta.scr

} elseif { ${pre_post} == "post" } {
    # Apply OCV Derate
    reset_timing_derate

    if { [file exist ${COMMON_STA_PT}/aocv_setup.22eHVG_7T.tcl]} {
         source -e -v ${COMMON_STA_PT}/aocv_setup.22eHVG_7T.tcl 

    } else {
        echo "ERROR : Need to check OCV margin, ${corner}"
        exit

    }

    # Setup Uncertainty @POST
    #  -> setup_uncertainty = 0.03 * $period + $setup_extra_margin
    # PLL Jitter + 50 ps (Sign-off Criteria for 0.8V Operation)
    set setup_extra_margin [expr 0.05 + $ovars(sta_pt,extra_setup_uncert)]
    source ${COMMON_STA_PT}/gen_setup_uncertainty.post_sta.tcl
    gen_setup_uncertainty setup_uncertainty.scr
    source -e -v ./setup_uncertainty.scr

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

#- set group_path
set clock_ports [get_ports -filter "is_clock_network"]
group_path -name IN2REG  -from [remove_from_collection [all_input] $clock_ports]
group_path -name REG2OUT -to [all_outputs]
group_path -name IN2OUT  -from [remove_from_collection [all_inputs] $clock_ports] -to [all_outputs]

#################################
# update timing
#################################
update_timing -full > ./reports/update_timing.rpt

sh date

if { ${pre_post} == "post" } {
    source ${COMMON_STA_PT}/report_unanno_net_analysis.tcl
    report_annotated_parasitics -list_not_annotated -max 1000000 > ./reports/pt_unannotated_net.log
    report_unanno_net_analysis ./reports/pt_unannotated_net.log > ./reports/summary_unannotated_net.rpt

    # Check OCV
    report_timing_derate -incr -sig 4 > ./reports/report_timing_derate_check_OCV.rpt
}

#################################
# save session
#################################
save_session session.${mode}_${corner}
sh touch SAVE_SESSION_DONE
sh date

# write sdc
if { ${pre_post} == "pre" } {
    write_sdc -nos ./sdc/${top_design}.${mode}.sdc
}

#################################
# reports
#################################
report_clock -nos > ./reports/clocks.rpt
check_timing -verbose -include {signal_level clock_crossing} > ./reports/check_timing.rpt
report_case_analysis -nosplit > ./reports/case_analysis.rpt
report_analysis_coverage -nos -status_details {untested violated} -sort_by slack \
    -check_type {setup hold recovery removal min_period clock_gating_setup clock_gating_hold out_setup out_hold} \
    -exclude_untested {constant_disabled mode_disabled user_disabled no_paths false_paths} > ./reports/analysis_coverage.rpt

# check Vth & GC
source ${COMMON_STA_PT}/report_Vth.tcl
vth_rpt > ./reports/cell_vth.rpt

# check_clock_tree_cells
source ${COMMON_STA_PT}/check_clock_tree_cells.tbc
check_clock_tree_cells -verbose
#file delete chk_clk_tree.cell_usage chk_clk_tree.cell_usage.sort_by_ref_name

#set CTS_CELL_TYPE "_lvt"
#source ${COMMON_STA_PT}/clock_network_check.tcl
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

if { ${pre_post} == "post" } {
    # PBA Report
    report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba)                               > ./reports/all_violators.$ovars(sta_pt,pba).rpt
    report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -max_delay -recovery          > ./reports/all_violators.max_delay.$ovars(sta_pt,pba).rpt
    report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -min_delay -removal           > ./reports/all_violators.min_delay.$ovars(sta_pt,pba).rpt
    report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -max_delay -recovery -verbose > ./reports/all_violators.max_delay.$ovars(sta_pt,pba).rpt.verbose
    report_constraint -nos -sig 4 -all_violators -pba_mode $ovars(sta_pt,pba) -min_delay -removal  -verbose > ./reports/all_violators.min_delay.$ovars(sta_pt,pba).rpt.verbose

    report_global_timing -pba_mode $ovars(sta_pt,pba) > ./reports/global_timing.$ovars(sta_pt,pba).rpt

    # check clock delta delay
    source ${COMMON_STA_PT}/report_clk_net_delta_delay.tcl
    report_clk_net_delta_delay > ./reports/shielding_check_${mode}_${corner}.rpt

    # check noise
    check_noise -nos -verbose > ./reports/check_noise.rpt
    update_noise > ./reports/update_noise.rpt
    report_noise -nos -all_violators -sig 3 > ./reports/gnoise_viols_${corner}.rpt

}

#*****************************************************************************************
# MTTV report
#*****************************************************************************************
source ${COMMON_STA_PT}/mttv.tcl
mttv ./reports/all_violators.max_transition.rpt ./reports/mttv_${mode}_${corner}.rpt

source -e -v ${COMMON_STA_PT}/mttv_check.22eHVG_7T.tcl

#*****************************************************************************************
# write_sdf
#*****************************************************************************************
if { ${pre_post} == "post" && $ovars(sta_pt,gen_sdf) } {
    reset_timing_derate
    update_timing -full

    file mkdir ./SDF
    write_sdf -version 3.0 -compress gzip \
        -exclude checkpins -context verilog -input_port_nets -significant 3 \
        -no_edge -no_edge_merging timing_checks -include {SETUPHOLD RECREM } \
        ./SDF/${top_design}.${mode}_${corner}.sdf
}


# write hack_sdf
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


# TODO: timing window file
if { ${pre_post} == "post" } {
        if { [regexp ff_0p88v_m40c_cmin ${corner}] || [regexp ss_0p72v_p125c_cmax ${corner}] } {
            source ${COMMON_STA_PT}/pt2timing.tcl
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
#           if { ![file exist ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file] } {
#               file mkdir ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file
#           }
#           file copy -force ${top_design}.${corner}.${mode}.timing ${PD_OUT_PATH}/layout/${SYN_VERSION}.${PD_RUN_VERSION}/${ECO_VERSION}/timing_window_file
        }
}

sh touch STA_PT_END

exit
