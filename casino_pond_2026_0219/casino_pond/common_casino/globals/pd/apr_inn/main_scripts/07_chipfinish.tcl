source ../common/user_define/dsc_decode_ovars.tcl
set stage "chipfinish"

setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source  ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
source ./dbs/postroute.enc




    optDesign -postRoute -expandedViews -setup

    timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix ${stage}
    timeDesign -expandedViews -hold -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix ${stage}_hold
    summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
    set fo [open ./report/${stage}/Short.rpt w] ; puts $fo "Short [llength [dbGet top.markers.subType *Short*]]" ; close $fo
    source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl
    



setFillerMode -fitGap true
setFillerMode -add_fillers_with_drc false 
setFillerMode -check_signal_drc true
deleteFiller -prefix POSTDECAP
deleteFiller -prefix POSTDECAP

deleteEmptyModule
deleteDanglingNet
#source ./util_scripts/cell_obs.tcl 

checkPlace ./report/${stage}/checkPlace_wo.filler.rpt
deleteCellPad *
deleteInstPad -all 
setPlaceMode -place_detail_use_check_drc true 


addFiller -cell [concat $DECAP_LIST_SORTED] \
  -prefix POSTDECAP \
  -markFixed \
  -minHoleCheck true
addFiller -cell [concat $GFILLER_LIST_SORTED] \
  -prefix POSTDECAP \
  -markFixed \
  -minHoleCheck true
setPlaceMode -place_detail_use_check_drc false
setFillerMode -add_fillers_with_drc true
addFiller -cell [concat $FILLER_LIST_SORTED] \
  -prefix POSTDECAP \
  -markFixed \
  -minHoleCheck true
checkFiller -file ./report/${stage}/filler.rpt
checkPlace ./report/${stage}/checkPlace_w.filler.rpt

#return

if { ![file exists $outfeedDirName] } { mkdir -p $outfeedDirName }

write_lef_abstract -noCutObs ${outfeedDirName}/lef/[dbGet top.name].lef -stripePin -PGPinLayers {8 9} -5.8 -specifyTopLayer 6
write_lef_library  ${outfeedDirName}/lef/[dbGet top.name]_allLefLibrary.lef -macro_only
write_lef_library  ${outfeedDirName}/lef/[dbGet top.name]_tech.lef -tech_only
saveNetlist -excludeLeafCell ${outfeedDirName}/netlist/[dbGet top.name].v
saveNetlist  -includePowerGround ${outfeedDirName}/netlist/[dbGet top.name].lvs.v.gz

setStreamOutMode -SEcompatible false -SEvianames true -virtualConnection false -version 6      
streamOut ${outfeedDirName}/gds/[dbGet top.name].gds.gz -mapFile ${common}/globals/pd/apr_inn/util_scripts/gds_layer_map -libName [dbGet top.name ] -stripes 1 -mode ALL -dieAreaAsBoundary 

set dbgDefOutLefVias 1
defOut -floorplan -netlist -routing ${outfeedDirName}/def/[dbGet top.name ].def.gz
touch ${outfeedDirName}/innovus.done

saveDesign ./dbs/${stage}.enc -tcon
chmod -R 775 ${outfeedDirName}


exit
