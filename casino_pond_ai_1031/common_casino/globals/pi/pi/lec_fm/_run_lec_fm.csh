#!/bin/csh
###############################################
#- Set Environment 
###############################################
#      -9  -8   -7   -6      -5               -4         -3                         -2   -1                   				  	     NF
# ex) /mnt/data/prjs/ANA6714/works_honggu.kim/dsc_decode/pi___dc-0.0_dk-0.0_tag-0.0/runs/00_inc-04_Automation_With_PV-fe00_te01_pv00/lec_fm
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_DIR    `pwd | sed 's;/lec_fm.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_LEC_FM  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/lec_fm
setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}

#clean-up
\cp -rf ./../common/globals/pi/lec_fm/:clean .

#make directories
mkdir -p ./logs/
mkdir -p ./reports/

#TODO: :restore_session.csh
echo "#! /bin/csh -f" > ./:restore_session.csh
echo "source all_tools_env.csh" >> ./:restore_session.csh
echo "fm_shell -x 'restore_session ${top_design}.session.fss'" >> ./:restore_session.csh
chmod +x ./:restore_session.csh

#run_lec_fm.tcl
\cp -rf ./../common/globals/pi/lec_fm/run_lec_fm.tcl .
fm_shell -f ./run_lec_fm.tcl | tee ./logs/lec_fm.log
