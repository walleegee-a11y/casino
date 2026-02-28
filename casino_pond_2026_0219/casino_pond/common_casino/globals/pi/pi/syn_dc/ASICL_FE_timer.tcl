##########################################
##		Timer			##
##########################################
proc GetDate {step} {
	global ClockSeconds
	global StartClockSeconds
	if ![info exist ClockSeconds] {
		set ClockSeconds [clock seconds]
		set StartClockSeconds [clock seconds]
		set CurDate [sh date +%y/%m/%d_%H:%M]

		echo "Host_Name : [sh hostname]" >> runtime.rpt
		echo [format "%-32s %-32s %-20s\n%-32s %-32s %-20s" "STAGE" "TIMESTAMP" "REALTIME"  "--------" "--------" "---------" ] >> runtime.rpt
		echo [format "%-32s %-32s" "$step" "$CurDate"] >> runtime.rpt
	} else {
		set CurTime [clock seconds]
		set RunTime [expr $CurTime - $ClockSeconds]
		set ClockSeconds [clock seconds]
		set RunTime_Cvt [AL_ConvertTime $RunTime]
		set CurDate [sh date +%y/%m/%d_%H:%M]

		echo [format "%-32s %-32s %-20s" "$step" "$CurDate" "$RunTime_Cvt"] >> runtime.rpt
	}

}

proc GetTotalRunTime {step} {
	global ClockSeconds
	global StartClockSeconds

	set CurTime [clock seconds]
	set TotalRunTime [expr $CurTime - $StartClockSeconds]
	set RunTime_Cvt [AL_ConvertTime $TotalRunTime]
	set CurDate [sh date +%y/%m/%d_%H:%M]

	echo "=====================================================================================" >> runtime.rpt
	echo [format "%-32s %-32s %-20s" "$step" "$CurDate" "$RunTime_Cvt"] >> runtime.rpt

}


proc AL_ConvertTime {timeInSec} {
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




