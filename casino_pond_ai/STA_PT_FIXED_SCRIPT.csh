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

#- generate ${prj_name}.${stage}.ovars.csh
${COMMON_PATH}/globals/pi/get_ovars.tcl ;# execute TCL file
source ./${prj_name}.${stage}.ovars.csh
if (-e ./${prj_name}.sta_pt.teco.csh) source ./sta_pt_teco.csh ;# for 'teco' task

#- touch
if !(${PWD} =~ "*-fe*_te*_pv*") setenv pre_post "pre"
if  (${PWD} =~ "*-fe*_te*_pv*") setenv pre_post "post"

while (${pre_post} == "post" && ! -e ${PD_DONE_FILE} )
    echo "`date`: waiting export (${PD_DONE_FILE})"
    sleep 60
end

if (-e ${RUN_COMMON_STA_PT}/run_sta_pt.tcl) then
	set RUN_STA_PT_TCL = "${RUN_COMMON_STA_PT}/run_sta_pt.tcl"
else
	set RUN_STA_PT_TCL = "${COMMON_STA_PT}/run_sta_pt.tcl"
endif

# Initialize arrays to store background process PIDs and job names
set xterm_pids = ()
set job_list = ()

foreach mode ( ${sta_pt_modes} )
	foreach corner ( ${sta_pt_corners} )
		if !(${corner} == "") then
			echo "${mode}.${corner}"

			echo "mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}"
			mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}
			cd       ${RUN_PATH}/sta_pt/${mode}/${corner}

			mkdir -p logs
			mkdir -p reports
			mkdir -p sdc

			\cp -rf   ${RUN_STA_PT_TCL} .
			chmod +x ./run_sta_pt.tcl

			#TODO: :restore_session.csh
			echo "#! /bin/csh -f" > :restore_session.csh
			echo "source /mnt/data/prjs/CASINO/scott/design_flow/env_selector/synopsys_env.csh" >> :restore_session.csh
			echo "pt_shell -x 'restore_session session.${mode}_${corner}'" >> :restore_session.csh
			chmod +x ./:restore_session.csh

			# Launch xterm in background and capture its PID
			xterm -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file ./logs/sta_pt.log' &
			set xterm_pids = ($xterm_pids $!)
			set job_list = ($job_list "${mode}.${corner}")

			cd ${RUN_PATH}/sta_pt

		else
#			echo "ERROR! ${mode}.${corner}"

		endif

	end
end

# Wait for all background processes to complete and monitor their status
echo ""
echo "=================================================="
echo "Launched ${#xterm_pids} pt_shell jobs in background"
echo "Waiting for all jobs to complete..."
echo "=================================================="

set return_value = 0
set completed_count = 0
set failed_count = 0

# Monitor loop - check every 10 seconds
while ( ${#xterm_pids} > 0 )
	set new_pids = ()
	set new_jobs = ()
	set idx = 1

	foreach pid ( $xterm_pids )
		# Check if process is still running
		ps -p $pid >& /dev/null
		if ( $status != 0 ) then
			# Process completed - check its log file for status
			set job_name = $job_list[$idx]
			echo "`date`: Job ${job_name} (PID: ${pid}) completed"
			@ completed_count++

			# Check log file for errors (optional - can be enhanced)
			set mode_corner = `echo $job_name | sed 's/\./ /g'`
			set log_file = "${RUN_PATH}/sta_pt/${mode_corner}/logs/sta_pt.log"
			if ( -e $log_file ) then
				# Check for critical errors in log
				grep -qi "error" $log_file
				if ( $status == 0 ) then
					echo "  WARNING: Found errors in ${log_file}"
					@ failed_count++
					set return_value = 1
				endif
			endif
		else
			# Process still running - keep in list
			set new_pids = ($new_pids $pid)
			set new_jobs = ($new_jobs $job_list[$idx])
		endif
		@ idx++
	end

	# Update lists
	set xterm_pids = ($new_pids)
	set job_list = ($new_jobs)

	# Report progress
	if ( ${#xterm_pids} > 0 ) then
		echo "`date`: ${completed_count} jobs completed, ${#xterm_pids} still running..."
		sleep 10
	endif
end

echo ""
echo "=================================================="
echo "All pt_shell jobs completed"
echo "Completed: ${completed_count} jobs"
if ( $failed_count > 0 ) then
	echo "WARNING: ${failed_count} jobs had errors in logs"
endif
echo "=================================================="

# Exit with appropriate code
exit $return_value
