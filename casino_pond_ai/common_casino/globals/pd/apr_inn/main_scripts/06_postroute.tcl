source ../common/user_define/dsc_decode_ovars.tcl
set stage "postroute"

setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
source ./dbs/route.enc

source ${common}/globals/pd/apr_inn/mode_scripts/route_option.tcl  
setOptMode -sizeOnlyFile ${common}/UTIL/DT/02_sizeonly
source  ${common}/globals/pd/apr_inn/user_scripts/pre_postroute.tcl 
if { ${GBAholdOpt} == "true" } { 
    optDesign -postRoute -expandedViews -setup -hold
} else {
    optDesign -postRoute -expandedViews -setup 
}
source  ${common}/globals/pd/apr_inn/user_scripts/post_postroute.tcl 
saveDesign ./dbs/${stage}.enc -tcon

# report
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix ${stage}
timeDesign -expandedViews -hold -outDir ./report/${stage} -numPaths 1000 -postRoute -prefix ${stage}_hold
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
report_power -outfile ./report/${stage}/${topName}_${stage}.power 
set fo [open ./report/${stage}/Short.rpt w] ; puts $fo "Short [llength [dbGet top.markers.subType *Short*]]" ; close $fo
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl


exit
