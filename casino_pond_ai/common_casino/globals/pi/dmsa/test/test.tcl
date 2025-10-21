set_distributed_variables [list ovars(dmsa,teco,target_groups) ovars(dmsa,teco,except_groups)]
current_scenario [index_collection [current_scenario] 0]

# Determines target path groups based on $ovars(dmsa,teco,target_groups) or all groups if empty.  
# Excludes groups specified in $ovars(dmsa,teco,except_groups) and collects the full names of the remaining groups.
remote_execute {
	if { [sizeof_collection [get_path_groups -q $ovars(dmsa,teco,target_groups)]] } {
		puts "\$target_groups: $ovars(dmsa,teco,target_groups)"
		set col_tg [get_path_groups $ovars(dmsa,teco,target_groups)]

	} else {
		puts "\$target_groups is empty."
		puts "Filling \$target_groups with all path groups."
		set col_tg [get_path_groups *]

	}

	if {$ovars(dmsa,teco,except_groups) != ""} {
		set col_tg [remove_from_collection $col_tg $ovars(dmsa,teco,except_groups)]

	}

	set target_groups ""
	foreach_in_collection ctg $col_tg {
		lappend target_groups [get_attribute $ctg full_name]

	}
}

get_distributed_variables -merge_type list { target_groups }
puts "\$target_groups: $target_groups"

# Defines slack range using lower and upper bounds for the fix_eco_timing command.
#  Usage example:
#  To fix setup timing violations with slack between 0 and -0.2:
#    fix_eco_timing -type setup -slack_lesser_than 0 -slack_greater_than -0.2
#  These options are specific to the `fix_eco_timing` command.
set slack_lesser_than  $ovars(dmsa,teco,slack_lesser_than)
set slack_greater_than $ovars(dmsa,teco,slack_greater_than)

# If no slack range is specified, use default values.
if {($slack_lesser_than == "") && ($slack_greater_than == "")} {
    set slack_lesser_than  "0.00"
    set slack_greater_than "infinity"
	puts "Info: Default slack range applied."
}

current_scenario -all
