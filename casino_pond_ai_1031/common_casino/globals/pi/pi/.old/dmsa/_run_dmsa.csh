#! /bin/csh -f

#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/sta_pt/dmsa
setenv prj_name   `pwd  | awk -F / '{print $(NF-7)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-5)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-4)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-2)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv run_dir    `pwd | sed 's;/sta_pt.*;;g'`
setenv prj_home   `pwd | sed 's;/works_.*;;g'`

#- generate ${prj_name}.${stage}.ovars.csh
${prj_home}/works_${USER}/${top_design}/${ws}/common/globals/pi/get_ovars.tcl ;# execute TCL file
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

#- setup ${dmsa_dir}
set cur_time = `date +%y%m%d_%H%M`
if ${dmsa_teco_physical_aware} then
	set log_or_phy = "physical"
else
    set log_or_phy = "logical"
endif

if ${dmsa_debug} then
	set dmsa_dir = "dmsa_debug_${log_or_phy}_${cur_time}"
else
	set dmsa_dir = "dmsa_${log_or_phy}_${cur_time}"
endif

if (-e ./${dmsa_dir}) then
	\rm -rf ${dmsa_dir}
endif
mkdir ${dmsa_dir}

\cp ${prj_home}/works_${USER}/${top_design}/${ws}/common/globals/pi/dmsa/run_dmsa.tcl ${dmsa_dir}
if (-e ./pre_source.tcl) then
	\cp pre_source.tcl ${dmsa_dir}
endif

mv ./${prj_name}.${stage}.ovars.csh ${dmsa_dir}
cd ${dmsa_dir}
#pt_shell -multi -f ./run_dmsa.tcl |& tee ./dmsa_master_eco.log
xterm -T ${dmsa_dir} -e pt_shell -multi -f ./run_dmsa.tcl  -output_log_file ./dmsa_master_eco.log &
