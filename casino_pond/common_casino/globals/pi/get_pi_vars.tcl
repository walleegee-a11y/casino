#!/usr/bin/env tclsh

###############################################
#- Determine ${stage_depth}
###############################################
#        0 1   2    3    4       5                  6          7                           8    9                                  10     11      12
# case 1) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_PI_RUN-00_PD_RUN-fe00_te00_pv00/sta_pt/${mode}/${corner}
# case 2) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_PI_RUN-00_PD_RUN-fe00_te00_pv00/sta_pt/dmsa/${dmsa_dir}
# case 3) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_PI_RUN-00_PD_RUN-fe00_te00_pv00/other_steps
# pre   ) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_PI_RUN/${stage}
# Split the current working directory into parts
set path_parts  [split [pwd] "/"]
set stage_depth [expr [llength $path_parts] - 1]

#- Determine the stage and adjust for specific cases
if {[regexp {/sta_pt/} [pwd]] && ![regexp {/dmsa/} [pwd]]} {
    # Case 1: ~/sta_pt/mode/corner
	set stage       [lindex ${path_parts} end-2]
    set stage_depth [expr {${stage_depth} - 2}]

} elseif {[regexp {/dmsa/} [pwd]]} {
    # Case 2: ~/sta_pt/dmsa/dmsa_*
	set stage       [lindex ${path_parts} end-1]
    set stage_depth [expr {${stage_depth} - 2}]

} else {
    # Case 3: ~/other_steps
	set stage       [lindex ${path_parts} end]

}

###############################################
#- Set path variables
###############################################
set prj_name   [lindex ${path_parts} [expr {${stage_depth} - 6}]]
set top_design [lindex ${path_parts} [expr {${stage_depth} - 4}]]
set ws         [lindex ${path_parts} [expr {${stage_depth} - 3}]]
set run_ver    [lindex ${path_parts} [expr {${stage_depth} - 1}]]

#- from ${ws}
regexp {^([^_]+)___(.*)$} $ws match role db_ver
set design_ver  [lindex [split ${db_ver} _] 0] ;# rtl-0.0
set dk_ver      [lindex [split ${db_ver} _] 1] ;# dk-0.0
set dk_ver_tag  [lindex [split ${db_ver} _] 2] ;# tag-0.0


#- PRJ/COMMON_PATH
#set PRJ_HOME        "$env(prj_base)/${prj_name}"
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
set DB_PATH           "${PRJ_HOME}/dbs"

set OUTFEED_PATH      "${PRJ_HOME}/outfeeds"
set PI_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
set PD_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
set PD_DONE_FILE      "${PD_OUT_PATH}/SMC.done"

set COMMON_PATH       "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
set RUN_COMMON_PATH   "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
set RUN_PATH          "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}"

set COMMON_SYN_DC      "${COMMON_PATH}/globals/pi/syn_dc"
set COMMON_STA_PT      "${COMMON_PATH}/globals/pi/sta_pt"
set COMMON_DMSA        "${COMMON_PATH}/globals/pi/dmsa"
set COMMON_LDRC_DC     "${COMMON_PATH}/globals/pi/ldrc_dc"
set COMMON_LEC_FM      "${COMMON_PATH}/globals/pi/lec_fm"
set COMMON_VCLP        "${COMMON_PATH}/globals/pi/vclp"
set RUN_COMMON_SYN_DC  "${RUN_COMMON_PATH}/globals/pi/syn_dc"
set RUN_COMMON_STA_PT  "${RUN_COMMON_PATH}/globals/pi/sta_pt"
set RUN_COMMON_DMSA    "${RUN_COMMON_PATH}/globals/pi/dmsa"
set RUN_COMMON_LDRC_DC "${RUN_COMMON_PATH}/globals/pi/ldrc_dc"
set RUN_COMMON_LEC_FM  "${RUN_COMMON_PATH}/globals/pi/lec_fm"
set RUN_COMMON_VCLP    "${RUN_COMMON_PATH}/globals/pi/vclp"

###############################################
#- Design Variables
###############################################
set top_name       ${prj_name}
set all_blks       $env(casino_all_blks)

#- from ${run_ver}
set pi_ver      [lindex [split ${run_ver} -] 0] ;# < 00_PI_RUN >
set pd_ver      [lindex [split ${run_ver} -] 1] ;# < 00_PD_RUN >
set eco_num     [lindex [split ${run_ver} -] 2] ;# < fe00_te00_pv00 >

set te_num      [lindex [split ${eco_num} _] 1] ;# < te00 >

    if {(${pd_ver} == "") && (${eco_num} == "")} { set pre_post "pre" }  \
elseif {[regexp {fe.*_te.*_pv.*} ${eco_num}]}    { set pre_post "post" } \
else   { echo "ERROR : Need to check run_ver, ${run_ver}" ; exit }

