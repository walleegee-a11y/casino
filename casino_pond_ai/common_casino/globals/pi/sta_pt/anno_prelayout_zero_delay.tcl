###############################################################################
#
#  FILE:    anno_prelayout_zero_delay.tcl
#
#  ABSTRACT:    This script is intended to backannotate zero delays & transition times 
#        on high-fanout nets.
#
#        Usage:
#         anno_prelayout_zero_delay 
#                 # Backannotate zero delays on high-fanout nets
#           [-preset_clear]        (annotate zero delay on preset and clear pins)
#           [file]                 (file that contains high-fanout net names)
#
#  AUTHOR:    J.-R. Lee
#
#  HISTORY:    05/04/11    Generated
#        06/12/07    There are clock nets used in data path.
#                We decided we don't need to annotate to the clock network
#                because ideal clock is assumed in pre-layout.
#                And this utility shows the script version.
#        07/01/08    Checks if the net from high-fanout net file exist or not.
#        07/01/17    Checks if the high-fanout net file or -preset_clear option
#                does exist.
#        07/04/16    Support the format of the high-fanout net file from CubicWare
#        07/05/09    Restored the feature of annotating zero delay on clock network.
#                It has the enhanced functionality.
#                And this version of script does not check if the high-fanout
#                net file or -preset_clear option exists.
#                The default annotation will be done on the clock nets. 
#        08/12/23    Use the option '-trace_arcs all' for all_fanin/all_fanout.
#
###############################################################################

# SCRIPT_PROTECT_BLOCK_BEGIN

global anno_scr_version 
set anno_scr_version "1.3 (2008.12.23)"

global sh_product_version pt_version
set pt_version    [string range [string trimleft $sh_product_version "\[A-Z\]-"] 0 6]

proc anno_prelayout_zero_delay { args } {
    global anno_scr_version
    echo "Version $anno_scr_version"

    global pt_version

    set curr_date [date]
    set curr_time [lindex $curr_date 3]
    set curr_pid [pid]

    set high_fanout_net_file ""
    set handle_ck_pin_file ""
    set preset_clear_flag false
    set verbose_flag false

    parse_proc_arguments -args $args results
    foreach argname [array names results] {
    switch -glob -- $argname {
        "-p*"   { 
        set preset_clear_flag true 
        }
        "-v*"   {
        set verbose_flag true
        }
        "-u*"   {
        set user_ck_pin_file $results($argname)
                if { [file exists $user_ck_pin_file] == 0 } {
                    echo "Error: Cannot find the file '$user_ck_pin_file'"
                    echo "Information: Abnormal exit ..."
                    return 0
                }

        set handle_ck_pin_file [open $user_ck_pin_file r]
        }
        default { 
        set high_fanout_net_file $results($argname) 
#        puts "# high-fanout net file : $high_fanout_net_file"
        if { [file exists $high_fanout_net_file] == 0 } {
            puts "Error: Cannot find the file '$high_fanout_net_file'"
            puts "Information: Abnormal exit without annotation of zero delay"
            return 0
        }

        set handle_net_file [open $high_fanout_net_file r]
        }
    }
    }

    #if { $high_fanout_net_file == "" && $preset_clear_flag == "false" } {
    #echo "Error: The high-fanout net file or -preset_clear option is required"
    #return 0
    #}

    echo "Info: Setting all cell/net delays on clock network to zero ..."

# In order to get the list of all clock nets, we use the file interface.
# The following command(without file interface) is also possible.
# But it takes long long time due to the '-unique' option.
# 
# set all_clk_nets [add_to_collection $all_clk_nets $nets -unique]
#
    #set handle1 [open ".pt_run_tmp1_$curr_pid" w]
    #set all_clk_pins [all_fanout -clock_tree -flat]
    #foreach_in_collection pin $all_clk_pins {
    #set net [get_nets -quiet -of_object $pin -segments -top_net_of_hierarchical_group]
    #set net_name [get_object_name $net]
    #puts $handle1 "$net_name"
    #}
    #close $handle1
    #exec sort -u .pt_run_tmp1_$curr_pid > .pt_run_tmp2_$curr_pid
    #exec rm .pt_run_tmp1_$curr_pid

    #
    # New code for finding nets from the clock network
    #
    # Network (fanout cone) from the clock source
    if { $pt_version >= 2007.12 } {
      set all_clk_pins_fore [all_fanout -trace_arcs all -clock_tree -flat]
    } else {
      set all_clk_pins_fore [all_fanout -clock_tree -flat]
    }
    set all_clk_nets_fore [get_nets -quiet -of $all_clk_pins_fore -top -seg]
    set num_all_clk_nets_fore [sizeof $all_clk_nets_fore]

    set user_ck_pins ""
    set user_not_ck_pins ""
    if { $handle_ck_pin_file != "" } {
      while { [gets $handle_ck_pin_file line] >= 0 } {
        set pin_name [lindex $line 0]
    set pin [get_pins -quiet $pin_name]
    if { $pin == "" } {
      set pin [get_ports -quiet $pin_name]
    }
    if { $pin == "" } {
      echo "Error: Cannot find the user-specified clock pin '$pin_name'"
      continue
    }

    # fanin cone from user-specified CK pin (port)
    if { $pt_version >= 2007.12 } {
      set fanin_user_ck_pin [all_fanin -trace_arcs all -flat -to $pin]
    } else {
      set fanin_user_ck_pin [all_fanin -flat -to $pin]
    }
    set fanin_user_nets [get_nets -quiet -of $fanin_user_ck_pin -top -seg]

    set num_nets [sizeof [remove_from_coll $all_clk_nets_fore $fanin_user_nets]]
    if { $num_all_clk_nets_fore != $num_nets } {
      append_to_coll user_ck_pins $pin
    } else {
      echo "INFO: User-specified pin '$pin_name' NOT connected to Clock"
      append_to_coll user_not_ck_pins $pin
    }
      }
      close $handle_ck_pin_file
    }

    if { $pt_version >= 2007.12 } {
      redirect -var ttt { set user_clk_nets_back [get_nets -quiet -of [all_fanin -trace_arcs all -flat -to $user_ck_pins] -top -seg] ; echo -n "" }
    } else {
      redirect -var ttt { set user_clk_nets_back [get_nets -quiet -of [all_fanin -flat -to $user_ck_pins] -top -seg] ; echo -n "" }
    }
    set all_user_clk_nets [remove_from_coll $user_clk_nets_back [remove_from_coll $user_clk_nets_back $all_clk_nets_fore]]

    # Network to register clock pin
    set reg_ck_pins [all_registers -clock_pins]
    append_to_coll reg_ck_pins $user_ck_pins
    if { $pt_version >= 2007.12 } {
      set all_clk_pins_back [all_fanin -trace_arcs all -flat -to $reg_ck_pins]
    } else {
      set all_clk_pins_back [all_fanin -flat -to $reg_ck_pins]
    }
    set all_clk_nets_back [get_nets -quiet -of $all_clk_pins_back -top -seg]

    # Common network from clock source to register clock pin
    set all_clk_nets [remove_from_coll $all_clk_nets_back [remove_from_coll $all_clk_nets_back $all_clk_nets_fore]]

    echo -n "" > .pt_run_annotate_$curr_pid

    echo "# Clock Network" >> .pt_run_annotate_$curr_pid

    #set handle2 [open ".pt_run_tmp2_$curr_pid" r]
    #while { [gets $handle2 line] >= 0 } {  #}
    #set net_name [lindex $line 0]
    foreach_in_coll net $all_clk_nets {
        set net_name [get_object_name $net]
    set net [get_nets $net_name]
    set net_from_pins [get_pins -of $net -filter "direction == out || direction == inout" -leaf -quiet]

# We do not annotate zero transition time on clock net 
# because designer may have set the transition time using set_clock_transition.
#
    foreach_in_collection from_pin $net_from_pins {
        set drv_cell [get_cell -of $from_pin]
        set ref_name_of_drv_cell [get_attr $drv_cell ref_name]
        if { $ref_name_of_drv_cell == "**logic_one**" 
            || $ref_name_of_drv_cell == "**logic_zero**" } {
        continue
        }

        set from_pin_name [get_object_name $from_pin]
        echo "set_annotated_delay -cell -to $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
    }

    set net_from_ports [get_ports -of $net -filter "direction == in || direction == inout" -quiet]
    foreach_in_collection from_pin $net_from_ports {
        set from_pin_name [get_object_name $from_pin]
        echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
    }
    }

    #close $handle2
    #exec rm .pt_run_tmp2_$curr_pid

########
    echo "# High Fanout Nets" >> .pt_run_annotate_$curr_pid

    if { $high_fanout_net_file != "" } {
    echo "Info: Setting all cell/net delays and slopes on high-fanout nets to zero ..."

    set handle2 [open $high_fanout_net_file r]
    set line_num 0
    while { [gets $handle_net_file line] >= 0 } {
        incr line_num
        regsub -all {\{} $line {\{} line
        regsub -all {\}} $line {\}} line 

        set arg1 [lindex $line 0]
        if { $arg1 == "#" || $line == "" } continue
        if { $line == "Huge Fanout \\\{" || $line == "Huge Load \\\{" || $line == "\\\}" } continue

        if { [llength $line] == 1 } {
        set net_name $arg1
        } elseif { [llength $line] == 2 } {
        if { [regexp {[0-9]+\) (.+)} $line all net_name] } {
        } else {
            echo "Error: Line '$line' is invalid (line $line_num)"
            continue
        }
        } else {
        echo "Error: Line '$line' is invalid (line $line_num)"
        continue
        }

        set net [get_nets -quiet $net_name]
        if { $net == "" } {
        echo "Error: Net '$net_name' from high-fanout file does not exist"
        continue
        }
        #echo " - processing $net_name"

        set net_from_pins [get_pins -of $net -filter "direction == out || direction == inout" -leaf -quiet]
        foreach_in_collection from_pin $net_from_pins {
        set drv_cell [get_cell -of $from_pin]
        set ref_name_of_drv_cell [get_attr $drv_cell ref_name]
        if { $ref_name_of_drv_cell == "**logic_one**" 
            || $ref_name_of_drv_cell == "**logic_zero**" } {
            continue
        }

        set from_pin_name [get_object_name $from_pin]
        echo "set_annotated_delay -cell -to $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_transition 0 $from_pin_name" >> .pt_run_annotate_$curr_pid
        }

        set net_from_ports [get_ports -of $net -filter "direction == in || direction == inout" -quiet]
        foreach_in_collection from_pin $net_from_ports {
        set from_pin_name [get_object_name $from_pin]
            echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_transition 0 $from_pin_name" >> .pt_run_annotate_$curr_pid
            }
           }

    close $handle2
    }

########
    echo "# Preset/Clear Pins" >> .pt_run_annotate_$curr_pid

    if { $preset_clear_flag == "true" } {
    echo "Info: Setting all cell/net delays and slopes about set/reset pins to zero ..."

    set handle3 [open ".pt_run_tmp3_$curr_pid" w]
    set preset_clear_pins [get_pins * -hier -filter "is_preset_pin == true || is_clear_pin == true"]

    foreach_in_collection pin $preset_clear_pins {
        set net [get_nets -quiet -of_object $pin -segments -top_net_of_hierarchical_group]
#        set pin_name [get_object_name $pin]
        set net_name [get_object_name $net]

        puts $handle3 "$net_name"
    }
    close $handle3
    exec sort -u .pt_run_tmp3_$curr_pid > .pt_run_tmp4_$curr_pid
    exec rm .pt_run_tmp3_$curr_pid

    set handle4 [open ".pt_run_tmp4_$curr_pid" r]
    while { [gets $handle4 line] >= 0 } {
        set net_name [lindex $line 0]
        set net [get_nets $net_name]

        set net_from_pins [get_pins -of $net -filter "direction == out || direction == inout" -leaf -quiet]
        foreach_in_collection from_pin $net_from_pins {
        set drv_cell [get_cell -of $from_pin]
        set ref_name_of_drv_cell [get_attr $drv_cell ref_name]
        if { $ref_name_of_drv_cell == "**logic_one**" 
            || $ref_name_of_drv_cell == "**logic_zero**" } {
            continue
        }

        set from_pin_name [get_object_name $from_pin]
        echo "set_annotated_delay -cell -to $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_transition 0 $from_pin_name" >> .pt_run_annotate_$curr_pid
        }

        set net_from_ports [get_ports -of $net -filter "direction == in || direction == inout" -quiet]
        foreach_in_collection from_pin $net_from_ports {
        set from_pin_name [get_object_name $from_pin]
            echo "set_annotated_delay -net -from $from_pin_name 0" >> .pt_run_annotate_$curr_pid
        echo "set_annotated_transition 0 $from_pin_name" >> .pt_run_annotate_$curr_pid
            }
    }
    close $handle4
    exec rm .pt_run_tmp4_$curr_pid
    }

########

    source .pt_run_annotate_$curr_pid
    if { $verbose_flag == "false" } {
    exec rm .pt_run_annotate_$curr_pid
    }

    return 1
}

define_proc_attributes anno_prelayout_zero_delay \
    -info "Backannotate zero delays on high-fanout nets" \
    -define_args {
    {-preset_clear "annotate zero delay on preset and clear pins" ""  boolean optional}
    {-verbose "make the annotation log .pt_run_annotate_%pid" ""  boolean optional}
    {-user_ck_pin "file that contains the user_specified clock pins" user_ck_pin_file string optional}
    {file_name "file that contains high-fanout net names" file string optional}
    }

# SCRIPT_PROTECT_BLOCK_END
