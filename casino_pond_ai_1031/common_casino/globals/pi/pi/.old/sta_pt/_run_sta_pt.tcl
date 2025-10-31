#!/usr/bin/env tclsh

# TODO: Env Variables, have to be setenv in Casino Flow
#    0 1   2    3    4       5                  6          7                           8    9                                10
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_pi_run-01_IMSI-fe00_te00_pv00/sta_pt

#- Setting environment variables based on the current directory
set prj_name   [lindex [split [pwd] "/"] end-6]
set top_design [lindex [split [pwd] "/"] end-4]
set ws         [lindex [split [pwd] "/"] end-3]
set run_ver    [lindex [split [pwd] "/"] end-1]
set stage      [lindex [split [pwd] "/"] end]

regexp {^([^_]+)___(.*)$} $ws match role db_ver
set run_dir [string map {"/sta_pt" ""} [pwd]]

#- PATH setup
#set PRJ_HOME        "$env(prj_base)/${prj_name}"
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
set DB_PATH         "${PRJ_HOME}/db"

set OUTFEED_PATH      "${PRJ_HOME}/outfeeds"
set PI_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
set PD_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
set PD_DONE_FILE      "${PD_OUT_PATH}/SMC.done"

set COMMON_PATH       "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
set RUN_COMMON_PATH   "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
set COMMON_STA_PT     "${COMMON_PATH}/globals/pi/sta_pt"
set RUN_COMMON_STA_PT "${RUN_COMMON_PATH}/globals/pi/sta_pt"

#- source ovars.tcl
source ${RUN_COMMON_PATH}/user_define/${prj_name}.ovars.tcl

#TODO waiting SPEF @post
# Wait for the done file to appear
#while {![file exists $PD_DONE_FILE]} {
#    puts "[clock format [clock seconds]]: waiting export ($PD_DONE_FILE)"
#    after 60000
#}


# Loop through modes and corners
foreach mode $ovars(sta_pt,modes) {
    foreach corner $ovars(sta_pt,corners) {
        if {[string length $corner] > 0} {
            puts "${mode}.${corner}"

            set run_sta_pt_dir "${run_dir}/sta_pt/${mode}/${corner}"
            exec mkdir -p ${run_sta_pt_dir}
            cd ${run_sta_pt_dir}

            # Copy the required files and set permissions
            file copy -force ${COMMON_STA_PT}/run_sta_pt.tcl .
#            exec chmod +x ./run_sta_pt.tcl

#            TODO: restoring session script
#            # Create restore session script
#            set restore_session_script ":restore_session.csh"
#            set restore_command "pt_shell -x 'restore_session session.${mode}_${corner}'"
#            set env_script "/mnt/data/prjs/CASINO/scott/design_flow/env_selector/synopsys_env.csh"
#
#            set restore_content "#! /usr/bin/env tclsh\n"
#            append restore_content "source $env_script\n"
#            append restore_content "$restore_command\n"
#            set restore_file [open $restore_session_script "w"]
#            puts $restore_file $restore_content
#            close $restore_file
#            exec chmod +x $restore_session_script

            # Execute pt_shell in a new terminal
            exec xterm -T "${run_ver}/sta/${mode}/${corner}" -e "pt_shell -f run_sta_pt.tcl -output_log_file ./logs/sta_pt.log" &

            # Go back to the original directory
            cd ${run_dir}/sta_pt

        } else {
            # Handle error or log the case where the corner is empty
            puts "ERROR! ${mode}.${corner}"
        }
    }
}
