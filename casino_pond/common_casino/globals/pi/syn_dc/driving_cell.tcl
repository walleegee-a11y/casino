# -----------------------------------------------------------------------------
# driving_cell (user block)
# -----------------------------------------------------------------------------
set driving_cell_type      "BUFM4NMB"
set clk_driving_cell_type  "BUFM4NMB" ;#TODO: need2update

#eval set driving_ports $driving_ports
foreach each_source [get_object_name [get_attribute [get_clocks] sources]] {
	if {![string match "*/*" $each_source]} { lappend ports_sources $each_source }

}

set clock_driving_ports [get_ports $ports_sources]
set driving_ports [remove_from_collection [all_inputs] [get_ports $ports_sources]]

regexp {.*/([A-Z]+)} [get_object_name [filter_collection [get_lib_pin -of [lindex [get_object_name [get_lib_cell */$driving_cell_type]] 0]] "direction == in"]] - driving_from_pin
regexp {.*/([A-Z]+)} [get_object_name [filter_collection [get_lib_pin -of [lindex [get_object_name [get_lib_cell */$clk_driving_cell_type]] 0]] "direction == in"]] - clock_driving_from_pin

regexp {.*/([A-Z]+)} [get_object_name [filter_collection [get_lib_pin -of [lindex [get_object_name [get_lib_cell */$driving_cell_type]] 0]] "direction == out"]] - driving_pin
regexp {.*/([A-Z]+)} [get_object_name [filter_collection [get_lib_pin -of [lindex [get_object_name [get_lib_cell */$clk_driving_cell_type]] 0]] "direction == out"]] - clock_driving_pin

puts "driving_from_pin       : $driving_from_pin"
puts "clock_driving_from_pin : $clock_driving_from_pin"
puts "driving_pin            : $driving_pin"
puts "clock_driving_pin      : $clock_driving_pin"

if { $driving_ports != "" } {
	# Drive input ports with a standard driving cell and input transition
	set_driving_cell -from_pin ${driving_from_pin} \
					 -lib_cell ${driving_cell_type} \
					 -pin ${driving_pin} \
						  ${driving_ports}
} 

if { $clock_driving_ports != "" } {
	# Drive clock input ports with a different driving cell and input transition
	set_driving_cell -from_pin ${clock_driving_from_pin} \
					 -lib_cell ${clk_driving_cell_type} \
					 -pin ${clock_driving_pin} \
						  ${clock_driving_ports}
}
