source ../common/user_define/dsc_decode_ovars.tcl
set stage "postcts"

setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
source ./dbs/cts.enc

setOptMode -sizeOnlyFile ${common}/UTIL/DT/02_sizeonly
source  ${common}/globals/pd/apr_inn/user_scripts/pre_postcts.tcl 
if { ${GBAholdOpt} == "true" } { 
    optDesign -postCTS -expandedViews -setup -hold 
} else {
    optDesign -postCTS -expandedViews -setup 
}
source  ${common}/globals/pd/apr_inn/user_scripts/post_postcts.tcl 
saveDesign ./dbs/${stage}.enc -tcon

# report
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postCTS -prefix ${stage}
timeDesign -expandedViews -hold -outDir ./report/${stage} -numPaths 1000 -postCTS -prefix ${stage}_hold
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
report_power -outfile ./report/${stage}/${topName}_${stage}.power 
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl

exit

