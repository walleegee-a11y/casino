set pins "
	DRV/LTPS_A[1]
	DRV/LTPS_A[2]
	DRV/LTPS_A[3]
	DRV/LTPS_A[4]
	DRV/LTPS_A[5]
	DRV/LTPS_A[6]
	DRV/LTPS_A[7]
	DRV/LTPS_A[8]
	DRV/LTPS_A[9]
	DRV/LTPS_A[10]
	DRV/LTPS_A[11]
	DRV/LTPS_A[12]
	DRV/LTPS_A[13]
	DRV/LTPS_A[14]
	DRV/LTPS_A[15]
	DRV/LTPS_A[16]
	DRV/LTPS_A[17]
	DRV/LTPS_A[18]
	DRV/LTPS_A[19]
	DRV/LTPS_A[20]
	DRV/LTPS_A[21]
	DRV/LTPS_A[22]
	DRV/LTPS_A[23]
	DRV/LTPS_A[24]
"

set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "LTPS_A pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] arrival]
	set SP            [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {oclk}] -to $EP] startpoint]]
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
	DRV/LTPS_B[1]
	DRV/LTPS_B[2]
	DRV/LTPS_B[3]
	DRV/LTPS_B[4]
	DRV/LTPS_B[5]
	DRV/LTPS_B[6]
	DRV/LTPS_B[7]
	DRV/LTPS_B[8]
	DRV/LTPS_B[9]
	DRV/LTPS_B[10]
	DRV/LTPS_B[11]
	DRV/LTPS_B[12]
	DRV/LTPS_B[13]
	DRV/LTPS_B[14]
	DRV/LTPS_B[15]
	DRV/LTPS_B[16]
	DRV/LTPS_B[17]
	DRV/LTPS_B[18]
	DRV/LTPS_B[19]
	DRV/LTPS_B[20]
	DRV/LTPS_B[21]
	DRV/LTPS_B[22]
	DRV/LTPS_B[23]
	DRV/LTPS_B[24]
"
set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "LTPS_B pins Data arrival delay"
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
