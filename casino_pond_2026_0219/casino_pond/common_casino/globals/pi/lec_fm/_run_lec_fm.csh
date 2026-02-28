#! /bin/csh -f

###############################################
# Setup path variables
###############################################
#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/lec_fm
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_PATH   `pwd | sed 's;/lec_fm.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_PI      ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi
setenv COMMON_LEC_FM  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/lec_fm
setenv RUN_COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common
setenv RUN_COMMON_PI      ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi
setenv RUN_COMMON_LEC_FM  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/lec_fm

setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

# backup old run data
source ${RUN_COMMON_PI}/backup_old_run.csh

\cp ${RUN_COMMON_LEC_FM}/run_lec_fm.tcl .
chmod +x run_lec_fm.tcl

# :clean.csh
echo '#! /bin/csh -f' > :clean.csh
echo '' >> :clean.csh
echo 'set DATE = `date "+%y%m%d_%H%M"`' >> :clean.csh
echo 'mkdir -p .trash/${DATE}' >> :clean.csh
echo 'foreach file (`ls -A | grep -v trash`)' >> :clean.csh
echo '    if (! -x $file || -d $file) then' >> :clean.csh
echo '        echo " move file to .trash/${DATE} -- $file"' >> :clean.csh
echo '        \mv -f $file .trash/${DATE}' >> :clean.csh
echo '    endif' >> :clean.csh
echo 'end' >> :clean.csh
chmod +x :clean.csh

# :restore_session.csh
echo "#! /bin/csh -f" > :restore_session.csh
echo "setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common" >> :restore_session.csh
echo "source all_tools_env.csh" >> :restore_session.csh
echo "" >> :restore_session.csh
echo "fm_shell -x 'restore_session ${top_design}.session.fss'" >> :restore_session.csh
chmod +x :restore_session.csh

# :run.csh
echo "#! /bin/csh -f" > :run.csh
echo "setenv COMMON_PATH ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common" >> :run.csh
echo "source all_tools_env.csh" >> :run.csh
echo "" >> :run.csh
echo ":clean.csh" >> :run.csh
echo "mkdir -p logs" >> :run.csh
echo "mkdir -p reports" >> :run.csh
echo "" >> :run.csh
echo "fm_shell -f run_lec_fm.tcl | tee logs/lec_fm.log" >> :run.csh
chmod +x :run.csh
:run.csh
