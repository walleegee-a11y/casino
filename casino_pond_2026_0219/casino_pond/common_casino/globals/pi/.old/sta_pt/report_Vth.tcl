proc vth_rpt {} {
	set design_all [get_cells -quiet -hier * -filter "is_hierarchical == false"]
	set design_dum [get_cells -quiet -hier * -filter "is_hierarchical == false && (ref_name =~ **logic_zero** || ref_name =~ **logic_one**)"]
	set design_hvt [get_cells -quiet -hier * -filter "is_hierarchical == false && (ref_name =~ *HM*)"]
	set design_rvt [get_cells -quiet -hier * -filter "is_hierarchical == false && (ref_name =~ *NM*)"]
	set design_lvt [get_cells -quiet -hier * -filter "is_hierarchical == false && (ref_name =~ *LM*)"]
	set design_seq [get_cells -quiet -hier * -filter "is_hierarchical == false && is_sequential == true"]
	set total_all  [expr [sizeof_collection $design_all] - [sizeof_collection $design_dum]]
	
	set total_hvt [sizeof_collection $design_hvt]
	set total_rvt [sizeof_collection $design_rvt]
	set total_lvt [sizeof_collection $design_lvt]
	set total_seq [sizeof_collection $design_seq]
	set total_pri [expr $total_hvt + $total_rvt + $total_lvt]
	
	puts [format "##################################################"]
	puts [format "### Instance Number"]
	puts [format "##################################################"]
	puts [format " Total LOGIC cell inst  #    : %s" $total_pri]
	puts [format "        - HVT cell inst #    : %s" $total_hvt]
	puts [format "        - RVT cell inst #    : %s" $total_rvt]
	puts [format "        - LVT cell inst #    : %s" $total_lvt]
	puts [format "       SEQUENTIAL cell  #    : %s" $total_seq]
	puts [format "##################################################"]
	puts [format " Total TOP cell inst    #    : %s" $total_all]
	puts [format "##################################################"]
	puts ""
	
	set design_all_area 0
	set design_hvt_area 0
	set design_rvt_area 0
	set design_lvt_area 0
    
    foreach_in_collection var $design_all {
    set design_all_area [expr $design_all_area + [get_attribute [get_cells $var] area]]
    }
	foreach_in_collection var $design_hvt {
	set design_hvt_area [expr $design_hvt_area + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $design_rvt {
	set design_rvt_area [expr $design_rvt_area + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $design_lvt {
	set design_lvt_area [expr $design_lvt_area + [get_attribute [get_cells $var] area]]
	}

	puts [format "##################################################"]
	puts [format "### Total Area"]
	puts [format "##################################################"]
	puts [format " Total    cell Area        : %s" $design_all_area]
	puts [format " Total  - HVT cell Area       : %s" $design_hvt_area]
	puts [format " Total  - RVT cell Area       : %s" $design_rvt_area]
	puts [format " Total  - LVT cell Area       : %s" $design_lvt_area]
	puts [format "##################################################"]
	puts ""

    #set NAND_CELL ND2M1NM
    set NAND_CELL ND2M1NMB
	set gc [get_attribute [get_lib_cells */$NAND_CELL] area]
	set area_pri [expr $design_hvt_area + $design_rvt_area + $design_lvt_area]
	
	puts [format "##################################################"]
	puts [format "### Gate Count ( $NAND_CELL / $gc )"]
	puts [format "##################################################"]
	puts [format " Total LOGIC cell G/C        : %s" [expr $area_pri/$gc]]
	puts [format " Total  - HVT cell G/C       : %s" [expr $design_hvt_area/$gc]]
	puts [format " Total  - RVT cell G/C       : %s" [expr $design_rvt_area/$gc]]
	puts [format " Total  - LVT cell G/C       : %s" [expr $design_lvt_area/$gc]]
	puts [format "##################################################"]
	puts [format " Total TOP cell G/C          : %s" [expr $design_all_area/$gc]]
	puts [format "##################################################"]
	puts [format " Primitive Vth Ratio (H:R:L) : %3.2f%%:%3.2f%%:%3.2f%%" [expr ($design_hvt_area/$area_pri)*100] [expr ($design_rvt_area/$area_pri)*100] [expr ($design_lvt_area/$area_pri)*100]] 
	puts [format "##################################################"]
}
