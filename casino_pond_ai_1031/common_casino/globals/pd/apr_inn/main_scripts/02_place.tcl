source ../common/user_define/dsc_decode_ovars.tcl

set stage "place"

setMultiCpuUsage -localCpu ${maxCpu} 
source ${common}/globals/pd/apr_inn/mode_scripts/set_load.tcl
restoreDesign ./dbs/init.enc.dat $topName

summaryReport -noHtml -outfile ./report/init/init_EU_TU

checkDesign -timingLibrary -noHtml -outfile  ./report/checkTimingLibrary.tcl

## attach Buffer
#   source ${common}/globals/util_scripts/attachMacroBuffer.tcl
#   source ${common}/globals/util_scripts/attachIOBuffer.tcl
#   source ${common}/globals/util_scripts/attachMacroBuffer.tcl

# mode options
source ${common}/globals/pd/apr_inn/mode_scripts/design_option.tcl 
source ${common}/globals/pd/apr_inn/mode_scripts/analysis_option.tcl
source ${common}/globals/pd/apr_inn/mode_scripts/place_option.tcl
source ${common}/globals/pd/apr_inn/mode_scripts/opt_option.tcl

# util 
source ${common}/globals/pd/apr_inn/util_scripts/createPathGroups.tcl
#source ${common}/globals/pd/apr_inn/util_scripts/dont_use_cell.tcl
source ${common}/globals/pd/apr_inn/util_scripts/ocv.tcl
source ${common}/globals/pd/apr_inn/util_scripts/cellPadding.tcl 
#source ${common}/UTIL/DT/01_Donttouch
#setOptMode -sizeOnlyFile ${common}/UTIL/DT/02_sizeonly
#source ${common}/globals/util_scripts/cell_obs.tcl 
#source ${common}/globals/util_scripts/ana38410_region.tcl
#source ${common}/globals/util_scripts/ana38410_dontTouch.tcl
#source ./util_scripts/convert_lib_clk.tcl


# max fanout & tran & length
set_interactive_constraint_modes [all_constraint_modes -active]
set_max_fanout $data_max_fanout [current_design ]          
set_max_transition $data_max_tran [current_design ]
setOptMode -maxLength $data_max_length

# report prePlace
# uncertainty
source ${common}/globals/pd/apr_inn/util_scripts/make_uncertainty.tcl

# ECF
#if { $ecfFlow == "true" } {
#   setDesignMode -earlyClockFlow true
#   source ./mode_scripts/cts_option.tcl  
#   source ./mode_scripts/route_option.tcl  
#   setOptMode -usefulSkewTNSPreCTS true
#   setVar LS_PLACEOPT::poEarlyClockFlowWNSOptSlackBandMultipler 8.0 ; # If you want more aggresive optimize, increase this value.
#   # create/source clock tree spec:
#   create_ccopt_clock_tree_spec -keep_all_sdc_clocks -filename ./ccopt.spec
#   source ./ccopt.spec
#   foreach ct [get_ccopt_clock_trees *] {
#     Puts "   INFO    >> setting max length constraints for clock tree : $ct"
#     set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type top ${cts_top_net_length} ;   # limit the top   net length - confirmed value for this technology and library
#     set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type trunk ${cts_turnk_net_length} ;   # limit the trunk net length - confirmed value for this technology and library
#     set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type leaf ${cts_leaf_net_length} ;   # limit the leaf  net length - confirmed value for this technology and library
#   }
#}

######SCAN Control#################
setPlaceMode -place_global_exp_allow_missing_scan_chain false
setPlaceMode -place_global_ignore_scan true
setPlaceMode -place_global_reorder_scan true

#defIn /mnt/data/prjs/CASINO/YMK/11_VER/ANA6710P/db/imported/design/20240909/def/ANA6710P_UMC28eHVP_pre0f_topo.scandef


###########Memoty latency##########
set_clock_latency -0.15 rc_buf/CK
set_clock_latency -0.15 prev_mem/CK

###################################


source ${common}/globals/pd/apr_inn/user_scripts/pre_place.tcl
place_opt_design -expanded_views
source ${common}/globals/pd/apr_inn/user_scripts/post_place.tcl

deleteCellPad * 
saveDesign ./dbs/${stage}.enc -tcon

# report
timeDesign -expandedViews -outDir ./report/${stage} -numPaths 1000 -preCTS -prefix ${stage}
summaryReport -noHtml -outfile ./report/${stage}/${stage}_EU_TU
report_power -outfile ./report/${stage}/${topName}_${stage}.power 
source ${common}/globals/pd/apr_inn/util_scripts/VTH.tcl
reportCongestion -hotSpot > ./report/${stage}/hotSpot.tcl


exit
