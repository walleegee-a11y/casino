###############################################
#- Start  
###############################################
sh date
sh touch LDRC_DC_START
###############################################
#- Set Variables
###############################################

source -e -v $env(RUN_COMMON_PATH)/globals/pi/get_pi_vars.tcl
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
#- link design
##########################################################
set_app_var link_library [list *]
set std_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/std/db/${ovars(pi,default_pvt)}/*]
foreach lib $std_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set mem_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/mem/db/${ovars(pi,default_pvt)}/*]
foreach lib $mem_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set io_ip_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/io_ip/db/${ovars(pi,default_pvt)}/*]
foreach lib $io_ip_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

##########################################################
# read design
##########################################################
# TODO: flatten LDRC
if { ${pre_post} == "pre" } {

	# RTL
	# TODO: syn run_ver?
	if { [regexp rtl- ${design_ver}] } {
				set netlist ${RUN_PATH}/syn_dc/results/${top_design}_syn.v
		} else {
			echo "ERROR : The netlist for performing LDRC is parsed based on $\{run_ver\}"
			echo "        $\{run_ver\} should indicate whether the synthesis was done with \"dc\" or \"dcg\"."
			echo "        ex) 01_dc_for-gen-def"
			echo "        ex) 02_dcg_def-v01"
			sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_run_ver
	#		exit

	# TODO: netlist name?
	} 
	if { [regexp net- ${design_ver}] } {
		set netlist ${DB_PATH}/vers/${db_ver}/design/v/${top_design}.v

	} else {
        echo "ERROR : need2chk $\{design_ver\}"
        sh touch :ABNORMAL_ERROR_PRE_NETLIST-need2chk_design_ver
   #     exit

    }

} elseif { ${pre_post} == "post" } {
    set netlist ${PD_OUT_PATH}/netlist/${top_design}.v
}

if { [file exist ${netlist}] } {
    echo "info : net - ${netlist}"
	echo "netlist : ${netlist}" > netlist_info
    read_verilog -netlist ${netlist}

} else {
    echo "ERROR : NO netlist - ${netlist}"
    sh touch :ABNORMAL_ERROR_NO_NETLIST
    exit

}
current_design ${top_design}
link > logs/link.log
##########################################################
#- uniquify
##########################################################
#if { [regexp net- ${design_ver}] } {
#    set_app_var uniquify_naming_style "${top_design}_%s_%d"
#    uniquify
#
#}

##########################################################
#- check_design
##########################################################
redirect -tee ./reports/check_design.rpt {
	check_design -multiple_designs

}

##########################################################
#- write netlist
##########################################################
#TODO: net name?
write -hierarchy -format verilog -output ./netlist/${top_design}.v

sh touch LDRC_DC_END

#exit
