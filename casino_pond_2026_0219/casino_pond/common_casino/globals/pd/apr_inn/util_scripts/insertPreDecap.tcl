
deselectAll
editSelect -subclass core_stripe -layer M5
set llx_lists [lsort -real [dbGet [dbGet -p2 selected.net.name VSSL].box_llx -u ]  ]

set_well_tap_mode -reset
set_well_tap_mode -rule $preDecapPitch -cell $preDecapCell 

for { set i 1 } { [llength [dbGet [dbGet -p2 selected.net.name VSSL].box_llx -u ]] > $i } { set i [expr $i + 60 ] } {
	if { [expr $i + 60] > [llength [dbGet [dbGet -p2 selected.net.name VDD09_DIG].box_llx -u]] } { set endIndex end 
	} else { set endIndex [expr $i + 60] }
	addWellTap -cell $preDecapCell -cellInterval $preDecapPitch -checkerBoard -area "[expr [lindex $llx_lists [expr $i] ] -2] 0 [lindex $llx_lists $endIndex] [dbGet top.fplan.box_ury]" -fixedGap -prefix PREDECAP

}

set_well_tap_mode -reset
deselectAll 
