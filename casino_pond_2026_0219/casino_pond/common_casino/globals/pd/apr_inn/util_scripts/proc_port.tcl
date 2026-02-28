
foreach pgInstTerm [dbGet [dbGet -p2 [dbGet -p top.insts.pstatus fixed].cell.subClass -v core].pgInstTerms] {
	set instName [dbGet ${pgInstTerm}.inst.name]
	set netName [dbGet ${pgInstTerm}.net.name]
	foreach allShape [dbGet ${pgInstTerm}.term.pins.allShapes.] {
		set pinLayerName [dbGet ${allShape}.layer.name]
		if { ${pinLayerName} == "M8" } {
			foreach a [dbTransform -inst $instName -localPt [dbGet ${allShape}.shapes.rect]] {
				if { $netName != "0x0" } {
					createPGPin $netName -geom "$pinLayerName $a"
				}
			}
		}
	}
}


deselectAll
selectIOPin *
set netLists ""
foreach pt_selected [dbGet selected] {
	set instName [dbGet ${pt_selected}.net.instTerms.inst.name]
	set netName [dbGet ${pt_selected}.net.name]
	set pinName [dbGet ${pt_selected}.name]
	foreach allShape [dbGet ${pt_selected}.net.instTerms.cellTerm.pins.allShapes] {
		set pinLayerName [dbGet ${allShape}.layer.name]
		if { ${pinLayerName} == "M8" } {
			setPtnPinStatus -cell [dbGet top.name] -pin $pinName -status unplaced -silent
			lappend netLists $netName
			foreach a [dbTransform -inst $instName -localPt [dbGet ${allShape}.shapes.rect]] {
				if { $netName != "0x0" } {
					createPhysicalPin $pinName -net $netName -layer $pinLayerName -rect "$a" 
				}
			}
		}
	}
}
deselectAll
foreach a $netLists {
	set_db net:${a} .dont_touch true
	setAttribute -net ${a} -skip_routing 1
}

if { [dbGet top.name] == "mem_core_wrap" } {
set ddrNets "ZN_SENSE VREF ALERT_N ZN A2 A0 A1 A3 CS_N A8 CKE A6 A4 A5 CK A7 ODT CK_N A9 DM3 DQ31 DQ30 DQ28 DQ29 DQS_N3 DQS3 DQ27 DQ26 DQ25 DQ24 DQ15 DM1 DQ14 DQ13 DQ11 DQ12 DQS_N1 DQS1 DQ9 DQ10 DQ7 DQ6 DQ8 DQ18 DQ19 DQS2 DQ0 DQ1 DQS0 DQ5 DQ3 DQ4 DQ2 DM0 DQS_N0 DQ23 DQ21 DQ22 DQ20 DM2 DQS_N2 DQ17 DQ16"
foreach a $ddrNets {
	deselectAll
	setPtnPinStatus -cell mem_core_wrap -pin $a -status unplaced
	editSelect  -net $a -layer M9      
	foreach b [dbGet selected.box] {
		createPhysicalPin $a -layer M9 -net $a -rect "$b" -samePort
	}
	set_db net:${a} .dont_touch true
	setAttribute -net $a -skip_routing 1	
}
}


if { [dbGet top.name] == "mem_core_wrap" } {
	deselectAll
	set netlists "VDD18_DDR VDD12_AC VDD12_DBYTE VDD09_DIG VSSD_CORE"
	foreach a $netlists {
		deselectAll
		editSelect -net $a -layer M9
		foreach b [dbGet selected.box] {
			createPGPin $a -geom "M9 $b"
		}
	}
}


if { [dbGet top.name] == "input_core" } {
	deselectAll
	set netlists "VDD09_DIG VSSD_CORE"
	foreach a $netlists {
		deselectAll
		editSelect -net $a -layer M9
		foreach b [dbGet selected.box] {
			createPGPin $a -geom "M9 $b"
		}
	}
}



