sh date
sh touch DMSA_START
sh mkdir ./eco_scripts
sh mkdir ./eco_reports
sh mkdir ./eco_reports/before_reports
sh mkdir ./eco_reports/after_reports

source -e -v $env(RUN_COMMON_PATH)/globals/pi/get_pi_vars.tcl

set RUN_STA_PT_PATH ${RUN_PATH}/sta_pt
set RUN_DMSA_PATH   [pwd]

###############################################
#- ${prj_name}.ovars.tcl
###############################################
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl
if { !$ovars(dmsa,teco,physical_aware) } { set ovars(dmsa,teco,physical_mode) "none" }

#- ${prj_name}.dmsa.teco.tcl
if { [file exist ${RUN_PATH}/dmsa/${prj_name}.dmsa.teco.tcl] } {
#	source -e -v ${RUN_PATH}/dmsa/${prj_name}.dmsa.teco.tcl
    source -e -v ${RUN_PATH}/dmsa/dmsa_teco.tcl
	set dmsa_teco "1"

}


set sh_source_uses_search_path true
#set pba_exhaustive_endpoint_path_limit 10000 ;# default: infinity
set eco_report_unfixed_reason_max_endpoints 	5000	


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

set LEAKAGE_PRIORITY                   "HMA NMB LMB"

###############################################
#- 
###############################################
#foreach mode $ovars(dmsa,teco,modes) {
#    foreach corner $ovars(dmsa,teco,corners) {
#	    create_scenario -name ${mode}_${corner} -image ${RUN_STA_PT_PATH}/${mode}/${corner}/session.${mode}_${corner}
#    }
#} 
#foreach mode $ovars(dmsa,teco,modes) {
#    foreach corner $ovars(dmsa,teco,corners) {
#        if {[string equal -nocase $mode "scap"] || [string equal -nocase $mode "scan_capture"]} {
#            set image "${RUN_STA_PT_PATH}/${mode}/${corner}/session.SCAN_CAPTURE_${corner}"
#        } else {
#            set image "${RUN_STA_PT_PATH}/${mode}/${corner}/session.${mode}_${corner}"
#        }
#        create_scenario -name "${mode}_${corner}" -image $image
#    }
#}

foreach mode $ovars(dmsa,teco,modes) {
    foreach corner $ovars(dmsa,teco,corners) {
        set path_base "${RUN_STA_PT_PATH}/${mode}/${corner}"
        set image_list [glob -nocomplain ${path_base}/session.*]
        
        if {[llength $image_list] == 1} {
            set image [lindex $image_list 0]
            puts "Found session file: $image"
            
            create_scenario -name "${mode}_${corner}" -image $image
        
        } else {
            puts "Warning: Could not uniquely determine session file for ${mode}_${corner} in ${path_base}. Skipping."
        }
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
    # set tech_lef_path  [list ${PD_OUT_PATH}/lef/${top_design}_tech.lef]
    ## set lef_path       [list [list [glob -nocomplain ${DB_PATH}/vers/${db_ver}/*/lef/*.lef]]]
    # set lef_path       [list ${PD_OUT_PATH}/lef/${top_design}_allLefLibrary.lef]
    # set def_path       [list ${PD_OUT_PATH}/def/${top_design}_dmsa.def.gz]
    
    # 1. LEF Files
    set lef_path [list \
        ${PD_OUT_PATH}/lef/${top_design}_allLefLibrary.lef \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_right/*/$ovars(sta_pt,sub_block_version,fb_right)/lef/fb_right_allLefLibrary.lef] \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_left/*/$ovars(sta_pt,sub_block_version,fb_left)/lef/fb_left_allLefLibrary.lef] \
    ]

    # 2. DEF Files
    set def_path [list \
        ${PD_OUT_PATH}/def/${top_design}_dmsa.def.gz \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_right/*/$ovars(sta_pt,sub_block_version,fb_right)/def/fb_right_dmsa.def.gz] \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_left/*/$ovars(sta_pt,sub_block_version,fb_left)/def/fb_left_dmsa.def.gz] \
    ]

    # 3. Tech LEF Files
    set tech_lef_path [list \
        ${PD_OUT_PATH}/lef/${top_design}_tech.lef \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_right/*/$ovars(sta_pt,sub_block_version,fb_right)/lef/fb_right_tech.lef] \
        {*}[glob -nocomplain ${OUTFEED_PATH}/fb_left/*/$ovars(sta_pt,sub_block_version,fb_left)/lef/fb_left_tech.lef] \
    ]

    # TODO: filler_cells -> ovars.tcl?
    # TODO(jake): Revise filler cell (related specific process : U* / T* ~)

    ## Filler cell of UMC
     set filler_cells [list \
         FILE16HMA FILE16NMB FILE2HMA FILE2NMB FILE32HMA FILE32NMB FILE3HMA FILE3NMB FILE4HMA FILE4NMB FILE64HMA FILE64NMB FILE8HMA FILE8NMB \
         EFILE8NMB EFILE4NMB EFILE32NMB EFILE2NMB EFILE1NMB EFILE16NMB EFILE8HMA EFILE4HMA EFILE32HMA EFILE2HMA EFILE1HMA EFILE16HMA \
         FIL16HMA FIL16NMB FIL1HMA FIL1NMB FIL2HMA FIL2NMB FIL32HMA FIL32NMB FIL3HMA FIL3NMB FIL4HMA FIL4NMB FIL64HMA FIL64NMB FIL8HMA FIL8NMB \
     ]

    ## Filler cell of TSMC 12nm
#    set filler_cells [list \
#        FILL4BWP7T30P140HVT \
#        FILL3BWP7T30P140HVT \
#        FILL2BWP7T30P140HVT \
#    ]

    # set filler_cells [list \
    #     FILL2BWP7T30P140HVT FILL3BWP7T30P140HVT FILL4BWP7T30P140HVT FILL8BWP7T30P140HVT FILL16BWP7T30P140HVT FILL32BWP7T30P140HVT FILL64BWP7T30P140HVT \
    #     FILL2BWP7T35P140     FILL3BWP7T35P140     FILL4BWP7T35P140     FILL8BWP7T35P140     FILL16BWP7T35P140     FILL32BWP7T35P140     FILL64BWP7T35P140 \
    #     FILL2BWP7T35P140LVT  FILL3BWP7T35P140LVT  FILL4BWP7T35P140LVT  FILL8BWP7T35P140LVT  FILL16BWP7T35P140LVT  FILL32BWP7T35P140LVT  FILL64BWP7T35P140LVT \
    # ]

    set_distributed_variables [list tech_lef_path lef_path def_path filler_cells]

    remote_execute -verbose {
        # to size cells only with identical pin names
        set eco_strict_pin_name_equivalence "true"

        # 1 rows 8
        set_app_var eco_insert_buffer_search_distance_in_site_rows "30"

        # settings for physical-aware ECO
        set eco_allow_filler_cells_as_open_sites "true"
        set_eco_options \
            -physical_tech_lib_path ${tech_lef_path} \
            -physical_lib_path      ${lef_path} \
            -physical_design_path   ${def_path} \
            -filler_cell_names      ${filler_cells} \
            -physical_enable_clock_data \
            -log_file               ./lef_def.log

        check_eco
    }
}

remote_execute {
    suppress_message RC-009
}

###############################################
#- dont_touch & dont_use
###############################################
set dont_touch_file $ovars(dmsa,dont_touch)

if {[llength $dont_touch_file] == 1 && [file exists [lindex $dont_touch_file 0]]} {

    set df [lindex $dont_touch_file 0]
    remote_execute [subst {source -e -v $df}]

} else {

    foreach df $dont_touch_file {
        if {[file exists $df]} {
            puts "Sourcing $df"
            remote_execute [subst {source -e -v $df}]
        } else {
            puts "Warning: File $df does not exist, skipping."
        }
    }
}

write_changes -format icc2tcl -o ./eco_scripts/dont_touch.icc2.tcl
write_changes -format ptsh    -o ./eco_scripts/dont_touch.pt.tcl
write_changes -reset

set dont_use_list $ovars(dmsa,dont_use)

if { [llength $ovars(dmsa,dont_use)] > 0 } {

    puts ">>> Applying dont_use to: $ovars(dmsa,dont_use)"

    remote_execute {
        set_dont_use [get_lib_cells $ovars(dmsa,dont_use)]
    }

    write_changes -format icc2tcl -o ./eco_scripts/dont_use.icc2.tcl
    write_changes -format ptsh    -o ./eco_scripts/dont_use.pt.tcl
    write_changes -reset

} else {
    puts ">>> dont_use list is empty"
}

###############################################
#- before report
###############################################
#report_qor -summary -pba_mode path -sig 3 \
#    > ./eco_reports/before_reports/report_qor.summary.BF

report_global_timing \
    > ./eco_reports/report_global_timing.rpt.BEFORE

report_global_timing -pba path \
    > ./eco_reports/before_reports/report_global_timing.rpt.BF

#report_constraint -max_delay -recovery -clock_gating_setup -pba_mode path -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_max_all_violators.path.simple.BF
#
#report_constraint -min_delay -removal -clock_gating_hold -pba_mode path -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_min_all_violators.path.simple.BF
#
#report_constraint -min_period -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_min_period.simple.BF
#
#report_constraint -min_pulse_width -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_min_pulse_width.simple.BF
#
#report_constraint -max_skew -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_max_skew.simple.BF
#
#report_constraint -max_cap -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_max_cap.simple.BF
#
#report_constraint -max_transition -all_violators -nosplit -sig 3 \
#    > ./eco_reports/before_reports/report_constraint_max_tran.simple.BF

report_cell_usage -pattern_priority $LEAKAGE_PRIORITY \
    > ./eco_reports/before_reports/report_cell_usage.simple.BF

#report_noise -nosplit -all -slack_type height \
#    > ./eco_reports/before_reports/report_si_noise_all.rpt.BF

date

###############################################
#- DMSA Debug
###############################################
if {$ovars(dmsa,debug)} { return }


# ----------------------------------------------------------------------------
# Pre Source
# ----------------------------------------------------------------------------
set_distributed_variables [list RUN_DMSA_PATH]

#if { [file exist $ovars(dmsa,pre_source)] } {
#	remote_execute [subst { source -e -v $ovars(dmsa,pre_source) }]
#
#	write_changes -format icc2tcl -o ./eco_scripts/pre_source.icc2.tcl
#	write_changes -format ptsh    -o ./eco_scripts/pre_source.pt.tcl
#	write_changes -reset
#}

set pre_sources $ovars(dmsa,pre_source)

if {[llength $pre_sources] == 1 && [file exists [lindex $pre_sources 0]]} {

    set f [lindex $pre_sources 0]
    remote_execute [subst {source -e -v $f}]

} else {

    foreach f $pre_sources {
        if {[file exists $f]} {
            puts "Sourcing $f"
            remote_execute [subst {source -e -v $f}]
        } else {
            puts "Warning: File $f does not exist, skipping."
        }
    }
}

write_changes -format icc2tcl -o ./eco_scripts/pre_source.icc2.tcl
write_changes -format ptsh    -o ./eco_scripts/pre_source.pt.tcl
write_changes -reset

# ----------------------------------------------------------------------------
# Power Opt
# ----------------------------------------------------------------------------
sh date
if { $ovars(dmsa,teco,fix_leakage) == "1" } {
# TODO: set_false_path to boundary path
# TODO: add option swiching ovars @ovars.tcl

    set eco_power_exclude_unconstrained_cells true
	fix_eco_leakage -cell_type {sequential combinational} -pattern_priority { HMA NMB LMB } -setup_margin 0.00 -verbose

    # TODO(jake) Revise pattern priority cell name
#	fix_eco_leakage -cell_type {sequential combinational} -pattern_priority { 140HVT 140 140LVT} -setup_margin 0.00 -verbose

    write_changes -format ptsh    -o ./eco_scripts/0_${eco_num}.fix_leakage.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/0_${eco_num}.fix_leakage.icc2.tcl
    write_changes -format text    -o ./eco_scripts/0_${eco_num}.fix_leakage.txt
    write_changes -reset

    report_constraint -all_violators -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba) > ./eco_reports/all_setup_violators.after_fix_leakage.$ovars(dmsa,teco,pba).rpt
    report_constraint -all_violators -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba) > ./eco_reports/all_hold_violators.after_fix_leakage.$ovars(dmsa,teco,pba).rpt

	sh touch leakage_dmsa_done

}


# -----------------------------------------------------------------------------
# Fix DRC
# -----------------------------------------------------------------------------
sh date
if { $ovars(dmsa,teco,fix_max_cap) == "1" } {
    ### MAX_CAP
	set eco_net_name_prefix		    N_ECO_${te_num}_MAXCAP
	set eco_instance_name_prefix  	U_ECO_${te_num}_MAXCAP
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
	set eco_net_name_prefix		    N_ECO_${te_num}_CLK_MTTV
	set eco_instance_name_prefix  	U_ECO_${te_num}_CLK_MTTV

	fix_eco_drc -type max_transition -cell clock_network \
		        -methods {insert_inverter_pair} -buffer_list $ovars(dmsa,drc,invs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### DATA MTTV
	set eco_net_name_prefix		    N_ECO_${te_num}_DATA_MTTV
	set eco_instance_name_prefix  	U_ECO_${te_num}_DATA_MTTV

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
	set eco_net_name_prefix		    N_ECO_${te_num}_CLK_NOISE
	set eco_instance_name_prefix  	U_ECO_${te_num}_CLK_NOISE
	fix_eco_drc -type noise -cell clock_network \
                -methods {size_cell insert_inverter_pair} -buffer_list $ovars(dmsa,drc,invs) \
                -physical_mode $ovars(dmsa,teco,physical_mode) -verbose

    ### DATA NOISE
	set eco_net_name_prefix		    N_ECO_${te_num}_DATA_NOISE
	set eco_instance_name_prefix  	U_ECO_${te_num}_DATA_NOISE
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
#	TODO: array cannot be distributed to workers..
#	set_distributed_variables [list ovars(dmsa,teco,target_groups) ovars(dmsa,teco,except_groups)]
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

	set eco_net_name_prefix		    N_ECO_${te_num}_SETUP
	set eco_instance_name_prefix  	U_ECO_${te_num}_SETUP

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


     # TODO(jake) fix group option
     #
     #	if { $ovars(dmsa,teco,physical_aware) } {
     #		fix_eco_timing -type setup -pba_mode $ovars(dmsa,teco,pba) \
     #					   -method {size_cell insert_buffer} -buffer_list $ovars(dmsa,setup,bufs) \
     #					   -group ${target_groups} \
     #					   -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
     #					   -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose
     #
     #	} else {
     #		fix_eco_timing -type setup -pba_mode $ovars(dmsa,teco,pba) \
     #					   -method {size_cell} \
     #					   -group ${target_groups} \
     #					   -slack_lesser_than ${slack_lesser_than} -slack_greater_than ${slack_greater_than} \
     #					   -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose
     #
     #	}
     #
	if { $ovars(dmsa,teco,physical_aware) } {
		fix_eco_timing -type setup -pba_mode $ovars(dmsa,teco,pba) \
					   -method {size_cell} \
					   -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
					   -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose

	} else {
		fix_eco_timing -type setup -pba_mode $ovars(dmsa,teco,pba) \
					   -methods {size_cell} -cell_type combinational \
					   -slack_lesser_than ${slack_lesser_than} -slack_greater_than ${slack_greater_than} \
					   -physical_mode $ovars(dmsa,teco,physical_mode) -max_iteration 30 -verbose

	}
    ### WRITE_CHANGES
	write_changes -format ptsh    -o ./eco_scripts/2_${eco_num}_fix.setup.pt.tcl
	write_changes -format icc2tcl -o ./eco_scripts/2_${eco_num}_fix.setup.icc2.tcl
	write_changes -format text    -o ./eco_scripts/2_${eco_num}_fix.setup.txt
    write_changes -reset

    ### REPORT
    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)     > ./eco_reports/all_setup_violators.after_fix_setup.$ovars(dmsa,teco,pba).rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)     > ./eco_reports/all_hold_violators.after_fix_setup.$ovars(dmsa,teco,pba).rpt

    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)  -verbose   > ./eco_reports/all_setup_violators.after_fix_setup.$ovars(dmsa,teco,pba).verbose.rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)  -verbose   > ./eco_reports/all_hold_violators.after_fix_setup.$ovars(dmsa,teco,pba).verbose.rpt

	sh touch setup_dmsa_done

}

###############################################
#- Fix hold
###############################################
if { $ovars(dmsa,teco,fix_hold) } {
    sh date

	set eco_net_name_prefix       N_ECO_${te_num}_HOLD
	set eco_instance_name_prefix  U_ECO_${te_num}_HOLD

    ## TODO(jake) fix group option
    #
    fix_eco_timing -type hold -pba_mode $ovars(dmsa,teco,pba) \
	               -method {insert_buffer} -buffer_list $ovars(dmsa,hold,bufs) \
				   -group ${target_groups} \
				   -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
	               -physical_mode $ovars(dmsa,teco,physical_mode) \
	               -max_iteration 30 -setup_margin 0.0 -verbose

#	fix_eco_timing -type hold -pba_mode $ovars(dmsa,teco,pba) \
#	               -method {size_cell insert_buffer} -buffer_list $ovars(dmsa,hold,bufs) \
#				   -slack_greater_than ${slack_greater_than} -slack_lesser_than ${slack_lesser_than} \
#	               -physical_mode $ovars(dmsa,teco,physical_mode) \
#	               -max_iteration 10 -setup_margin 0.0 -verbose


    ### WRITE_CHANGES
    write_changes -format ptsh    -o ./eco_scripts/3_${eco_num}_fix.hold.pt.tcl
    write_changes -format icc2tcl -o ./eco_scripts/3_${eco_num}_fix.hold.icc2.tcl
    write_changes -format text    -o ./eco_scripts/3_${eco_num}_fix.hold.txt
    write_changes -reset
	
    ### REPORT
    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)     > ./eco_reports/all_setup_violators.after_fix_hold.$ovars(dmsa,teco,pba).rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)     > ./eco_reports/all_hold_violators.after_fix_hold.$ovars(dmsa,teco,pba).rpt

    report_constraint -all_violators  -max_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)  -verbose   > ./eco_reports/all_setup_violators.after_fix_hold.$ovars(dmsa,teco,pba).verbose.rpt
    report_constraint -all_violators  -min_delay -nosplit -significant_digits 3 -pba_mode $ovars(dmsa,teco,pba)  -verbose   > ./eco_reports/all_hold_violators.after_fix_hold.$ovars(dmsa,teco,pba).verbose.rpt

	sh touch hold_dmsa_done

}

###############################################
#- Final report
###############################################
# Save main reports to eco_reports directory

#report_qor -summary -pba_mode path -sig 3\
#    > ./eco_reports/after_reports/report_qor.summary.AF

report_global_timing -pba path \
    > ./eco_reports/after_reports/report_global_timing.rpt.AF

#report_constraint -max_delay -recovery -clock_gating_setup -pba_mode path -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_max_all_violators.path.simple.AF
#
#report_constraint -min_delay -removal -clock_gating_hold -pba_mode path -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_min_all_violators.path.simple.AF
#
#report_constraint -min_period -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_min_period.simple.AF
#
#report_constraint -min_pulse_width -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_min_pulse_width.simple.AF
#
#report_constraint -max_skew -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_max_skew.simple.AF
#
#report_constraint -max_cap -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_max_cap.simple.AF
#
#report_constraint -max_transition -all_violators -nosplit -sig 3 \
#    > ./eco_reports/after_reports/report_constraint_max_tran.simple.AF

report_cell_usage -pattern_priority $LEAKAGE_PRIORITY \
    > ./eco_reports/after_reports/report_cell_usage.simple.AF

#report_noise -nosplit -all -slack_type height \
#    > ./eco_reports/after_reports/report_si_noise_all.rpt.AF

date

#remote_execute {    
# Save session for debug or resume
    save_session ./save_session.${mode}_${corner}
    date
#}

###############################################
#- Finish DMSA
###############################################
sh date
if { $ovars(dmsa,save_session) } { remote_execute { save_session ECOed_session.${mode}_${corner} } }

#TODO: export script
if { [info exist dmsa_teco] && ${dmsa_teco} } {
	file mkdir ${PI_OUT_PATH}/ECO/
	file copy ./eco_scripts/*.icc2.tcl ${PI_OUT_PATH}/ECO/
    file copy ./eco_scripts/*.inn.tcl  ${PI_OUT_PATH}/ECO/ ; # added
}


report_global_timing > ./eco_reports/report_global_timing.rpt.FINAL 

sh touch DMSA_DONE 
#stop_hosts
# exit
