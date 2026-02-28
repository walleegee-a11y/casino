#!/bin/csh -f 

#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/sta_pt
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_PATH   `pwd | sed 's;/sta_pt.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_STA_PT  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/sta_pt
setenv RUN_COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common
setenv RUN_COMMON_STA_PT  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/sta_pt

setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

#- generate ${prj_name}.sta_pt.ovars.csh
${RUN_COMMON_PATH}/globals/pi/get_ovars.tcl ;# execute TCL file
source ./${prj_name}.sta_pt.ovars.csh
if (-e ./${prj_name}.sta_pt.teco.csh) source ./sta_pt_teco.csh ;# for 'teco' task

#- touch
if !(${PWD} =~ "*-fe*_te*_pv*") setenv PRE_POST "PRE"
if  (${PWD} =~ "*-fe*_te*_pv*") setenv PRE_POST "POST"

while (${PRE_POST} == "POST" && ! -e ${PD_DONE_FILE} )
    echo "`date`: waiting export (${PD_DONE_FILE})"
    sleep 60
end

if (-e ${RUN_COMMON_STA_PT}/run_sta_pt.tcl) then
	set RUN_STA_PT_TCL = "${RUN_COMMON_STA_PT}/run_sta_pt.tcl"
else
	set RUN_STA_PT_TCL = "${COMMON_STA_PT}/run_sta_pt.tcl"
endif

foreach mode ( ${sta_pt_modes} )
    foreach corner ( ${sta_pt_corners} )
        if !(${corner} == "") then
            echo "${mode}.${corner}"

            echo "mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}"
            \mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}
            cd        ${RUN_PATH}/sta_pt/${mode}/${corner}

            \cp -rf   ${RUN_STA_PT_TCL} .
            chmod +x ./:run.csh

            #TODO: :restore_session.csh
            echo "#! /bin/csh -f" > :restore_session.csh
            echo "source /mnt/data/prjs/CASINO/scott/design_flow/env_selector/synopsys_env.csh" >> :restore_session.csh
            echo "pt_shell -x 'restore_session session.${mode}_${corner}'" >> :restore_session.csh
            chmod +x ./:restore_session.csh

            xterm -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file ./logs/pt.log' &
            \cd ${RUN_PATH}/sta_pt

        else
#           echo "ERROR! ${mode}.${corner}"
    
        endif

    end
end

#TODO: wait & monitoring status
