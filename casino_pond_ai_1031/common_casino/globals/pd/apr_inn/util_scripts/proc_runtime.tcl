
##########################################
##		Timer			##
##########################################
proc StartTimer {stage} {
	global CpuTime RealTime RuntimeRpt
	set RealTime($stage) [clock seconds]
	set CpuTime($stage) [timestamp]
	set timestamp [clock format [clock scan now] -format "%Y-%m-%d_%H-%M"]
	redirect -file  $RuntimeRpt -append { echo [format "%-32s %-32s" "$stage START" "$timestamp"] }
	return 1
}

proc GetResources {stage} {
        global CpuTime RealTime

        set elapsed_cputime  [ConvertTime [expr [timestamp]  - $CpuTime($stage)]]
        set elapsed_realtime [ConvertTime [expr [clock seconds] - $RealTime($stage)]]
        set time_list [list $elapsed_cputime $elapsed_realtime ]
 
        return $time_list
}
                  
proc ReportResourceUtil {stage} {
        global RuntimeRpt CpuTime RealTime

        if { [info exists CpuTime($stage)] } { 
                set util_list [GetResources $stage]
                set elapsed_cputime [lindex $util_list 0]
                set elapsed_realtime [lindex $util_list 1]
                set timestamp [clock format [clock scan now] -format "%Y-%m-%d_%H-%M"]
                redirect -file  $RuntimeRpt -append { echo [format "%-32s %-32s %-20s %-20s " "$stage END" "$timestamp" "$elapsed_cputime" "$elapsed_realtime"  ] }
        } else {
                redirect -file  $RuntimeRpt -append { echo [format "%-32s %-32s %-20s %-20s " "$stage" "NA" "NA" "NA" ] }
        }
}
 
proc CreateRuntimeRpt {} {
	global step RuntimeRpt
	 
	if {![file exists report]} {
		exec mkdir report
	}
	set RuntimeRpt "report/runtime\.rpt"
	if {![file exists $RuntimeRpt]} {
		redirect -file  $RuntimeRpt -append { echo [format "%-32s %-32s %-20s %-20s\n%-32s %-32s %-20s %-20s" "STAGE" "TIMESTAMP" "CPUTIME" "REALTIME"  "--------" "--------" "--------" "---------" ] }
	}
 
}
proc ConvertTime {timeInSec} {
        # to take care of floating input numbers
        if { [regexp {^[0-9]+\.[0-9]*} $timeInSec] } {
                 set timeInSec [lindex [split $timeInSec .] 0]
        } elseif { [regexp {^\.[0-9]+} $timeInSec] } {
                 return "00h:00m:00s"
        }

        # logic to caluculate the hours and minutes and seconds
        set sec $timeInSec
        set hr [expr $timeInSec/3600]
        set min [expr $timeInSec/60]
        set secMod [expr $timeInSec%60]
        if {[string length $sec] == 1} {
                set sec 0$sec
        }
        if {[string length $secMod] == 1} {
                set secMod 0$secMod
        }
        if {[string length $min] == 1} {
                set min 0$min
        }
        if {$hr > 0} {
                  set minRemain [expr ($sec - ($hr*3600))/60]
                  if {[string length $minRemain] == 1} {
                          set minRemain 0$minRemain
                  }
                  set days [expr $hr/24]
                  if {[string length $days] == 1} {
                          set days 0$days
                  }
                  set hrsRemain [expr $hr%24]
                  if {[string length $hrsRemain] == 1} {
                          set hrsRemain 0$hrsRemain
                  }
                  return "$days\d:$hrsRemain\h:$minRemain\m:$secMod\s"
        } elseif {$min > 0} {
                  return "00\d:00\h:$min\m:$secMod\s"
        } else {
                  return "00\d:00\h:00\m:$sec\s"
        }
}
