#! /bin/csh -f
###############################################
#- Set Environment 
###############################################
#    1 2   3    4    5       6                7          8                          9    10                                          11
# ex) /mnt/data/prjs/ANA6714/works_honggu.kim/dsc_decode/pi___dc-0.0_dk-0.0_tag-0.0/runs/00_inc-04_Automation_With_PV-fe00_te01_pv00/lec_fm
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_DIR    `pwd | sed 's;/vclp.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_VCLP    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/vclp
setenv RUN_COMMON_PATH  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common
setenv RUN_COMMON_VCLP  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/vclp

setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

# scripts
\cp ${RUN_COMMON_VCLP}/run_vclp.tcl .
\cp ${RUN_COMMON_VCLP}/:clean .

# :restore_session.csh
echo "#! /bin/csh -f" > :restore_session.csh
echo "setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common" >> :restore_session.csh
echo "source ./all_tools_env.csh" >> :restore_session.csh
echo "" >> :restore_session.csh
echo "vc_static_shell -full64 -output_log_file ./logs/session.log -x 'restart_session -session ${top_design}.session'" >> :restore_session.csh
chmod +x :restore_session.csh

# :run.csh
echo "#! /bin/csh -f" > :run.csh
echo "setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common" >> :run.csh
echo "source ./all_tools_env.csh" >> :run.csh
echo "" >> :run.csh
echo "mkdir -p ./logs" >> :run.csh
echo "mkdir -p ./reports" >> :run.csh
echo "" >> :run.csh
echo "vc_static_shell -full64 -f run_vclp.tcl -output_log_file ./logs/vclp.log" >> :run.csh
chmod +x :run.csh

:run.csh
