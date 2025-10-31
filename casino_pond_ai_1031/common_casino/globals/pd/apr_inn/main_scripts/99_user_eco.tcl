source ../common/user_define/dsc_decode_ovars.tcl

set stage eco


setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
set beforeECO [glob -nocomplain -directory ./dbs *dat*]
restoreDesign $beforeECO ${topName}

return 





#Prepare ECO
setEcoMode -batchMode true -LEQCheck true -updateTiming false -refinePlace false -prefixName ${run_inn} -honorDontUse false


    deleteFiller -prefix POST_DECAP
    deleteFiller -prefix POST_GFILLER
    deleteFiller -prefix POST_FILLER

    setEcoMode 


#Manual (MTTV Noise)

#Eco List
    
    mkdir ECO
    cp -rf ${pi_outfeedDirName}/ECO/* ECO
    ln -s ${pi_outfeedDirName}/ECO ECO/PI_ECO

#    source ./ECO/
#    source ./ECO/


    #Automation
    foreach ecolist [glob -type f ./ECO/*] {
    source $ecolist
    }



#ECO Palce

    ecoPlace
    setEcoMode -reset
    checkPlace ./report/check_eco_Place.rpt



#ECO Route

source ${common}/globals/pd/apr_inn/mode_scripts/route_option.tcl  
ecoRoute

#FILLER

    setFillerMode -fitGap true
    setFillerMode -add_fillers_with_drc false 
    setFillerMode -check_signal_drc true
    
    deleteEmptyModule
    deleteDanglingNet
    
    checkPlace ./report/${stage}/checkPlace_wo.filler.rpt
    deleteCellPad *
    deleteInstPad -all 
    setPlaceMode -place_detail_use_check_drc true 
    
    
    addFiller -cell [concat $DECAP_LIST_SORTED] \
      -prefix POST_DECAP \
      -markFixed \
      -minHoleCheck true
    addFiller -cell [concat $GFILLER_LIST_SORTED] \
      -prefix POST_GFILLER \
      -markFixed \
      -minHoleCheck true
    setPlaceMode -place_detail_use_check_drc false
    setFillerMode -add_fillers_with_drc true
    addFiller -cell [concat $FILLER_LIST_SORTED] \
      -prefix POST_FILLER \
      -markFixed \
      -minHoleCheck true
    checkFiller -file ./report/${stage}/filler.rpt
    checkPlace ./report/${stage}/checkPlace_w.filler.rpt

#OUTPUT
    if { ![file exists $outfeedDirName] } { mkdir -p $outfeedDirName }
    
    write_lef_abstract -noCutObs ${outfeedDirName}/lef/[dbGet top.name].lef -stripePin -PGPinLayers {8 9} -5.8 -specifyTopLayer 6
    write_lef_library  ${outfeedDirName}/lef/[dbGet top.name]_allLefLibrary.lef -macro_only
    write_lef_library  ${outfeedDirName}/lef/[dbGet top.name]_tech.lef -tech_only
    saveNetlist -excludeLeafCell ${outfeedDirName}/netlist/[dbGet top.name].v
    saveNetlist  -includePowerGround ${outfeedDirName}/netlist/[dbGet top.name].lvs.v.gz
    
    setStreamOutMode -SEcompatible false -SEvianames true -virtualConnection false -version 6      
    streamOut ${outfeedDirName}/gds/[dbGet top.name].gds.gz -mapFile ${common}/globals/pd/apr_inn/util_scripts/gds_layer_map -libName [dbGet top.name ] -stripes 1 -mode ALL -dieAreaAsBoundary  -unit 1000
    
    set dbgDefOutLefVias 1
    defOut -floorplan -netlist -routing ${outfeedDirName}/def/[dbGet top.name ].def.gz
    touch ${outfeedDirName}/innovus.done
    
    saveDesign ./dbs/${run_inn}.enc -tcon
    chmod -R 775 ${outfeedDirName}

exit
