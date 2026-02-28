source ../common/user_define/dsc_decode_ovars.tcl

set stage "cts"

setMultiCpuUsage -localCpu ${maxCpu} 
#source ./util_scripts/proc_runtime.tcl ; CreateRuntimeRpt ; StartTimer $stage

source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
source ./dbs/place.enc


#Add DontUse
dbSet [dbGet -p head.libCells.name CK*NMB].dontUse 0
dbSet [dbGet -p head.libCells.name CKINVM3NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKINVM2NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKINVM1NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKINVM0NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKBUFM3NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKBUFM2NMB].dontUse 1
dbSet [dbGet -p head.libCells.name CKBUFM1NMB].dontUse 1

#################################
#source ../../UTIL/TIMING/imsi_ignore.tcl


# ECF
if { $ecfFlow == "false" } {
    source ${common}/globals/pd/apr_inn/mode_scripts/cts_option.tcl  
    source ${common}/globals/pd/apr_inn/mode_scripts/route_option.tcl  
}

# uncertainty
source ${common}/globals/pd/apr_inn/util_scripts/make_uncertainty.tcl

source  ${common}/globals/pd/apr_inn/user_scripts/pre_cts.tcl
if { $usefulSkewCCOpt == "none" } {
    ccopt_design -cts 
} else {
    ccopt_design  
}
source  ${common}/globals/pd/apr_inn/user_scripts/post_cts.tcl 

#Add DontUse
dbSet [dbGet -p head.libCells.name CK*].dontUse 1


set_interactive_constraint_modes [all_constraint_modes -active]
set_propagated_clock [all_clocks ]
#if {![file exists ./report/${stage}]} { exec mkdir ./report/${stage} }
#source ./util_scripts/fixing_clock_tree_VTH.tcl
saveDesign ./dbs/${stage}.enc -tcon

mkdir -p ./report/${stage}



# report
report_ccopt_skew_groups -histograms -summary  -file ./report/${stage}/ccopt_skew_groups.rpt
report_ccopt_clock_trees -histograms -summary -file ./report/${stage}/ccopt_clock_trees.rpt
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postCTS -prefix ${stage}
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -postCTS -hold -prefix ${stage}_hold
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl
source ${common}/globals/pd/apr_inn/util_scripts/Skew.check


exit
