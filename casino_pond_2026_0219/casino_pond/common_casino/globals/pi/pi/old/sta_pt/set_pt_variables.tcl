###############################################################################
#
#  FILE:    set_pt_variables.tcl
#
#  ABSTRACT:    Set PrimeTime variables to the values of SEC methodology
#
#        Usage:
#         set_pt_variables
#           [-pre]                 (pre-layout stage)
#           [-post]                (post-layout stage (including SI variables))
#           [-check_only]          (checks the values of variables without setting)
#
#  AUTHOR:    J.-R. Lee,  MS Kim
#
#  HISTORY:    07/10/01    Generated
#        07/12/07    Variable 'auto_wire_load_selection' added.
#        09/03/02    Modified the default value of 'timing_save_pin_arrival_and_slack'
#                into false in order to improve PT performance.
#        09/03/18    Added the '-celtic' option to set the variable above
#                to true (the original setting).
#        09/04/27    Removed the setting for the 'si_xtalk_reselect_critical_path'
#                variable because it will be obsoleted.
#        09/05/15    Restored the default value of 'timing_save_pin_arrival_and_slack'
#                to its original value because it can cause some problem
#                during running PT utility, especially pt_to_timing.tcl.
#                And removed the '-celtic' option.
#        09/07/23    Added the options of '-aocvm', '-no_aocvm', '-multi_core',
#                and '-cpu'.
#                If you want to apply AOCVM, the '-aocvm' option should be used.
#                Otherwise, the '-no_aocvm' option should be used.
#                And if you apply the multi-core analysis feature,
#                the '-multi_core' option should be used.
#                In the case, you can use the '-cpu' option to specify
#                how many cpus you are going to take. 
#        09/07/30    For AOCVM flow, it was determined that CRPR variable
#                should not be 'same_transition', but 'normal' (the original value).
#        10/09/10    Supports the variable change in the 2010.06 version and 
#                distributed/threaded multicore analyses.
#        10/10/11    Removed a typo in a variable name (110 line). 
#        10/12/15    Informs that threaded multicore is recommendation from 2010.06.
#        11/06/01        timing_enable_max_capacitance_set_case_analysis = true
#                        timing_edge_specific_source_latency = true
#                               unlimit # of PTE-060 messages
#        11/11/18        timing_early_launch_at_borrowing_latches = false 
#                default threaded_multicore_flag = true
#               12/05/08        Remove obsolete variables for 1106; timing_enable_multiple_clocks_per_reg
#                Support primetime_slave mode for threaded multicore setting
#               12/05/21        Fix bug of error occurred when using PT 1012 version
#               12/07/16        Prevent unknown var error in multi-scenario mode
###############################################################################

# SCRIPT_PROTECT_BLOCK_BEGIN

global set_var_scr_version 
set set_var_scr_version "2.3 (2012.7.16)"

global sh_product_version _pt_version_
regexp {[A-Z]-([0-9]+\.[0-9]+)} $sh_product_version all _pt_version_

proc set_pt_variables { args } {
  global set_var_scr_version _pt_version_
  global pt_shell_mode
  echo "Version $set_var_scr_version\n"
  echo "Note: This script should be used in L9 or later, NOT in L13\n"

  set pre_post_flag ""
  set check_only_flag false
  set aocvm_flag ""
  set distributed_multicore_flag false
  set threaded_multicore_flag true
  set num_of_cores 4
  set multi_work_dir "./multi_work_dir"

  parse_proc_arguments -args $args results
  foreach argname [array names results] {
    switch -glob -- $argname {
      "-pr*"    {
        set pre_post_flag pre
      }
      "-po*"    {
        set pre_post_flag post
      }
      "-ch*"    {
        set check_only_flag true
      }
      "-a*"    {
        set aocvm_flag true
      }
      "-n*"    {
        set aocvm_flag false
      }
      "-multi_c*"    {
    echo "INFO: '-multi_core' option will be obsolete. Instead, use '-distributed_multicore'.\n"
        set distributed_multicore_flag true
      }
      "-d*"    {
        set distributed_multicore_flag true
      }
      "-t*"    {
        set threaded_multicore_flag true
      }
      "-cp*"    {
        echo "INFO: '-cpu' option will be obsolete. Instead, use '-core' option.\n"
        set num_of_cores $results($argname)
    if { $num_of_cores < 2 || $num_of_cores > 8 } {
      echo "Error: The number of cores is incorrect"
      echo "       Please perform this procedure again!"
      return 0
    }
      }
      "-co*"    {
        set num_of_cores $results($argname)
    if { $num_of_cores < 2 || $num_of_cores > 8 } {
      echo "Error: The number of cores is incorrect"
      echo "       Please perform this procedure again!"
      return 0
    }
      }
      "-multi_w*"    {
        set multi_work_dir $results($argname)
      }
    }
  }

  if { $pre_post_flag == "" } {
    echo "Error: You should use the '-pre' or '-post' option"
    echo "       Please perform this procedure again!"
    return 0
  }
  
  if { $aocvm_flag == "" } {
    echo "Error: You should use the '-aocvm' or '-no_aocvm' option"
    echo "       Please perform this procedure again!"
    return 0
  }

  if { ${_pt_version_} >= 2009.12 && $threaded_multicore_flag == "false" &&
    $distributed_multicore_flag == "true" } {
    echo "Error: From the 2010.06 version, DT's recommendation is to use threaded multicore."
    echo "       Please use the '-threaded_multicore' option."
    return 0
  }

  # ---------------------------------------------------------------------------
  # PT variables
  # ---------------------------------------------------------------------------
  set pt_var_arr(1) "timing_remove_clock_reconvergence_pessimism true"
  set pt_var_arr(2) "timing_disable_clock_gating_checks false"
  set pt_var_arr(3) "timing_report_unconstrained_paths true"
  set pt_var_arr(4) "rc_degrade_min_slew_when_rd_less_than_rnet true"
  set pt_var_arr(5) "timing_save_pin_arrival_and_slack true"
  set pt_var_arr(6) "svr_keep_unconnected_nets true"
  set pt_var_arr(7) "timing_enable_preset_clear_arcs false"
  #set pt_var_arr(8) "timing_enable_multiple_clocks_per_reg true"
  set pt_var_arr(8) "timing_edge_specific_source_latency true"
  set pt_var_arr(9) "auto_wire_load_selection false"
  set pt_var_arr(10) "timing_enable_max_capacitance_set_case_analysis true"
  set pt_var_arr(11) "timing_early_launch_at_borrowing_latches false"
  if { ${_pt_version_} < 2009.12 } {
    set pt_var_arr(12) "timing_non_unate_clock_compatibility true"
  } elseif { ${_pt_version_} < 2011.06 } {
    set pt_var_arr(12) "timing_enable_multiple_clocks_per_reg true"
  }
  
  for { set index 1 } { $index <= [array size pt_var_arr] } { incr index } {
    global [lindex $pt_var_arr($index) 0]
  }

  # ---------------------------------------------------------------------------
  # PT SI variables
  # ---------------------------------------------------------------------------
  set ptsi_var_arr(1) "si_enable_analysis true"
  set ptsi_var_arr(2) "si_xtalk_reselect_clock_network true"
  set ptsi_var_arr(3) "si_xtalk_reselect_delta_delay 0.1"
  set ptsi_var_arr(4) "si_xtalk_reselect_delta_delay_ratio 0.3"
  set ptsi_var_arr(5) "si_xtalk_reselect_max_mode_slack 0.5"
  set ptsi_var_arr(6) "si_xtalk_reselect_min_mode_slack 0.1"
  set ptsi_var_arr(7) "si_xtalk_exit_on_max_iteration_count 2"

  for { set index 1 } { $index <= [array size ptsi_var_arr] } { incr index } {
    global [lindex $ptsi_var_arr($index) 0]
  }

  set ptsi_suppress_arr(1) "PARA-007"
  set ptsi_suppress_arr(2) "RC-004"
#  set ptsi_suppress_arr(3) "RC-009"

  # ---------------------------------------------------------------------------
  # AOCVM variables
  # ---------------------------------------------------------------------------
  set aocvm_var_arr(1) "read_parasitics_load_locations true"
  set aocvm_var_arr(2) "timing_aocvm_enable_analysis true"
  set aocvm_var_arr(3) "timing_report_use_worst_parallel_cell_arc true"
  set aocvm_var_arr(4) "timing_aocvm_analysis_mode single_path_metrics"
  set aocvm_var_arr(5) "pba_aocvm_only_mode false"

  for { set index 1 } { $index <= [array size aocvm_var_arr] } { incr index } {
    global [lindex $aocvm_var_arr($index) 0]
  }

  # ---------------------------------------------------------------------------
  # Multi-core variables
  # ---------------------------------------------------------------------------
  set multi_var_arr(1) "multi_core_working_directory ${multi_work_dir}"
  if { ${_pt_version_} <= 2009.06 } {
    set multi_var_arr(2) "multi_core_enable_analysis true"
  }

  if { $check_only_flag == "false" } {
    ;###########################################################################
    ;#  setting the variables
    ;###########################################################################
    echo "Setting the general PrimeTime variables ..."
    for { set index 1 } { $index <= [array size pt_var_arr] } { incr index } {
      set varname     [lindex $pt_var_arr($index) 0]
      if {$pt_shell_mode == "primetime_master" || $pt_shell_mode == "primetime_slave"} {
        if {$varname == "svr_keep_unconnected_nets"} {
      continue
    }
      }
      echo ". set_app_var $pt_var_arr($index)"
      set_app_var [lindex $pt_var_arr($index) 0] [lindex $pt_var_arr($index) 1]
    }
    echo ""

    if { $pre_post_flag == "post" } {
      echo "Setting the PrimeTime SI crosstalk analysis variables ..."
      for { set index 1 } { $index <= [array size ptsi_var_arr] } { incr index } {
    set varname     [lindex $ptsi_var_arr($index) 0]
    if {($pt_shell_mode == "primetime_master" || $pt_shell_mode == "primetime_slave")} {
      if {$varname == ""} {
        continue
      }
    }
        echo ". set_app_var $ptsi_var_arr($index)"
        set_app_var [lindex $ptsi_var_arr($index) 0] [lindex $ptsi_var_arr($index) 1]
      }

      for { set index 1 } { $index <= [array size ptsi_suppress_arr] } { incr index } {
    set varname     [lindex $ptsi_suppress_arr($index) 0]
    if {($pt_shell_mode == "primetime_master" || $pt_shell_mode == "primetime_slave")} {
      if {$varname == ""} {
        continue
      }
    }
        echo ". suppress_message $ptsi_suppress_arr($index)"
    suppress_message $ptsi_suppress_arr($index)
      }

      echo ""
    }

    if { $aocvm_flag == "true" } {
      echo "Setting the AOCVM-related variables ..."
      for { set index 1 } { $index <= [array size aocvm_var_arr] } { incr index } {
    set varname     [lindex $aocvm_var_arr($index) 0]
    if {($pt_shell_mode == "primetime_master" || $pt_shell_mode == "primetime_slave")} {
      if {$varname == "read_parasitics_load_locations"} {
        continue
      }
    }
        echo ". set_app_var $aocvm_var_arr($index)"
    set_app_var [lindex $aocvm_var_arr($index) 0] [lindex $aocvm_var_arr($index) 1]
      }
      echo ""
    }

    if { ${_pt_version_} >= 2009.12 } {
      echo "Setting the variables related to threaded multicore feature ..."
      echo "From the 2010.06 version, DT's recommendation is to use threaded multicore."
      if {$::pt_shell_mode == "primetime_slave"} {
          echo "Skip to \'Setting the variables related to threaded multicore feature\' in the primetime_slave mode"
    echo "     User should set # of cores for slave mode in primetime_master mode"
      } else {
    if { $threaded_multicore_flag == "false" } {
        echo " (Threaded multicore feature will not be applied"
        echo "  If you want to turn it on, use '-threaded_multicore' option)"
        echo ". set_host_options -local_process -max_cores 1"
            set_host_options -local_process -max 1
          } else {
            echo " (Threaded multicore feature will be applied)"
        echo ". set_host_options -local_process -max_cores $num_of_cores"
            set_host_options -local_process -max $num_of_cores
          }
      }
      echo ""
    }

    if { $distributed_multicore_flag == "true" } {
      echo "Setting the variables related to distributed multicore feature ..."
      for { set index 1 } { $index <= [array size multi_var_arr] } { incr index } {
        echo ". set_app_var $multi_var_arr($index)"
    set_app_var [lindex $multi_var_arr($index) 0] [lindex $multi_var_arr($index) 1]
      }
      echo ". set_host_options -name dist_multicore -num_process $num_of_cores"
      set_host_options -name dist_multicore -num_process $num_of_cores
      start_hosts
      echo ""
    }

    redirect -variable a {printvar pt_tmp_dir}
    if { [lindex $a 2] != "/tmp" } {
      echo "Error: checking the variable related to temporary storage ..."
      echo " . pt_tmp_dir ([lindex $a 2])"
      echo "   -> pt_tmp_dir should be set to '/tmp'"
      echo "      Otherwise, it will cause the very long run time!"
      echo ""
    }

    ;# unlimit PTE-060 messages
    if {$pt_shell_mode != "primetime_master" && $pt_shell_mode != "primetime_slave"} {
      set_app_var sh_limited_messages [lminus ${::sh_limited_messages} PTE-060]
    }
  } elseif { $check_only_flag == "true" } {
    ;###########################################################################
    ;#  checking the variables
    ;###########################################################################
    set num_of_incorrect_vars 0

    echo "Checking PT variables ..."
    for { set index 1 } { $index <= [array size pt_var_arr] } { incr index } {
      redirect -variable a {printvar [lindex $pt_var_arr($index) 0]}
      #echo $a

      echo -n " . [lindex $a 0] ([lindex $a 2])"
      if { [lindex $a 2] != [lindex $pt_var_arr($index) 1] } {
        echo ""
    echo "   -> '[lindex $pt_var_arr($index) 0]' should be set to '[lindex $pt_var_arr($index) 1]'" 
    incr num_of_incorrect_vars
      } else {
        echo " : OK"
      }
    }
    echo ""

    if { $pre_post_flag == "post" } {
      echo "Checking PT SI variables ..."
      for { set index 1 } { $index <= [array size ptsi_var_arr] } { incr index } {
        redirect -variable a {printvar [lindex $ptsi_var_arr($index) 0]}

        #echo $a
        echo -n " . [lindex $a 0] ([lindex $a 2])"
    if { [lindex $a 2] != [lindex $ptsi_var_arr($index) 1] } {
      echo ""
      echo "   -> '[lindex $ptsi_var_arr($index) 0]' should be set to '[lindex $ptsi_var_arr($index) 1]'"
      incr num_of_incorrect_vars
    } else {
      echo " : OK"
    }
      }
      echo ""
    }

    if { $aocvm_flag == "true" } {
      echo "Checking AOCVM variables ..."
      for { set index 1 } { $index <= [array size aocvm_var_arr] } { incr index } {
        redirect -variable a {printvar [lindex $aocvm_var_arr($index) 0]}

    echo -n " . [lindex $a 0] ([lindex $a 2])"
    if { [lindex $a 2] != [lindex $aocvm_var_arr($index) 1] } {
      echo ""
      echo "   -> '[lindex $aocvm_var_arr($index) 0]' should be set to '[lindex $aocvm_var_arr($index) 1]'"
      incr num_of_incorrect_vars
    } else {
      echo " : OK"
    }
      }
      echo ""
    }

    if { $distributed_multicore_flag == "true" } {
      echo "Checking the variabled related to multi-core ..."
      for { set index 1 } { $index <= [array size multi_var_arr] } { incr index } {
        redirect -variable a {printvar [lindex $multi_var_arr($index) 0]}

    echo -n " . [lindex $a 0] ([lindex $a 2])"
    if { [lindex $a 2] != [lindex $multi_var_arr($index) 1] } {
      echo ""
      echo "   -> '[lindex $multi_var_arr($index) 0]' should be set to '[lindex $multi_var_arr($index) 1]'"
      incr num_of_incorrect_vars
    } else {
      echo " : OK"
    }
      }
      echo ""
    }

    redirect -variable a {printvar pt_tmp_dir}
    if { [lindex $a 2] != "/tmp" } {
      echo "Checking the variable related to temporary storage ..."
      echo " . pt_tmp_dir ([lindex $a 2])"
      echo "   -> pt_tmp_dir should be set to '/tmp'"
      echo "      Otherwise, it will cause the very long run time"
      incr num_of_incorrect_vars
      echo ""
    }

    echo "INFO: Setting of '$num_of_incorrect_vars' variables is incorrect\n"
  }


  return 1
}

define_proc_attributes set_pt_variables \
    -info "Set PrimeTime Variables to the values of SEC methodology" \
    -define_args {
    {-pre "pre-layout stage" ""  boolean optional}
    {-post "post-layout stage (including SI variables)" ""  boolean optional}
    {-check_only "check the values of variables without setting" "" boolean optional}
    {-aocvm "setting for AOCVM analysis" "" boolean optional}
    {-no_aocvm "setting for non-AOCVM analysis" "" boolean optional}
    {-multi_core "(will be obsolete)" "" boolean optional}
    {-distributed_multicore "enable the distributed multicore feature" "" boolean optional}
    {-threaded_multicore "enable the threaded multicore feature" "" boolean optional}
    {-multi_work_dir "directory for multicore analysis data (default: ./multi_work_dir)" multi_work_dir string optional} 
    {-cpu "(will be obsolete)" num_of_cores string optional}
    {-core "number of cores for multicore feature (default: 4)" num_of_cores string optional}
    }

# SCRIPT_PROTECT_BLOCK_END
