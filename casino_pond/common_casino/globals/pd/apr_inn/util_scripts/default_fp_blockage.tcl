


deselectAll
deletePlaceBlockage -all 
deleteRoutingHalo -allBlocks

# padAreaIO
if { [dbGet top.insts.cell.subClass padAreaIO] != "0x0" } {
deselectAll
select_obj [dbGet -p2 [dbGet -p top.insts.pstatus fixed].cell.subClass padAreaIO]
createPlaceBlockage -boxList [dbShape [dbGet selected.boxes] SIZE 15]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}

# POR
if { [dbGet top.insts.cell.name A38407_POR_T22ULP_A00] != "0x0" } {
deselectAll ; selectInstByCellName A38407_POR_T22ULP_A00
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.box] SIZEX 50] SIZEY 60]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}
# PLL
if { [dbGet top.insts.cell.name PLLTS22ULPAFRAC2] != "0x0" } {
deselectAll ; selectInstByCellName PLLTS22ULPAFRAC2
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.box] SIZEX 60] SIZEY 20]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}
# UPI
if { [dbGet top.insts.cell.name UPITX18CH_T22ULP_A00] != "0x0" } {
deselectAll ; selectInstByCellName UPITX18CH_T22ULP_A00
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.boxes] SIZEX 40] SIZEY 40]
#addRoutingHalo -inst "[dbGet selected.name ]" -space 30 -bottom M1 -top M6
deselectAll
}
# OSC
if { [dbGet top.insts.cell.name A38409_RCOSC_T22ULP_A00] != "0x0" } {
deselectAll ; selectInstByCellName A38409_RCOSC_T22ULP_A00
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.boxes] SIZEX 90] SIZEY 90]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}
# efuse
if { [dbGet top.insts.cell.name TEF22ULP8X32HD18_PHRM] != "0x0" } {
deselectAll ; selectInstByCellName TEF22ULP8X32HD18_PHRM
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.boxes] SIZEX 50] SIZEY 40]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}
# DDR
if { [dbGet top.insts.cell.name dwc_ddrphymaster_top] != "0x0" } {
deselectAll
selectInstByCellName dwc_ddrphyacx4_top_ew 
selectInstByCellName dwc_ddrphymaster_top 
selectInstByCellName dwc_ddrphydbyte_top_ns
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.boxes] SIZEX 20] SIZEY 20]
addRoutingHalo -inst "[dbGet selected.name ]" -space 2 -bottom M1 -top M6
deselectAll
}
# hir
if { [dbGet top.name] == "ANA38410" } {
deselectAll
selectInstByCellName mem_core_wrap
selectInstByCellName input_core
createPlaceBlockage -boxList [dbShape [dbShape [dbGet selected.boxes] SIZEX 3] SIZEY 3]
addRoutingHalo -inst "[dbGet selected.name ]" -space 1 -bottom M1 -top M6
deselectAll
}

# PCLAMPEC_13
if { [dbGet top.insts.cell.name PCLAMPEC_V_G] != "0x0"} {
deselectAll
selectInstByCellName PCLAMPEC_V_G
foreach a [dbGet selected] {
   set llx [expr [dbGet $a.box_llx]-2]
   set lly [expr [dbGet $a.box_lly]-2]
   set urx [expr [dbGet $a.box_urx]+18]
   set ury [expr [dbGet $a.box_ury]+2]
   createPlaceBlockage -box "$llx $lly $urx $ury"
}
foreach a [dbGet selected] {
	set llx [expr [dbGet $a.box_llx]-1]   ;	 set lly [expr [dbGet $a.box_lly]-1]
	set urx [expr [dbGet $a.box_urx]+17]  ;	 set ury [expr [dbGet $a.box_ury]+1]
	createRouteBlk -layer "M1 M2 M3 M4 M5 M6" -spacing 0 -box "$llx $lly $urx $ury" -name clampRblkg  -exceptpgnet
}
deselectAll
}


# PCLAMPEC_13
if { [dbGet top.insts.cell.name PCLAMPEC_H_G] != "0x0"} {
deselectAll
selectInstByCellName PCLAMPEC_H_G
foreach a [dbGet selected] {
   set llx [expr [dbGet $a.box_llx]-2]
   set lly [expr [dbGet $a.box_lly]-18]
   set urx [expr [dbGet $a.box_urx]+2]
   set ury [expr [dbGet $a.box_ury]+2]
   createPlaceBlockage -box "$llx $lly $urx $ury"
}
foreach a [dbGet selected] {
	set llx [expr [dbGet $a.box_llx]-1]   ;	 set lly [expr [dbGet $a.box_lly]-17]
	set urx [expr [dbGet $a.box_urx]+1]  ;	 set ury [expr [dbGet $a.box_ury]+1]
	createRouteBlk -layer "M1 M2 M3 M4 M5 M6" -spacing 0 -box "$llx $lly $urx $ury" -name clampRblkg  -exceptpgnet
}
deselectAll
}




