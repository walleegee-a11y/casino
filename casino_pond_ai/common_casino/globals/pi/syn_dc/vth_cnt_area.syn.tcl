# vth_cnt_area.syn.tcl: 230829 ver
##################################################################################################################################################
# ${CELL_LIST}: STD ref_name in ${target_library}
##################################################################################################################################################

#block info ex) set block_info(hier.X330_TOP)                      "AIXV_cluster AIXV_lfcvt_wrapper codec_top cpu_cluster pcie_top GDDR6CLUSTER"
#block info ex) set block_info(hier.AIXV_cluster)                  "AIXV_MXC_lvd AIXV_CORE_ucx AIXV_CORE_lcx"
#block info ex) set block_info(hier.AIXV_lfcvt_wrapper)            ""
#block info ex) set block_info(hier.cpu_cluster)                   ""
#block info ex) set block_info(hier.pcie_top)                      ""
#block info ex) set block_info(hier.GDDR6CLUSTER)                  ""
#block info ex) set block_info(hier.codec_top)                     "wave517_msvc coda980_msvc"
#block info ex) set block_info(hier.wave517_msvc)                  ""
#block info ex) set block_info(hier.coda980_msvc)                  ""
#block info ex) set block_info(hier.AIXV_CORE_ucx)                 ""
#block info ex) set block_info(hier.AIXV_CORE_lcx)                 "AIXV_LTC_tile AIXV_NVP_coretile"
#block info ex) set block_info(hier.AIXV_LTC_tile)                 ""
#block info ex) set block_info(hier.AIXV_NVP_coretile)             ""
#block info ex) set block_info(hier.AIXV_MXC_lvd)                  "AIXV_MXC_pslice"
#block info ex) set block_info(hier.AIXV_MXC_pslice)               ""

# Made on 22 / 05 / 31
set cur_dir [pwd]
set WRITE_AREA_REPORT "${top_design}_vth_cnt_area.rpt"

if { [file exists ${WRITE_AREA_REPORT} ] } {
	exec mv ${WRITE_AREA_REPORT} ${WRITE_AREA_REPORT}.old
}
##################################################################################################################################################
##################################################################################################################################################

if { [ info exist lib_list] == 1 } {
	unset lib_list
}

echo $target_library
foreach itr $target_library {
	# Use regsub to extract the database name
	regsub {^.*/([^/]+)_hm.*\.db$} $itr {\1} db_name
	puts "Database Name: ${db_name}_ccs"

	lappend lib_list "${db_name}_ccs"
}

echo ""
echo " ###############"

foreach each_primitive ${lib_list} {
	puts " #  LIB  used  # > ${each_primitive} "
}

##################################################################################################################################################
##################################################################################################################################################

### Variable Declaration
set TOTAL_INST_COUNT 0
set STD_INST_COUNT 0
set MEM_INST_COUNT 0
set IP_INST_COUNT 0
set IO_INST_COUNT 0
set DB_INST_COUNT 0

set TOTAL_AREA 0
set STD_AREA 0
set MEM_AREA 0
set IP_AREA 0
set IO_AREA 0

set TOTAL_GATE_COUNT 0
set STD_GATE_COUNT 0
set MEM_GATE_COUNT 0
set IP_GATE_COUNT 0
set IO_GATE_COUNT 0

#set std_list ""
set mem_list ""
set io_list ""
set ip_list ""
set db_list ""

set cell_FLOAT_LIST ""

##################################################################################################################################################
##################################################################################################################################################

set CELL_LIST ""

foreach each_lib ${lib_list} {

	set full_lib_list [ get_object_name [get_lib_cells ${each_lib}/*] ]
	
	foreach lib_each $full_lib_list {
		regsub {.*/} $lib_each "" lib_each
		lappend CELL_LIST $lib_each
	}

}

set CELL_LIST [lsort -uniq $CELL_LIST]
### TEST
###set CELL_LIST "ND2D1BWP20P90CPDULVT ND2D1BWP16P90CPDULVT ND2D1BWP20P90CPDLVT ND2D1BWP20P90CPD ND2D1BWP16P90CPDLVT ND2D1BWP16P90CPD"

##################################################################################################################################################
### Calculate Area of IP Cells
##################################################################################################################################################

### Memory Cells
###  (Related Memory Cell Attribute Does Not Set @DC, only is_macro_cell)
set MEM_CELLS     [get_cells -quiet -hierarchical -filter "ref_name =~ ${env(syn_dc_mem_ref_name)}"]
if { [lsort -uniq [get_attri ${MEM_CELLS} ref_name]] != ""} {
	set used_mem_type [lsort -uniq [get_attri ${MEM_CELLS} ref_name]]
} else {
	set used_mem_type "N/A"
}

### IO Cells
set IO_CELLS     [get_cells -quiet -hierarchical -filter "is_pad_cell == true"]
if { [lsort -uniq [get_attri ${IO_CELLS} ref_name]] != ""} {
	set used_io_type [lsort -uniq [get_attri ${IO_CELLS} ref_name]]
} else {
	set used_io_type "N/A"
}

### Macro Cells
###  (neither Memory nor IO)
set MACRO_CELLS     [get_cells -quiet -hierarchical -filter "is_macro_cell==true && ref_name !~ ${env(syn_dc_mem_ref_name)} && pad_cell == false"]
if { [lsort -uniq [get_attri ${MACRO_CELLS} ref_name]] != ""} {
	set used_macro_type [lsort -uniq [get_attri ${MACRO_CELLS} ref_name]]
} else {
	set used_macro_type "N/A"
}

### IP Instance Count
set MEM_INST_COUNT [sizeof $MEM_CELLS]
set  IO_INST_COUNT [sizeof $IO_CELLS]
set  IP_INST_COUNT [sizeof $MACRO_CELLS]

### IP Area Count
foreach_in_collection each_cell $MEM_CELLS {
	set MEM_AREA [ expr $MEM_AREA + [get_attribute [get_cells -quiet $each_cell] area] ]
}	

foreach_in_collection each_cell $IO_CELLS {
	set IO_AREA [ expr $IO_AREA + [get_attribute [get_cells -quiet $each_cell] area] ]
}	

foreach_in_collection each_cell $MACRO_CELLS {
	set IP_INST_COUNT [ expr $IP_INST_COUNT + [get_attribute [get_cells -quiet $each_cell] area] ]
}	

##################################################################################################################################################
##################################################################################################################################################

######  -  INFORM  - #######
##  HDB : SYNS STD CELL   ##
##  HDP : SYNS LVL CELL   ##
##  BWP : TSMC STD CELL   ##
##  HSB & HSP : for pcie  ##
############################
	
echo " # --- --- --- #"
echo " # --- ing --- #"
echo " # ---  |  --- #"
echo " # ---  v  --- #"

set hier_instance ""
set made_filter ""

# - To remove hyper model instance and make "made_filter" var
### TODO: need2chk @DC
if { ( $block_info(hier.$top_design) != "" ) && ( $pre_post == "POST" ) } {
	foreach each_block $block_info(hier.$top_design) {
	
		set hier_instance "[ get_object_name [get_cells -h * -filter "ref_name =~ $each_block"] ]"
		#puts "##- info : hier_instance   :   $hier_instance"   ;# for debug
		foreach each_instance $hier_instance {
			set made_filter "&& full_name !~ $each_instance/* $made_filter"
			#puts "##- info : made_filter  :  $made_filter"  ;# for debug
		}
	}
} else {
	set made_filter ""
}

##################################################################################################################################################
##################################################################################################################################################

# 230620 seonholee For STD_TYPE if condition 
#redirect -variable list_lib_temp { list_lib }
echo "######################################################################################################"	
echo "STD_LIB_LIST"
#foreach each_lib $list_lib_temp {
foreach each_lib ${lib_list} {
#	if { [regexp {[ ]+([^ ])[ ].*/STD/.*} $each_lib - lib] } {
		lappend STD_LIB_LIST $each_lib
		echo "$each_lib"
#	}		
}
echo "######################################################################################################"
set total_ref_cell_count [llength $CELL_LIST]
set checked_ref_cell_count 1

### foreach STD ref_name in ${target_library} Declare as ${CELL_LIST}
### TODO: Consider How to Reduce Runtime by Modifing Script Structure (get_cells -hier *)
foreach CELL $CELL_LIST {

	set cell_FOUND		   [get_cells -quiet -h * -filter "ref_name =~ $CELL $made_filter "]

	# - Add float checking script
	### TODO: Need to Check @DC
	foreach_in_collection cell_EACH $cell_FOUND {
		set cell_PINS [get_pins -quiet -of_objects [get_cells $cell_EACH] -filter "direction==in"]

		foreach_in_collection each_pin $cell_PINS {

			set float_con_net   [get_nets -quiet -of_objects $each_pin]
			if { $float_con_net == "" } {
				set case_val    [get_attribute -quiet [get_pins -quiet $each_pin] case_value]
				if { $case_val != "0" && $case_val != "1" } {
					set cell_FLOAT_EACH [get_object_name $cell_EACH]
  		      		lappend cell_FLOAT_LIST $cell_FLOAT_EACH
				 
				    set cell_FLOAT_data($cell_FLOAT_EACH.pin) [get_object_name $each_pin] 
				    set cell_FLOAT_data($cell_FLOAT_EACH.ref) $CELL 
  				}
			} else {
				set float_check [sizeof_collection [filter_collection [all_connected [get_nets -quiet -of_objects $each_pin] -leaf ] "direction == out"]]

				if {$float_check < "1" } {

					set value_port [sizeof_collection [get_ports -quiet -of_objects [get_nets -quiet -of_objects [get_pins -quiet $each_pin] -top_net_of_hierarchical_group -segments]]]
					
					if { $value_port == "0" } {

						set case_val    [get_attribute -quiet [get_pins -quiet $each_pin] case_value]
						
						if { $case_val != "0" && $case_val != "1" } {
 
							set cell_FLOAT_EACH [get_object_name $cell_EACH]
  		      				lappend cell_FLOAT_LIST $cell_FLOAT_EACH
				 
				    		set cell_FLOAT_data($cell_FLOAT_EACH.pin) [get_object_name $each_pin] 
				    		set cell_FLOAT_data($cell_FLOAT_EACH.ref) $CELL 
						}
					}
				}
			}
		}
	}

	set cell_COUNT($CELL)  [sizeof_collection $cell_FOUND]
	if { $cell_COUNT($CELL) == "0"} {
		#230620 seonholee
		echo "check process : $checked_ref_cell_count / $total_ref_cell_count ( checked_ref_cell_count / total_ref_cell_count )"
		incr checked_ref_cell_count
		continue
	} 
	set cell_only_one	   [lindex [get_object_name $cell_FOUND] 0]

	### Sum Area of ${cell_FOUND}
	set foreach_area_COUNT 0
	foreach_in_collection area_each_cell $cell_FOUND  {
		set foreach_area_COUNT [ expr $foreach_area_COUNT + [get_attribute [get_cells -quiet $area_each_cell] area] ]
	}	

	# mod 230424 taeblue
	if { [ lsearch $block_info(hier.$top_design) $CELL ] != -1 } {
					## - Hier Block db CELL
					### TODO: need2chk
					set DB_INST_COUNT [expr $DB_INST_COUNT + $cell_COUNT($CELL) ]
					lappend db_list $CELL
# 230620 seonholee
#	 elseif {  ( [string match "HDB*" $CELL] ) || ( [string match "HDP*" $CELL] ) || ( [string match "*D*BWP*PD*" $CELL] ) || ( [string match "HSB*" $CELL] ) || ( [string match "HSP*" $CELL] )  } {}
	} elseif { [regexp [get_object_name [get_lib -of [get_lib_cell */$CELL]]] $STD_LIB_LIST] } {
	 				## - STD cell
	 				set STD_INST_COUNT  [expr $STD_INST_COUNT + $cell_COUNT($CELL) ]
	 				set STD_AREA 		 [expr $STD_AREA + $foreach_area_COUNT ]
	} else {

	}
#230620 seonholee
echo "check process : $checked_ref_cell_count / $total_ref_cell_count ( checked_ref_cell_count / total_ref_cell_count )"
incr checked_ref_cell_count 

}

	##################################################################################################################################################
	# - Write report
	##################################################################################################################################################
	echo ""                                            >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|             Instance Count            |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}

	set TOTAL_INST_COUNT             [ expr $STD_INST_COUNT + $MEM_INST_COUNT + $IP_INST_COUNT + $IO_INST_COUNT ]

	echo " > -   STD INSTANCE COUNT  : $STD_INST_COUNT"   >> ${WRITE_AREA_REPORT}
	echo " > -   MEM INSTANCE COUNT  : $MEM_INST_COUNT"   >> ${WRITE_AREA_REPORT}
	echo " > -    IP INSTANCE COUNT  : $IP_INST_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > -    IO INSTANCE COUNT  : $IO_INST_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > - TOTAL INSTANCE COUNT  : $TOTAL_INST_COUNT" >> ${WRITE_AREA_REPORT}
	echo ""                                             >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|        Vth Instance Count/Rate        |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}

	set RVT_CELLS  [get_cells -quiet -hierarchical -filter "ref_name =~ *CPD"]
	set LVT_CELLS  [get_cells -quiet -hierarchical -filter "ref_name =~ *CPDLVT"]
	set ULVT_CELLS [get_cells -quiet -hierarchical -filter "ref_name =~ *CPDULVT"]
	
	set RVT_INST_COUNT   0
	set LVT_INST_COUNT   0
	set ULVT_INST_COUNT  0
	set LOGIC_INST_COUNT 0
	
	set RVT_INST_COUNT    [sizeof $RVT_CELLS]
	set LVT_INST_COUNT    [sizeof $LVT_CELLS]
	set ULVT_INST_COUNT   [sizeof $ULVT_CELLS]
	set LOGIC_INST_COUNT  [expr $RVT_INST_COUNT + $LVT_INST_COUNT + $ULVT_INST_COUNT]

	set RVT_INST_COUNT_RATE   [expr ${RVT_INST_COUNT}  / $LOGIC_INST_COUNT * 100]
	set LVT_INST_COUNT_RATE   [expr ${LVT_INST_COUNT}  / $LOGIC_INST_COUNT * 100]
	set ULVT_INST_COUNT_RATE  [expr ${ULVT_INST_COUNT} / $LOGIC_INST_COUNT * 100]


	echo " > -   RVT INSTANCE COUNT  : $RVT_INST_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > -   LVT INSTANCE COUNT  : $LVT_INST_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > -  ULVT INSTANCE COUNT  : $ULVT_INST_COUNT"   >> ${WRITE_AREA_REPORT}
	echo " > - LOGIC INSTANCE COUNT  : $LOGIC_INST_COUNT"  >> ${WRITE_AREA_REPORT}
	echo ""                                                >> ${WRITE_AREA_REPORT}

	echo " > -   RVT INSTANCE RATE   : [ format %.2f ${RVT_INST_COUNT_RATE} ]%"  >> ${WRITE_AREA_REPORT}
	echo " > -   LVT INSTANCE RATE   : [ format %.2f ${LVT_INST_COUNT_RATE} ]%"  >> ${WRITE_AREA_REPORT}
	echo " > -  ULVT INSTANCE RATE   : [ format %.2f ${ULVT_INST_COUNT_RATE} ]%" >> ${WRITE_AREA_REPORT}
	echo ""                                                                      >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|               Area Count              |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}

	set TOTAL_AREA  [ expr $STD_AREA + $MEM_AREA + $IP_AREA + $IO_AREA ]

	echo " > -   STD AREA           : $STD_AREA"   >> ${WRITE_AREA_REPORT}
	echo " > -   MEM AREA           : $MEM_AREA"   >> ${WRITE_AREA_REPORT}
	echo " > -    IP AREA           : $IP_AREA"    >> ${WRITE_AREA_REPORT}
	echo " > -    IO AREA           : $IO_AREA"    >> ${WRITE_AREA_REPORT}
	echo " > - TOTAL AREA           : $TOTAL_AREA" >> ${WRITE_AREA_REPORT}
	echo ""                                        >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|          Vth Area Count/Rate          |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}

	set RVT_AREA   0
	set LVT_AREA   0
	set ULVT_AREA  0
	set LOGIC_AREA 0
	
	foreach_in_collection rvt $RVT_CELLS {
		set RVT_AREA [expr $RVT_AREA + [get_attribute $rvt area]]
	}
	
	foreach_in_collection lvt $LVT_CELLS {
		set LVT_AREA [expr $LVT_AREA + [get_attribute $lvt area]]
	}
	
	foreach_in_collection ulvt $ULVT_CELLS {
		set ULVT_AREA [expr $ULVT_AREA + [get_attribute $ulvt area]]
	}

	set LOGIC_AREA      [ expr $RVT_AREA + $LVT_AREA + $ULVT_AREA ]

	set RVT_AREA_RATE   [expr ${RVT_AREA}  / $LOGIC_AREA * 100]
	set LVT_AREA_RATE   [expr ${LVT_AREA}  / $LOGIC_AREA * 100]
	set ULVT_AREA_RATE  [expr ${ULVT_AREA} / $LOGIC_AREA * 100]
	

	echo " > -   RVT AREA           : $RVT_AREA"    >> ${WRITE_AREA_REPORT}
	echo " > -   LVT AREA           : $LVT_AREA"    >> ${WRITE_AREA_REPORT}
	echo " > -  ULVT AREA           : $ULVT_AREA"   >> ${WRITE_AREA_REPORT}
	echo " > - LOGIC AREA           : $LOGIC_AREA"  >> ${WRITE_AREA_REPORT}
	echo ""                                         >> ${WRITE_AREA_REPORT}
	
	echo " > -   RVT AREA RATE      : [ format %.2f ${RVT_AREA_RATE} ]%"  >> ${WRITE_AREA_REPORT}
	echo " > -   LVT AREA RATE      : [ format %.2f ${LVT_AREA_RATE} ]%"  >> ${WRITE_AREA_REPORT}
	echo " > -  ULVT AREA RATE      : [ format %.2f ${ULVT_AREA_RATE} ]%" >> ${WRITE_AREA_REPORT}
	echo ""                                                               >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|               Gate Count              |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}
	
	set STD_GATE_COUNT      		[ expr  $STD_AREA / ${env(pi_nd2_area)} ] 
    set MEM_GATE_COUNT      		[ expr  $MEM_AREA / ${env(pi_nd2_area)} ] 
    set IP_GATE_COUNT       		[ expr  $IP_AREA  / ${env(pi_nd2_area)} ] 
	set IO_GATE_COUNT       		[ expr  $IO_AREA  / ${env(pi_nd2_area)} ] 
	
	set TOTAL_GATE_COUNT     		[ expr $STD_GATE_COUNT + $MEM_GATE_COUNT + $IP_GATE_COUNT + $IO_GATE_COUNT ]

	echo " > -   STD GATE COUNT     : $STD_GATE_COUNT"   >> ${WRITE_AREA_REPORT}
	echo " > -   MEM GATE COUNT     : $MEM_GATE_COUNT"   >> ${WRITE_AREA_REPORT}
	echo " > -    IP GATE COUNT     : $IP_GATE_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > -    IO GATE COUNT     : $IO_GATE_COUNT"    >> ${WRITE_AREA_REPORT}
	echo " > - TOTAL GATE COUNT     : $TOTAL_GATE_COUNT" >> ${WRITE_AREA_REPORT}
	echo ""                                              >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|                DFF Count              |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}
	
	set s_dff_cnt 0
	set m_dff_cnt 0
	set a_dff_cnt 0

	if { $STD_TYPE == "SNPS" } {
		set s_dff_cnt [sizeof_collection [remove_from_collection [get_cells -quiet -hierarchical * -filter "is_sequential==true && (ref_name=~ *FSD* || ref_name=~*FD*) $made_filter "] [get_cells -quiet -hierarchical * -filter "is_sequential==true && ((ref_name=~*FSD*M2*) || (ref_name=~ *FD*M2*)) $made_filter " ] ] ] 	
	} elseif { $STD_TYPE == "TSMC" } {		
		set s_dff_cnt [sizeof_collection [get_cells -quiet -hierarchical * -filter "is_sequential==true && (ref_name=~ DF* || ref_name=~EDF* || ref_name=~SDF* || ref_name=~SEDF*) $made_filter "]]
	}
	
	if { $STD_TYPE == "SNPS" } {
		set m_dff_cnt [sizeof_collection [get_cells -quiet -hierarchical * -filter "is_sequential==true && ((ref_name=~ *FSD*M2*) || (ref_name=~ *FD*M2*)) $made_filter "]]
	} elseif { $STD_TYPE == "TSMC" } {		
		set m_dff_cnt [sizeof_collection [get_cells -quiet -hierarchical * -filter "is_sequential==true && (ref_name=~ MB*) $made_filter "]]
	}

	set a_dff_cnt [ expr $a_dff_cnt + $m_dff_cnt + $s_dff_cnt ]


	echo " > - Single Bit DFF COUNT : $s_dff_cnt" >> ${WRITE_AREA_REPORT}
	echo " > -  Multi Bit DFF COUNT : $m_dff_cnt" >> ${WRITE_AREA_REPORT}
	echo " > -  TOTAL Bit DFF COUNT : $a_dff_cnt" >> ${WRITE_AREA_REPORT}
	echo ""                                       >> ${WRITE_AREA_REPORT}
	
	##################################################################################################################################################
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|               Macro List              |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}

	echo " > - MEMORY LIST          : $used_mem_type"   >> ${WRITE_AREA_REPORT}
	echo " > -   IP   LIST          : $used_macro_type" >> ${WRITE_AREA_REPORT}
	echo " > -   IO   LIST          : $used_io_type"    >> ${WRITE_AREA_REPORT}
	echo ""                                             >> ${WRITE_AREA_REPORT}
	
	##################################################################################################################################################
	### TODO: need2chk @DC
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|              Block DB Info            |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}
	
	if { $db_list != "" } { 
		foreach db_each $db_list {

			set INDEX(0) " > - $db_each"    
			set INDEX(1) $cell_COUNT($db_each)
			
			set FORMET [format "%-33s %s %-10s" $INDEX(0) : $INDEX(1)]
			echo "$FORMET" >> ${WRITE_AREA_REPORT}
		}
	} else {
		echo " > - No exists DB blocks " >> ${WRITE_AREA_REPORT}

	}

	echo "" >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	### TODO: need2chk IP Pins
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo "#|             Input Floating            |#" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}
	echo ""                                            >> ${WRITE_AREA_REPORT}
	
	if { $cell_FLOAT_LIST != "" } {
		foreach cell_FLOAT_each $cell_FLOAT_LIST {
			echo " > - $cell_FLOAT_data($cell_FLOAT_each.pin) \($cell_FLOAT_data($cell_FLOAT_each.ref)\)" >> ${WRITE_AREA_REPORT}
		}
	} else {
		echo " > - No exists Inuput Floating Point " >> ${WRITE_AREA_REPORT}

	}

	echo "" >> ${WRITE_AREA_REPORT}
	echo "#+---------------------------------------+#" >> ${WRITE_AREA_REPORT}

	##################################################################################################################################################
	##################################################################################################################################################
	
	echo " # --- / \\ --- #"
	echo " # --- END --- #"
	echo " ###############"
	echo ""
