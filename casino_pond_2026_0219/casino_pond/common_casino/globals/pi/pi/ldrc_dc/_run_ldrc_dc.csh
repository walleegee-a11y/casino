#! /bin/csh -f
###############################################
#- Set Environment 
###############################################
#      -9  -8   -7   -6      -5               -4         -3                         -2   -1                   				  	     NF
# ex) /mnt/data/prjs/ANA6714/works_honggu.kim/dsc_decode/pi___dc-0.0_dk-0.0_tag-0.0/runs/00_inc-04_Automation_With_PV-fe00_te01_pv00/ldrc_dc
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_DIR    `pwd | sed 's;/ldrc_dc.*;;g'`

setenv COMMON_PATH     ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_LDRC_DC  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/ldrc_dc
setenv RUN_COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common
setenv RUN_COMMON_LDRC_DC ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/ldrc_dc

setenv OUTFEED_PATH    ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH     ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH     ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

#clean-up
rm -rf LDRC_DC_*

#make directories
mkdir -p logs
mkdir -p reports
mkdir -p netlist

if (-e ${RUN_COMMON_LDRC_DC}/run_ldrc_dc.tcl) then
	set RUN_LDRC_DC_TCL = "${RUN_COMMON_LDRC_DC}/run_ldrc_dc.tcl"
else
	set RUN_LDRC_DC_TCL = "${COMMON_LDRC_DC}/run_ldrc_dc.tcl"
endif
	
#run_ldrc_dc.tcl
\cp -rf ${RUN_LDRC_DC_TCL} .
dc_shell -f run_ldrc_dc.tcl -output_log_file ./logs/ldrc_dc.log
