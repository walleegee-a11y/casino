###############################################
#- Start  
###############################################
sh date
sh touch LDRC_DC_START
###############################################
#- Set Variables
###############################################
# #- from [pwd]
# #    0 9   8    7    6       5                  4          3                           2    1                                0
# # ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/00_dc_init-00_PD_RUN-fe00_te00_pv00/lec_fm
# set prj_name   [lindex [split [pwd] "/"] end-6]
# set top_design [lindex [split [pwd] "/"] end-4]
# set ws         [lindex [split [pwd] "/"] end-3]
# set run_ver    [lindex [split [pwd] "/"] end-1]
# set stage      [lindex [split [pwd] "/"] end]
# 
# set RUN_PATH   [regsub {/lec_fm.*} [pwd] ""]
# 
# #- from ${ws}
# regexp {^([^_]+)___(.*)$} $ws match role db_ver
# set design_ver  [lindex [split ${db_ver} _] 0] ;# rtl-0.0
# set dk_ver      [lindex [split ${db_ver} _] 1] ;# dk-0.0
# set dk_ver_tag  [lindex [split ${db_ver} _] 2] ;# tag-0.0
# 
# #- from ${run_ver}
# set pi_ver      [lindex [split ${run_ver} -] 0] ;# < 00_dc_init >
# set pd_ver      [lindex [split ${run_ver} -] 1] ;# < 00_PD_RUN >
# set eco_num     [lindex [split ${run_ver} -] 2] ;# < fe00_te00_pv00 >
# 
#     if { ${eco_num} == "" }                      { set pre_post "pre" } \
# elseif {[string match "fe*_te*_pv*" ${eco_num}]} { set pre_post "post" } \
# else   { echo "ERROR : Need to check run_ver, ${run_ver}" ; exit }
# 
# #TODO: multi-level LEC
# #- Design Variables
# set top_name       ${prj_name}
# set all_blks       $env(all_blks)
# 
# #- PATH setup
# set PRJ_HOME        "$env(prj_base)/${prj_name}"
# eval regexp {^(.*?)/${prj_name}} [pwd] PRJ_HOME prj_base
# set DB_PATH           "${PRJ_HOME}/db"
# 
# set OUTFEED_PATH      "${PRJ_HOME}/outfeeds"
# set PI_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pi___${db_ver}/${run_ver}"
# set PD_OUT_PATH       "${PRJ_HOME}/outfeeds/${top_design}/pd___${db_ver}/${run_ver}"
# set PD_DONE_FILE      "${PD_OUT_PATH}/SMC.done"
# 
# set COMMON_PATH       "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/common"
# set RUN_COMMON_PATH   "${PRJ_HOME}/works_$env(USER)/${top_design}/${ws}/runs/${run_ver}/common"
source -e -v $env(COMMON_PATH)/globals/pi/get_pi_vars.tcl

##################################################
# ${prj_name}.ovars.tcl
##################################################
source -e -v ${RUN_COMMON_PATH}/user_define/${prj_name}_ovars.tcl

set_app_var hdlin_check_no_latch true
set_app_var power_cg_auto_identify true
set_app_var report_default_significant_digits 4
set_app_var case_analysis_with_logic_constants true
set_app_var write_name_nets_same_as_ports true
set_app_var verilogout_no_tri true
set_app_var hdlin_shorten_long_module_name ture

##########################################################
# read design
##########################################################
# TODO: flatten LDRC
if { ${pre_post} == "pre" } {

	# RTL
	# TODO: syn run_ver?
	if { [regexp rtl- ${design_ver}] } {
		# DC
		if { [regexp _dc_ ${run_ver}] && ![regexp _dcg_ ${run_ver}] } {
			set netlist ${RUN_PATH}/syn_dc/results/${top_design}_syn.v

		# DCG
		} elseif { [regexp _dcg_ ${run_ver}] } {
			set netlist ${RUN_PATH}/syn_dc/results/${top_design}_syn.v

		} else {
			echo "ERROR : The netlist for performing LDRC is parsed based on $\{run_ver\}"
			echo "        $\{run_ver\} should indicate whether the synthesis was done with \"dc\" or \"dcg\"."
			echo "        ex) 01_dc_for-gen-def"
			echo "        ex) 02_dcg_def-v01"
			sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
			exit

		}

	# TODO: netlist name?
	} elseif { [regexp dc- ${design_ver}] } {
		set netlist ${DB_PATH}/vers/${db_ver}/design/v/${top_design}_syn.v

	} elseif { [regexp dcg- ${design_ver}] } {
		set netlist ${DB_PATH}/vers/${db_ver}/design/v/${top_design}_syn.v
	
    } else {
        echo "ERROR : need2chk $\{design_ver\}"
        sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
        exit

    }

} elseif { ${pre_post} == "post" } {
    set netlist ${PD_OUT_PATH}/netlist/${top_design}.v
}

if { [file exist ${netlist}] } {
    echo "info : net - ${netlist}"
	echo "netlist : ${netlist}" > net_info
    read_verilog ${netlist}

} else {
    echo "ERROR : NO netlist - ${netlist}"
    sh touch :ABNORMAL_ERROR_NO_NETLIST
    exit

}


##########################################################
#- link design
##########################################################
set_app_var link_library [list *]
set std_list [glob -nocomplain -type f ${DB_PATH}/std/db/${ovars(pi,default_pvt)}/*]
foreach lib $std_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set mem_list [glob -nocomplain -type f ${DB_PATH}/mem/db/${ovars(pi,default_pvt)}/*]
foreach lib $mem_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set io_ip_list [glob -nocomplain -type f ${DB_PATH}/io_ip/db/${ovars(pi,default_pvt)}/*]
foreach lib $io_ip_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

link > logs/link.log
current_design ${top_design}

##########################################################
#- uniquify
##########################################################
if { [regexp dc- ${design_ver}] || [regexp dcg- ${design_ver}] } {
    set_app_var uniquify_naming_style "${top_design}_%s_%d"
    uniquify

}

##########################################################
#- check_design
##########################################################
redirect -tee ./reports/check_design.rpt {
	check_design

}

##########################################################
#- write netlist
##########################################################
#TODO: net name?
if { [regexp dc- ${design_ver}] } {
    write -hierarchy -format verilog -output ./netlist/${top_design}_dc.v

} elseif { [regexp dcg- ${design_ver}] } {
    write -hierarchy -format verilog -output ./netlist/${top_design}_dcg.v
}

sh touch LDRC_DC_END

exit
