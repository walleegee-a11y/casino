#!/usr/bin/env tclsh

# TODO: Env Variables, have to be setenv in Casino Flow
#    0 1   2    3    4       5                  6          7                           8    9                                10     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_pi_run-01_IMSI-fe00_te00_pv00/sta_pt/dmsa

#- Setting environment variables based on the current directory
set prj_name   [lindex [split [pwd] "/"] end-7]
set top_design [lindex [split [pwd] "/"] end-5]
set ws         [lindex [split [pwd] "/"] end-4]
set run_ver    [lindex [split [pwd] "/"] end-2]
set stage      [lindex [split [pwd] "/"] end]

regexp {^([^_]+)___(.*)$} $ws match role db_ver
set run_dir [string map {"/sta_pt" ""} [pwd]]

#- PATH setup
#set PRJ_HOME        "$env(prj_base)/${prj_name}"
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
set DB_PATH         "${PRJ_HOME}/db"

set OUTFEED_PATH    "${PRJ_HOME}/outfeeds"
set PI_OUT_PATH     "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
set PD_OUT_PATH     "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
set PD_DONE_FILE    "${PD_OUT_PATH}/SMC.done"

set COMMON_PATH     "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
set RUN_COMMON_PATH "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
set COMMON_DMSA     "${COMMON_PATH}/globals/pi/dmsa"
set RUN_COMMON_DMSA "${RUN_COMMON_PATH}/globals/pi/dmsa"

#- source ovars.tcl
source ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

# Loop through modes and corners
foreach mode $ovars(dmsa,modes) {
    foreach corner $ovars(dmsa,corners) {
        if {[string length $corner] > 0} {
            puts "${mode}.${corner}"

            # Wait for the SAVE_SESSION_DONE file
            set session_done "./../${mode}/${corner}/SAVE_SESSION_DONE"
            while {![file exists ${session_done}]} {
                puts "waiting save session : ${mode}/${corner}"
                after 10000  ;# Sleep for 10 seconds
            }
        }
        puts "session done ${mode}/${corner}"
    }
}

# Setup run_dmsa_dir
set cur_time [exec date +%y%m%d_%H%M]
    if { !$ovars(dmsa,physical_aware) } { set log_or_phy "logical" } \
elseif {  $ovars(dmsa,physical_aware) } { set log_or_phy "physical" }

set run_dmsa_dir "dmsa_${log_or_phy}_${cur_time}"
if {[file exists ${run_dmsa_dir}]} {
	file delete ${run_dmsa_dir}_old
	exec mv -f ${run_dmsa_dir} ${run_dmsa_dir}_old
}
file mkdir ${run_dmsa_dir}

# Copy files
file copy ${COMMON_DMSA}/run_dmsa.tcl ${run_dmsa_dir}
if {[file exists ./$ovars(dmsa,pre_source)]} {
    file copy ./$ovars(dmsa,pre_source) ${run_dmsa_dir}
}

# Run pt_shell with xterm
cd ${run_dmsa_dir}
exec xterm -T ${run_dmsa_dir} -e "pt_shell -multi -f ./run_dmsa.tcl -output_log_file ./dmsa_master_eco.log" &
