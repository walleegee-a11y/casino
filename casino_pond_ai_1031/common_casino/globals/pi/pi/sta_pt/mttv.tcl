######################################################################
#          MTTV report like Cubic 
#      Copyright (c), Samsung Electronics Co., Ltd., 2006
#                     All rights reserved.
#
# FUNCTION: A PrimeTime TCL procedure for MTTV summary report.
# Written by In-Sun Cho, Eung-Chul Jeon, Samsung Electronics Co., Ltd.
# PHONE: 82-31-209-3428
######################################################################

# SCRIPT_PROTECT_BLOCK_BEGIN

global mttv_scr_version
set mttv_scr_version "2.3 (2008.05.25)"

proc mttv { args } {
    global mttv_scr_version

    parse_proc_arguments -args $args results
    set file $results(all_vio_file)
    set out $results(output_file)

    set input [open $file r] ; # Open all_viol.rpt file to read


    ## if finding max_transition index, stop reading file.
    while { [gets $input line] >=0 } {
      if {[lindex $line 0] == "max_transition"} {
        break
      }
    }


    ## from max_transition field, listing pin and required transition.
    foreach list [split [read $input] "\n"] {
        if { [llength $list] == 5 } {
            if [string match "*pad*\/P" $list] {
            } elseif { [regsub -all {\/} [lindex $list 0] { } tmp] == 0 } {
            } else {
                set pin [lindex $list 0]
                set req [lindex $list 1]
                lappend myList($pin) $req
            }
        } else {
            continue
        }
    }

    close $input



    if { [ file exists tmp ] > 0 } {
        sh rm tmp
    }
    if { [ file exists viol.tran ] > 0 } {
        sh rm viol.tran
    }


    if { [llength [array names myList]] == 0 } {
        set FO [open $out w]
        puts $FO "-----------------" 
        puts $FO " There's NO MTTV"
        puts $FO "-----------------"
    } else {
    foreach itr [array names myList] {
        echo "$itr $myList($itr)" >> tmp
    }

    ## Sort by REQ.
    sh sort -k 2 tmp > viol.tran
    set input [open "viol.tran" r]
    set pins [list ]

    while { [gets $input line] != -1 } {
        lappend pins [lindex $line 0]
    }
    close $input


    set find_net [list ]
    set driver_list [list ]
    
    if { [ file exists $out ] > 0 } {
        sh rm $out
    }

    set FO [open $out w]
    
    puts $FO "### Reporting MTTV Summary ..."
    puts $FO "### Version $mttv_scr_version"
    echo "Reporting MTTV Summary ..."
    echo "Version $mttv_scr_version"

    foreach pin $pins {
        set nets [all_connected $pin]
        foreach_in_collection net $nets {
            if { [lsearch $find_net [get_object_name $net]] < 0 } {
                lappend find_net [get_object_name $net]

                set fanouts [sort_collection [get_pins -leaf -of [get_nets [get_object_name $net]]] full_name]

                if { [regsub -all {\/} $pin { } tmp] == 0 } {
                    ## It is "Port".
                    set fanouts [sort_collection [add_to_collection $fanouts [get_ports -of [get_nets [get_object_name $net]]]] full_name]
                    set num [sizeof_collection $fanouts]
                    set tmp1 "+ $pin : REQ : $myList($pin) : (#.fanout [expr $num - 1])"
                    set tmp2 "  +-- Net: [get_object_name $net]"
                    #puts $FO "+ $pin : REQ : $myList($pin) : (#.fanout [expr $num - 1])"
                    #puts $FO "  +-- Net: [get_object_name $net]"
                } else {
                    ## It is "Pin".
                    set num [sizeof_collection $fanouts]
                    set tmp1 "+ $pin ([get_attribute [get_cells -of $pin] ref_name]): REQ : $myList($pin) (#.fanout [expr $num - 1])"
                    set tmp2 "  +-- Net: [get_object_name $net]"
                    #puts $FO "+ $pin ([get_attribute [get_cells -of $pin] ref_name]): REQ : $myList($pin) (#.fanout [expr $num - 1])"
                    #puts $FO "  +-- Net: [get_object_name $net]"
                }

                set fanin [sort_collection [filter_collection $fanouts "direction == out"] full_name]
                set fanout [sort_collection [filter_collection $fanouts "direction == in"] full_name]
                set inout [sort_collection [filter_collection $fanouts "direction == inout"] full_name]

                set tmp [add_to_collection $fanin $inout]
#                
                set uni 0  ; # port problem(driveless mttv violation fix

                foreach_in_collection itr $tmp {
                      if { [lsearch $driver_list [get_object_name $itr]] < 0 } {
                          set uni 0
                        lappend driver_list [get_object_name $itr]
                        break;
                    } else {
                          set uni 1
                        break;
                    }
                }

                if { $uni == 0 } {
                    puts $FO ""
                      puts $FO "$tmp1"
                    puts $FO "$tmp2"
                    #set tmp1 ""
                    #set tmp2 ""
                    set uni 1

                foreach_in_collection in $fanin {
                    if { [regsub -all {\/} [get_object_name $in] { } tmp] == 0 } {
                        #echo "          +-- [get_object_name $in]    :: (D) - out" >> $out
                        puts $FO "          +-- [get_object_name $in]    :: (D) - out"
                    } else {            
                            #echo "          +-- [get_object_name $in] ([get_attribute [get_cells -of $in] ref_name]) (r)[get_attribute [get_pins $in] actual_rise_transition_max]/(f)[get_attribute [get_pins $in] actual_fall_transition_max] :: (D) - out" >> $out
                            puts $FO "          +-- [get_object_name $in] ([get_attribute [get_cells -of $in] ref_name]) (r)[get_attribute [get_pins $in] actual_rise_transition_max]/(f)[get_attribute [get_pins $in] actual_fall_transition_max] :: (D) - out"
                    }
                }
                    
                foreach_in_collection out $fanout {
                    if { [regsub -all {\/} [get_object_name $out] { } tmp] == 0 } {
                        #echo "          +-- [get_object_name $out] :: (L) - in" >> $out
                        puts $FO "          +-- [get_object_name $out] :: (L) - in"
                    } else {            
                            #echo "          +-- [get_object_name $out] ([get_attribute [get_cells -of $out] ref_name]) (r)[get_attribute [get_pins $out] actual_rise_transition_max]/(f)[get_attribute [get_pins $out] actual_fall_transition_max] :: (L) - in" >> $out
                            puts $FO "          +-- [get_object_name $out] ([get_attribute [get_cells -of $out] ref_name]) (r)[get_attribute [get_pins $out] actual_rise_transition_max]/(f)[get_attribute [get_pins $out] actual_fall_transition_max] :: (L) - in"
                    }
                }

                if { [sizeof_collection $inout] != 0 } {
                    #echo "        +-- inout pins" >> $out
                    puts $FO "        +-- inout pins"

                    foreach_in_collection itr $inout {
                        if { [regsub -all {\/} [get_object_name $inout] { } tmp] == 0 } {
                            #echo "        +-- [get_object_name $itr] :: inout" >> $out
                            puts $FO "        +-- [get_object_name $itr] :: inout"
                        } else {
                            #echo "        +-- [get_object_name $itr] ([get_attribute [get_cells -of $itr] ref_name]) (r)[get_attribute [get_pins $itr] actual_rise_transition_max]/(f)[get_attribute [get_pins $itr] actual_fall_transition_max] :: inout" >> $out
                            puts $FO "        +-- [get_object_name $itr] ([get_attribute [get_cells -of $itr] ref_name]) (r)[get_attribute [get_pins $itr] actual_rise_transition_max]/(f)[get_attribute [get_pins $itr] actual_fall_transition_max] :: inout"
                        }
                    }
                }; #End of $inout if
                }; #End of $uni if
            }
        }

        #echo " " >> $out
        #puts $FO ""
    }

    sh rm viol.tran
    sh rm tmp
    }
    close $FO
}

define_proc_attributes mttv \
    -info "Report MTTV summary like Cubic LDRC report file" \
        -define_args {
                {all_vio_file "report file: report_constraint -all_violators -nosplit -sig 3 " all_viol_file string required}
                {output_file "output file name" output_file string required}
        }

# SCRIPT_PROTECT_BLOCK_END
