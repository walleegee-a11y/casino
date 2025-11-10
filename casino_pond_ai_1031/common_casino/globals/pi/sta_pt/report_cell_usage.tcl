
#!/usr/bin/tclsh

set fout [open ./user_cell_usage.rpt w]

proc user_cell_usage {} {
	global ovars
	set collection_result_display_limit 100

	global fout
	global cur_instance

	set ND2_CELL         "ND2M1NMB"
	set BUF_REF_NAME     "BUF"
	set INV_REF_NAME     "INV"
	set CLK_BUF_REF_NAME "CKBUF"
	set CLK_INV_REF_NAME "CKINV"

	set ALL_CELLS [get_cells -q -h -f "is_hierarchical == false
									&& ref_name!~**logic_**
									&& ref_name!~ANTENNABWP*
									&& ref_name!~*decap*"]

	set ND2_AREA [get_attr [get_lib_cells */$ND2_CELL] area]

	# Cell type
	set COMB_CELLS      [get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name !~ ${BUF_REF_NAME}* && ref_name !~ ${CLK_BUF_REF_NAME}* && ref_name !~ ${INV_REF_NAME}* && ref_name !~ ${CLK_INV_REF_NAME}*"]
	set BUF_CELLS		[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${BUF_REF_NAME}* || ref_name =~ ${CLK_BUF_REF_NAME}*"]
	set INV_CELLS		[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${INV_REF_NAME}* || ref_name =~ ${CLK_INV_REF_NAME}*"]
	set FF_CELLS        [get_cells -q $ALL_CELLS -f "!is_black_box && is_sequential && ref_name =~ *DF*BWP*CPD*"]
	set LATCH_CELLS     [get_cells -q $ALL_CELLS -f "!is_black_box && is_sequential && !is_integrated_clock_gating_cell && ref_name =~ LAG*"]
	set ICG_CELLS       [get_cells -q $ALL_CELLS -f "!is_black_box && is_sequential && is_integrated_clock_gating_cell && ref_name =~ LAG*"]
	set PAD_CELLS       [get_cells -q $ALL_CELLS -f "is_pad_cell"]
	set MEM_CELLS       [get_cells -q $ALL_CELLS -f "is_memory_cell"]
	set IP_CELLS        [remove_from_collection [get_cells -q $ALL_CELLS -f "is_black_box && !is_pad_cell"] $MEM_CELLS]
	set DATA_BUF_CELLS 	[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${BUF_REF_NAME}* && ref_name !~ ${CLK_BUF_REF_NAME}*"]
	set DATA_INV_CELLS	[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${INV_REF_NAME}* && ref_name !~ ${CLK_INV_REF_NAME}*"]
	set CLK_BUF_CELLS	[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${CLK_BUF_REF_NAME}*"]
	set CLK_INV_CELLS	[get_cells -q $ALL_CELLS -f "!is_black_box && is_combinational && !is_pad_cell && ref_name !~ PCBRTE* && ref_name =~ ${CLK_INV_REF_NAME}*"]

	set BUF_INV_CELLS $BUF_CELLS
	append_to_collection BUF_INV_CELLS $INV_CELLS

	set DATA_BUF_INV_CELLS $DATA_BUF_CELLS
	append_to_collection DATA_BUF_INV_CELLS $DATA_INV_CELLS
	
	set CLK_BUF_INV_CELLS $CLK_BUF_CELLS
	append_to_collection CLK_BUF_INV_CELLS $CLK_INV_CELLS

	set STD_CELLS $COMB_CELLS
	append_to_collection STD_CELLS $BUF_INV_CELLS
	append_to_collection STD_CELLS $FF_CELLS
	append_to_collection STD_CELLS $LATCH_CELLS
	append_to_collection STD_CELLS $ICG_CELLS

	set NUM_STD_CELLS       [sizeof_collection $STD_CELLS]
	set NUM_COMB_CELLS      [sizeof_collection $COMB_CELLS]
	set NUM_BUF_INV_CELLS   [sizeof_collection $BUF_INV_CELLS]	
	set NUM_FF_CELLS        [sizeof_collection $FF_CELLS]
	set NUM_LATCH_CELLS     [sizeof_collection $LATCH_CELLS]
	set NUM_ICG_CELLS       [sizeof_collection $ICG_CELLS]
	set NUM_PAD_CELLS       [sizeof_collection $PAD_CELLS]
	set NUM_MEM_CELLS       [sizeof_collection $MEM_CELLS]
	set NUM_IP_CELLS        [sizeof_collection $IP_CELLS]
	set NUM_DATA_BUF_INV_CELLS  [sizeof_collection $DATA_BUF_INV_CELLS]	
	set NUM_CLK_BUF_INV_CELLS   [sizeof_collection $CLK_BUF_INV_CELLS]

	set AREA_STD_CELLS       "0"
	set AREA_COMB_CELLS      "0"
	set AREA_BUF_INV_CELLS   "0"
	set AREA_FF_CELLS        "0"
	set AREA_LATCH_CELLS     "0"
	set AREA_ICG_CELLS       "0"
	set AREA_PAD_CELLS       "0"
	set AREA_MEM_CELLS       "0"
	set AREA_IP_CELLS        "0"
	set AREA_DATA_BUF_INV_CELLS  "0"
	set AREA_CLK_BUF_INV_CELLS   "0"


	foreach_in_collection CELL $STD_CELLS       { set AREA_STD_CELLS       [expr $AREA_STD_CELLS         + [get_attr $CELL area]] }
	foreach_in_collection CELL $COMB_CELLS      { set AREA_COMB_CELLS      [expr $AREA_COMB_CELLS        + [get_attr $CELL area]] }
	foreach_in_collection CELL $BUF_INV_CELLS 	{ set AREA_BUF_INV_CELLS   [expr $AREA_BUF_INV_CELLS  	 + [get_attr $CELL area]] }
	foreach_in_collection CELL $FF_CELLS        { set AREA_FF_CELLS        [expr $AREA_FF_CELLS          + [get_attr $CELL area]] }
	foreach_in_collection CELL $LATCH_CELLS     { set AREA_LATCH_CELLS     [expr $AREA_LATCH_CELLS       + [get_attr $CELL area]] }
	foreach_in_collection CELL $ICG_CELLS       { set AREA_ICG_CELLS       [expr $AREA_ICG_CELLS         + [get_attr $CELL area]] }
	foreach_in_collection CELL $PAD_CELLS       { set AREA_PAD_CELLS       [expr $AREA_PAD_CELLS         + [get_attr $CELL area]] }
	foreach_in_collection CELL $MEM_CELLS       { set AREA_MEM_CELLS       [expr $AREA_MEM_CELLS         + [get_attr $CELL area]] }
	foreach_in_collection CELL $IP_CELLS        { set AREA_IP_CELLS        [expr $AREA_IP_CELLS          + [get_attr $CELL area]] }
	foreach_in_collection CELL $DATA_BUF_INV_CELLS  { set AREA_DATA_BUF_INV_CELLS  [expr $AREA_DATA_BUF_INV_CELLS    + [get_attr $CELL area]] }
	foreach_in_collection CELL $CLK_BUF_INV_CELLS   { set AREA_CLK_BUF_INV_CELLS   [expr $AREA_CLK_BUF_INV_CELLS     + [get_attr $CELL area]] }

	set GC_STD_CELLS        [format %.0f [expr $AREA_STD_CELLS        / $ND2_AREA]]
	set GC_COMB_CELLS       [format %.0f [expr $AREA_COMB_CELLS       / $ND2_AREA]]
	set GC_BUF_INV_CELLS   	[format %.0f [expr $AREA_BUF_INV_CELLS  	  / $ND2_AREA]]
	set GC_FF_CELLS         [format %.0f [expr $AREA_FF_CELLS         / $ND2_AREA]]
	set GC_LATCH_CELLS      [format %.0f [expr $AREA_LATCH_CELLS      / $ND2_AREA]]
	set GC_ICG_CELLS        [format %.0f [expr $AREA_ICG_CELLS        / $ND2_AREA]]
	set GC_PAD_CELLS        [format %.0f [expr $AREA_PAD_CELLS        / $ND2_AREA]]
	set GC_MEM_CELLS        [format %.0f [expr $AREA_MEM_CELLS        / $ND2_AREA]]
	set GC_IP_CELLS         [format %.0f [expr $AREA_IP_CELLS         / $ND2_AREA]]
	set GC_DATA_BUF_INV_CELLS   [format %.0f [expr $AREA_DATA_BUF_INV_CELLS   / $ND2_AREA]]
	set GC_CLK_BUF_INV_CELLS    [format %.0f [expr $AREA_CLK_BUF_INV_CELLS    / $ND2_AREA]]

	set TOTAL_NUM      	   [expr $NUM_STD_CELLS  + $NUM_PAD_CELLS  + $NUM_MEM_CELLS  + $NUM_IP_CELLS]
	set TOTAL_AREA     	   [expr $AREA_STD_CELLS + $AREA_PAD_CELLS + $AREA_MEM_CELLS + $AREA_IP_CELLS]
	set TOTAL_GC       	   [expr $GC_STD_CELLS   + $GC_PAD_CELLS   + $GC_MEM_CELLS   + $GC_IP_CELLS]
	set TOTAL_BUF_INV_NUM  [expr $NUM_DATA_BUF_INV_CELLS  + $NUM_CLK_BUF_INV_CELLS]
	set TOTAL_BUF_INV_AREA [expr $AREA_DATA_BUF_INV_CELLS + $AREA_CLK_BUF_INV_CELLS]
	set TOTAL_BUF_INV_GC   [expr $GC_DATA_BUF_INV_CELLS   + $GC_CLK_BUF_INV_CELLS]

	# Vth
	set HVT_PATTERN  "HMA"
	set RVT_PATTERN  "NMB"
	set LVT_PATTERN  "LMB"

	set HVT_CELLS [get_cells -q $ALL_CELLS -f "ref_name =~ *${HVT_PATTERN}"]
	set RVT_CELLS  [get_cells -q $ALL_CELLS -f "ref_name =~ *${RVT_PATTERN}"]
	set LVT_CELLS  [get_cells -q $ALL_CELLS -f "ref_name =~ *${LVT_PATTERN}"]

	set NUM_HVT [sizeof_collection $HVT_CELLS]
	set NUM_RVT  [sizeof_collection $RVT_CELLS]
	set NUM_LVT  [sizeof_collection $LVT_CELLS]

	set AREA_HVT "0"
	set AREA_RVT  "0"
	set AREA_LVT  "0"
	foreach_in_collection CELL $HVT_CELLS { set AREA_HVT [expr $AREA_HVT + [get_attr $CELL area]] }
	foreach_in_collection CELL $RVT_CELLS  { set AREA_RVT  [expr $AREA_RVT  + [get_attr $CELL area]] }
	foreach_in_collection CELL $LVT_CELLS  { set AREA_LVT  [expr $AREA_LVT  + [get_attr $CELL area]] }

	set GC_HVT  [format %.0f [expr $AREA_HVT/$ND2_AREA]]
	set GC_RVT   [format %.0f [expr $AREA_RVT/$ND2_AREA]]
	set GC_LVT   [format %.0f [expr $AREA_LVT/$ND2_AREA]]

	set STD_TOTAL_NUM   [expr $NUM_RVT + $NUM_LVT + $NUM_HVT]
	set STD_TOTAL_AREA  [expr $AREA_RVT + $AREA_LVT + $AREA_HVT]
	set STD_TOTAL_GC    [format %.0f [expr $GC_RVT + $GC_LVT + $GC_HVT]]
	set RATIO_HVT      [expr $AREA_HVT/$STD_TOTAL_AREA*100]
	set RATIO_RVT       [expr $AREA_RVT/$STD_TOTAL_AREA*100]
	set RATIO_LVT       [expr $AREA_LVT/$STD_TOTAL_AREA*100]
	set STD_TOTAL_RATIO [format %.2f [expr $RATIO_RVT + $RATIO_LVT + $RATIO_HVT]]


	puts $fout "###########################################################################################"
	puts $fout "# TOP_MODULE : $cur_instance"
	puts $fout "# NAND2 Area : $ND2_AREA ($ND2_CELL)"
	puts $fout "###########################################################################################"
	puts $fout "============================================================================"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "Cell type" "Inst count" Area G/C]"
	puts $fout "============================================================================"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "STD Cell"      $NUM_STD_CELLS   			 [format %.2f $AREA_STD_CELLS]   	$GC_STD_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "|-- COMB Cell(w/o BUF/INV)" $NUM_COMB_CELLS  [format %.2f $AREA_COMB_CELLS]  	$GC_COMB_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "|-- BUF/INV Cell"  $NUM_BUF_INV_CELLS  		 [format %.2f $AREA_BUF_INV_CELLS]  $GC_BUF_INV_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "|-- Flip-flop" $NUM_FF_CELLS    			 [format %.2f $AREA_FF_CELLS]    	$GC_FF_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "|-- Latch    " $NUM_LATCH_CELLS 			 [format %.2f $AREA_LATCH_CELLS] 	$GC_LATCH_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" "|-- ICG      " $NUM_ICG_CELLS   			 [format %.2f $AREA_ICG_CELLS]   	$GC_ICG_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" PAD             $NUM_PAD_CELLS   			 [format %.2f $AREA_PAD_CELLS]   	$GC_PAD_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" Memory          $NUM_MEM_CELLS   			 [format %.2f $AREA_MEM_CELLS]   	$GC_MEM_CELLS]"
	puts $fout " [format "%-28s | %-15s %-15s %-s" IP              $NUM_IP_CELLS    			 [format %.2f $AREA_IP_CELLS]    	$GC_IP_CELLS]"
	puts $fout "------------------------------+---------------------------------------------"
	puts $fout " [format "%-28s | %-15s %-15s %-s" TOTAL ${TOTAL_NUM} [format %.2f $TOTAL_AREA] ${TOTAL_GC}]"
	puts $fout "============================================================================"
	puts $fout ""
	puts $fout "# BUF INV info"
	puts $fout "==============================================================="
	puts $fout " [format "%-15s | %-15s %-15s %-s" "Cell type" "Inst count" Area G/C]"
	puts $fout "==============================================================="
	puts $fout " [format "%-15s | %-15s %-15s %-s" "BUF/INV   "  $NUM_DATA_BUF_INV_CELLS    [format %.2f $AREA_DATA_BUF_INV_CELLS]  $GC_DATA_BUF_INV_CELLS]"
	puts $fout " [format "%-15s | %-15s %-15s %-s" "DCCKB/N "  $NUM_CLK_BUF_INV_CELLS     [format %.2f $AREA_CLK_BUF_INV_CELLS]   $GC_CLK_BUF_INV_CELLS]"
	puts $fout "-----------------+---------------------------------------------"
	puts $fout " [format "%-15s | %-15s %-15s %-s" TOTAL ${TOTAL_BUF_INV_NUM} [format %.2f $TOTAL_BUF_INV_AREA] ${TOTAL_BUF_INV_GC}]"
	puts $fout "==============================================================="
	puts $fout ""

	puts $fout "# STD Cell Vth usage"
	puts $fout "=============================================================================="
	puts $fout " [format "%-15s | %-15s %-15s %-15s %-s" "Vth type" "Inst count" Area G/C Ratio]"
	puts $fout "=============================================================================="
	puts $fout " [format "%-15s | %-15s %-15s %-15s %-s" HVT($HVT_PATTERN)   $NUM_HVT [format %.2f $AREA_HVT] ${GC_HVT} [format %.2f ${RATIO_HVT}]%]"
	puts $fout " [format "%-15s | %-15s %-15s %-15s %-s" RVT($RVT_PATTERN)   $NUM_RVT  [format %.2f $AREA_RVT]  ${GC_RVT}  [format %.2f ${RATIO_RVT}]%]"
	puts $fout " [format "%-15s | %-15s %-15s %-15s %-s" LVT($LVT_PATTERN)   $NUM_LVT  [format %.2f $AREA_LVT]  ${GC_LVT}  [format %.2f ${RATIO_LVT}]%]"
	puts $fout "-----------------+------------------------------------------------------------"
	puts $fout " [format "%-15s | %-15s %-15s %-15s %-s" TOTAL ${STD_TOTAL_NUM} [format %.2f $STD_TOTAL_AREA] ${STD_TOTAL_GC} ${STD_TOTAL_RATIO}%]"
	puts $fout "=============================================================================="
	puts $fout ""
	puts $fout "# Vth portion"
	puts $fout "======================"
	puts $fout " HVT   : RVT   : LVT"
	puts $fout " [format %.2f $RATIO_HVT] : [format %.2f $RATIO_RVT] : [format %.2f $RATIO_LVT]"
	puts $fout "======================"
	puts $fout ""
	
	puts $fout "# For weekly block info"	
	puts $fout "[format "%-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s %-12s" "STD_AREA" "STD_GC" "STD_NUM" "MEM_AREA" "MEM_GC" "MEM_NUM" "IP_AREA" "IP_GC" "IP_NUM" "PAD_AREA" "PAD_GC" "PAD_NUM" "RVT_GC" "RVT_RATIO" "LVT_GC" "LVT_RATIO" "ULVT_GC" "ULVT_RATIO" ]" 
	puts $fout "[format "%-12.2f %-12s %-12s %-12.2f %-12s %-12s %-12.2f %-12s %-12s %-12.2f %-12s %-12s %-12s %-12.2f %-12s %-12.2f %-12s %-12.2f" $AREA_STD_CELLS $GC_STD_CELLS $NUM_STD_CELLS  $AREA_MEM_CELLS $GC_MEM_CELLS $NUM_MEM_CELLS $AREA_IP_CELLS $GC_IP_CELLS $NUM_IP_CELLS $AREA_PAD_CELLS $GC_PAD_CELLS $NUM_PAD_CELLS $GC_HVT $RATIO_HVT $GC_RVT $RATIO_RVT $GC_LVT $RATIO_LVT]" 



	unset ALL_CELLS
}

set cur_instance "$top_design"
puts "TOP_MODULE : $top_design"
user_cell_usage

if { $top_design == $top_name && $ovars(sta_pt,is_flatten) == "1"} {
	set sub_block_list [lminus $all_blks $top_design]
	puts "sub block list : $sub_block_list"
	foreach sub_block $sub_block_list {
		set sub_block_inst_name [get_attr [get_cells -h -f "ref_name==$sub_block"] full_name]
		puts "$sub_block : $sub_block_inst_name"
		set cur_instance "$sub_block ($sub_block_inst_name)"
		current_instance $sub_block_inst_name
		user_cell_usage
		current_instance
	}
}

close $fout
