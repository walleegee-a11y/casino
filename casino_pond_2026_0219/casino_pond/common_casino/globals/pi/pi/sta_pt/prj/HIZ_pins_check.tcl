set pins "
	DRV/HIZ_A[1]
	DRV/HIZ_A[2]
	DRV/HIZ_A[3]
	DRV/HIZ_A[4]
	DRV/HIZ_A[5]
	DRV/HIZ_A[6]
	DRV/HIZ_A[7]
	DRV/HIZ_A[8]
	DRV/HIZ_A[9]
	DRV/HIZ_A[10]
	DRV/HIZ_A[11]
	DRV/HIZ_A[12]
	DRV/HIZ_A[13]
	DRV/HIZ_A[14]
	DRV/HIZ_A[15]
	DRV/HIZ_A[16]
	DRV/HIZ_A[17]
	DRV/HIZ_A[18]
	DRV/HIZ_A[19]
	DRV/HIZ_A[20]
	DRV/HIZ_A[21]
	DRV/HIZ_A[22]
	DRV/HIZ_A[23]
	DRV/HIZ_A[24]
"

set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "HIZ_A pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] startpoint]]
	lappend all_arrival_delay $arrival_delay
	set max_arrival_delay [lindex [lsort -real -decreasing $all_arrival_delay] 0]
	set min_arrival_delay [lindex [lsort -real $all_arrival_delay] 0]
	if {$arrival_delay >= $max_arrival_delay} {
		set max_pin [get_object_name [get_attr [get_timing_path -delay $max_min -to $EP] endpoint]]
		set max_pin_out (${max_pin})
	}
	if {$arrival_delay <= $min_arrival_delay} {
		set min_pin [get_object_name [get_attr [get_timing_path -delay $max_min -to $EP] endpoint]]
		set min_pin_out (${min_pin})
	}
	puts [format "%-60s | %-14s | %-.3fns" $SP $EP $arrival_delay]
 }
puts [string repeat "-" 93]
set arrival_skew [format "%.3f" [expr $max_arrival_delay - $min_arrival_delay]]
puts "[format "%-s %-16s : %-.3fns " "Max_arrival_delay" $max_pin_out $max_arrival_delay]"
puts "[format "%-s %-16s : %-.3fns " "Min_arrival_delay" $min_pin_out $min_arrival_delay]"
puts "Data skew : ${arrival_skew}ns"
if {$arrival_skew > 0.5} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""

set pins "
	DRV/HIZ_B[1]
	DRV/HIZ_B[2]
	DRV/HIZ_B[3]
	DRV/HIZ_B[4]
	DRV/HIZ_B[5]
	DRV/HIZ_B[6]
	DRV/HIZ_B[7]
	DRV/HIZ_B[8]
	DRV/HIZ_B[9]
	DRV/HIZ_B[10]
	DRV/HIZ_B[11]
	DRV/HIZ_B[12]
	DRV/HIZ_B[13]
	DRV/HIZ_B[14]
	DRV/HIZ_B[15]
	DRV/HIZ_B[16]
	DRV/HIZ_B[17]
	DRV/HIZ_B[18]
	DRV/HIZ_B[19]
	DRV/HIZ_B[20]
	DRV/HIZ_B[21]
	DRV/HIZ_B[22]
	DRV/HIZ_B[23]
	DRV/HIZ_B[24]
"
set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "HIZ_B pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] startpoint]]
	lappend all_arrival_delay $arrival_delay
	set max_arrival_delay [lindex [lsort -real -decreasing $all_arrival_delay] 0]
	set min_arrival_delay [lindex [lsort -real $all_arrival_delay] 0]
	if {$arrival_delay >= $max_arrival_delay} {
		set max_pin [get_object_name [get_attr [get_timing_path -delay $max_min -to $EP] endpoint]]
		set max_pin_out (${max_pin})
	}
	if {$arrival_delay <= $min_arrival_delay} {
		set min_pin [get_object_name [get_attr [get_timing_path -delay $max_min -to $EP] endpoint]]
		set min_pin_out (${min_pin})
	}
	puts [format "%-60s | %-14s | %-.3fns" $SP $EP $arrival_delay]
 }
puts [string repeat "-" 93]
set arrival_skew [format "%.3f" [expr $max_arrival_delay - $min_arrival_delay]]
puts "[format "%-s %-16s : %-.3fns " "Max_arrival_delay" $max_pin_out $max_arrival_delay]"
puts "[format "%-s %-16s : %-.3fns " "Min_arrival_delay" $min_pin_out $min_arrival_delay]"
puts "Data skew : ${arrival_skew}ns"
if {$arrival_skew > 0.5} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""
