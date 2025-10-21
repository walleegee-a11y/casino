#- AOCV Sign-off Criteria for 0.8V Operation
if { [regexp WCG ${op_cond}] } {
    set max_transition_clock 0.44
    set max_transition_data  0.61
} elseif { [regexp BCG ${op_cond}] } {
    set max_transition_clock 0.155
    set max_transition_data  0.24
}
if { [regexp BCG ${op_cond}] || [regexp WCG ${op_cond}] } {
set fp [open ./reports/max_transition_check_${op_cond}.rpt "w"]

puts $fp "### The max.transition at ${op_cond}: clock path ${max_transition_clock}ns, data path ${max_transition_data}ns"

set clk_mttv_violated_pins  [get_pins -q * -hierarchical -filter "actual_transition_max >= $max_transition_clock && (is_clock_pin == true || is_clock_network == true)"]
set data_mttv_violated_pins [get_pins -q * -hierarchical -filter "actual_transition_max >= $max_transition_data  && (is_data_pin == true)"]

puts $fp "## Number of CLK  MTTV : [sizeof ${clk_mttv_violated_pins}]"
puts $fp "## Number of DATA MTTV : [sizeof ${data_mttv_violated_pins}]"

puts $fp "# Pin : Actual_trasition_time:"
puts $fp "# Clock Path"
foreach_in_collection col [get_pins -q * -hierarchical -filter "actual_transition_max >= $max_transition_clock && (is_clock_pin == true || is_clock_network == true)"] {
    set inst_name [get_object_name $col]
    set actual_transition [get_attr $col actual_transition_max]
    if { ![regexp "/PAD " $inst_name] } {
        puts $fp "$inst_name : $actual_transition (VIOLATED / Criteria $max_transition_clock)"
    }
}
puts $fp "# Data Path"
foreach_in_collection col [get_pins -q * -hierarchical -filter "actual_transition_max >= $max_transition_data && (is_data_pin == true)"] {
    set inst_name [get_object_name $col]
    set actual_transition [get_attr $col actual_transition_max]
    if { ![regexp "/PAD " $inst_name] } {
        puts $fp "$inst_name : $actual_transition (VIOLATED / Criteria $max_transition_clock)"
    }
}

close $fp

}
