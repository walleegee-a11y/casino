### app_var in UMC 22eHVG_SignOff_Criteria.pdf (v0.1)
# Currently Using S-2021.06-SP5-2 <- OK ! (Use primetime 2019.03-SP3 or later)
set_app_var timing_aocvm_enable_analysis true
set_app_var timing_enable_cumulative_incremental_derate true
set_app_var timing_remove_clock_reconvergence_pessimism true
set_app_var delay_calc_waveform_analysis_mode full_design
set_app_var si_enable_analysis true
#set_operating_conditions -analysis_type on_chip_variation

#-----------------------------------------------------------------------------------------------------------#
#- How to add margin for on-chip variation effects                                                          #
#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#- Setup: Library Corner WCG1/WCG2, RC Corner CMAX/RCMAX                                                    #
#- set_timing_derate -early -cell_delay -increment -(${CLK_VOLT_MARGIN} + ${CLK_TEMP_MARGIN})               #
#- set_timing_derate -early -net_delay (1 - ${SETUP_NET_DERATE})                                            #
#                                                                                                           #
#- Hold: Library Corner WCG1/WCG2, RC Corner CMAX/RCMAX                                                     #
#- set_timing_derate -early -cell_delay -clock -increment -(${CLK_VOLT_MARGIN} + ${CLK_TEMP_MARGIN})        #
#- set_timing_derate -early -cell_delay -data -increment -(${DATA_VOLT_MARGIN} + ${DATA_TEMP_MARGIN})       #
#- set_timing_derate -late -net_delay (1 + ${HOLD_NET_DERATE})                                              #
#                                                                                                           #
#- Hold: Library Corner WCG1/WCG2, RC Corner CMIN/RCMIN                                                     #
#- set_timing_derate -early -cell_delay -clock -increment -(${CLK_VOLT_MARGIN} + ${CLK_TEMP_MARGIN})        #
#- set_timing_derate -early -cell_delay -data -increment -(${DATA_VOLT_MARGIN} + ${DATA_TEMP_MARGIN})       #
#- set_timing_derate -early -net_delay (1 -${HOLD_NET_DERATE})                                              #
#                                                                                                           #
#- Hold: Library Corner BCG1/BCG2, RC Corner CMAX/RCMAX                                                     #
#- set_timing_derate -late -cell_delay -increment (${CLK_VOLT_MARGIN} + ${CLK_TEMP_MARGIN})                 #
#- set_timing_derate -early -net_delay (1 -${HOLD_NET_DERATE})                                              #
#                                                                                                           #
#- Hold: Library Corner BCG1/BCG2, RC Corner CMIN/RCMIN                                                     #
#- set_timing_derate -late -cell_delay -increment (${CLK_VOLT_MARGIN} + ${CLK_TEMP_MARGIN})                 #
#- set_timing_derate -late -net_delay (1 + ${HOLD_NET_DERATE})                                              #
#-----------------------------------------------------------------------------------------------------------#

###
# TODO: need2update -> set variables as array
# Operating Voltage
set WST_OP_VOLT                   0.72 ;# [V]
set BST_OP_VOLT                   0.88 ;# [V]
                                  
# Dynamic IR Drop Value (default: assume 5% to add Volt. variation margin)
set WCG1_DYNAMIC_IR_DROP          5.00 ;# [%]
set WCG2_DYNAMIC_IR_DROP          5.00 ;# [%]
set BCG1_DYNAMIC_IR_DROP          5.00 ;# [%]
set BCG2_DYNAMIC_IR_DROP          5.00 ;# [%]

set WCG1_DYNAMIC_IR_DROP_mV       [expr [expr ${WCG1_DYNAMIC_IR_DROP} / 100] * ${WST_OP_VOLT} * 1000];# [mV]
set WCG2_DYNAMIC_IR_DROP_mV       [expr [expr ${WCG2_DYNAMIC_IR_DROP} / 100] * ${WST_OP_VOLT} * 1000];# [mV]
set BCG1_DYNAMIC_IR_DROP_mV       [expr [expr ${BCG1_DYNAMIC_IR_DROP} / 100] * ${BST_OP_VOLT} * 1000];# [mV]
set BCG2_DYNAMIC_IR_DROP_mV       [expr [expr ${BCG2_DYNAMIC_IR_DROP} / 100] * ${BST_OP_VOLT} * 1000];# [mV]

# WCG1 OCV Margin (Setup/Hold)
set WCG1_HVT_VOLT_MARGIN_PER_mV   0.00144
set WCG1_RVT_VOLT_MARGIN_PER_mV   0.00124
set WCG1_LVT_VOLT_MARGIN_PER_mV   0.00125

set WCG1_HVT_VOLT_MARGIN          [expr ${WCG1_DYNAMIC_IR_DROP_mV} * ${WCG1_HVT_VOLT_MARGIN_PER_mV}]
set WCG1_RVT_VOLT_MARGIN          [expr ${WCG1_DYNAMIC_IR_DROP_mV} * ${WCG1_RVT_VOLT_MARGIN_PER_mV}]
set WCG1_LVT_VOLT_MARGIN          [expr ${WCG1_DYNAMIC_IR_DROP_mV} * ${WCG1_LVT_VOLT_MARGIN_PER_mV}]

set WCG1_HVT_TEMP_MARGIN          0.01370
set WCG1_RVT_TEMP_MARGIN          0.02650
set WCG1_LVT_TEMP_MARGIN          0.02800

# WCG2 OCV Margin (Setup/Hold)
set WCG2_HVT_VOLT_MARGIN_PER_mV   0.00279
set WCG2_RVT_VOLT_MARGIN_PER_mV   0.00215
set WCG2_LVT_VOLT_MARGIN_PER_mV   0.00208

set WCG2_HVT_VOLT_MARGIN          [expr ${WCG2_DYNAMIC_IR_DROP_mV} * ${WCG2_HVT_VOLT_MARGIN_PER_mV}]
set WCG2_RVT_VOLT_MARGIN          [expr ${WCG2_DYNAMIC_IR_DROP_mV} * ${WCG2_RVT_VOLT_MARGIN_PER_mV}]
set WCG2_LVT_VOLT_MARGIN          [expr ${WCG2_DYNAMIC_IR_DROP_mV} * ${WCG2_LVT_VOLT_MARGIN_PER_mV}]

set WCG2_HVT_TEMP_MARGIN          0.02070
set WCG2_RVT_TEMP_MARGIN          0.01400
set WCG2_LVT_TEMP_MARGIN          0.00420

# BCG1 OCV Margin (Hold only)
set BCG1_HVT_VOLT_MARGIN_PER_mV   0.00091
set BCG1_RVT_VOLT_MARGIN_PER_mV   0.00084
set BCG1_LVT_VOLT_MARGIN_PER_mV   0.00075

set BCG1_HVT_VOLT_MARGIN          [expr ${BCG1_DYNAMIC_IR_DROP_mV} * ${BCG1_HVT_VOLT_MARGIN_PER_mV}]
set BCG1_RVT_VOLT_MARGIN          [expr ${BCG1_DYNAMIC_IR_DROP_mV} * ${BCG1_RVT_VOLT_MARGIN_PER_mV}]
set BCG1_LVT_VOLT_MARGIN          [expr ${BCG1_DYNAMIC_IR_DROP_mV} * ${BCG1_LVT_VOLT_MARGIN_PER_mV}]

set BCG1_HVT_TEMP_MARGIN          0.01040
set BCG1_RVT_TEMP_MARGIN          0.02810
set BCG1_LVT_TEMP_MARGIN          0.02350

# BCG2 OCV Margin (Hold only)
set BCG2_HVT_VOLT_MARGIN_PER_mV   0.00070
set BCG2_RVT_VOLT_MARGIN_PER_mV   0.00066
set BCG2_LVT_VOLT_MARGIN_PER_mV   0.00063

set BCG2_HVT_VOLT_MARGIN          [expr ${BCG2_DYNAMIC_IR_DROP_mV} * ${BCG2_HVT_VOLT_MARGIN_PER_mV}]
set BCG2_RVT_VOLT_MARGIN          [expr ${BCG2_DYNAMIC_IR_DROP_mV} * ${BCG2_RVT_VOLT_MARGIN_PER_mV}]
set BCG2_LVT_VOLT_MARGIN          [expr ${BCG2_DYNAMIC_IR_DROP_mV} * ${BCG2_LVT_VOLT_MARGIN_PER_mV}]

set BCG2_HVT_TEMP_MARGIN          0.02690
set BCG2_RVT_TEMP_MARGIN          0.02090
set BCG2_LVT_TEMP_MARGIN          0.01740

# Net OCV Margin
set SETUP_NET_DERATE              0.060
set HOLD_NET_DERATE               0.085


# Read spacial table
# ${DB_PATH               }      ${db_ver             }
# /mnt/data/prjs/ANA6714/db/vers/rtl_0.0_dk_0.0_tag_0.0/pdk/ocv/aocv/
#TODO: exception error
set OCV_FILES [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/pdk/ocv/aocv/${pvt_corner}/*]
foreach ocv_file ${OCV_FILES} {
    echo "read_aocvm ${ocv_file}"
    read_aocvm ${ocv_file}
}

set PRIMITIVE_CELLS [get_cells -quiet -hier -filter "!is_hierarchical && !is_black_box"]
set HVT_CELLS [filter_collection -regexp ${PRIMITIVE_CELLS} {ref_name =~ ".*HM[ABC].*"}]
set RVT_CELLS [filter_collection -regexp ${PRIMITIVE_CELLS} {ref_name =~ ".*NM[ABC].*"}]
set LVT_CELLS [filter_collection -regexp ${PRIMITIVE_CELLS} {ref_name =~ ".*LM[ABC].*"}]

#- WCG1 V-T OCV
	puts "====================================================="
	puts "V-T OCV in ${corner}"
	puts "====================================================="
if {[regexp ss_0p72v_p125c ${corner}]} {
	# Setup : Derate Capture Clock -early
	# Hold  : Derate Launch Clock & Data -early
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG1_HVT_VOLT_MARGIN} + ${WCG1_HVT_TEMP_MARGIN}] ${HVT_CELLS}
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG1_RVT_VOLT_MARGIN} + ${WCG1_RVT_TEMP_MARGIN}] ${RVT_CELLS}
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}] ${LVT_CELLS}
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG1_HVT_VOLT_MARGIN} + ${WCG1_HVT_TEMP_MARGIN}] \${HVT_CELLS}"
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG1_RVT_VOLT_MARGIN} + ${WCG1_RVT_TEMP_MARGIN}] \${RVT_CELLS}"
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}] \${LVT_CELLS}"

#- WCG2 V-T OCV
} elseif {[regexp ss_0p72v_m40c ${corner}]} {
	# Setup : Derate Capture Clock -early
	# Hold  : Derate Launch Clock & Data -early
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG2_HVT_VOLT_MARGIN} + ${WCG2_HVT_TEMP_MARGIN}] ${HVT_CELLS}
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG2_RVT_VOLT_MARGIN} + ${WCG2_RVT_TEMP_MARGIN}] ${RVT_CELLS}
 	set_timing_derate -cell_delay -increment -early -[expr ${WCG2_LVT_VOLT_MARGIN} + ${WCG2_LVT_TEMP_MARGIN}] ${LVT_CELLS}
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG2_HVT_VOLT_MARGIN} + ${WCG2_HVT_TEMP_MARGIN}] \${HVT_CELLS}"
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG2_RVT_VOLT_MARGIN} + ${WCG2_RVT_TEMP_MARGIN}] \${RVT_CELLS}"
	puts "set_timing_derate -cell_delay -increment -early -[expr ${WCG2_LVT_VOLT_MARGIN} + ${WCG2_LVT_TEMP_MARGIN}] \${LVT_CELLS}"

#- BCG1 V-T OCV
} elseif {[regexp ff_0p88v_m40c ${corner}]} {
	# Hold  : Derate Capture Clock -late
 	set_timing_derate -cell_delay -increment -late [expr ${BCG1_HVT_VOLT_MARGIN} + ${BCG1_HVT_TEMP_MARGIN}] ${HVT_CELLS}
 	set_timing_derate -cell_delay -increment -late [expr ${BCG1_RVT_VOLT_MARGIN} + ${BCG1_RVT_TEMP_MARGIN}] ${RVT_CELLS}
 	set_timing_derate -cell_delay -increment -late [expr ${BCG1_LVT_VOLT_MARGIN} + ${BCG1_LVT_TEMP_MARGIN}] ${LVT_CELLS}
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG1_HVT_VOLT_MARGIN} + ${BCG1_HVT_TEMP_MARGIN}] \${HVT_CELLS}"
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG1_RVT_VOLT_MARGIN} + ${BCG1_RVT_TEMP_MARGIN}] \${RVT_CELLS}"
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG1_LVT_VOLT_MARGIN} + ${BCG1_LVT_TEMP_MARGIN}] \${LVT_CELLS}"

#- BCG2 V-T OCV
} elseif {[regexp ff_0p88v_p125c ${corner}]} {
	# Hold  : Derate Capture Clock -late
 	set_timing_derate -cell_delay -increment -late [expr ${BCG2_HVT_VOLT_MARGIN} + ${BCG2_HVT_TEMP_MARGIN}] ${HVT_CELLS}
 	set_timing_derate -cell_delay -increment -late [expr ${BCG2_RVT_VOLT_MARGIN} + ${BCG2_RVT_TEMP_MARGIN}] ${RVT_CELLS}
 	set_timing_derate -cell_delay -increment -late [expr ${BCG2_LVT_VOLT_MARGIN} + ${BCG2_LVT_TEMP_MARGIN}] ${LVT_CELLS}
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG2_HVT_VOLT_MARGIN} + ${BCG2_HVT_TEMP_MARGIN}] \${HVT_CELLS}"
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG2_RVT_VOLT_MARGIN} + ${BCG2_RVT_TEMP_MARGIN}] \${RVT_CELLS}"
    puts "set_timing_derate -cell_delay -increment -late [expr ${BCG2_LVT_VOLT_MARGIN} + ${BCG2_LVT_TEMP_MARGIN}] \${LVT_CELLS}"

#- ERROR !!!
} else {
    puts "====================================================="
    puts "Error: Check \${corner} for add OCV margin - ${corner}"
    puts "====================================================="

}


# TODO: need2update -> set variables as array
#- Print Margin & Net Derate
if {[regexp setup ${corner}]} {
	puts "====================================================="
	puts "V-T OCV on Setup Path in ${corner}"
	puts "====================================================="
	puts "Derate Capture Clock -early on HVT : -[expr ${WCG1_HVT_VOLT_MARGIN} + ${WCG1_HVT_TEMP_MARGIN}]"
	puts "Derate Capture Clock -early on RVT : -[expr ${WCG1_RVT_VOLT_MARGIN} + ${WCG1_RVT_TEMP_MARGIN}]"
	puts "Derate Capture Clock -early on LVT : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts ""

	# Net OCV Derate
	if {[regexp _cmax ${corner}] || [regexp _rcmax ${corner}]} {
		set_timing_derate -early -net_delay [expr 1 - $SETUP_NET_DERATE]
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""

	} elseif {[regexp _cmin ${corner}] || [regexp _rcmin ${corner}]} {
		set_timing_derate -late  -net_delay [expr 1 + $SETUP_NET_DERATE]
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""
	}

} elseif {[regexp hold ${corner}]} {
	puts "====================================================="
	puts "V-T OCV on Hold Path in ${corner}"
	puts "====================================================="
	puts "Derate Launch Clock & Data -early on HVT : -[expr ${WCG1_HVT_VOLT_MARGIN} + ${WCG1_HVT_TEMP_MARGIN}]"
	puts "Derate Launch Clock & Data -early on RVT : -[expr ${WCG1_RVT_VOLT_MARGIN} + ${WCG1_RVT_TEMP_MARGIN}]"
	puts "Derate Launch Clock & Data -early on LVT : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"

	# Net OCV Derate
	if {[regexp _cmax ${corner}] || [regexp _rcmax ${corner}]} {
		set_timing_derate -early -net_delay [expr 1 - $HOLD_NET_DERATE]
	puts ""
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""
	} elseif {[regexp _cmin ${corner}] || [regexp _rcmin ${corner}]} {
		set_timing_derate -late  -net_delay [expr 1 + $HOLD_NET_DERATE]
	puts ""
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""
	}

} else {
	puts "====================================================="
	puts "V-T OCV on Hold Path in ${corner}"
	puts "====================================================="
	puts "Derate Launch Clock & Data -early on HVT : -[expr ${WCG1_HVT_VOLT_MARGIN} + ${WCG1_HVT_TEMP_MARGIN}]"
	puts "Derate Launch Clock & Data -early on RVT : -[expr ${WCG1_RVT_VOLT_MARGIN} + ${WCG1_RVT_TEMP_MARGIN}]"
	puts "Derate Launch Clock & Data -early on LVT : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"

	# Net OCV Derate
	if {[regexp _cmax ${corner}] || [regexp _rcmax ${corner}]} {
		set_timing_derate -early -net_delay [expr 1 - $HOLD_NET_DERATE]
	puts ""
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""

	} elseif {[regexp _cmin ${corner}] || [regexp _rcmin ${corner}]} {
		set_timing_derate -late  -net_delay [expr 1 + $HOLD_NET_DERATE]
	puts ""
	puts "Net Derate -early (cmax) : -[expr ${WCG1_LVT_VOLT_MARGIN} + ${WCG1_LVT_TEMP_MARGIN}]"
	puts "====================================================="
	puts ""

	}
}

# TODO: need2chk
# MEM OCV
    set_timing_derate -cell_delay -increment -late   0.03 [get_cells * -hierarchical -filter "is_memory_cell == true"]
    set_timing_derate -cell_delay -increment -early -0.03 [get_cells * -hierarchical -filter "is_memory_cell == true"]

