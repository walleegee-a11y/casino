#set rpt_path  ${RUN_PATH}/sta_pt/${mode}
sh mkdir -p ./../Data_Skew

suppress_message UITE-416

set max_min max
	source  ${COMMON_STA_PT}/prj/LTPS_pins_check.tcl  >   ./../Data_Skew/${corner}_max.rpt
	source  ${COMMON_STA_PT}/prj/EQ_pins_check.tcl    >>  ./../Data_Skew/${corner}_max.rpt
	source  ${COMMON_STA_PT}/prj/HIZ_pins_check.tcl   >>  ./../Data_Skew/${corner}_max.rpt

set max_min min
	source  ${COMMON_STA_PT}/prj/LTPS_pins_check.tcl  >   ./../Data_Skew/${corner}_min.rpt
	source  ${COMMON_STA_PT}/prj/EQ_pins_check.tcl    >>  ./../Data_Skew/${corner}_min.rpt
	source  ${COMMON_STA_PT}/prj/HIZ_pins_check.tcl   >>  ./../Data_Skew/${corner}_min.rpt

unsuppress_message UITE-416
