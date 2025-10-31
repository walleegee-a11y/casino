source ../common/user_define/dsc_decode_ovars.tcl


set stage "init"


setMultiCpuUsage -localCpu ${maxCpu}


    set init_pwr_net "$pName"
    set init_gnd_net "$gName"
    set init_lef_file "$techLef $stdLef $memLef "

source ${common}/globals/pd/apr_inn/util_scripts/make_view_definition.tcl 
set init_mmmc_file "viewDefinitionFile.tcl"
set init_verilog $verilog
set init_top_cell ${topName}

set init_design_uniquify 1
set init_no_new_assigns 1

setIoFlowFlag 0


init_design


##LVT Swap
#source ../common/UTIL/SCRIPT/:CHAGE_RVT
##Clock Swap
#timeDesign -reportOnly
#setEcoMode -refinePlace false -updateTiming false -batchMode true
#
#foreach target [dbGet [dbGet -p top.nets.isClock 1].instTerms.inst] {
#    set inst [dbGet $target.name]
#    set cell [dbGet $target.cell.name]
#
#    if {[string match "*CDM*" $cell]} {
#    puts "CDM"
#    } elseif {[string match "*BUF*" $cell]} {
#        ecoChangeCell -inst $inst -cell CKBUFM6NMB
#    } elseif {[string match "*INV*" $cell]} {
#        ecoChangeCell -inst $inst -cell CKINVM6NMB
#    } elseif {[string match "*HMA" $cell]} {
#        regsub "HMA" $cell "NMB" swap
#        ecoChangeCell -inst $inst -cell $swap
#    }
#}
#setEcoMode -reset
#
#
#
#free_power_intent
#read_power_intent /mnt/data/prjs/CASINO/YMK/11_VER/ANA6710P/db/imported/design/20240909/upf/ANA6710P_UMC28eHVP_pre0f_topo.scaniso2c.upf -1801
#commit_power_intent



#############
# DK Cehck
check_instance_library_in_views
checkDesign -noHtml -physicalLibrary -outfile LEF_CHECK.tcl
#
#




source ${common}/globals/pd/apr_inn/mode_scripts/design_option.tcl


################################################
#Chip Size & IP/IO Place & Pbloakcage
################################################
source ${common}/globals/pd/apr_inn/YMK/FP/Chipsize.tcl
source ${common}/globals/pd/apr_inn/YMK/FP/IO.tcl
source ${common}/globals/pd/apr_inn/YMK/FP/Hard_Blockage.tcl
placeInstance prev_mem {1.0 1.0} MY -fixed
placeInstance rc_buf {1.0 113.06} MY -fixed


################################################
# globalNetConnet
################################################


globalNetConnect VDDL -pin VDD -type pgpin -inst * -module {}
globalNetConnect VSSL -pin VSS -type pgpin -inst * -module {}
globalNetConnect VDDL -pin * -type tiehi -inst * -module {}
globalNetConnect VSSL -pin * -type tielo -inst * -module {}


################################################
# rBlkg for edge
################################################



################################################
# pBlkg for macro
################################################


################################################
# cutRow 
################################################
cutRow
#deletePlaceBlockage -type hard 
################################################
# physcial cell ( EndCap and TapCell )
################################################
####Endcap
setPlaceMode -place_detail_legalization_inst_gap 2
setEndCapMode -reset
setEndCapMode \
    -rightEdge $rowLeftEndCap -leftEdge $rowRightEndCap -boundary_tap true

addEndCap -prefix ENDCAP 


###TAP CELL
set_well_tap_mode -reset
set_well_tap_mode -rule $tapCellRule -cell $tapCell -bottom_tap_cell $tapCell -top_tap_cell $tapCell
addWellTap -cell $tapCell -check_channel -cellInterval $tapCellRule -checkerBoard 
set_well_tap_mode -rule [expr $tapCellRule / 2] -cell $tapCell -bottom_tap_cell $tapCell -top_tap_cell $tapCell

setEndCapMode -reset
set_well_tap_mode -reset

#Verify
checkPlace
verifyWellTap -rule 50

################################################
# power Mesh
################################################

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

    #MEM Blockage
    setAddStripeMode -stacked_via_bottom_layer  M4 -stacked_via_top_layer M5
    deselectAll
    selectInstByCellName *SYN*
#    deselect_obj [dbGet -p selected.objType hInst]
    foreach box [dbGet selected.box] {
    addStripe -direction vertical -uda memory_stripe -create_pins 0 -area "$box" -layer M5 -nets "$pName  $gName " -width $M5_PG_memory_width -set_to_set_distance $M5_memory_PG_pitch -spacing $M5_PG_memory_spacing_bw_PG -start_offset $M5_offset_memory_PG_stripe
    createRouteBlk -boxList $box -layer M5 -name mem_rblk
    }


    addStripe -direction vertical -uda core_stripe -create_pins 0  -layer M5 -nets "$pName  $gName " -width $M5_PG_core_width -set_to_set_distance $M5_PG_core_pitch -spacing $M5_PG_core_spacing_bw_PG -start_offset 4 
    deleteRouteBlk -name mem_rblk



    ################################################
    # M6
    ################################################
    setAddStripeMode -stacked_via_bottom_layer  M5 -stacked_via_top_layer M7
    addStripe -direction horizontal -uda core_stripe -create_pins 0  -layer M6 -nets "$pName  $gName " -width $M6_PG_width -set_to_set_distance $M6_PG_pitch -spacing $M6_PG_spacing_bw_PG -start_offset 4  


    
    ################################################
    # M7
    ################################################
    setAddStripeMode -stacked_via_bottom_layer  M6 -stacked_via_top_layer M7
    addStripe -direction vertical -uda core_stripe -create_pins 0  -layer M7 -nets "VDDL  VSSL " -width $M7_PG_width -set_to_set_distance $M7_PG_pitch -spacing $M7_PG_spacing_bw_PG 
    
    ################################################
    # M8
    ################################################
    setAddStripeMode -stacked_via_bottom_layer  M7 -stacked_via_top_layer M8
    addStripe -direction horizontal -uda core_stripe -create_pins 0  -layer M8 -nets "VDDL  VSSL " -width $M8_PG_width -set_to_set_distance $M8_PG_pitch -spacing $M8_PG_spacing_bw_PG 
    ################################################
    # M1
    ################################################
    sroute -connect { corePin } -layerChangeRange { M1(1) M1(1) } -allowJogging 0  -nets "VDDL VSSL " -allowLayerChange 0 

################################################
# Power Via
################################################
deselectAll
editSelectVia -cut_layer {VI1 VI2 VI3 VI4 VI5 VI6 VI7 TMV_RDL}
editDelete -objects selected
setViaGenMode -reset
    #power rail via
    setViaGenMode -optimize_via_on_routing_track 1
    setViaGenMode -optimize_cross_via 1
    setViaGenMode -ignore_viarule_enclosure true
    setViaGenMode -cutclass_preference square
    editPowerVia -bottom_layer ME1 -top_layer ME5 -add_vias 1 -skip_via_on_pin Block

    #Another Power Via
    setViaGenMode -cutclass_preference square -ignore_viarule_enclosure true
    editPowerVia -add_vias 1 -bottom_layer ME4 -top_layer ME5
    editPowerVia -add_vias 1 -bottom_layer ME5 -top_layer ME6
    editPowerVia -add_vias 1 -bottom_layer ME6 -top_layer ME7
    editPowerVia -add_vias 1 -bottom_layer ME7 -top_layer ME8

deselectAll
editSelectVia -shape FOLLOWPIN -type SPECIAL
dbSet selected.shape stripe
deselectAll


################################################
# preDecap
################################################
#source ${common}/globals/util_scripts/insertPreDecap.tcl

set_well_tap_mode -reset
set_well_tap_mode -rule $preDecapPitch -cell $preDecapCell 

    addWellTap -cell $preDecapCell -cellInterval $preDecapPitch -checkerBoard  -fixedGap -prefix PREDECAP  -fixedGap
################################################
# SpareCells
################################################
#source ./util_scripts/spare.tcl
#proc_insert_spare_cells

################################################
# softBlkg && rBlkg
################################################
deselectAll ; selectInstByCellName *SYN*  
createPlaceBlockage -type partial -density 40  -boxList  [dbShape [dbGet [dbGet -p2 selected.cell.subClass -v none].box] SIZE 10]
#setFinishFPlanMode -activeObj "routeblkg partialblkg" ; finishFloorplan -fillPlaceBlockage partial 50 
deselectAll



createPlaceBlockage -type soft -name defScreenName -box {450.8200000000 160.6000000000 463.0000000000 204.0000000000}



################################################
# Finish Add FloorPlan
################################################
################################################
# create PG Pin and IP signal Pin
################################################
#################################################
#Add FP
#################################################
# report
#set_well_tap_mode -rule [expr $tapCellRule / 2] -cell $tapCell -bottom_tap_cell $tapCell -top_tap_cell $tapCell
#verifyWellTap ; set_well_tap_mode -reset
#verify_drc
##verify_connectivity -no_weak_connect -type special -net "VDD09_DIG VSSD_CORE" -no_antenna
#checkPlace
#source ./util_scripts/vth.tcl ; proc_report_vth ./report/${stage}/vth.rpt
#write_lef_abstract -noCutObs ./report/${stage}/[dbGet top.name ].lef -stripePin -PGPinLayers {8 9} -5.8 -specifyTopLayer 6
#saveNetlist -excludeLeafCell ./report/${stage}/[dbGet top.name].v
#report_preserves -dont_touch -obj_type net > ./report/${stage}/dont_touch_net_by_proc_port.rpt

#set lefDefOutVersion 5.5 ; defOut -usedVia -floorplan -unit 1000 ./report/${stage}/[dbGet top.name ].5p5.def
#set lefDefOutVersion 5.8 ; defOut -usedVia -floorplan -unit 1000 ./report/${stage}/[dbGet top.name ].5p8.def


saveDesign ./dbs/${stage}.enc 

timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -prePlace -prefix ${stage}
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl



#return

exit



