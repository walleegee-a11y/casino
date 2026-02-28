#!/usr/bin/tclsh

set STA_DIR [pwd]
set RPT_DIR reports
set LOG_DIR logs

# auto set MODE_LIST
set TARGET_MODES [list func bist misn ssft scap socc]
foreach MODE $TARGET_MODES {
	set MODE [glob -nocomplain -type d $MODE]
	if {$MODE != ""} {
		lappend MODE_LIST $MODE
	}
}

# auto set CORNER_LIST
foreach MODE $MODE_LIST {
	set ALL_DIR [glob -nocomplain -type d $MODE/*]
	foreach DIR $ALL_DIR {
		if { [regexp {\w+_\w+v_\w+c} $DIR] } {
			set CORNER [lindex [split $DIR /] 1]
			lappend CORNER_LIST $CORNER
		}
	}
}
set CORNER_LIST [lsort -uniq -decreasing $CORNER_LIST]

######################################################################
#For except twf corner
set EXCLUDE_CORNER_PATTERNS [list \
    ff_0p99v_p125c_Cworst \
]

set _FILTERED_CORNER_LIST {}
foreach _c $CORNER_LIST {
    set _drop 0
    foreach _pat $EXCLUDE_CORNER_PATTERNS {
        if {[string match $_pat $_c]} {
            set _drop 1
            break
        }
    }
    if {!$_drop} {
        lappend _FILTERED_CORNER_LIST $_c
    }
}
set CORNER_LIST $_FILTERED_CORNER_LIST
unset _FILTERED_CORNER_LIST _drop _c _pat
######################################################################

set VIOLATION_LIST [list SETUP HOLD MTTV MAX_CAP MIN_PERIOD NOISE]
set SCOPE_BOUND_LIST [list 0.000_0.005 0.005_0.010 0.010_0.020 0.020_0.030 0.030_0.050 0.050_0.100 0.100_0.200 0.200_0.300 0.300_0.400 0.400_0.500 0.500_0.600 0.600_0.700 0.700_0.800 0.800_0.900 0.900_1.000 1.000_99999]

set INPUT_to_REG    IN2REG  ;# group_path -name IN2REG -from [all_input]
set REG_to_OUTPUT   REG2OUT ;# group_path -name REG2OUT -to [all_outputs]
set INPUT_to_OUTPUT IN2OUT  ;# group_path -name IN2OUT -from [remove_from_collection [all_inputs] [all_clocks]] -to [all_outputs]

set BOUNDARY_PATH [concat $INPUT_to_REG $REG_to_OUTPUT $INPUT_to_OUTPUT]

# auto select pba mode report
if { [string match "*exhaustive*" [glob -nocomplain -type f */*/$RPT_DIR/all_violators.*.rpt]] } {
	puts "INFO : check pba exhaustive report..."
	set SETUP_RPT      "all_violators.max_delay.exhaustive.rpt"
	set HOLD_RPT       "all_violators.min_delay.exhaustive.rpt"
} elseif { [string match "*path*" [glob -nocomplain -type f */*/$RPT_DIR/all_violators.*.rpt]] } {
	puts "INFO : check pba path report..."
	set SETUP_RPT      "all_violators.max_delay.path.rpt"
	set HOLD_RPT       "all_violators.min_delay.path.rpt"
} else {
	puts "INFO : check gba report..."
	set SETUP_RPT      "all_violators.max_delay.rpt"
	set HOLD_RPT       "all_violators.min_delay.rpt"
}

set MTTV_RPT       "all_violators.max_transition.rpt"
set MAX_CAP_RPT    "all_violators.max_capacitance.rpt"
set MIN_PERIOD_RPT "all_violators.min_period.rpt"
set NOISE_RPT      {gnoise_viols_${CORNER}.rpt}
set LINK_RPT       "link.log"
set SPEF_LOG       "parasitics_command.log"

##################### proc start #####################
proc Setup_Report {MODE CORNER} {
	set VIOLATION SETUP

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global SCOPE_BOUND_LIST
	global SCOPE_COUNT
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]

	global BOUNDARY_PATH
	global BOUNDARY_CHECK

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		set is_boundary 0
		while { [gets $fin line] >= 0 } {
			if { [regexp {max_delay/setup \('(.*)' group\)} $line match path_group] } {
				if { $BOUNDARY_CHECK == 0} {
					set is_boundary [expr [lsearch -exact $BOUNDARY_PATH $path_group] + 1]
				}
			}

			if { [string match "*VIOLATED*" $line] && $is_boundary == 0} {
				set slack [lindex $line 1]

				set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) [format "%.4f" [expr $DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) + $slack]]
				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}

				if { $slack <= 0 && $slack >= -0.005 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.000_0.005) } \
				elseif { $slack < -0.005 && $slack >= -0.010 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.005_0.010) } \
				elseif { $slack < -0.010 && $slack >= -0.020 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.010_0.020) } \
				elseif { $slack < -0.020 && $slack >= -0.030 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.020_0.030) } \
				elseif { $slack < -0.030 && $slack >= -0.050 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.030_0.050) } \
				elseif { $slack < -0.050 && $slack >= -0.100 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.050_0.100) } \
				elseif { $slack < -0.100 && $slack >= -0.200 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.100_0.200) } \
				elseif { $slack < -0.200 && $slack >= -0.300 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.200_0.300) } \
				elseif { $slack < -0.300 && $slack >= -0.400 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.300_0.400) } \
				elseif { $slack < -0.400 && $slack >= -0.500 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.400_0.500) } \
				elseif { $slack < -0.500 && $slack >= -0.600 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.500_0.600) } \
				elseif { $slack < -0.600 && $slack >= -0.700 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.600_0.700) } \
				elseif { $slack < -0.700 && $slack >= -0.800 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.700_0.800) } \
				elseif { $slack < -0.800 && $slack >= -0.900 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.800_0.900) } \
				elseif { $slack < -0.900 && $slack >= -1.000 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.900_1.000) } \
				elseif { $slack < -1.000 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.1.000_99999) }
			}
		}
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) [format "%.2f" $DATA_LIST($MODE.$CORNER.$VIOLATION.TNS)]
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
		foreach SCOPE_BOUND $SCOPE_BOUND_LIST {
			set SCOPE_COUNT($MODE.$CORNER.$VIOLATION.$SCOPE_BOUND) "-"
		}
	}
}

proc Hold_Report {MODE CORNER} {
	set VIOLATION HOLD

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global SCOPE_BOUND_LIST
	global SCOPE_COUNT
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]

	global BOUNDARY_PATH
	global BOUNDARY_CHECK

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		set is_boundary 0
		while { [gets $fin line] >= 0 } {
			if { [regexp {min_delay/hold \('(.*)' group\)} $line match path_group] } {
				if { $BOUNDARY_CHECK == 0} {
					set is_boundary [expr [lsearch -exact $BOUNDARY_PATH $path_group] + 1]
				}
			}

			if { [string match "*VIOLATED*" $line] && $is_boundary == 0} {
				set slack [lindex $line 1]

				set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) [format "%.4f" [expr $DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) + $slack]]
				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}

				if { $slack <= 0 && $slack >= -0.005 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.000_0.005) } \
				elseif { $slack < -0.005 && $slack >= -0.010 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.005_0.010) } \
				elseif { $slack < -0.010 && $slack >= -0.020 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.010_0.020) } \
				elseif { $slack < -0.020 && $slack >= -0.030 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.020_0.030) } \
				elseif { $slack < -0.030 && $slack >= -0.050 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.030_0.050) } \
				elseif { $slack < -0.050 && $slack >= -0.100 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.050_0.100) } \
				elseif { $slack < -0.100 && $slack >= -0.200 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.100_0.200) } \
				elseif { $slack < -0.200 && $slack >= -0.300 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.200_0.300) } \
				elseif { $slack < -0.300 && $slack >= -0.400 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.300_0.400) } \
				elseif { $slack < -0.400 && $slack >= -0.500 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.400_0.500) } \
				elseif { $slack < -0.500 && $slack >= -0.600 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.500_0.600) } \
				elseif { $slack < -0.600 && $slack >= -0.700 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.600_0.700) } \
				elseif { $slack < -0.700 && $slack >= -0.800 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.700_0.800) } \
				elseif { $slack < -0.800 && $slack >= -0.900 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.800_0.900) } \
				elseif { $slack < -0.900 && $slack >= -1.000 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.0.900_1.000) } \
				elseif { $slack < -1.000 } { incr SCOPE_COUNT($MODE.$CORNER.$VIOLATION.1.000_99999) }
			}
		}
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) [format "%.2f" $DATA_LIST($MODE.$CORNER.$VIOLATION.TNS)]
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
		foreach SCOPE_BOUND $SCOPE_BOUND_LIST {
			set SCOPE_COUNT($MODE.$CORNER.$VIOLATION.$SCOPE_BOUND) "-"
		}
	}
}

proc Mttv_Report {MODE CORNER} {
	set VIOLATION MTTV

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [string match "*VIOLATED*" $line] } {
				set slack [lindex $line 3]

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

proc MaxCap_Report {MODE CORNER} {
	set VIOLATION MAX_CAP

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [string match "*VIOLATED*" $line] } {
				set slack [lindex $line 3]

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

proc MinPeriod_Report {MODE CORNER} {
	set VIOLATION MIN_PERIOD

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [string match "*VIOLATED*" $line] } {
				set slack [lindex $line 5]

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

proc Noise_Report {MODE CORNER} {
	set VIOLATION NOISE

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global ${VIOLATION}_RPT
	set RPT [subst [subst $${VIOLATION}_RPT]]

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT_DIR}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [regexp { (-\d+.\d+)} $line match slack] } {

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
				if { $slack < $DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) } {
					set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) $slack
				}
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) "-"
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

proc Link_Report {MODE CORNER} {
	set VIOLATION LINK

	global STA_DIR
	global RPT_DIR
	global LOG_DIR
	global DATA_LIST
	global ${VIOLATION}_RPT
	set RPT [subst $${VIOLATION}_RPT]
	set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) 0

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${LOG_DIR}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${LOG_DIR}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [regexp {^Error|^Warning.*resolve} $line match] } {

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

proc Parasitic_log {MODE CORNER} {
	set VIOLATION SPEF

	global STA_DIR
	global RPT_DIR
	global DATA_LIST
	global ${VIOLATION}_LOG
	set RPT [subst $${VIOLATION}_LOG]
	set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) 0

	if { [file exists ${STA_DIR}/${MODE}/${CORNER}/${RPT}] } {
		set fin [open ${STA_DIR}/${MODE}/${CORNER}/${RPT} r]
		while { [gets $fin line] >= 0 } {
			if { [regexp {^Error} $line match] } {

				incr DATA_LIST($MODE.$CORNER.$VIOLATION.NUM)
			}
		}
		close $fin
	} else {
		set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) "-"
	}
}

##################### proc end #####################

foreach BOUNDARY_CHECK {0 1} RPT_NAME {timing_summary_r2r.rpt timing_summary.rpt} {
	foreach MODE $MODE_LIST {
		foreach CORNER $CORNER_LIST {
			foreach VIOLATION $VIOLATION_LIST {
				set DATA_LIST($MODE.$CORNER.$VIOLATION.WNS) 0
				set DATA_LIST($MODE.$CORNER.$VIOLATION.TNS) 0
				set DATA_LIST($MODE.$CORNER.$VIOLATION.NUM) 0
				if { [regexp {SETUP|HOLD} $VIOLATION] } {
					foreach SCOPE_BOUND $SCOPE_BOUND_LIST {
						set SCOPE_COUNT($MODE.$CORNER.$VIOLATION.$SCOPE_BOUND) 0
					}
				}
			}
		}
	}
	
	set fout [open ./$RPT_NAME w]
	puts $fout "# Report date : [clock format [clock second] -format %Y/%m/%d\ %H:%M]"
	puts $fout "# STA Run_Path : $STA_DIR"
	puts $fout ""
	puts $fout "/[string repeat = 245]\\"
	puts $fout "| [format "%*s" -43 ""] | [format "%*s" -34 "              SETUP"] | [format "%*s" -34 "              HOLD"] | [format "%*s" -22 "         MTTV"] | [format "%*s" -22 "        MAX_CAP"] | [format "%*s" -22 "      MIN_PERIOD"] | [format "%*s" -22 "        NOISE"] | [format "%*s" -10 "LINK_CHK"] | [format "%*s" -10 "SPEF_Error"] |"
	puts $fout "| [format "%*s" -8 "MODE"] [format "%*s" -35 "CORNER"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "TNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "TNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "NUM"]| [format "%*s" -10 "NUM"] |"
	puts $fout "|---------------------------------------------+------------------------------------+------------------------------------+------------------------+------------------------+------------------------+------------------------+------------+------------|"
	
	foreach MODE $MODE_LIST {
		foreach CORNER $CORNER_LIST {
			Setup_Report     $MODE $CORNER
			Hold_Report      $MODE $CORNER
			Mttv_Report      $MODE $CORNER
			MaxCap_Report    $MODE $CORNER
			MinPeriod_Report $MODE $CORNER
			Noise_Report     $MODE $CORNER
			Link_Report      $MODE $CORNER
			Parasitic_log    $MODE $CORNER
	
			puts $fout "| [format "%*s" -8 ${MODE}] [format "%*s" -35 ${CORNER}]| [format "%*s" -11 $DATA_LIST($MODE.$CORNER.SETUP.WNS)     ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.SETUP.TNS)     ] [format "%*s" -11    $DATA_LIST($MODE.$CORNER.SETUP.NUM)      ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.HOLD.WNS)      ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.HOLD.TNS)      ] [format "%*s" -11    $DATA_LIST($MODE.$CORNER.HOLD.NUM)       ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MTTV.WNS)      ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MTTV.NUM)      ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MAX_CAP.WNS)   ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MAX_CAP.NUM)   ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MIN_PERIOD.WNS)] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MIN_PERIOD.NUM)]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.NOISE.WNS)     ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.NOISE.NUM)     ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.LINK.NUM)       ]|\
	                                                                              [format "%*s" -11 $DATA_LIST($MODE.$CORNER.SPEF.NUM)      ]|"
		}
		if { $MODE == [lindex $MODE_LIST [expr [llength $MODE_LIST] -1]] } {
		} else {
			puts $fout "|---------------------------------------------+------------------------------------+------------------------------------+------------------------+------------------------+------------------------+------------------------+------------+------------|"
		}
	}
	
	puts $fout "\\[string repeat = 245]/"
	puts $fout ""
	puts $fout "[string repeat # [expr 41 * [llength $CORNER_LIST]]]"
	puts $fout ""
	
	foreach MODE $MODE_LIST {
		puts $fout "[string repeat "/=====================================\\  " [llength $CORNER_LIST]]"
		foreach CORNER $CORNER_LIST {
			lappend corners "| [format "%*s" -35 ${MODE}.${CORNER}] | "
		}
	
		puts $fout [regsub -all {\}|\{} $corners {}]
		puts $fout "[string repeat "|=====================================|  " [llength $CORNER_LIST]]"
		puts $fout "[string repeat "| [format "%*s" -11 "   Slack"] | [format "%*s" -9 "SETUP"] | [format "%*s" -9 "HOLD"] |  " [llength $CORNER_LIST]]"
		puts $fout "[string repeat "|[string repeat - 13]|[string repeat - 11]|[string repeat - 11]|  " [llength $CORNER_LIST]]"
		foreach SCOPE_BOUND $SCOPE_BOUND_LIST {
			set output_data [list ]
			foreach CORNER $CORNER_LIST {
				set SETUP_DATA $SCOPE_COUNT($MODE.$CORNER.SETUP.$SCOPE_BOUND)
				set HOLD_DATA  $SCOPE_COUNT($MODE.$CORNER.HOLD.$SCOPE_BOUND)
				lappend output_data "| [format %*s -9 $SCOPE_BOUND] | [format %*s -9 $SETUP_DATA] | [format %*s -9 $HOLD_DATA] | "
			}
			puts $fout [regsub -all {\}|\{} $output_data {}]
			unset output_data
		}
		puts $fout "[string repeat "\\=====================================/  " [llength $CORNER_LIST]]"
		puts $fout ""
		unset corners
	}
	puts $fout "[string repeat # [expr 41 * [llength $CORNER_LIST]]]"
}
### # timing dominant corner
### puts $fout "# timing dominant corners"
### puts $fout "[string repeat # [expr 41 * [llength $CORNER_LIST]]]"
### 
### set CORNER_LIST [list \
### 				FUNC_cworst_CCworst_T_ssgnpm40c \
### 				FUNC_rcworst_CCworst_T_ssgnp125c \
### 				FUNC_cbest_CCbest_ffgnp125c \
### 				FUNC_cworst_CCworst_ffgnp125c \
### 				FUNC_rcbest_CCbest_ffgnp125c \
### 				FUNC_rcworst_CCworst_ffgnp125c \
### 				FUNC_rcworst_CCworst_ffgnpm40c \
### ]
### 
### puts $fout "/[string repeat = 219]\\"
### puts $fout "| [format "%*s" -43 ""] | [format "%*s" -34 "              SETUP"] | [format "%*s" -34 "              HOLD"] | [format "%*s" -22 "         MTTV"] | [format "%*s" -22 "        MAX_CAP"] | [format "%*s" -22 "      MIN_PERIOD"] | [format "%*s" -22 "        NOISE"] |"
### puts $fout "| [format "%*s" -8 "MODE"] [format "%*s" -35 "CORNER"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "TNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "TNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]| [format "%*s" -11 "WNS"] [format "%*s" -11 "NUM"]|"
### puts $fout "|---------------------------------------------+------------------------------------+------------------------------------+------------------------+------------------------+------------------------+------------------------+------------+------------|"
### 
### foreach MODE $MODE_LIST {
### 	foreach CORNER $CORNER_LIST {
### 		puts $fout "| [format "%*s" -8 FUNC] [format "%*s" -35 [regsub "FUNC_" ${CORNER} ""]]| [format "%*s" -11 $DATA_LIST($MODE.$CORNER.SETUP.WNS)     ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.SETUP.TNS)     ] [format "%*s" -11    $DATA_LIST($MODE.$CORNER.SETUP.NUM)      ]|\
###                                                                                                [format "%*s" -11 $DATA_LIST($MODE.$CORNER.HOLD.WNS)      ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.HOLD.TNS)      ] [format "%*s" -11    $DATA_LIST($MODE.$CORNER.HOLD.NUM)       ]|\
###                                                                                                [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MTTV.WNS)      ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MTTV.NUM)      ]|\
###                                                                                                [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MAX_CAP.WNS)   ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MAX_CAP.NUM)   ]|\
###                                                                                                [format "%*s" -11 $DATA_LIST($MODE.$CORNER.MIN_PERIOD.WNS)] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.MIN_PERIOD.NUM)]|\
###                                                                                                [format "%*s" -11 $DATA_LIST($MODE.$CORNER.NOISE.WNS)     ] [format "%*s" -11  $DATA_LIST($MODE.$CORNER.NOISE.NUM)     ]|"
### 	}
### 	if { $MODE == [lindex $MODE_LIST [expr [llength $MODE_LIST] -1]] } {
### 	} else {
### 		puts $fout "|---------------------------------------------+------------------------------------+------------------------------------+------------------------+------------------------+------------------------+------------------------+------------+------------|"
### 	}
### }
### puts $fout "\\[string repeat = 219]/"
### puts $fout ""
### 
### close $fout
### 
### puts DONE
