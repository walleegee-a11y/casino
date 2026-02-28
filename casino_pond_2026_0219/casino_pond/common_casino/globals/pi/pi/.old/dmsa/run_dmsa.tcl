sh date
sh touch DMSA_START
sh mkdir ./eco_scripts
sh mkdir ./eco_reports

###############################################
#- Environment variables
###############################################
#- from [pwd]
#    0 1   2    3    4       5                  6          7                           8    9                                10     11   12
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_pi_run-01_IMSI-fe00_te00_pv00/sta_pt/dmsa/dmsa_${log_or_phy}_${cur_time}
set prj_name   [lindex [split [pwd] "/"] end-8]
set top_design [lindex [split [pwd] "/"] end-6]
set ws         [lindex [split [pwd] "/"] end-5]
set run_ver    [lindex [split [pwd] "/"] end-3]
set stage      [lindex [split [pwd] "/"] end-1]

set RUN_DIR         [regsub {/sta_pt.*} [pwd] ""]
set sta_pt_dir      [regsub {/dmsa/.*}  [pwd] ""]
set dmsa_master_dir [pwd]

#- from ${ws}
regexp {^([^_]+)___(.*)$} $ws match role db_ver

#- from ${run_ver}
set pi_ver      [lindex [split ${run_ver} -] 0] ;# < 00_dc_init >
set pd_ver      [lindex [split ${run_ver} -] 1] ;# < 00_PD_RUN >
set eco_num     [lindex [split ${run_ver} -] 2] ;# < fe00_te00_pv00 >

set te_num      [lindex [split ${eco_num} _] 1] ;# < te00 >

#- Design Variables
set top_name       ${prj_name}
set all_blks       $env(all_blks)

#- PATH setup
#set PRJ_HOME        "$env(prj_base)/${prj_name}"
eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
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
#- ${prj_name}.ovars.tcl
###############################################
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl
if { !$ovars(dmsa,teco,physical_aware) } { set ovars(dmsa,teco,physical_mode) "none" }

#- ${prj_name}.dmsa.teco.tcl
if { [file exist ${RUN_DIR}/dmsa/dmsa_teco.tcl] } {
    source -e -v ${RUN_DIR}/dmsa/dmsa_teco.tcl
    set dmsa_teco "1"

}


set sh_source_uses_search_path true
#set pba_exhaustive_endpoint_path_limit 10000 ;# default: infinity
set eco_report_unfixed_reason_max_endpoints     5000    


###############################################
#- Resources to be used for DMSA
###############################################
set dmsa_num_of_hosts           [expr [llength $ovars(dmsa,teco,modes)] * [llength $ovars(dmsa,teco,corners)]]
set dmsa_num_of_licenses        [expr [llength $ovars(dmsa,teco,modes)] * [llength $ovars(dmsa,teco,corners)]]

#file delete -force ./eco
set multi_scenario_working_directory ./eco
set multi_scenario_merged_error_log  ./eco/error_merged.log

#- run processes on the local machine
set_host_options -num_processes $dmsa_num_of_hosts -max_cores 4

###############################################
#- 
###############################################
foreach mode $ovars(dmsa,teco,modes) {
    foreach corner $ovars(dmsa,teco,corners) {
        create_scenario -name ${mode}_${corner} -image ${sta_pt_dir}/${mode}/${corner}/session.${mode}_${corner}
    }
} 


#- start processes on all remote machines
#   if this hangs, check to make sure that you can run this version
#   of PrimeTime on the specified machines/farm
start_hosts

#- set session focus to all scenarios
current_session -all


###############################################
#- set_eco_options for physical aware DMSA
###############################################
if { $ovars(dmsa,teco,physical_aware) == "1" } {
    # TODO: clean-up *_PATH variables, as APR tool type
    set tech_lef_path  [list ${PD_OUT_PATH}/lef/${top_design}_tech.lef]
#   set lef_path       [list [list [glob -nocomplain ${DB_PATH}/vers/${db_ver}/*/lef/*.lef]]]
    set lef_path       [list ${PD_OUT_PATH}/lef/${top_design}_allLefLibrary.lef]
    set def_path       [list ${PD_OUT_PATH}/def/${top_design}.def.gz]

    #TODO: filler_cells -> ovars.tcl?
    set filler_cells   [list \
                                FILE16HMA FILE16NMB FILE2HMA FILE2NMB FILE32HMA FILE32NMB FILE3HMA FILE3NMB FILE4HMA FILE4NMB FILE64HMA FILE64NMB FILE8HMA FILE8NMB \
                                EFILE8NMB EFILE4NMB EFILE32NMB EFILE2NMB EFILE1NMB EFILE16NMB EFILE8HMA EFILE4HMA EFILE32HMA EFILE2HMA EFILE1HMA EFILE16HMA \
                                FIL16HMA FIL16NMB FIL1HMA FIL1NMB FIL2HMA FIL2NMB FIL32HMA FIL32NMB FIL3HMA FIL3NMB FIL4HMA FIL4NMB FIL64HMA FIL64NMB FIL8HMA FIL8NMB \
                       ]

    set_distributed_variables [list tech_lef_path lef_path def_path filler_cells]
    remote_execute -verbose {
        # to size cells only with identical pin names
        set eco_strict_pin_name_equivalence "true"

        # 1 rows 8
        set_app_var eco_insert_buffer_search_distance_in_site_rows  "30"

        # settings for physical-aware ECO
        set eco_allow_filler_cells_as_open_sites "true"
        set_eco_options -physical_tech_lib_path ${tech_lef_path} \
                        -physical_lib_path      ${lef_path} \
                        -physical_design_path   ${def_path} \
                        -filler_cell_names      ${filler_cells} \
                        -physical_enable_clock_data \
                        -log_file ./lef_def.log

        check_eco

    }
}

remote_execute {
    suppress_message RC-009

###############################################
#- dont_touch & dont_use
###############################################
# TODO: dont_touch, dont_use -> ovars.tcl
#    set cell_dont_touch [get_cells * -hierarchical -filter "full_name =~ *FALSE_PATH* || full_name =~ *u_GC_* || full_name =~ *u_CLKMUX_* || full_name =~ *u_CLKBUF_* || full_name =~ *u_CLKINV_* || full_name =~ *u_INST_*"]
#    set_dont_touch $cell_dont_touch
#    set_dont_touch u_image_processor/u_spr_render/u_spr_in_buffer/u_dft_intf_* true
#    set_dont_touch u_image_processor/u_spr_render/u_spr_out_buffer/u_dft_intf_* true
#   source -e -v $ovars(dmsa,dont_touch)
    set_dont_use $ovars(dmsa,dont_use)
    
}



###############################################
#- DMSA Debug
###############################################
if {$ovars(dmsa,debug)} { return }


# ----------------------------------------------------------------------------
# Pre Source
# ----------------------------------------------------------------------------
set_distributed_variables [list dmsa_master_dir]
if { [file exist ${dmsa_master_dir}/$ovars(dmsa,pre_source)] } {
    remote_execute { source -e -v ${dmsa_master_dir}/$ovars(dmsa,pre_source) }

    write_changes -format icc2tcl -o ./eco_scripts/pre_source.icc2.tcl
    write_changes -format ptsh    -o ./eco_scripts/pre_source.pt.tcl
    write_changes -reset
}

# ----------------------------------------------------------------------------
# Power Opt
# ----------------------------------------------------------------------------
sh date
if { $ovars(dmsa,teco,fix_leakage) == "1" } {
# TODO: set_false_path to boundary path
# TODO: add option swiching ovars @ovars.tcl

    set eco_power_exclude_unconstrained_cells true
    fix_eco_leakage -cell_type {sequential combinational} -pattern_priority { HMA NMB LMB } -setup_margin 0.00 -verbose

    write_changes -format ptsh    -o ./eco_scripts/0_${eco_num}.fix_leakage.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/0_${eco_num}.fix_leakage.icc2.tcl
    write_changes -format text    -o ./eco_scripts/0_${eco_num}.fix_leakage.txt
    write_changes -reset

    report_constraint -all_violators -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba) > ./eco_reports/all_setup_violators.after_fix_leakage.$ovars(dmsa,pba).rpt
    report_constraint -all_violators -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba) > ./eco_reports/all_hold_violators.after_fix_leakage.$ovars(dmsa,pba).rpt

    sh touch leakage_dmsa_done

}


# -----------------------------------------------------------------------------
# Fix DRC
# -----------------------------------------------------------------------------
sh date
if { $ovars(dmsa,teco,fix_max_cap) == "1" } {
    ### MAX_CAP
    set eco_net_name_prefix         N_ECO_${te_num}_MAXCAP
    set eco_instance_name_prefix    U_ECO_${te_num}_MAXCAP
    fix_eco_drc -type max_capacitance \
                -methods {size_cell insert_buffer} -buffer_list $ovars(dmsa,drc,bufs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/1_${eco_num}_fix.max_cap.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/1_${eco_num}_fix.max_cap.icc2.tcl
    write_changes -format text    -o ./eco_scripts/1_${eco_num}_fix.max_cap.txt
    write_changes -reset

}

if { $ovars(dmsa,teco,fix_mttv) == "1" } {
    ### CLK MTTV
    set eco_net_name_prefix         N_ECO_${te_num}_CLK_MTTV
    set eco_instance_name_prefix    U_ECO_${te_num}_CLK_MTTV

    fix_eco_drc -type max_transition -cell clock_network \
                -methods {insert_inverter_pair} -buffer_list $ovars(dmsa,drc,invs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### DATA MTTV
    set eco_net_name_prefix         N_ECO_${te_num}_DATA_MTTV
    set eco_instance_name_prefix    U_ECO_${te_num}_DATA_MTTV

    fix_eco_drc -type max_transition -cell combinational \
                -methods {size_cell insert_buffer} -buffer_list $ovars(dmsa,drc,bufs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/1_${eco_num}_fix.mttv.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/1_${eco_num}_fix.mttv.icc2.tcl
    write_changes -format text    -o ./eco_scripts/1_${eco_num}_fix.mttv.txt
    write_changes -reset

}

if { $ovars(dmsa,teco,fix_noise) == "1" } {
    ### CLK NOISE
    set eco_net_name_prefix         N_ECO_${te_num}_CLK_NOISE
    set eco_instance_name_prefix    U_ECO_${te_num}_CLK_NOISE
    fix_eco_drc -type noise -cell clock_network \
                -methods {size_cell insert_inverter_pair} -buffer_list $ovars(dmsa,drc,invs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### DATA NOISE
    set eco_net_name_prefix         N_ECO_${te_num}_DATA_NOISE
    set eco_instance_name_prefix    U_ECO_${te_num}_DATA_NOISE
    fix_eco_drc -type noise -cell combinational \
                -methods {size_cell insert_buffer} -buffer_list $ovars(dmsa,drc,bufs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/1_${eco_num}_fix.noise.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/1_${eco_num}_fix.noise.icc2.tcl
    write_changes -format text    -o ./eco_scripts/1_${eco_num}_fix.noise.txt
    write_changes -reset

}

###############################################
#- Fix timing violations
###############################################
if {$ovars(dmsa,teco,fix_setup) || $ovars(dmsa,teco,fix_hold)} {
#   TODO: array cannot be distributed to workers..
#   set_distributed_variables [list ovars(dmsa,teco,target_groups) ovars(dmsa,teco,except_groups)]
    set dmsa_target_group $ovars(dmsa,teco,target_groups)
    set dmsa_except_group $ovars(dmsa,teco,except_groups)
    set_distributed_variables [list dmsa_except_group dmsa_target_group]


    # Determines target path groups based on $ovars(dmsa,teco,target_groups) or all groups if empty.  
    # Excludes groups specified in $ovars(dmsa,teco,except_groups) and collects the full names of the remaining groups.
    current_scenario [index_collection [current_scenario] 0]
    remote_execute -verbose {
        if { [sizeof_collection [get_path_groups -q ${dmsa_target_group}]] } {
            puts "\$target_groups: ${dmsa_target_group}"
            set col_tg [get_path_groups ${dmsa_target_group}]

        } else {
            puts "\$target_groups is empty."
            puts "Filling \$target_groups with all path groups."
            set col_tg [get_path_groups *]

        }

        if {${dmsa_except_group} != ""} {
            set col_tg [remove_from_collection $col_tg ${dmsa_except_group}]

        }

        set target_groups ""
        foreach_in_collection ctg $col_tg {
            lappend target_groups [get_attribute $ctg full_name]

        }
    }

    get_distributed_variables -merge_type list { target_groups }
    puts "Info: \$target_groups- $target_groups"

    current_scenario -all

    # Defines slack range using lower and upper bounds for the fix_eco_timing command.
    #  Usage example:
    #  To fix setup timing violations with slack between 0 and -0.2:
    #    fix_eco_timing -type setup -slack_lesser_than 0 -slack_greater_than -0.2
    #  These options are specific to the `fix_eco_timing` command.
    set slack_lesser_than  $ovars(dmsa,teco,slack_lesser_than)
    set slack_greater_than $ovars(dmsa,teco,slack_greater_than)

    # If no slack range is specified, use default values.
    if { ${slack_greater_than} == "" } { set slack_greater_than "-inf" }
    if { ${slack_lesser_than}  == "" } { set slack_lesser_than  "0.00" }

    puts "Info: slack range: ${slack_greater_than} < SLACK < ${slack_lesser_than}"

}


###############################################
#- Fix setup
###############################################
sh date
if { $ovars(dmsa,teco,fix_setup) } {

    set eco_net_name_prefix         N_ECO_${te_num}_SETUP
    set eco_instance_name_prefix    U_ECO_${te_num}_SETUP

#   remote_execute {
#TODO: swap only Vth
###     define_user_attribute -classes lib_cell -type string ECO_SWAP
###     foreach_in_collection cell [get_lib_cells */*] {
###         set base_name [get_attribute $cell base_name]
###         set full_name [get_attribute $cell full_name]
###         if {[regexp tcbn22ulpbwp $full_name]} {
###             set attr_name [lindex [split $base_name BWP] 0]
###             set_user_attribute -class lib_cell $full_name ECO_SWAP $attr_name
###         }
###     }
### 
###     set eco_alternative_cell_attribute_restrictions ECO_SWAP
###     set eco_alternative_area_ratio_threshold 1
### 
###     set_dont_use {*/*LVT}

#    }
    if { $ovars(dmsa,teco,physical_aware) } {
        fix_eco_timing -type setup -pba_mode $ovars(dmsa,pba) \
                       -method {size_cell insert_buffer} -buffer_list $ovars(dmsa,setup,bufs) \
                       -group ${target_groups} \
                       -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
                       -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose

    } else {
        fix_eco_timing -type setup -pba_mode $ovars(dmsa,pba) \
                       -method {size_cell} \
                       -group ${target_groups} \
                       -slack_lesser_than ${slack_lesser_than} -slack_greater_than ${slack_greater_than} \
                       -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose

    }

    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/2_${eco_num}_fix.setup.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/2_${eco_num}_fix.setup.icc2.tcl
    write_changes -format text    -o ./eco_scripts/2_${eco_num}_fix.setup.txt
    write_changes -reset

    ### REPORT
    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)     > ./eco_reports/all_setup_violators.after_fix_setup.$ovars(dmsa,pba).rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)     > ./eco_reports/all_hold_violators.after_fix_setup.$ovars(dmsa,pba).rpt

    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)  -verbose   > ./eco_reports/all_setup_violators.after_fix_setup.$ovars(dmsa,pba).verbose.rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)  -verbose   > ./eco_reports/all_hold_violators.after_fix_setup.$ovars(dmsa,pba).verbose.rpt

    sh touch setup_dmsa_done

}

###############################################
#- Fix hold
###############################################
if { $ovars(dmsa,teco,fix_hold) } {
    sh date

    set eco_net_name_prefix       N_ECO_${te_num}_HOLD
    set eco_instance_name_prefix  U_ECO_${te_num}_HOLD

    fix_eco_timing -type hold -pba_mode $ovars(dmsa,pba) \
                   -method {insert_buffer} -buffer_list $ovars(dmsa,hold,bufs) \
                   -group ${target_groups} \
                       -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
                   -physical_mode $ovars(dmsa,teco,physical_mode) \
                   -max_iteration 30 -setup_margin 0.0 -verbose

    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/3_${eco_num}_fix.hold.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/3_${eco_num}_fix.hold.icc2.tcl
    write_changes -format text    -o ./eco_scripts/3_${eco_num}_fix.hold.txt
    write_changes -reset
    
    ### REPORT
    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)     > ./eco_reports/all_setup_violators.after_fix_hold.$ovars(dmsa,pba).rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)     > ./eco_reports/all_hold_violators.after_fix_hold.$ovars(dmsa,pba).rpt

    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)  -verbose   > ./eco_reports/all_setup_violators.after_fix_hold.$ovars(dmsa,pba).verbose.rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,pba)  -verbose   > ./eco_reports/all_hold_violators.after_fix_hold.$ovars(dmsa,pba).verbose.rpt

    sh touch hold_dmsa_done

}

###############################################
#- Finish DMSA
###############################################
sh date
if { $ovars(dmsa,save_session) } { remote_execute { save_session ECOed_session.${mode}_${corner} } }

#TODO: export script
if { ${dmsa_teco} } {
    file mkdir ${PI_OUT_PATH}/ECO/
    file copy ./eco_scripts/*.icc2.tcl ${PI_OUT_PATH}/ECO/
}

sh touch DMSA_DONE 
#stop_hosts
# exit
