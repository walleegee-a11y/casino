#!/usr/bin/env tclsh

###############################################
#- path setup
###############################################
#    0 1   2    3    4       5                  6          7                           8    9                                10     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_pi_run-01_IMSI-fe00_te00_pv00/sta_pt/dmsa
set path_parts  [split [pwd] "/"]
set path_length [llength ${path_parts}]
set stage       [lindex ${path_parts} end]
if {${stage} eq "dmsa"} { set path_length [expr ${path_length} - 1] }

set prj_name   [lindex ${path_parts} [expr {${path_length} - 7}]]
set top_design [lindex ${path_parts} [expr {${path_length} - 5}]]
set ws         [lindex ${path_parts} [expr {${path_length} - 4}]]
set run_ver    [lindex ${path_parts} [expr {${path_length} - 2}]]

set run_dir [string map {"/sta_pt" ""} [pwd]]
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base

set COMMON_PATH     "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
set RUN_COMMON_PATH "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"

###############################################
#- source ovars.tcl
###############################################
source ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

###############################################
#- Write the file "${prj_name}.${stage}.ovars.csh"
###############################################
set ovars_csh [open "${prj_name}.${stage}.ovars.csh" w]
puts $ovars_csh "# ${stage}"

foreach key [lsort [array names ovars]] {
    #- Check if the key matches the pattern "<stage>,*"
    if {[string match "${stage},*" $key]} {
        #- Extract the part of the key after "<stage>,"
#       set clean_key [string trimleft $key "${stage}\,"]
#		regexp {^(.+?),(.+)$} $key match prefix suffix
        #- Get the corresponding value from the array
    	set clean_key [string map {"," "_"} $key]
        set value $ovars($key)

        #- Write the formatted output to the file
        puts "setenv ${clean_key} \"${value}\""
        puts $ovars_csh "setenv ${clean_key} \"${value}\""
    }
}

#- Close the file
close $ovars_csh

