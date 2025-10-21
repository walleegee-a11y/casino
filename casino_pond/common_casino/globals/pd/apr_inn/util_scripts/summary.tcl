

set fo [open ./report/SUMMARY.tcl w]


set topName $topName
set i_s_lists "powerplan place cts postcts route postroute"

foreach i_s $i_s_lists {

	set ${i_s}_wns_all ""
	set ${i_s}_tns_all ""
	set ${i_s}_fed_all ""
	set ${i_s}_hwns_all ""
	set ${i_s}_htns_all ""
	set ${i_s}_hfed_all ""
	set ${i_s}_wns_reg2reg ""
	set ${i_s}_wns_reg2cgate ""
	set ${i_s}_wns_reg2out ""
	set ${i_s}_wns_in2reg ""
	set ${i_s}_wns_in2out ""
	set ${i_s}_wns_default ""
	set ${i_s}_tns_reg2reg ""
	set ${i_s}_tns_reg2cgate ""
	set ${i_s}_tns_reg2out ""
	set ${i_s}_tns_in2reg ""
	set ${i_s}_tns_in2out ""
	set ${i_s}_tns_default ""
	set ${i_s}_fed_reg2reg ""
	set ${i_s}_fed_reg2cgate ""
	set ${i_s}_fed_reg2out ""
	set ${i_s}_fed_in2reg ""
	set ${i_s}_fed_in2out ""
	set ${i_s}_fed_default ""
	set ${i_s}_of_h ""
	set ${i_s}_of_v ""
	set ${i_s}_hwns_reg2reg ""
	set ${i_s}_hwns_reg2cgate ""
	set ${i_s}_htns_reg2reg ""
	set ${i_s}_htns_reg2cgate ""
	set ${i_s}_hfed_reg2reg ""
	set ${i_s}_hfed_reg2cgate ""
	set ${i_s}_eu ""
	set ${i_s}_tu ""
	set ${i_s}_insts ""
	set ${i_s}_hs ""
	set ${i_s}_tg ""
	set ${i_s}_hg ""
	set ${i_s}_rg ""
	set ${i_s}_lg ""
	set ${i_s}_vth_h ""
	set ${i_s}_vth_r ""
	set ${i_s}_vth_l ""
	set ${i_s}_drc_s ""
	set ${i_s}_drc_t ""
	set stageName ""

if { [file exists ./report/${i_s}] } {
	if { $i_s == "powerplan" } { set stageName prePlace } 
	if { $i_s == "place" } { set stageName preCTS } 
	if { $i_s == "cts" } { set stageName postCTS } 
	if { $i_s == "postcts" } { set stageName postCTS } 
	if { $i_s == "route" } { set stageName postRoute } 
	if { $i_s == "postroute" } { set stageName postRoute } 



	if { [file exists ./report/${i_s}/${topName}_${stageName}.summary.gz] } {
		# find index
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Setup ./report/${i_s}/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		for { set i 0 } { $i < [llength $sp_edit_line] } { incr i } {
			if { [lindex $sp_edit_line $i] == "reg2reg" }   { set i_reg2reg   $i }
			if { [lindex $sp_edit_line $i] == "reg2cgate" } { set i_reg2cgate $i }
			if { [lindex $sp_edit_line $i] == "reg2out" }   { set i_reg2out   $i }
			if { [lindex $sp_edit_line $i] == "in2reg" }    { set i_in2reg    $i }
			if { [lindex $sp_edit_line $i] == "in2out" }    { set i_in2out    $i }
			if { [lindex $sp_edit_line $i] == "default" }   { set i_default   $i }
			if { [lindex $sp_edit_line $i] == "all" }   { set i_all   $i }
		}
		# WNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep WNS ./report/${i_s}/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_wns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_wns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_wns_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_wns_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_wns_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_wns_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_wns_all    [lindex $sp_edit_line $i_all   ]
		# TNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep TNS ./report/${i_s}/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_tns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_tns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_tns_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_tns_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_tns_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_tns_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_tns_all    [lindex $sp_edit_line $i_all   ]
		# FED
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Violating ./report/${i_s}/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_fed_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_fed_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_fed_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_fed_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_fed_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_fed_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_fed_all    [lindex $sp_edit_line $i_all   ]

		# Overflow
		if { $i_s != "route" && $i_s != "postroute" } {
			regsub -all {\s+} [string map {"|" " "} [exec zgrep Routing ./report/${i_s}/${topName}_${stageName}.summary.gz]] " " edit_line
			set sp_edit_line [split $edit_line " "]
			set ${i_s}_of_h [lindex $sp_edit_line 2]
			set ${i_s}_of_v [lindex $sp_edit_line 5]
		}
	}


	if { [file exists ./report/${i_s}/${topName}_${stageName}_hold.summary.gz] } {
		# find index
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Hold ./report/${i_s}/${topName}_${stageName}_hold.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		for { set i 0 } { $i < [llength $sp_edit_line] } { incr i } {
			if { [lindex $sp_edit_line $i] == "reg2reg" }   { set i_reg2reg   $i }
			if { [lindex $sp_edit_line $i] == "reg2cgate" } { set i_reg2cgate $i }
			if { [lindex $sp_edit_line $i] == "all" }   { set i_all   $i }
		}
		# WNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep WNS ./report/${i_s}/${topName}_${stageName}_hold.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_hwns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_hwns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_hwns_all        [lindex $sp_edit_line $i_all ]
		# TNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep TNS ./report/${i_s}/${topName}_${stageName}_hold.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_htns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_htns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_htns_all  [lindex $sp_edit_line $i_all ]
		# FED
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Violating ./report/${i_s}/${topName}_${stageName}_hold.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_hfed_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_hfed_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_hfed_all  [lindex $sp_edit_line $i_all ]
	}

	if { ${i_s} == "powerplan" } {
	if { [file exists ./report/pre_place/${topName}_${stageName}.summary.gz] } {
		# find index
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Setup ./report/pre_place/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		for { set i 0 } { $i < [llength $sp_edit_line] } { incr i } {
			if { [lindex $sp_edit_line $i] == "reg2reg" }   { set i_reg2reg   $i }
			if { [lindex $sp_edit_line $i] == "reg2cgate" } { set i_reg2cgate $i }
			if { [lindex $sp_edit_line $i] == "reg2out" }   { set i_reg2out   $i }
			if { [lindex $sp_edit_line $i] == "in2reg" }    { set i_in2reg    $i }
			if { [lindex $sp_edit_line $i] == "in2out" }    { set i_in2out    $i }
			if { [lindex $sp_edit_line $i] == "default" }   { set i_default   $i }
			if { [lindex $sp_edit_line $i] == "all" }   { set i_all   $i }
		}
		# WNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep WNS ./report/pre_place/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_wns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_wns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_wns_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_wns_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_wns_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_wns_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_wns_all    [lindex $sp_edit_line $i_all   ]
		# TNS
		regsub -all {\s+} [string map {"|" " "} [exec zgrep TNS ./report/pre_place/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_tns_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_tns_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_tns_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_tns_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_tns_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_tns_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_tns_all    [lindex $sp_edit_line $i_all   ]
		# FED
		regsub -all {\s+} [string map {"|" " "} [exec zgrep Violating ./report/pre_place/${topName}_${stageName}.summary.gz]] " " edit_line
		set sp_edit_line [split $edit_line " "]
		set ${i_s}_fed_reg2reg    [lindex $sp_edit_line $i_reg2reg   ]
		set ${i_s}_fed_reg2cgate  [lindex $sp_edit_line $i_reg2cgate ]
		set ${i_s}_fed_reg2out    [lindex $sp_edit_line $i_reg2out   ]
		set ${i_s}_fed_in2reg     [lindex $sp_edit_line $i_in2reg    ]
		set ${i_s}_fed_in2out     [lindex $sp_edit_line $i_in2out    ]
		set ${i_s}_fed_default    [lindex $sp_edit_line $i_default   ]
		set ${i_s}_fed_all    [lindex $sp_edit_line $i_all   ]

	}
	}



	if { [file exists ./report/${i_s}/EU_TU.rpt] } {
		set ${i_s}_eu [lindex [split [exec grep "Effective EU /" ./report/${i_s}/EU_TU.rpt]] 6]
		set ${i_s}_tu [lindex [split [exec grep "Effective EU /" ./report/${i_s}/EU_TU.rpt]] 8]
	}
	if { [file exists ./report/${i_s}/${topName}.${i_s}.summaryReport] } {
		set ${i_s}_insts [format "%.2f" [expr [lindex [split [exec grep "# Instances: " ./report/${i_s}/${topName}.${i_s}.summaryReport] ] 2] / 1000000.0]]
	}
	if { [file exists ./report/${i_s}/hotSpot.tcl] } {
		set fi [open ./report/${i_s}/hotSpot.tcl r]
		for { set i 0 } { $i < 11 } { incr i } { gets $fi line }
		set ${i_s}_hs [lindex $line end-1] 
		close $fi
	}
	if { [file exists ./report/${i_s}/vth.rpt] } {
		set ${i_s}_tg [format "%.2f" [expr [lindex [exec grep "LOGIC cell" ./report/${i_s}/vth.rpt] end] / 1000000.0]]
		set ${i_s}_hg [format "%.2f" [expr [lindex [exec grep "HVT cell" ./report/${i_s}/vth.rpt] end] / 1000000.0]]
		set ${i_s}_rg [format "%.2f" [expr [lindex [exec grep "RVT cell" ./report/${i_s}/vth.rpt] end] / 1000000.0]]
		set ${i_s}_lg [format "%.2f" [expr [lindex [exec grep "LVT cell" ./report/${i_s}/vth.rpt] end] / 1000000.0]]
		set ${i_s}_vth_h [lindex [exec grep "Primitive" ./report/${i_s}/vth.rpt] 5]
		set ${i_s}_vth_r [lindex [exec grep "Primitive" ./report/${i_s}/vth.rpt] 7]
		set ${i_s}_vth_l [lindex [exec grep "Primitive" ./report/${i_s}/vth.rpt] 9]
	}
	if { [file exists ./report/${i_s}/DRC.rpt] } {
		set ${i_s}_drc_s [lindex [exec grep "Short" ./report/${i_s}/DRC.rpt] end]
		set ${i_s}_drc_t [lindex [exec grep "Total" ./report/${i_s}/DRC.rpt] end] 
	}
}

}

set place_runtime ""
set cts_runtime ""
set postcts_runtime ""
set route_runtime  ""
set postroute_runtime ""


if { [file exists ./report/runtime.rpt] } {
	set fi [open ./report/runtime.rpt r]
	while {[gets $fi line] != -1} {
		if { [string match "place END*" $line] }	{ set place_runtime [lindex [split  $line " "] end-6] }
		if { [string match "cts END*" $line] } 		{ set cts_runtime [lindex [split  $line " "] end-6] }
		if { [string match "postcts END*" $line] } 	{ set postcts_runtime [lindex [split  $line " "] end-6] }
		if { [string match "route END*" $line] } 	{ set route_runtime [lindex [split  $line " "] end-6] }
		if { [string match "postroute END*" $line] } 	{ set postroute_runtime [lindex [split  $line " "] end-6] }
	}
	close $fi
}


eval "puts $fo \"\n\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"\" \"pre-place\" \"place\" \"cts\" \"postcts\" \"route\" \"postroute\" \]"
eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""


eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Setup reg2reg (wns/tns/fed)\" \"${powerplan_wns_reg2reg} / ${powerplan_tns_reg2reg} / ${powerplan_fed_reg2reg}\" \"${place_wns_reg2reg} / ${place_tns_reg2reg} / ${place_fed_reg2reg}\" \"${cts_wns_reg2reg} / ${cts_tns_reg2reg} / ${cts_fed_reg2reg}\" \"${postcts_wns_reg2reg} / ${postcts_tns_reg2reg} / ${postcts_fed_reg2reg}\" \"${route_wns_reg2reg} / ${route_tns_reg2reg} / ${route_fed_reg2reg}\" \"${postroute_wns_reg2reg} / ${postroute_tns_reg2reg} / ${postroute_fed_reg2reg}\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"reg2cgate (wns/tns/fed)\" \"${powerplan_wns_reg2cgate} / ${powerplan_tns_reg2cgate} / ${powerplan_fed_reg2cgate}\" \"${place_wns_reg2cgate} / ${place_tns_reg2cgate} / ${place_fed_reg2cgate}\" \"${cts_wns_reg2cgate} / ${cts_tns_reg2cgate} / ${cts_fed_reg2cgate}\" \"${postcts_wns_reg2cgate} / ${postcts_tns_reg2cgate} / ${postcts_fed_reg2cgate}\" \"${route_wns_reg2cgate} / ${route_tns_reg2cgate} / ${route_fed_reg2cgate}\" \"${postroute_wns_reg2cgate} / ${postroute_tns_reg2cgate} / ${postroute_fed_reg2cgate}\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"all (wns/tns/fed)\" \"${powerplan_wns_all} / ${powerplan_tns_all} / ${powerplan_fed_all}\" \"${place_wns_all} / ${place_tns_all} / ${place_fed_all}\" \"${cts_wns_all} / ${cts_tns_all} / ${cts_fed_all}\" \"${postcts_wns_all} / ${postcts_tns_all} / ${postcts_fed_all}\" \"${route_wns_all} / ${route_tns_all} / ${route_fed_all}\" \"${postroute_wns_all} / ${postroute_tns_all} / ${postroute_fed_all}\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Hold reg2reg (wns/tns/fed)\" \"${place_hwns_reg2reg} / ${place_htns_reg2reg} / ${place_hfed_reg2reg}\" \"${place_hwns_reg2reg} / ${place_htns_reg2reg} / ${place_hfed_reg2reg}\" \"${cts_hwns_reg2reg} / ${cts_htns_reg2reg} / ${cts_hfed_reg2reg}\" \"${postcts_hwns_reg2reg} / ${postcts_htns_reg2reg} / ${postcts_hfed_reg2reg}\" \"${route_hwns_reg2reg} / ${route_htns_reg2reg} / ${route_hfed_reg2reg}\" \"${postroute_hwns_reg2reg} / ${postroute_htns_reg2reg} / ${postroute_hfed_reg2reg}\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"reg2cgate (wns/tns/fed)\" \"${place_hwns_reg2cgate} / ${place_htns_reg2cgate} / ${place_hfed_reg2cgate}\" \"${place_hwns_reg2cgate} / ${place_htns_reg2cgate} / ${place_hfed_reg2cgate}\" \"${cts_hwns_reg2cgate} / ${cts_htns_reg2cgate} / ${cts_hfed_reg2cgate}\" \"${postcts_hwns_reg2cgate} / ${postcts_htns_reg2cgate} / ${postcts_hfed_reg2cgate}\" \"${route_hwns_reg2cgate} / ${route_htns_reg2cgate} / ${route_hfed_reg2cgate}\" \"${postroute_hwns_reg2cgate} / ${postroute_htns_reg2cgate} / ${postroute_hfed_reg2cgate}\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"all (wns/tns/fed)\" \"${place_hwns_reg2cgate} / ${place_htns_reg2cgate} / ${place_hfed_reg2cgate}\" \"${place_hwns_all} / ${place_htns_all} / ${place_hfed_all}\" \"${cts_hwns_all} / ${cts_htns_all} / ${cts_hfed_all}\" \"${postcts_hwns_all} / ${postcts_htns_all} / ${postcts_hfed_all}\" \"${route_hwns_all} / ${route_htns_all} / ${route_hfed_all}\" \"${postroute_hwns_all} / ${postroute_htns_all} / ${postroute_hfed_all}\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Overflow(HotSpot) or DRC\" \"\" \"${place_of_h}H / ${place_of_v}V (${place_hs})\" \"${cts_of_h}H / ${cts_of_v}V (${cts_hs})\" \"${postcts_of_h}H / ${postcts_of_v}V (${postcts_hs})\" \"Short ${route_drc_s} / Total ${route_drc_t}\" \"Short ${postroute_drc_s} / Total ${postroute_drc_t}\"  \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Vth ratio ( HVT / RVT / LVT )\" \"${powerplan_vth_h} / ${powerplan_vth_r} / ${powerplan_vth_l}\" \"${place_vth_h} / ${place_vth_r} / ${place_vth_l}\"  \"${cts_vth_h} / ${cts_vth_r} / ${cts_vth_l}\" \"${postcts_vth_h} / ${postcts_vth_r} / ${postcts_vth_l}\" \"${route_vth_h} / ${route_vth_r} / ${route_vth_l}\" \"${postroute_vth_h} / ${postroute_vth_r} / ${postroute_vth_l}\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Logic G/C Total\" \"${powerplan_tg} M\" \"${place_tg} M\"  \"${cts_tg} M\"  \"${postcts_tg} M\"  \"${route_tg} M\"  \"${postroute_tg} M\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Logic G/C HVT\"   \"${powerplan_hg} M\" \"${place_hg} M\"  \"${cts_hg} M\"  \"${postcts_hg} M\"  \"${route_hg} M\"  \"${postroute_hg} M\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Logic G/C RVT\"   \"${powerplan_rg} M\" \"${place_rg} M\"  \"${cts_rg} M\"  \"${postcts_rg} M\"  \"${route_rg} M\"  \"${postroute_rg} M\" \]"
eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Logic G/C LVT\"   \"${powerplan_lg} M\" \"${place_lg} M\"  \"${cts_lg} M\"  \"${postcts_lg} M\"  \"${route_lg} M\"  \"${postroute_lg} M\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"EU / TU\" \" ${powerplan_eu} / ${powerplan_tu}\" \" ${place_eu} / ${place_tu}\" \" ${cts_eu} / ${cts_tu}\" \" ${postcts_eu} / ${postcts_tu}\" \" ${route_eu} / ${route_tu}\" \" ${postroute_eu} / ${postroute_tu}\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""

eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"Instances\" \"${powerplan_insts} M\" \"${place_insts} M\"  \"${cts_insts} M\"  \"${postcts_insts} M\"  \"${route_insts} M\"  \"${postroute_insts} M\" \]"

eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\""


eval "puts $fo \[format \"\t| %30s | %30s | %30s | %30s | %30s | %30s | %30s |\" \"RunTime\" \" \" \"${place_runtime}\"  \"${cts_runtime}\"  \"${postcts_runtime}\"  \"${route_runtime}\"  \"${postroute_runtime}\" \]"


eval "puts $fo \"\t+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+--------------------------------+\n\""

close $fo
