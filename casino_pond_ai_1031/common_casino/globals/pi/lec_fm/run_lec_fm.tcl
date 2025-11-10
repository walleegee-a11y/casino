##################################################
# Start
##################################################
#set_host_options -max_cores n ;#default core is 1

sh touch LEC_FM_START

##################################################
# formality Variable
##################################################
source -e -v $env(COMMON_PATH)/globals/pi/get_pi_vars.tcl

##################################################
# ${prj_name}.ovars.tcl
##################################################
#TODO: ovars.tcl
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

##################################################
# formality configuration
##################################################
set hdlin_ignore_full_case false                                                ;#ignore error by full case
set hdlin_ignore_parallel_case false                                            ;#ignore error by parallel case 
set hdlin_dyn_array_bnd_check none                                              ;#check whether in the out of range index case
#set hdlin_unresolved_modules black_box
 
set hdlin_allow_partial_pg_netlist true                                         ;#allow pg aware verification,but if upf file is exists, formality ignore this value
set hdlin_dwroot /mnt/appl/Tools/synopsys/Design_Compiler/syn/Q-2019.12-SP5-2   ;#

set verification_failing_point_limit 1000                                       ;#failing point limit
set verification_set_undriven_signals 0:X

set verification_effort_level high                                              ;#how detailed verification will be
set verification_verify_unread_tech_cell_pins true                              ;#create *unread* bbox to no load tech cell pins
set verification_clock_gate_edge_analysis true                                  ;#allow clock gating logic aware verification
set svf_presto_parameter_naming true                                            
##################################################
## Set SVF                                        
##################################################
if { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
	if { [file exists ${RUN_PATH}/syn_dc/results/${top_design}.mapped.svf] } {
        set svf ${RUN_PATH}/syn_dc/results/${top_design}.mapped.svf
        set_svf $svf

    }
}

##################################################
# DB Source
##################################################
set std_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/std/db/${ovars(pi,default_pvt)}/*]
foreach lib $std_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set mem_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/mem/db/${ovars(pi,default_pvt)}/*]
foreach lib $mem_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set io_ip_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/io_ip/db/${ovars(pi,default_pvt)}/*]
foreach lib $io_ip_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

read_db $link_library


## TODO(jake) Add flatten EQ condition (Revise read REF & IMP)
##################################################
# Read REF Netlist
##################################################
#set RTL or NETLIST for reference design

##USER_DEFINE(ovar.tcl)
if { ${ovars(lec_fm,is_flatten)} == "0" } {

    ## Default (No flatten)
    if { (${ovars(lec_fm,user_ref)} != "") && [file exist ${ovars(lec_fm,user_ref)}] } {
        set reference $ovars(lec_fm,user_ref)
        set ref_type "net"

    #- r2n
    } elseif { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
        set ref_type "rtl"
        set common_rtl_path   "${DB_PATH}/vers/${db_ver}/design/${ref_type}/common"
        eval set ${top_design}_rtl_path  "${DB_PATH}/vers/${db_ver}/design/${ref_type}/${top_design}"
        # RTL to NETLIST file list
        set reference ${DB_PATH}/vers/${db_ver}/design/rtl/${top_design}/${top_design}.rtl_list.f

    #- n2n
    } else {
        set ref_type "net"
        # set reference ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${pi_ver}/netlist/${top_design}.v ;# TODO: need2chk syn results netlist name
        set reference ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${pi_ver}/netlist/${top_design}.v          ;# TODO: need2chk syn results netlist name
    }

    if { ${ref_type} == "rtl" } {
        read_verilog -container r -libname WORK -f ${reference}
    } elseif { ${ref_type} == "net" } {
        read_verilog -container r -libname WORK -netlist ${reference}
    }

    ## BBOX (top_only)
    if { ${ovars(lec_fm,top_only)} == "1" } {
        if { ${ovars(lec_fm,bbox_1)} != "" } {
            read_verilog -container r -libname WORK -netlist ${ovars(lec_fm,bbox_1)}
        }
        if { ${ovars(lec_fm,bbox_2)} != "" } {
            read_verilog -container r -libname WORK -netlist ${ovars(lec_fm,bbox_2)}
        }
    }

} elseif { ${ovars(lec_fm,is_flatten)} == "1" } {

    ## Revision (Flatten)
    set ref_type "net"
    set implementation [list \
        ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${pi_ver}/netlist/${top_design}.v \
        ${OUTFEED_PATH}/fb_right/pi___${db_ver}/${pi_ver}/netlist/fb_right.v \
        ${OUTFEED_PATH}/fb_left/pi___${db_ver}/${pi_ver}/netlist/fb_left.v \
    ]

    foreach ref_net_itr $reference {
        read_verilog -container r -libname WORK -netlist ${ref_net_itr}
    }

} else {
    ## Else: blk ref net read (fallback)
    puts "BLK $top_design reference net read"
}

## set top once (avoid double-call)
set_top r:/WORK/$top_design

##################################################
# Read IMP Netlist
##################################################
#set NETLIST for implementation design
if { ${ovars(lec_fm,is_flatten)} == "0" } {

    ## Default (No flatten)
    if { ${ovars(lec_fm,user_imp)} != "" } {
        set implementation ${ovars(lec_fm,user_imp)}

    } elseif { (${ref_type} == "rtl") && ($pd_ver == "") } {
        set implementation ${RUN_PATH}/syn_dc/results/${top_design}_syn.v

    } else {
        set implementation ${PD_OUT_PATH}/netlist/${top_design}.v
    }

    # Override by design_ver/pre_post rule
    if { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
        set implementation ${RUN_PATH}/syn_dc/results/${top_design}_syn.v
    } else {
        set implementation ${PD_OUT_PATH}/netlist/${top_design}.v
    }

    ## USER_DEFINE(ovar.tcl)
    if { (${ovars(lec_fm,user_imp)} != "") && [file exist ${ovars(lec_fm,user_imp)}] } {
        set implementation ${ovars(lec_fm,user_imp)}
    }

    read_verilog -container i -libname WORK -netlist ${implementation}

    ## BBOX (top_only)
    if { ${ovars(lec_fm,top_only)} == "1" } {
        if { ${ovars(lec_fm,bbox_1)} != "" } {
            read_verilog -container i -libname WORK -netlist ${ovars(lec_fm,bbox_1)}
        }
        if { ${ovars(lec_fm,bbox_2)} != "" } {
            read_verilog -container i -libname WORK -netlist ${ovars(lec_fm,bbox_2)}
        }
    }

} elseif { ${ovars(lec_fm,is_flatten)} == "1" } {

    ## Revision (Flatten)
    set implementation [list \
        ${PD_OUT_PATH}/netlist/${top_design}.v \
        ${OUTFEED_PATH}/fb_right/pd___${db_ver}/$ovars(lec_fm,sub_block_version,fb_right)/netlist/fb_right.v \
        ${OUTFEED_PATH}/fb_left/pd___${db_ver}/$ovars(lec_fm,sub_block_version,fb_right)/netlist/fb_left.v \
    ]

    foreach imp_net_itr $implementation {
        read_verilog -container i -libname WORK -netlist ${imp_net_itr}
    }

} else {
    ## Else: blk implementation net read (fallback)
    puts "BLK $top_design implementation net read"
}

## set top once (avoid double-call)
set_top i:/WORK/$top_design

##################################################
# Set constant
##################################################
if { ${top_design} == "ANA6716" && $ovars(sta_pt,is_flatten) == 1 } {
    puts "INFO: no set_constant rule for $top_design"
    set_constant -type port r:/WORK/ANA6716/TCON/u_pads/u_mode_ctrl/u_scan_mode_dont/Z 0
    set_constant -type port i:/WORK/ANA6716/TCON/u_pads/u_mode_ctrl/u_scan_mode_dont/Z 0
} else {
    puts "INFO: no set_constant rule for $top_design"
}

##################################################
### Set dont verify
##################################################
#source /home1/PROJECT/ANA38411_Rev0/PI/4_Postlayout/lec/common/dont_verify.list
### set_dont_verify_points r:/WORK/ANA38411/u_pads/P_BreakCell_T2/PROT_N -type pin
### set_dont_verify_points i:/WORK/ANA38411/u_pads/P_BreakCell_T2/PROT_N -type pin

##################################################
# Verify
##################################################
verify

if {${verification_status} == "SUCCEEDED"} {
	sh touch LEC_FM_SUCCEEDED
} elseif {${verification_status} == "FAILED"} { 
    sh touch LEC_FM_FAILED
} elseif {${verification_status} == "INCONCLUSIVE"} { 
	sh touch LEC_FM_INCONCLUSIVE                        
} else { 
    sh touch LEC_FM_NOT_RUN
}

##################################################
# Report Gen
##################################################
#restore_session
save_session ${top_design}.session.fss -replace

write_hierarchical_verification_script -replace  ./reports/pre_verify_fail.log.v

#reports 
report_unmatched_points              > ./reports/${top_design}.unmatched_point.rpt
report_failing_points                > ./reports/${top_design}.failing_point.rpt
report_matched_points -status unread > ./reports/${top_design}.unread_point.rpt
report_matched_points -status const  > ./reports/${top_design}.const_point.rpt
report_black_box                     > ./reports/${top_design}.black_box.rpt
report_loop                          > ./reports/${top_design}.loop.rpt
report_aborted_points                > ./reports/${top_design}.aborted_point.rpt
report_unverified_points             > ./reports/${top_design}.unverified_point.rpt
report_hdlin_mismatches              > ./reports/${top_design}.hdlin_mismatches.rpt
##################################################
# Done
##################################################
sh touch LEC_FM_DONE
exit

