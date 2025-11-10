sh date
sh touch VCLP_START
##########################################################################################################################################################################################################
### - SETUP VCLP - ###
##########################################################################################################################################################################################################
source -e -v $env(RUN_COMMON_PATH)/globals/pi/get_pi_vars.tcl
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

#set_app_var ignore_unconnected_load true
#set_app_var ignore_unconnected_driver true
#set_app_var autobb_unresolved_modules false
#set_app_var ignore_multiple_module_def true
#set_app_var ignore_error_on_name_collision true
#set_app_var physical_only_cell true
## SYN
#set upf_hetero_fanout_isolation true
#set enable_local_policy_match true
#set dump_crossover true
# DFT
set upf_hetero_fanout_isolation true
#set enable_local_policy_match true
set dump_crossover true
# RODFT
#set upf_hetero_fanout_isolation true
#set enable_local_policy_match true
#set dump_crossover true

set_app_var sh_continue_on_error true
set_app_var handle_hanging_crossover true
set_app_var enable_local_policy_match true
set_app_var upf_iso_filter_elements_with_applies_to ENABLE
set_app_var enable_multi_driver_analysis true
set_app_var enable_verdi_debug true

set_message_severity -names UPF_SUPPLY_PORT_IMPLICIT_CONNECTION error

set_app_var report_lp_limit 100000

# read db
source -e -v ${RUN_COMMON_VCLP}/tech_lib.tcl

# set input files
if { ${pre_post} == "pre" } {
	if { [regexp rtl- ${design_ver}] } {
		if { [regexp -nocase dc ${run_ver}] && ![regexp -nocase dcg ${run_ver}] } {
			set NETLIST ${RUN_PATH}/syn_dc/results/${top_design}.incr.v
			set UPF     ${RUN_PATH}/syn_dc/results/${top_design}.upf
		} elseif { [regexp -nocase dcg ${run_ver}] } {
			set NETLIST ${RUN_PATH}/syn_dc/results/${top_design}.incr.v
			set UPF     ${RUN_PATH}/syn_dc/results/${top_design}.upf
		} else {
			echo "ERROR : The netlist for performing STA is parsed based on $\{run_ver\}"
			echo "        $\{run_ver\} should indicate whether the synthesis was done with \"dc\" or \"dcg\"."
			echo "        ex) 01_dc_for_gen_def"
			echo "        ex) 02_dcg_def_v01"
			sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
			sh chmod +s :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
			exit
		}
	} elseif { [regexp net- ${design_ver}] } {
		set NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v
		set UPF     ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.upf
###	} elseif { [regexp dcg- ${design_ver}] } {
###		set NETLIST ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v
###		set UPF ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.upf
	} else {
		echo "ERROR : need2chk $\{design_ver\}"
		sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
		sh chmod +s :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
		exit
	}
} elseif { ${pre_post} == "post" } {

    set NETLIST [list ${PD_OUT_PATH}/netlist/${top_design}.v]

    set need_subblocks 0
    if { [info exists ovars(sta_pt,is_flatten)] && $ovars(sta_pt,is_flatten) == 1 } {
        set need_subblocks 1
    }

    if { $need_subblocks } {
        if { [info exists ovars(sta_pt,sub_block_list)] && $ovars(sta_pt,sub_block_list) != "" } {
            set sub_block_list $ovars(sta_pt,sub_block_list)
        } else {
            # Except TOP netlist
            set sub_block_list [lminus $all_blks $top_design]
        }
        foreach sub_block $sub_block_list {
            # BLK version => ovars(sta_pt,sub_block_version,*)
            if { [info exists ovars(sta_pt,sub_block_version,${sub_block})] } {
                set sb_ver $ovars(sta_pt,sub_block_version,${sub_block})
            } else {
                echo "WARN : no version set for sub-block '${sub_block}', use 'latest' semantics or fail as needed."
                set sb_ver "*"
            }
            lappend NETLIST ${OUTFEED_PATH}/${sub_block}/pd___${db_ver}/${sb_ver}/netlist/${sub_block}.v
        }
    }

    if { $need_subblocks } {
        set UPF ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.flatten.upf
    } else {
        set UPF ${DB_PATH}/vers/${db_ver}/design/upf/${top_design}.upf
    }

    # TODO : post UPF & PG netlist
    # TODO : check_pg
    # set PG_NETLIST ${PD_OUT_PATH}/netlist/${top_design}.pg.v
    # set UPF ${PD_OUT_PATH}/netlist/${top_design}.upf
}

# read design
if { [llength $NETLIST] > 0 } {
    sh rm -f ./NET_UPF_INFO
    foreach net $NETLIST {
        echo "NETLIST : ${net}" >> ./NET_UPF_INFO
        echo "read_verilog ${net}"
        read_verilog -netlist ${net}
    }

    echo "# read design (list)" >> ./NET_UPF_INFO
    echo "read_verilog -netlist \{$NETLIST\}" >> ./NET_UPF_INFO
    read_verilog -netlist ${NETLIST}

    sh mkdir -p ./logs ./reports
    current_design $top_design
    link_design $top_design > ./logs/link.log
    report_link >> ./reports/link.rpt

    set cnt 0
    if { [file exists ./reports/link.rpt] } {
        set fin [open ./reports/link.rpt r]
        while { [gets $fin line] >= 0 } {
            if { [regexp {Unresolved} $line] } {
                echo "ERROR : Unresolved reference found in link report"
                sh touch :ABNORMAL_ERROR_LINK
                sh chmod +s :ABNORMAL_ERROR_LINK
                incr cnt
                break
            }
        }
        close $fin
    } else {
        echo "ERROR : Missing link report ./reports/link.rpt"
        sh touch :ABNORMAL_ERROR_MISSING_LINK_RPT
        sh chmod +s :ABNORMAL_ERROR_MISSING_LINK_RPT
        exit 1
    }

    if { $cnt > 0 } {
        exit 1
    }

    # read UPF
    if { [info exists UPF] && $UPF ne "" } {
        if { [file exists $UPF] } {
            echo "UPF    : ${UPF}" >> ./NET_UPF_INFO
            echo "read_upf ${UPF}"
            read_upf ${UPF}
        } else {
            echo "ERROR : UPF file not found - ${UPF}"
            sh touch :ABNORMAL_ERROR_NO_UPF_FILE
            sh chmod +s :ABNORMAL_ERROR_NO_UPF_FILE
            exit 1
        }
    } else {
        echo "WARN  : No UPF specified (var UPF missing or empty)"
    }

} else {
    echo "ERROR : NO NETLIST - ${NETLIST}"
    sh touch :ABNORMAL_ERROR_NO_NETLIST
    sh chmod +s :ABNORMAL_ERROR_NO_NETLIST
    exit 1
}


# check_lp & report
check_lp -force -stage upf
check_lp -force -stage design

report_lp          > ./reports/report_lp.b4waive.summary.rpt
report_lp -verbose > ./reports/report_lp.b4waive.rpt

# waiver
source -e -v ${RUN_COMMON_VCLP}/waiver.tcl

# report
report_lp          > ./reports/report_lp.summary.rpt
report_lp -verbose > ./reports/report_lp.rpt

#if { [ string match "POST" ${pre_post} ] && ${check_pg} == 1 } {
if { [ string match "post" ${pre_post} ] && $ovars(vclp,check_pg) == 1 } {
	check_lp -stage pg -force
	report_lp -verbose -file ./reports/report_lp.pg.rpt
}

checkpoint_session -session ${top_design}.session
sh touch VCLP_END
exit
