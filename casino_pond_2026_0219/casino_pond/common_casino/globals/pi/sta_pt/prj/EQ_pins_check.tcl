#DRV/EQ_A[*]
set pins "
	DRV/EQ_A[1]
	DRV/EQ_A[2]
	DRV/EQ_A[3]
	DRV/EQ_A[4]
	DRV/EQ_A[5]
	DRV/EQ_A[6]
	DRV/EQ_A[7]
	DRV/EQ_A[8]
	DRV/EQ_A[9]
	DRV/EQ_A[10]
	DRV/EQ_A[11]
	DRV/EQ_A[12]
	DRV/EQ_A[13]
	DRV/EQ_A[14]
	DRV/EQ_A[15]
	DRV/EQ_A[16]
	DRV/EQ_A[17]
	DRV/EQ_A[18]
	DRV/EQ_A[19]
	DRV/EQ_A[20]
	DRV/EQ_A[21]
	DRV/EQ_A[22]
	DRV/EQ_A[23]
	DRV/EQ_A[24]
"

set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "EQ_A pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] startpoint]]
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
if {$arrival_skew > 1.0} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""

#DRV/EQ_B[*]
set pins "
	DRV/EQ_B[1]
	DRV/EQ_B[2]
	DRV/EQ_B[3]
	DRV/EQ_B[4]
	DRV/EQ_B[5]
	DRV/EQ_B[6]
	DRV/EQ_B[7]
	DRV/EQ_B[8]
	DRV/EQ_B[9]
	DRV/EQ_B[10]
	DRV/EQ_B[11]
	DRV/EQ_B[12]
	DRV/EQ_B[13]
	DRV/EQ_B[14]
	DRV/EQ_B[15]
	DRV/EQ_B[16]
	DRV/EQ_B[17]
	DRV/EQ_B[18]
	DRV/EQ_B[19]
	DRV/EQ_B[20]
	DRV/EQ_B[21]
	DRV/EQ_B[22]
	DRV/EQ_B[23]
	DRV/EQ_B[24]
"
set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "EQ_B pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] startpoint]]
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
if {$arrival_skew > 1.0} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""

#DRV/XEQ_A[*]
set pins "
	DRV/XEQ_A[1]
	DRV/XEQ_A[2]
	DRV/XEQ_A[3]
	DRV/XEQ_A[4]
	DRV/XEQ_A[5]
	DRV/XEQ_A[6]
	DRV/XEQ_A[7]
	DRV/XEQ_A[8]
	DRV/XEQ_A[9]
	DRV/XEQ_A[10]
	DRV/XEQ_A[11]
	DRV/XEQ_A[12]
	DRV/XEQ_A[13]
	DRV/XEQ_A[14]
	DRV/XEQ_A[15]
	DRV/XEQ_A[16]
	DRV/XEQ_A[17]
	DRV/XEQ_A[18]
	DRV/XEQ_A[19]
	DRV/XEQ_A[20]
	DRV/XEQ_A[21]
	DRV/XEQ_A[22]
	DRV/XEQ_A[23]
	DRV/XEQ_A[24]
"
set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "EQ_B pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] startpoint]]
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
if {$arrival_skew > 1.0} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""

#DRV/XEQ_B[*]
set pins "
	DRV/XEQ_B[1]
	DRV/XEQ_B[2]
	DRV/XEQ_B[3]
	DRV/XEQ_B[4]
	DRV/XEQ_B[5]
	DRV/XEQ_B[6]
	DRV/XEQ_B[7]
	DRV/XEQ_B[8]
	DRV/XEQ_B[9]
	DRV/XEQ_B[10]
	DRV/XEQ_B[11]
	DRV/XEQ_B[12]
	DRV/XEQ_B[13]
	DRV/XEQ_B[14]
	DRV/XEQ_B[15]
	DRV/XEQ_B[16]
	DRV/XEQ_B[17]
	DRV/XEQ_B[18]
	DRV/XEQ_B[19]
	DRV/XEQ_B[20]
	DRV/XEQ_B[21]
	DRV/XEQ_B[22]
	DRV/XEQ_B[23]
	DRV/XEQ_B[24]
"
set all_arrival_delay ""
set max_arrival_delay ""
set min_arrival_delay ""

puts [string repeat "-" 93]
puts "EQ_B pins Data arrival delay"
puts [string repeat "-" 93]
puts "[format "%-s %-54s | %-s %-10s | %-s" "Start" "point" "End" "point" "Delay"]"
puts [string repeat "-" 93]

foreach EP $pins {
	set arrival_delay [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] arrival]
	set SP [get_object_name [get_attr [get_timing_path -delay $max_min -from [get_clocks {iclk}] -to $EP] startpoint]]
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
if {$arrival_skew > 1.0} {
	puts "Result    : FAIL"
} else {
	puts "Result    : PASS"
}
puts [string repeat "-" 93]
puts ""
puts ""
