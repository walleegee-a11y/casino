# Get all cells matching the pattern
#set all_cells [get_lib_cells tcbn12ffcllbwp6t*/*]
set all_cells [get_lib_cells u022lschv08bdhg*/*]

# Iterate over each cell
foreach_in_collection cell $all_cells {
    set lib_cell_name [get_attr $cell full_name]
    
    # Get the number of input pins
    set num_of_input_pins [sizeof_collection [get_lib_pins -of $cell -filter "direction==in"]]
    
    # Print the cell name and the number of input pins
    puts "Cell: $lib_cell_name"
    puts "Number of input pins: $num_of_input_pins"
    
    # If the cell has 5 or more input pins, set it to dont_use
    if { $num_of_input_pins >= 5 } {
        puts "Setting dont_use for cell: $lib_cell_name with $num_of_input_pins input pins"
        set_dont_use $lib_cell_name
    }
}
