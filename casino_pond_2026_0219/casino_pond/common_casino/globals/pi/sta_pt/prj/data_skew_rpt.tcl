#set rpt_path  ${RUN_PATH}/sta_pt/${mode}
sh mkdir -p ./../Data_Skew
sh mkdir -p ./../Data_Skew/merge

suppress_message UITE-416

set max_min max
	source  ${RUN_COMMON_STA_PT}/prj/LTPS_pins_check.tcl  >   ./../Data_Skew/${corner}_max.rpt
	source  ${RUN_COMMON_STA_PT}/prj/EQ_pins_check.tcl    >>  ./../Data_Skew/${corner}_max.rpt
	source  ${RUN_COMMON_STA_PT}/prj/HIZ_pins_check.tcl   >>  ./../Data_Skew/${corner}_max.rpt
	source  ${RUN_COMMON_STA_PT}/prj/SR_LOAD.tcl          >>  ./../Data_Skew/${corner}_max.rpt

set max_min min
    source  ${RUN_COMMON_STA_PT}/prj/LTPS_pins_check.tcl  >  ./../Data_Skew/${corner}_min.rpt
    source  ${RUN_COMMON_STA_PT}/prj/EQ_pins_check.tcl    >> ./../Data_Skew/${corner}_min.rpt
    source  ${RUN_COMMON_STA_PT}/prj/HIZ_pins_check.tcl    >> ./../Data_Skew/${corner}_min.rpt
    source  ${RUN_COMMON_STA_PT}/prj/SR_LOAD.tcl           >> ./../Data_Skew/${corner}_min.rpt


set MERGE_OUTPUT "./../Data_Skew/merge/${corner}_total_skew.rpt"

source ${RUN_COMMON_STA_PT}/prj/test_single.tcl 

unsuppress_message UITE-416
