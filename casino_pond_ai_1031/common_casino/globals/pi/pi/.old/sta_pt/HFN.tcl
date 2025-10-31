set_app_var auto_wire_load_selection false
set hfn_threshold  $max_fanout

set ideal_net_delay  0.0
set ideal_cell_delay 0.0
set ideal_transition 0.0

set ALL_NETS [get_nets -hier * -top_net]

foreach_in_collection net $ALL_NETS {
  set net_pins [all_connected $net -leaf]
  if {[sizeof $net_pins] < $hfn_threshold } {
    continue;
  }
  set net_name [get_attribute -quiet $net full_name]
  if { [string match "*/\*Logic1\*" $net_name] || [string match "*/\*Logic0\*" $net_name]} {
    continue
  }
  foreach_in_collection pin $net_pins {
    set dir [get_attribute -quiet $pin direction]
    if {$dir == "out"} {
      set net_name [get_attribute -quiet $net full_name]
      set pin_name [get_attribute -quiet $pin full_name]
      echo "## high fanout net: $net_name ([sizeof $net_pins])"
      echo "  set_annotated_delay -net $ideal_net_delay -from \[get_pins $pin_name\]"
      echo "  set_annotated_delay -cell $ideal_cell_delay -to \[get_pins $pin_name\]"
      echo "  set_annotated_transition $ideal_transition \[get_pins $pin_name\]"
      echo ""
      set_annotated_delay -net $ideal_net_delay -from $pin
      set_annotated_delay -cell $ideal_cell_delay -to $pin
      set_annotated_transition $ideal_transition $pin
    }
  }
}

set high_fanout_threshold ${max_fanout}

set fpOut [open "high_fanout.list" "w"]
foreach_in_collection net [get_nets -hier * ] {
  set net_fanout_pins [get_pins -quiet -leaf -of $net -filter "direction != out"]
  if { [sizeof $net_fanout_pins] > $high_fanout_threshold } {
    puts $fpOut [get_object_name $net]
  }
}
close $fpOut
source ${PT_COMMON_SCRIPT}/anno_prelayout_zero_delay.tcl
anno_prelayout_zero_delay ./high_fanout.list
