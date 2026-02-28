#!/bin/csh -f

#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/sta_pt/dmsa
#    1 2   3    4     5     6      7       8           9           10               11      12                          13    14        15                
# ex) /mnt/data/prjs/CASINO/rachel/Release/20_20241114/TACHY_BS12H/works_rachel.han/psu_top/pi___rtl-0.0_dk-0.0_tag-0.0/runs/03_dc_init/syn_dc
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

setenv run_dir    `pwd | sed 's;/syn_dc.*;;g'`
setenv prj_home   `pwd | sed 's;/works_.*;;g'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_PATH   `pwd | sed 's;/syn_dc.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_SYN_DC  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/syn_dc

setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

setenv STD_PATH   ${PRJ_HOME}/db/vers/${db_ver}/std/db/${default_pvt}
/mnt/data/prjs/CASINO/rachel/Release/24_20241219/TACHY_BS12H/db/imported/std/241219/db/ss_0p72v_m40c
#- generate ${prj_name}.${stage}.ovars.csh
#${prj_home}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/get_ovars.tcl ;# execute TCL file
${prj_home}/works_${USER}/${top_design}/${ws}/common/globals/pi/get_ovars.tcl ;# execute TCL file
source ./${prj_name}.${stage}.ovars.csh

\cp -f ${COMMON_SYN_DC}/run_syn_dc.tcl .

# Copy user_dont_use.tcl & user_dont_touch.tcl
\cp -f ${COMMON_SYN_DC}/user_dont_use.tcl .
\cp -f ${COMMON_SYN_DC}/user_dont_touch.tcl .

mkdir -p logs
mkdir -p reports
mkdir -p outputs

#dc_shell -64 -f /mnt/data/prjs/CASINO/rachel/Release/latest/TACHY_BS12H/works_rachel.han/psu_top/pi___rtl-0.0_dk-0.0_tag-0.0/runs/03_dc_init/common/globals/pi/syn_dc/synthesis.tcl -output_log_file ./logs/dc.log
dc_shell -64 -f ./run_syn_dc.tcl -output_log_file ./logs/syn_dc.log
