proc vth_rpt {} {
    #set NAND_CELL ND2M1NM
    set NAND_CELL ND2M1NMB


	set col_all [get_cells -quiet -hier * -filter "!is_hierarchical"]
	set col_dum [get_cells -quiet -hier * -filter "!is_hierarchical && (ref_name =~ **logic_zero** || ref_name =~ **logic_one**)"]
	set col_mem [get_cells -quiet -hier * -filter "is_memory_cell"]
	set col_ip  [get_cells -quiet -hier * -filter "is_black_box && !is_memory_cell"]
	set col_pad [get_cells -quiet -hier * -filter "is_pad_cell"]
	set col_hvt [get_cells -quiet -hier * -filter "!is_hierarchical && (ref_name =~ *HMA*)"]
	set col_rvt [get_cells -quiet -hier * -filter "!is_hierarchical && (ref_name =~ *NMB*)"]
	set col_lvt [get_cells -quiet -hier * -filter "!is_hierarchical && (ref_name =~ *LMB*)"]
	set col_seq [get_cells -quiet -hier * -filter "!is_hierarchical && is_sequential"]
	set col_pri [get_cells -quiet -hier * -filter "!is_hierarchical && !is_black_box"]

	set num_all [expr [sizeof_collection $col_all] - [sizeof_collection $col_dum]]

	set num_ip  [sizeof_collection $col_ip ]
	set num_mem [sizeof_collection $col_mem]
	set num_pad [sizeof_collection $col_pad]

	set num_hvt [sizeof_collection $col_hvt]
	set num_rvt [sizeof_collection $col_rvt]
	set num_lvt [sizeof_collection $col_lvt]
	set num_seq [sizeof_collection $col_seq]
	set num_pri [expr $num_hvt + $num_rvt + $num_lvt]
	
	set area_all 0
	set area_hvt 0
	set area_rvt 0
	set area_lvt 0
	set area_mem 0
	set area_ip  0
	set area_pad 0
    

	puts [format " Total LOGIC inst      : %s" $num_pri]
	puts [format "  SEQUENTIAL inst      : %s" $num_seq]
	puts [format "         MEM inst      : %s" $num_mem]
	puts [format "          IP inst      : %s" $num_ip]
	puts [format "         PAD inst      : %s" $num_pad]
	puts [format " Total TOP   inst      : %s" $num_all]
	

    foreach_in_collection var $col_all {
		set area_all [expr $area_all + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_hvt {
		set area_hvt [expr $area_hvt + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_rvt {
		set area_rvt [expr $area_rvt + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_lvt {
		set area_lvt [expr $area_lvt + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_mem {
		set area_mem [expr $area_mem + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_ip {
		set area_ip [expr $area_ip + [get_attribute [get_cells $var] area]]
	}
	foreach_in_collection var $col_pad {
		set area_pad [expr $area_pad + [get_attribute [get_cells $var] area]]
	}

	puts [format " Total LOGIC Area      : %s" $area_all]
	puts [format "      - MEM  Area      : %s" $area_mem]
	puts [format "      -  IP  Area      : %s" $area_ip]
	puts [format "      - PAD  Area      : %s" $area_pad]
	puts [format " Total       Area      : %s" [expr $area_all + $area_mem + $area_ip + $area_pad]]

	set gc [get_attribute [get_lib_cells */$NAND_CELL] area]
	set area_pri [expr $area_hvt + $area_rvt + $area_lvt]
	

	puts [format " Total LOGIC G/C       : %s" [expr $area_pri/$gc]]
	puts [format "       - MEM G/C       : %s" [expr $area_mem/$gc]]
	puts [format "       -  IP G/C       : %s" [expr $area_ip/$gc]]
	puts [format "       - PAD G/C       : %s" [expr $area_pad/$gc]]
	puts [format " Total - TOP G/C       : %s" [expr $area_all/$gc]]
	
	puts ""
	puts ""
	puts [format " Vth G/C & Ratio"]
	puts [format " HVT cell G/C          : %s" [expr $area_hvt/$gc]]
	puts [format " RVT cell G/C          : %s" [expr $area_rvt/$gc]]
	puts [format " LVT cell G/C          : %s" [expr $area_lvt/$gc]]
	puts [format " Vth Ratio(H:R:L)      : %3.2f%% : %3.2f%% : %3.2f%%" [expr ($area_hvt/$area_pri)*100] [expr ($area_rvt/$area_pri)*100] [expr ($area_lvt/$area_pri)*100]] 

}
