#! /bin/csh -f

###############################################
# Setup path variables
###############################################
#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/sta_pt/dmsa
setenv prj_name   `pwd  | awk -F / '{print $(NF-7)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-5)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-4)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-2)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_PATH   `pwd | sed 's;/sta_pt.*;;g'`

setenv COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_DMSA    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/dmsa

setenv OUTFEED_PATH   ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH    ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE   ${PD_OUT_PATH}/SMC.done

###############################################
#- Generate ${prj_name}.${stage}.ovars.csh
###############################################
${COMMON_PATH}/globals/pi/get_ovars.tcl ;# execute TCL file
source ./${prj_name}.${stage}.ovars.csh

foreach mode ( ${dmsa_teco_modes} )
    foreach corner ( ${dmsa_teco_corners} )
		if !(${corner} == "") then
			echo "${mode}.${corner}"
			while (! -e ./../${mode}/${corner}/SAVE_SESSION_DONE)
				echo "waiting save session ${mode} ${corner}"
				sleep 10
			end
		endif
        echo "session done ${mode} ${corner}"
    end
end

###############################################
#- Setup ${dmsa_dir}
###############################################
set cur_time = `date +%y%m%d_%H%M`
if (! ${dmsa_teco_physical_aware}) set log_or_phy = "logical"
if (  ${dmsa_teco_physical_aware}) set log_or_phy = "physical"

if (! ${dmsa_debug}) set dmsa_dir = "dmsa_${log_or_phy}_${cur_time}"
if (  ${dmsa_debug}) set dmsa_dir = "dmsa_debug_${log_or_phy}_${cur_time}"

if (-e ./${dmsa_dir}) then
	\rm -rf ${dmsa_dir}
endif
mkdir ${dmsa_dir}

\cp ${COMMON_DMSA}/run_dmsa.tcl ${dmsa_dir}
if (-e ./${dmsa_pre_source}) then
	\cp ${dmsa_pre_source} ${dmsa_dir}
endif

mv ./${prj_name}.${stage}.ovars.csh ${dmsa_dir}

###############################################
#- Run DMSA
###############################################
cd ${dmsa_dir}
#pt_shell -multi -f ./run_dmsa.tcl |& tee ./dmsa_master_eco.log
xterm -T ${dmsa_dir} -e pt_shell -multi -f ./run_dmsa.tcl  -output_log_file ./dmsa_master_eco.log &
