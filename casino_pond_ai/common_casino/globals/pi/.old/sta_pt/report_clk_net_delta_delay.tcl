###############################################################################
#
#  PROCEDURE:   report_clk_net_delta_delay
#
#  AUTHOR  :    J.-R. Lee
#               Chul Rim (since 2012)
#
#  ABSTRACT:    Reports the information about the delta delay values larger 
#        than 'threshold percentage to the stage delay'.
#
#  SYNTAX:      report_clk_net_delta_delay
#          [-threshold threshold_percentage]
#                    (Percentage threshold for reporting (default: 10))
#          [file]                 (file that contains the user-specified clock pins)
#
#  OUTPUT:
#        Report large delta delay(& perc. to stage delay) on clock net processing ...
#        INFO: Net 'clk_temp_3' has max rise delta stage delay 0.052ns (14.8%)
#              (drv. pin 'clk_temp_L0_1/Y')
#        INFO: Net 'clk_temp_3' has min rise delta stage delay -0.042ns (16.4%)
#              (drv. pin 'clk_temp_L0_1/Y')
#
#  RETURNS:     NA
#
#  HISTORY:    05/04/24    Generated.
#        06/05/01    Modified the mothod of searching the clock path.
#                (new: backward search from the register clock pin
#                      + exclusion of data path net)
#                Includes the clock path from the user-specified clock pin.
#                For violation net, also reports the driving pin of the net.
#        06/05/19    Removed the check 'defined(clocks)' for a pin,
#                (for some data path pins, 'clocks are defined as {...}')
#                and modified the method of clock network search.
#        06/05/22    Improved the process of user-specified clock pin.
#                - pin is connected to the clock network
#                  : add the network common to (fanin of the pin) and (clock network) 
#                - pin is NOT connected to the clock network
#                  : add the fanin network of the pin
#        06/06/26    Get the clock net length file from BF or Astro and 
#                checks the violation only for the leaf clock nets of which length 
#                is larger than 200um.
#        07/01/08    Changed the file format from BF.
#                BF should write the clock net (total-)length file, not pin-to-pin length file.
#                And this utility shows the script version.
#        08/01/02    Process the comment statement from BF/Astro net length file.
#        08/07/18    Don't check for the leaf nets in 45nm process.
#        08/12/23    Use the option '-trace_arcs all' for all_fanin/all_fanout. 
#        09/05/02    Removed the option '-trace_arcs all' in all_fain/all_fanout
#                because it caused to trace data path nets also.
#        09/07/30    Updated for support of 32nm process technology.
#        09/12/09    Does not check for the leaf net. Thus, this procedure 
#                doesn't need the clock length file any more.
#        11/02/14    Fixed a bug for the case where net timing arc isn't defined.
#        12/02/02    enhanced clock net collection algorithm
#                               provide ignore threshold for delta delay
#                               runtime enhanced by 2X ++
###############################################################################

# SCRIPT_PROTECT_BLOCK_BEGIN

global shielding_scr_version 
set shielding_scr_version "1.8 (2012.02.02)"

global sh_product_version pt_version
set pt_version    [string range [string trimleft $sh_product_version "\[A-Z\]-"] 0 6]

global verbose_mode debug_mode
set verbose_mode     0
set debug_mode         0

proc report_clk_net_delta_delay { args } {
    global shielding_scr_version
    global verbose_mode debug_mode
    global pt_version


    set st_global         [clock seconds]
    set thre_perc        10    ;# default 10%
    set user_ck_pin_file     ""
    set handle_ck_pin_file     ""
    set verbose_mode         0
    set debug_mode         0
    set use_pt_clk_tree        0
    set add_pt_clk_tree        0
    set honor_disabled        1
    set options         ""
    set filter_threshold     0.000    ;# don't care delta delay < $threshold

    parse_proc_arguments -args $args results
    foreach argname [array names results] {
    switch -glob -- $argname {
        "-filter_threshold" {
          set filter_threshold    $results($argname)
        }
        "-threshold" {
          set thre_perc         $results($argname)
        }
        "-verbose" {
          set verbose_mode         1
          
        }
        "-debug" {
          set debug_mode         1
        }
        "-dishonor_disabled" {
          set honor_disabled     0
          set options         "$options -dishonor_disabled"
        }
        "-use_pt_clock_tree" {
          set use_pt_clk_tree     1
          set options         "$options -use_pt_clock_tree"
        }
        "-add_pt_clock_tree" {
          set add_pt_clk_tree     1
          set options         "$options -add_pt_clock_tree"
        }
        default {
        set user_ck_pin_file $results($argname)
        if { [file exists $user_ck_pin_file] == 0 } {
            echo "Error: Cannot find the file '$user_ck_pin_file'"
            echo "Information: Abnormal exit ..."
            return 0
        }

        set handle_ck_pin_file [open $user_ck_pin_file r]
        }
    }
    }

    # -------------------------------------------------------------------------
    # Collect clock nets 
    # -------------------------------------------------------------------------
    eval "set all_clk_nets     \[sec_collect_clock_network_objects $options -type net\]"

    # -------------------------------------------------------------------------
    # Checks the delta delay for each clock net
    # -------------------------------------------------------------------------
    set num_violation     0
    set num_nets     [sizeof $all_clk_nets]
    set prog_step    [expr $num_nets / 20]    ;# every 5%
    echo "INFO: processing $num_nets clock nets"
    # check the clock shielding and report the violation
    set cnt        0
    set st       [clock seconds]
    foreach_in_collection net $all_clk_nets {
      set net_name [get_object_name $net]
#      set all_net_arcs [get_timing_arcs -quiet -of_objects $net]
      ;# to improve runtime
      if {$filter_threshold == 0.0} {
    set all_net_arcs [get_timing_arcs -quiet -of_objects $net -filter \
              "annotated_delay_delta_max_rise != 0.0 || \
              annotated_delay_delta_max_fall != 0.0 || \
              annotated_delay_delta_min_rise != 0.0 || \
              annotated_delay_delta_min_fall != 0.0"]
      } else {
    set all_net_arcs [get_timing_arcs -quiet -of_objects $net -filter \
              "annotated_delay_delta_max_rise >= $filter_threshold || annotated_delay_delta_max_rise <= -$filter_threshold || \
              annotated_delay_delta_max_fall >= $filter_threshold || annotated_delay_delta_max_fall <= -$filter_threshold || \
              annotated_delay_delta_min_rise >= $filter_threshold || annotated_delay_delta_min_rise <= -$filter_threshold || \
              annotated_delay_delta_min_fall >= $filter_threshold || annotated_delay_delta_min_fall <= -$filter_threshold"]
      }

      ;# ignore the port net because port net doesn't have the real parasitic
      if { [get_port -quiet -of $net] != "" } {
      continue
      }

      set is_leaf_net     0
      set load_pins [get_pin -quiet -leaf -of $net -filter "direction == in"]
      if {$load_pins == ""} {
    continue
      }

      if {[filter_collection $load_pins "is_clock_pin == true"] != ""} {
    set is_leaf_net     1
      } else {
    set is_leaf_net     0
      }

      set m_delta_max_rise 0
      set m_delta_max_fall 0
      set m_delta_min_rise 0
      set m_delta_min_fall 0
      set max_delta_perc_max 0
      set max_delta_perc_min 0
      set delta_max 0
      set delta_min 0
      set arc_type_max ""
      set arc_type_min ""

      foreach_in_collection net_arc $all_net_arcs {
    set delta_min_rise     [get_attr $net_arc annotated_delay_delta_min_rise]
    set delta_min_fall     [get_attr $net_arc annotated_delay_delta_min_fall]
    set delta_max_rise     [get_attr $net_arc annotated_delay_delta_max_rise]
    set delta_max_fall     [get_attr $net_arc annotated_delay_delta_max_fall]
    set net_min_rise     [get_attr $net_arc delay_min_rise -quiet]
    set net_min_fall    [get_attr $net_arc delay_min_fall -quiet]
    set net_max_rise    [get_attr $net_arc delay_max_rise -quiet]
    set net_max_fall    [get_attr $net_arc delay_max_fall -quiet]
    set net_from_pin    [get_attr $net_arc from_pin]
    set net_to_pin         [get_attr $net_arc to_pin]

    if { $net_min_rise == "" } { set net_min_rise 0 }
    if { $net_min_fall == "" } { set net_min_fall 0 }
    if { $net_max_rise == "" } { set net_max_rise 0 }
    if { $net_max_fall == "" } { set net_max_fall 0 }

    ;# need processing for the port of the core
    set all_cell_arcs [filter_collection [get_timing_arcs -to $net_from_pin] \
                {is_cellarc == true && sense != clear_high && sense != clear_low && sense != preset_high && sense != preset_low}]
    foreach_in_collection cell_arc $all_cell_arcs {
        set cell_min_rise [get_attr $cell_arc delay_min_rise -quiet]
        set cell_min_fall [get_attr $cell_arc delay_min_fall -quiet]
        set cell_max_rise [get_attr $cell_arc delay_max_rise -quiet]
        set cell_max_fall [get_attr $cell_arc delay_max_fall -quiet]

        if { $cell_min_rise != "" && $cell_min_rise != 0} {
        set stage_min_rise [expr $cell_min_rise + $net_min_rise]
        } else {
        set stage_min_rise 0
        }
        if { $cell_min_fall != "" && $cell_min_fall != 0} {
        set stage_min_fall [expr $cell_min_fall + $net_min_fall]
        } else {
        set stage_min_fall 0
        }
        if { $cell_max_rise != "" && $cell_max_rise != 0} {
        set stage_max_rise [expr $cell_max_rise + $net_max_rise]
        } else {
        set stage_max_rise 0
        }
        if { $cell_max_fall != "" && $cell_max_fall != 0} {
        set stage_max_fall [expr $cell_max_fall + $net_max_fall]
        } else {
        set stage_max_fall 0
        }

        set delta_perc_min_rise 0; set delta_perc_min_fall 0
        set delta_perc_max_rise 0; set delta_perc_max_fall 0

        if { $stage_min_rise != 0 && $is_leaf_net == 0 } {
        set delta_perc_min_rise [expr abs($delta_min_rise / $stage_min_rise * 100)]
        if { $max_delta_perc_min < $delta_perc_min_rise } {
            set max_delta_perc_min     $delta_perc_min_rise
            set delta_min         $delta_min_rise
            set arc_type_min         "min-rise"
            set net_from_pin_min     [get_object_name $net_from_pin]
            set net_to_pin_min         [get_object_name $net_to_pin]
        }
        }
        if { $stage_min_fall != 0 && $is_leaf_net == 0 } {
        set delta_perc_min_fall [expr abs($delta_min_fall / $stage_min_fall * 100)]
        if { $max_delta_perc_min < $delta_perc_min_fall } {
            set max_delta_perc_min     $delta_perc_min_fall
            set delta_min         $delta_min_fall
            set arc_type_min         "min-fall"
            set net_from_pin_min     [get_object_name $net_from_pin]
            set net_to_pin_min         [get_object_name $net_to_pin]
        }
        }
        if { $stage_max_rise != 0 && $is_leaf_net == 0 } {
        set delta_perc_max_rise [expr $delta_max_rise / $stage_max_rise * 100]
        if { $max_delta_perc_max < $delta_perc_max_rise } {
            set max_delta_perc_max     $delta_perc_max_rise
            set delta_max         $delta_max_rise
            set arc_type_max         "max-rise"
            set net_from_pin_max     [get_object_name $net_from_pin]
            set net_to_pin_max         [get_object_name $net_to_pin]
        }
        }
        if { $stage_max_fall != 0 && $is_leaf_net == 0 } {
        set delta_perc_max_fall [expr $delta_max_fall / $stage_max_fall * 100]
        if { $max_delta_perc_max < $delta_perc_max_fall } {
            set max_delta_perc_max     $delta_perc_max_fall
            set delta_max         $delta_max_fall
            set arc_type_max        "max-fall"
            set net_from_pin_max    [get_object_name $net_from_pin]
            set net_to_pin_max         [get_object_name $net_to_pin]
        }
        }

        #if { $delta_perc_min_rise >= 0 || $delta_perc_min_fall >= 0 || $delta_perc_max_rise >= 0 || $delta_perc_max_fall >= 0 } {
        #  echo [format "%s %.5g:%.5g:%.5g:%.5g" $net_name $delta_perc_min_rise $delta_perc_min_fall $delta_perc_max_rise $delta_perc_max_fall]
        #}
    }
      }

      # ----------------------------------------------------------------------
      # Reports about the violation
      # ----------------------------------------------------------------------
      if { $max_delta_perc_max > $thre_perc } {
      echo [format "INFO: Net '%s' has %s delta stage delay %.3f%s (%.1f%%)" \
          $net_name $arc_type_max $delta_max "ns" $max_delta_perc_max]
      echo [format "      (drv. pin '%s')" $net_from_pin_max]

      incr num_violation
      }
      if { $max_delta_perc_min > $thre_perc } {
      echo [format "INFO: Net '%s' has %s delta stage delay %.3f%s (%.1f%%)" \
          $net_name $arc_type_min $delta_min "ns" $max_delta_perc_min]
      echo [format "      (drv. pin '%s')" $net_from_pin_min]

      incr num_violation
      }
      if {$verbose_mode} {
    incr cnt
    if {[expr $cnt % $prog_step] == 0 } {
      echo [format "... %d nets processed (%.0f %% completed)" $cnt [expr ($cnt / double($num_nets)) * 100.0]]
    }
      }
    }
    set elapsed_time_string \
          [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $st] \
              -format "%H hours %M mins %S secs"]
    verbose_msg "... Examination took {$elapsed_time_string}"

    echo "\n* Number of Violations : $num_violation\n"
    set elapsed_time_string \
          [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $st_global] \
              -format "%H hours %M mins %S secs"]
    verbose_msg "... Totally took for clock net Xtalk check - {$elapsed_time_string}"
}


# -----------------------------------------------------------------------------
# procedure collect and return clock network cells
# -----------------------------------------------------------------------------
proc sec_collect_clock_network_objects {args} {
  global verbose_mode debug_mode
  global sh_product_version pt_version

  set include_seq        0
  set include_bypass        0
  set only_bypass        0
  set use_pt_clock_tree        0
  set add_pt_clock_tree        0
  set honor_disabled_arcs    1
  set options            ""
  set obj_type             "net"

  set starttime0       [clock seconds]

  parse_proc_arguments -args $args results
  foreach argname [array names results] {
    switch -glob -- $argname {
      "-type" {
    set obj_type        $results($argname)
    if {$obj_type == "cell"} {
      set options "$options -only_cells"
    } 
      }
      "-include_seq" {
    set include_seq        1
      }
      "-include_bypass" {
    set include_bypass    1
      }
      "-dishonor_disabled" {
    set honor_disabled_arcs    0
      }
      "-only_bypass" {
    set only_bypass        1
      }
      "-use_pt_clock_tree" {
    set use_pt_clock_tree    1
      }
      "-add_pt_clock_tree" {
    set add_pt_clock_tree    1
      }
      default {
    echo "** SEC_ERROR: unknown argument - $args"
    continue
      }
    }
  }

  if {$honor_disabled_arcs == 0} {
    set options "$options -trace_arcs all"
  } else {
    set options "$options -trace_arcs timing"
  }

  set starttime       [clock seconds]
  ;# extract clock tree
  if { $use_pt_clock_tree == 0} {
    ;#------------------------------------------------------------------------------
    ;# Custom clock tree extraction
    ;#------------------------------------------------------------------------------

    verbose_msg "   - step 1. Tracing clock tree objects from all clock sources... (incluiding leaf flops)"
    ;#------------------------------------------------------------------------------
    ;# collect fanout cone from clock sources
    ;#------------------------------------------------------------------------------
    eval "set CONE_FROM_SRC    \[all_fanout -flat -clock_tree $options\]"

    ;# add possible master sources to cope with wrongly defined gen clocks
    set gen_clk_sources  [get_attr -quiet [filter_collection [all_clocks] "is_generated == true"] sources]
    if {$gen_clk_sources != ""} {
      set possible_master_sources [filter_collection [all_fanin -flat -start -to $gen_clk_sources] "is_clock_gating_pin == false"]
      if {$verbose_mode} {
    set all_clock_sources     [get_attr -quiet [all_clocks] sources]
    foreach_in_collection src $possible_master_sources {
      if {[set cell [get_cells -quiet -of $src]] == ""} {    ;# port
        if {[filter_collection $all_clock_sources "full_name == [get_object_name $src]"] == ""} { ;# no clock defined
          verbose_msg "             WARN: adding possible missing clock source - [get_object_name $src]"
        }
        continue
      }
      set is_clk_defined     0
      foreach_in_collection pin [get_pins -of $cell -filter "direction != in"] {
        if {[filter_collection $all_clock_sources "full_name == [get_object_name $pin]"] != ""} {
          set is_clk_defined     1
          break
        }
      }
      if {$is_clk_defined == 0} {
        verbose_msg "             WARN: adding possible missing clock source - [get_object_name $src]"
      }
    }
      }
      if {$possible_master_sources != "" } {
    eval "append_to_collection -unique CONE_FROM_SRC \[all_fanout -flat $options -from $possible_master_sources\]"
      }
    }

    set elapsed_time_string \
          [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $starttime] \
              -format "%H hours %M mins %S secs"]
    verbose_msg "             ... took {$elapsed_time_string}"
    verbose_msg "             --> [sizeof $CONE_FROM_SRC] objects"

    ;#------------------------------------------------------------------------------
    ;# collect possible sink pins
    ;#------------------------------------------------------------------------------
    verbose_msg "   - step 2. Tracing clock tree objects backwards from clk sink pins..."
    verbose_msg "             (this may take time)"
    set starttime       [clock seconds]

    if {$only_bypass == 0} {
      ;# collect possible clock pins 
      set ALL_SINK_PINS     [filter_collection [all_registers -clock_pin] "is_data_pin == false"]

      ;# add possible macro clock pins
      set unknown_clock_pins     [get_pins -quiet -hier * -filter \
                  {direction != out && is_hierarchical == false && is_clock_pin == false && \
                    ( lib_pin_name =~ "CK*" || lib_pin_name =~ "CLK*" )}]
      append_to_collection -unique ALL_SINK_PINS $unknown_clock_pins
      if {$unknown_clock_pins != ""} {
    verbose_msg "             *info* adding [sizeof $unknown_clock_pins] undefined 'CK*' and 'CLK*' pins as sink"
      }
      if {$debug_mode} {
    foreach_in_collection pin $unknown_clock_pins {
      verbose_msg "             ... suspicious clock pin - [get_object_name $pin]"
    }
      }
      
      ;# add generated clock sources
      set gen_clk_sources  [get_attr -quiet [filter_collection [all_clocks] "is_generated == true"] sources]
      if {$gen_clk_sources != ""} {
    append_to_collection ALL_SINK_PINS $gen_clk_sources
    verbose_msg "             *info* adding [sizeof $gen_clk_sources] generated clock sources as sink"
      }

      ;# add bypassing clock paths
      if {$include_bypass == 1} {
    verbose_msg "             *info* including clock by-passing paths"
    append_to_collection ALL_SINK_PINS    [all_outputs]
      }

      ;# exclude possible macro clock pins
      set bogus_clk_pins    [filter_collection $ALL_SINK_PINS \
                  "lib_pin_name =~ TCEN* || lib_pin_name =~ RET* || lib_pin_name =~ CEN* || lib_pin_name =~ DFTRAM* || lib_pin_name =~ PGEN*"]
      if {$bogus_clk_pins != ""} {
    verbose_msg "             *info* excluding [sizeof $bogus_clk_pins] bogus clock pins such as RET*, CEN*, DFTRAM*, PGEN*"
    set ALL_SINK_PINS        [remove_from_collection $ALL_SINK_PINS $bogus_clk_pins]
      }
    } else {    ;# only bypassing pins
      verbose_msg "             *info* checking only clock by-passing paths"
      append_to_collection ALL_SINK_PINS    [all_outputs]
    }
    ;#------------------------------------------------------------------------------
    ;# trace back
    ;#------------------------------------------------------------------------------
    verbose_msg "             *info* tracing back from [sizeof $ALL_SINK_PINS] clock sink points"
    eval "set CONE_TO_SINK \[all_fanin -flat $options -to $ALL_SINK_PINS\]"
    set elapsed_time_string \
          [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $starttime] \
              -format "%H hours %M mins %S secs"]
    verbose_msg "             ... took {$elapsed_time_string}"
    verbose_msg "             --> [sizeof $CONE_TO_SINK] objects"

    verbose_msg "   - step 3. Intersecting (1) & (2) ..."
    set ABANDON1        [remove_from_collection \
                  $CONE_FROM_SRC $CONE_TO_SINK]
    set ABANDON2        [remove_from_collection \
                  $CONE_TO_SINK $CONE_FROM_SRC]


    set REAL_CLKNET_OBJS    \
      [remove_from_collection [add_to_collection -unique $CONE_FROM_SRC $CONE_TO_SINK] \
                  [add_to_collection $ABANDON1 $ABANDON2]]

    verbose_msg "             --> [sizeof $REAL_CLKNET_OBJS] objects"
    ;#------------------------------------------------------------------------------
    ;# adding PrimeTime's identified clock tree
    ;#------------------------------------------------------------------------------
    if {$add_pt_clock_tree} {
      verbose_msg "             Adding PrimeTime clock tree..."
      set PT_CLKNET_OBJS [all_fanout -flat -clock_tree -only_cells]
      verbose_msg "             ... unite [sizeof $PT_CLKNET_OBJS] objects"
      append_to_collection -unique REAL_CLKNET_OBJS ${PT_CLKNET_OBJS}
      verbose_msg "             ... [sizeof $REAL_CLKNET_OBJS] united objects"
    }
  } elseif { $use_pt_clock_tree == 1 } {
    ;#------------------------------------------------------------------------------
    ;# Use PrimeTime's native clock tree
    ;# This may includes clock propagates into data paths
    ;#------------------------------------------------------------------------------
    verbose_msg "   - skipping manual clock tree collection steps (1 ~ 3)"
    verbose_msg "   - Collecting PrimeTime inferring clock tree cells instead ..."
    set starttime       [clock seconds]
    eval "set REAL_CLKNET_OBJS \[all_fanout -flat -clock_tree $options\]"
    set elapsed_time_string \
          [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $starttime] \
              -format "%H hours %M mins %S secs"]
    verbose_msg "             ... took {$elapsed_time_string}"
    verbose_msg "             --> [sizeof $REAL_CLKNET_OBJS] objects"
  }
  ;#------------------------------------------------------------------------------
  ;# Exclude leaf flops
  ;#------------------------------------------------------------------------------
  if { $include_seq == 0  && $obj_type == "cell"} {
    verbose_msg "   - step 4. Excluding leaf flops ..."
    unset -nocomplain flops_to_remove
    set seq_cells [filter_collection $REAL_CLK_TREE_CELLS \
            "is_sequential == true && is_integrated_clock_gating_cell == false"]

    set seq_opins [get_pins -quiet -of $seq_cells -filter "direction == out"]
    set gclk_seq_opins     [filter_collection $seq_opins defined(clocks)]
    set flops_to_remove [remove_from_collection $seq_cells [get_cells -quiet -of $gclk_seq_opins]]
    append_to_collection flops_to_remove [filter_collection $seq_cells {ref_name =~ "*FPC*"}]

    if {[info exist flops_to_remove]} {
      verbose_msg "             --> [sizeof $flops_to_remove] flops to remove"
      if {[info exist flops_to_remove]} {
    set REAL_CLKNET_OBJS     [remove_from_collection $REAL_CLKNET_OBJS $flops_to_remove]
      }
    } else {
      verbose_msg "             --> no flops to remove"
    }
  } elseif {$obj_type == "net"} {
    verbose_msg "   - extracting nets from [sizeof $REAL_CLKNET_OBJS] pins"
    set REAL_CLKNET_OBJS     [get_nets -quiet -top_net -segments -of $REAL_CLKNET_OBJS]
  }

  verbose_msg "   ... finally [sizeof $REAL_CLKNET_OBJS] clock tree objects collected."
  set elapsed_time_string \
        [clock format [expr [clock scan 1999-10-31] + [clock seconds] - $starttime0] \
            -format "%H hours %M mins %S secs"]
  verbose_msg "   ... totally took {$elapsed_time_string} for clock net object collecting"
  return $REAL_CLKNET_OBJS
}


proc verbose_msg { args } {
  global verbose_mode
  if {$verbose_mode == 0} {
    return
  }
  if { [llength $args] > 1 } {
    set fp      [lindex $args 0]
    set msg     [lindex [lrange $args 1 [expr [llength $args] - 1]] 0]
  } else {
    set fp      "stdout";
    set msg     [lindex $args 0]
  }
  if {$fp == "stdout"} {
    echo $msg
  } else {
    echo "$msg"
    puts $fp $msg
  }
}


define_proc_attributes sec_collect_clock_network_objects \
    -info "SEC-custom collecting clock tree" \
    -define_args {
      {-type             "object type" "" one_of_string {optional {values {cell net}}} required}
      {-dishonor_disabled     "dishonor disabled timing arcs" "" boolean optional}
      {-use_pt_clock_tree    "use PrimeTime's clock tree (all_fanout -flat -clock_tree)" "" boolean optional}
      {-add_pt_clock_tree    "unite PrimeTime's clock tree with the custom extracted" "" boolean optional}
    }


define_proc_attributes report_clk_net_delta_delay \
    -info "Reports the large delta delay for clock nets" \
    -define_args { 
      {-threshold         "percentage threshold for reporting (default: 10)" threshold_percentage string optional} 
      {-dishonor_disabled     "dishonor disabled timing arcs (to cover possible other modes)" "" boolean optional}
      {-use_pt_clock_tree    "use PrimeTime's clock tree (all_fanout -flat -clock_tree)" "" boolean optional}
      {-add_pt_clock_tree    "unite PrimeTime's clock tree with the custom extracted" "" boolean optional}
      {-filter_threshold    "don't care if ABS delta delay is less than the threshold (in ns, default = 0.0, recommended < 0.001" "" float optional}
      {-verbose         "issue messages" "" boolean optional}
      {-debug             "turn on debug mode" "" boolean {optional hidden}}
      {file_name         "file that contains the user-specified clock pins" file string optional}
    }

# SCRIPT_PROTECT_BLOCK_END
