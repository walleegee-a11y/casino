source ../common/user_define/dsc_decode_ovars.tcl
set stage "route"

setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
source ./dbs/postcts.enc

source ${common}/globals/pd/apr_inn/mode_scripts/route_option.tcl  
source ${common}/globals/pd/apr_inn/util_scripts/ocv.tcl
setExtractRCMode -lefTechFileMap ${common}/globals/pd/apr_inn/util_scripts/qrc.map



#setTieHiLoMode -honorDontTouch false -maxFanout 5 -maxDistance 10
#addTieHiLo -cell "${tieHiLoCells}"

# uncertainty
source ${common}/globals/pd/apr_inn/util_scripts/make_uncertainty.tcl

source  ${common}/globals/pd/apr_inn/user_scripts/pre_route.tcl 
routeDesign -trackOpt
source  ${common}/globals/pd/apr_inn/user_scripts/post_route.tcl 
saveDesign ./dbs/${stage}.enc -tcon

# report
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix {$stage}
timeDesign -expandedViews -hold -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix ${stage}_hold
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
set fo [open ./report/${stage}/Short.rpt w] ; puts $fo "Short [llength [dbGet top.markers.subType *Short*]]" ; close $fo
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl

exit
