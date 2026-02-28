

setPlaceMode -place_detail_legalization_inst_gap 2

# EndCap
setEndCapMode -reset
setEndCapMode \
	-rightEdge $rowLeftEndCap -leftEdge $rowRightEndCap -boundary_tap true
addEndCap -prefix ENDCAP	

# Well Tap
set_well_tap_mode -reset
set_well_tap_mode -rule $tapCellRule -cell $tapCell -bottom_tap_cell $tapCell -top_tap_cell $tapCell
addWellTap -cell $tapCell -check_channel -cellInterval $tapCellRule -checkerBoard
set_well_tap_mode -rule [expr $tapCellRule / 2] -cell $tapCell -bottom_tap_cell $tapCell -top_tap_cell $tapCell

setEndCapMode -reset
set_well_tap_mode -reset

