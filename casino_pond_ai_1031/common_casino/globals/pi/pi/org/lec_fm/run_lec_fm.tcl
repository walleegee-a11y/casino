sh touch LEC_FM_START

##################################################
# Environment variables
##################################################
# #- from [pwd]
# #    0 9   8    7    6       5                  4          3                           2    1                                0
# # ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_pi_run-01_IMSI-fe00_te00_pv00/lec_fm
# set prj_name   [lindex [split [pwd] "/"] end-6]
# set top_design [lindex [split [pwd] "/"] end-4]
# set ws         [lindex [split [pwd] "/"] end-3]
# set run_ver    [lindex [split [pwd] "/"] end-1]
# set stage      [lindex [split [pwd] "/"] end-0]
# 
# set RUN_PATH   [regsub {/lec_fm.*} [pwd] ""]
# 
# #- from ${ws}
# regexp {^([^_]+)___(.*)$} $ws match role db_ver
# set design_ver  [lindex [split ${db_ver} _] 0] ;# rtl-0.0
# set dk_ver      [lindex [split ${db_ver} _] 1] ;# dk-0.0
# set dk_ver_tag  [lindex [split ${db_ver} _] 2] ;# tag-0.0
# 
# #- from ${run_ver}
# set pi_ver      [lindex [split ${run_ver} -] 0] ;# < 00_dc_init >
# set pd_ver      [lindex [split ${run_ver} -] 1] ;# < 00_PD_RUN >
# set eco_num     [lindex [split ${run_ver} -] 2] ;# < fe00_te00_pv00 >
# 
#     if { ${eco_num} == "" }               { set pre_post "pre" } \
# elseif {[regexp fe.*te.*pv.* ${eco_num}]} { set pre_post "post" } \
# else   { echo "ERROR : Need to check run_ver, ${run_ver}" ; exit }
# 
# #TODO: multi-level LEC
# #- Design Variables
# #set top_name       ${prj_name}
# #set all_blks       $env(all_blks)
# 
# #- PATH setup
# set PRJ_HOME        "$env(prj_base)/${prj_name}"
# eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
# set DB_PATH           "${PRJ_HOME}/db"
# 
# set OUTFEED_PATH      "${PRJ_HOME}/outfeeds"
# set PI_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
# set PD_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
# set PD_DONE_FILE      "${PD_OUT_PATH}/SMC.done"
# 
# set COMMON_PATH       "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
# set RUN_COMMON_PATH   "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
source -e -v $env(COMMON_PATH)/globals/pi/get_path_vars.tcl


##################################################
# ${prj_name}.ovars.tcl
##################################################
#TODO: ovars.tcl
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

##################################################
# formality configuration
##################################################
set hdlin_ignore_full_case false
set hdlin_ignore_parallel_case false
set hdlin_dyn_array_bnd_check none
#set hdlin_unresolved_modules black_box
 
set hdlin_allow_partial_pg_netlist true
set hdlin_dwroot /mnt/appl/Tools/synopsys/Design_Compiler/syn/Q-2019.12-SP5-2
set verification_failing_point_limit 1000
#set verification_set_undriven_signals X
set verification_effort_level high
set verification_verify_unread_tech_cell_pins true
set verification_clock_gate_edge_analysis true
set svf_presto_parameter_naming true


##########################################################
## Set SVF                                              ##
##########################################################
if { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
	if { [file exists ${RUN_PATH}/syn_dc/results/${top_design}.svf] } {
        set svf ${RUN_PATH}/syn_dc/results/${top_design}.svf
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

##################################################
# Read REF Netlist
##################################################
#set RTL or NETLIST for reference design
#- r2n
if { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
    set ref_type "rtl"
    set reference ${DB_PATH}/vers/${db_ver}/design/rtl/${top_design}.rtl_list.f ;#RTL to NETLIST 

#- n2n
} else {
    set ref_type "net"
    set reference ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${pi_ver}/netlist/${top_design}_syn.v ;#TODO: need2chk syn results netlist name

}

##USER_DEFINE(ovar.tcl)
if {(${ovars(lec_fm,user_ref)} != "") && [file exist ${ovars(lec_fm,user_ref)}] } {
    set reference $ovars(lec_fm,user_ref)

}

if { ${ref_type} == "rtl" } {
    read_verilog -container r -libname WORK -f ${reference}

} elseif { ${ref_type} == "net" } {
    read_verilog -container r -libname WORK -netlist ${reference}

}

##BBOX
if { ${ovars(lec_fm,bbox)} != "" } {
read_verilog -container r -libname WORK -netlist ${ovars(lec_fm,bbox)}
}

set_top r:/WORK/${top_design}

##################################################
# Read IMP Netlist
##################################################
#set NETLIST for implimentation design
if { ${ovars(lec_fm,user_imp)} != "" } {
    set implimentation ${ovars(lec_fm,user_imp)}

} else {
    if { (${ref_type} == "rtl") && ($pd_ver == "") } {
        set implimentation ${RUN_PATH}/syn_dc/results/${top_design}_syn.v
    } else { 
        set implimentation ${PD_OUT_PATH}/netlist/${top_design}.v
    }
}

if { [regexp rtl- ${design_ver}] && (${pre_post} == "pre") } {
    set implimentation ${RUN_PATH}/syn_dc/results/${top_design}_syn.v

} else {
    set implimentation ${PD_OUT_PATH}/netlist/${top_design}.v

}

##USER_DEFINE(ovar.tcl)
if {(${ovars(lec_fm,user_imp)} != "") && [file exist ${ovars(lec_fm,user_imp)}] } {
    set implimentation ${ovars(lec_fm,user_imp)}

}

read_verilog -container i -netlist ${implimentation} 

##BBOX
if { ${ovars(lec_fm,bbox)} != "" } {
read_verilog -container i -libname WORK -netlist ${ovars(lec_fm,bbox)}
}

set_top i:/WORK/${top_design}

##################################################
# Set constant
##################################################

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

#reports 
report_unmatched_points              > ./reports/${top_design}.unmatched_point.rpt
report_failing_points                > ./reports/${top_design}.failing_point.rpt
report_matched_points -status unread > ./reports/${top_design}.unread_point.rpt
report_matched_points -status const  > ./reports/${top_design}.const_point.rpt
report_black_box                     > ./reports/${top_design}.black_box.rpt
report_loop                          > ./reports/${top_design}.loop.rpt

##################################################
# Done
##################################################
sh touch LEC_FM_DONE
exit

