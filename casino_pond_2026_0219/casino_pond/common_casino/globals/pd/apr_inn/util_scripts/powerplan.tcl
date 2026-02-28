setLayerPreference node_net -isVisible 1
setLayerPreference node_route -isVisible 1
setLayerPreference node_layer -isVisible 1
setLayerPreference node_layer -isSelectable 1
setLayerPreference node_inst -isVisible 1
setLayerPreference node_inst -isSelectable 1

setAddStripeMode -reset ; setAddStripeMode -ignore_DRC true
setViaGenMode -reset ; setViaGenMode -allow_via_expansion false -allow_wire_shape_change false

################################################
# M5
################################################
setAddStripeMode -stacked_via_bottom_layer  M4 -stacked_via_top_layer M5
if {[dbGet top.fplan.rblkgs.name temp_fp] != "0x0"} { deleteRouteBlk -name temp_fp }

# prevent M5 mesh on the CLAMP
deselectAll
if { [dbGet top.insts.cell.name PCLAMPEC_H_G] != "0x0"} { selectInstByCellName PCLAMPEC_H_G }
foreach a [dbGet selected] {
	set llx [expr [dbGet $a.box_llx]-1]   ;	 set lly [expr [dbGet $a.box_lly]-17]
	set urx [expr [dbGet $a.box_urx]+1]  ;	 set ury [expr [dbGet $a.box_ury]+1]
	createRouteBlk -layer M5 -spacing 0 -box "$llx $lly $urx $ury" -name clampTempRblkg
}
deselectAll
deselectAll
if { [dbGet top.insts.cell.name PCLAMPEC_V_G] != "0x0"} { selectInstByCellName PCLAMPEC_V_G }
foreach a [dbGet selected] {
	set llx [expr [dbGet $a.box_llx]-1]   ;	 set lly [expr [dbGet $a.box_lly]-1]
	set urx [expr [dbGet $a.box_urx]+17]  ;	 set ury [expr [dbGet $a.box_ury]+1]
	createRouteBlk -layer M5 -spacing 0 -box "$llx $lly $urx $ury" -name clampTempRblkg
}
deselectAll



# checking narrow channel direction y
clearDrc
set box_dy [report_narrow_channel -width $narrow_channel_direction_y -direction y -active_objects {macro hardBlkg routeBlkg}] ; # fixing bug 
set box_dy [report_narrow_channel -width $narrow_channel_direction_y -direction y -active_objects {macro hardBlkg routeBlkg}]
if { $box_dy != "" } {createRouteBlk -layer "[dbGet [dbGet -p head.layers.type routing].name -u]" -boxList [join $box_dy] -name temp_fp}
deselectAll
if { [dbGet top.insts.cell.name *SROM*] != "0x0" } {selectInstByCellName *SROM*}
if { [dbGet top.insts.cell.name *SRAM*] != "0x0" } {selectInstByCellName *SRAM*}
foreach a [join [dbGet [dbGet -p2 selected.cell.subClass -v none].boxes ]] {createRouteBlk -layer [dbGet [dbGet -p head.layers.type routing].name -u] -boxList $a -name temp_fp}
deselectAll

# checking narrow channel direction x
clearDrc
set box_dx [report_narrow_channel -width $narrow_channel_direction_x -direction x -active_objects {macro hardBlkg routeBlkg}]
if { $box_dx != "" } {createRouteBlk -layer "[dbGet [dbGet -p head.layers.type routing].name -u]" -boxList [join $box_dx] -name temp_fp}

# start memory PG stripe
# PG stripe over all macro and bw macro. user class memory_stripe
clearDrc
set M5_track_offset [lindex [dbGet [dbGet -p2 top.fplan.tracks.layers.name M5].start] 1]
set allMacroAndBwMacro [dbShape [dbGet [dbGet -p top.fplan.rBlkgs.name temp_fp].boxes ] AND [dbGet top.fplan.box]]
foreach a $allMacroAndBwMacro { createMarker -bbox $a }
clearDrc
deleteRouteBlk -name temp_fp
addStripe -uda memory_stripe -create_pins 0 -area "$allMacroAndBwMacro" -layer M5 -nets "$pName  $gName " -width $M5_PG_memory_width -set_to_set_distance $M5_memory_PG_pitch -spacing $M5_PG_memory_spacing_bw_PG
##foreach a $allMacroAndBwMacro {
##	set llx [lindex $a 0] ; set lly [lindex $a 1] ; set urx [lindex $a 2] ; set ury [lindex $a 3]
##	set llx [expr [format "%.1f" $llx] + $M5_offset_memory_PG_stripe + $M5_track_offset] ; # for aligning track
##	if { [expr $urx - $llx] > [expr ($M5_PG_memory_width*2) + $M5_PG_memory_spacing_bw_PG + $M5_offset_memory_PG_stripe ] } { ; # ignore narrow width
##		addStripe -uda memory_stripe -create_pins 0 -area "$llx $lly $urx $ury" -layer M5 -nets "$pName  $gName " -width $M5_PG_memory_width -set_to_set_distance $M5_memory_PG_pitch -spacing $M5_PG_memory_spacing_bw_PG
##	}
##}

setLayerPreference node_layer -isVisible 0
setLayerPreference M5 -isVisible 1

# delete PG strip on bw macro
deselectAll
foreach a [dbShape $box_dy SIZEX $M5_PG_memory_width ] { ; # serching SIZEX $M5_PG_memory_width
	if { [expr [lindex $a 2] - [lindex $a 0]] > [expr $M5_PG_memory_width * 2 + 3] } { ; # do not delete PG strip under 3um spacing
		editCutWire -only_visible_wires -box [dbShape $a SIZEY 12]
		deleteSelectedFromFPlan
		editCutWire -only_visible_wires -box [dbShape $a SIZEY 12]
		deleteSelectedFromFPlan
	}
}

setLayerPreference node_layer -isVisible 1

# delete PG strip under $M5_PG_memory_width
deselectAll ; editSelect -layer M5 -shape STRIPE 
set a [get_db selected  -if {.width < $M5_PG_memory_width || .area < 20}]
deselectAll ; select_obj $a ;  deleteSelectedFromFPlan

# PG stripe on bw macro. user class memory_bw_stripe
foreach a $box_dy {
	set llx [lindex $a 0] ; set lly [expr [lindex $a 1] - 12] ; set urx [lindex $a 2] ; set ury [expr [lindex $a 3] + 12]
	if { [expr $urx - $llx] > [expr ($M5_PG_bw_memory_width*2) + $M5_PG_bw_memory_spacing_bw_PG + $M5_offset_bw_memory_PG_stripe ] } { ; # ignore narrow width
		set llx [expr [format "%.1f" $urx] + $M5_track_offset - ($M5_PG_bw_memory_width*2) - $M5_PG_bw_memory_spacing_bw_PG - $M5_offset_bw_memory_PG_stripe] ; # for aligning track
		addStripe -uda memory_bw_stripe -create_pins 0 -area "$llx $lly $urx $ury" -layer M5 -nets "$pName  $gName " -width $M5_PG_bw_memory_width -set_to_set_distance $M5_memory_PG_pitch -spacing $M5_PG_bw_memory_spacing_bw_PG
	}
}

# PG stripe on Core. user class core_stripe
foreach a [dbShape $allMacroAndBwMacro SIZEY 1] {createRouteBlk -layer "[dbGet [dbGet -p head.layers.type routing].name -u]" -boxList "$a" -name temp_fp -spacing 0}
set llx 0 ; set lly [dbGet top.fPlan.box_lly] ; set urx [dbGet top.fPlan.box_urx] ; set ury [dbGet top.fPlan.box_ury]
set llx [expr [format "%.1f" $llx] + $M5_offset_core_PG_stripe] ; # for aligning track
addStripe -uda core_stripe -create_pins 0 -area "$llx $lly $urx $ury" -layer M5 -nets "$pName  $gName " -width $M5_PG_core_width -set_to_set_distance $M5_PG_core_pitch -spacing $M5_PG_core_spacing_bw_PG
deleteRouteBlk -name temp_fp


if {[dbGet top.fplan.rblkgs.name clampTempRblkg] != "0x0"} { deleteRouteBlk -name clampTempRblkg }
################################################
# M6
################################################
setAddStripeMode -stacked_via_bottom_layer  M5 -stacked_via_top_layer M7
addStripe -direction horizontal -uda core_stripe -create_pins 0 -area "[dbGet top.fPlan.box]" -layer M6 -nets "$pName  $gName " -width $M6_PG_width -set_to_set_distance $M6_PG_pitch -spacing $M6_PG_spacing_bw_PG -start_offset 4

deselectAll
if { [dbGet top.insts.cell.name PCLAMPEC_V_G] != "0x0"} { selectInstByCellName PCLAMPEC_V_G }
if { [dbGet top.insts.cell.name PCLAMPEC_H_G] != "0x0"} { selectInstByCellName PCLAMPEC_H_G }
if { [dbGet top.insts.name MPLL_VDD08_PCLAMPEC_V_G] != "0x0" } { deselect_obj MPLL_VDD08_PCLAMPEC_V_G }
foreach a [dbGet selected.box] {
	set ptx1 [lindex $a 0]
	set pty1 [lindex $a 1]
	set ptx2 [lindex $a 2]
	set pty2 [lindex $a 3]

	for { set pty [expr (int($pty1/2) * 2) + 2 ] } { $pty2 >= [expr $pty + 1.5]   } { set pty [expr $pty + 2] } {
		setEditMode -reset
		if { [expr ($pty/2)%2] == 0 } { set netName $pName } else { set netName $gName }
		setEditMode -create_crossover_vias true -create_via_on_pin true -layer_horizontal M6 -layer_vertical M6 \
			-nets $netName -shape STRIPE -snap false \
			-spacing 0.050 -spacing_horizontal 2 -spacing_vertical 0.400 -status fixed \
			-type special -width_horizontal 1.5 -width_vertical 1.5
		editAddRoute $ptx1 [expr $pty + 0.75]
		editCommitRoute $ptx2 [expr $pty + 0.75]
	}
}
deselectAll


if { [dbGet top.name] == "mem_core_wrap" } {
	set layers "M7 M8 M9"
	foreach a $layers {
		deselectAll
		editSelect -layer $a
		foreach b [dbGet selected.box] {	createRouteBlk -layer $a -box "$b" -pgnetonly -name rBlkgDDR }
	}
}

################################################
# M7
################################################
setAddStripeMode -stacked_via_bottom_layer  M6 -stacked_via_top_layer M7
addStripe -direction vertical -uda core_stripe -create_pins 0 -area "[dbGet top.fPlan.box]" -layer M7 -nets "$pName  $gName " -width $M7_PG_width -set_to_set_distance $M7_PG_pitch -spacing $M7_PG_spacing_bw_PG 

################################################
# M8
################################################
setAddStripeMode -stacked_via_bottom_layer  M7 -stacked_via_top_layer M8
addStripe -direction horizontal -uda core_stripe -create_pins 0 -area "[dbGet top.fPlan.box]" -layer M8 -nets "$pName  $gName " -width $M8_PG_width -set_to_set_distance $M8_PG_pitch -spacing $M8_PG_spacing_bw_PG

################################################
# M9
################################################
setAddStripeMode -stacked_via_bottom_layer  M8 -stacked_via_top_layer M9
addStripe -direction vertical -uda core_stripe -create_pins 0 -area "[dbGet top.fPlan.box]" -layer M9 -nets "$pName  $gName " -width $M9_PG_width -set_to_set_distance $M9_PG_pitch -spacing $M9_PG_spacing_bw_PG

################################################
# sroute followpin
################################################
setAddStripeMode -stacked_via_bottom_layer AP -stacked_via_top_layer AP
sroute -connect { corePin } -layerChangeRange { M1(1) M1(1) } -allowJogging 0  -nets "$pName  $gName " -allowLayerChange 0 
deselectAll
editSelect -subclass memory_bw_stripe ; puts "select memory_bw_stripe" 
editSelect -subclass core_stripe      ; puts "select core_stripe" 
editSelect -shape FOLLOWPIN           ; puts "select FOLLOWPIN" 
setViaGenMode -optimize_cross_via 1
if { [dbGet top.name] != "mem_core_wrap" } {
	editPowerVia -skip_via_on_pin Standardcell -bottom_layer M1 -selected_wires 1 -nets "$pName  $gName " -add_vias 1 -top_layer M5
} else {
	editPowerVia -skip_via_on_pin Standardcell -bottom_layer M1 -selected_wires 1 -nets "$pName  $gName " -add_vias 1 -top_layer M5 -via_scale_height 40
}

deselectAll

if { [dbGet top.name] != "ANA38410" } {
deselectAll
editSelect -layer "M8 M9" -net "VDD09_DIG VSSD_CORE"
createPGPin -selected -onDie 
deselectAll
}

clearDrc 
setAddStripeMode -reset 
setViaGenMode -reset 

if {[dbGet top.fplan.rblkgs.name rBlkgDDR] != "0x0"} { deleteRouteBlk -name rBlkgDDR }


