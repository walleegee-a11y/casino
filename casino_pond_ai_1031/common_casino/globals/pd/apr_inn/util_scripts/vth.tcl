
proc proc_report_vth fileName {
global stdTrack
set fo [open $fileName w ]

set design_hvt_area [expr [join [get_db [get_db insts -if { .is_physical == false && .base_cell.class == core && .base_cell.name == *HVT }] .area] +]]
set design_rvt_area [expr [join [get_db [get_db insts -if { .is_physical == false && .base_cell.class == core && .base_cell.name == *140 }] .area] +]]
set design_lvt_area [expr [join [get_db [get_db insts -if { .is_physical == false && .base_cell.class == core && .base_cell.name == *LVT }] .area] +]]
set area_pri [expr $design_hvt_area + $design_rvt_area + $design_lvt_area]

set ND2D1_cell ND2D1BWP${stdTrack}35P140

set gc [get_db [get_db base_cells -if { .name == $ND2D1_cell }] .area]

	puts $fo [format "\n#################################################################################"]
	puts $fo [format "### Gate Count ( ND2D1BWP${stdTrack}35P140 / $gc )"] 
	puts $fo [format "#################################################################################"]




	puts $fo [format " Total LOGIC cell G/C        : %s" [expr $area_pri/$gc]]
	puts $fo [format " Total  - HVT cell G/C       : %s" [expr $design_hvt_area/$gc]]
	puts $fo [format " Total  - RVT cell G/C       : %s" [expr $design_rvt_area/$gc]]
	puts $fo [format " Total  - LVT cell G/C       : %s" [expr $design_lvt_area/$gc]]
	puts $fo [format "\n#################################################################################"]
	puts $fo [format " Primitive Vth Ratio (H:R:L) : %3.2f%% : %3.2f%% : %3.2f%%" [expr ($design_hvt_area/$area_pri)*100] [expr ($design_rvt_area/$area_pri)*100] [expr ($design_lvt_area/$area_pri)*100]] 
	puts $fo [format "#################################################################################\n"]

close $fo
}

