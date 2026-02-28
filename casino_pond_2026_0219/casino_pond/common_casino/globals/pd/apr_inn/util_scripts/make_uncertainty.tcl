
if {[regexp {place} $stage]} {
    set UNCERT_VAR $PLACE_UNCERT_VAR
} elseif {[regexp {cts} $stage]} {
        set UNCERT_VAR $CTS_UNCERT_VAR
} elseif {[regexp {route} $stage]} {
        set UNCERT_VAR $ROUTE_UNCERT_VAR
} 
exec mkdir -p tempfiles

set viewLists $setup_views

foreach view $viewLists {

report_clocks -view $view > ./tempfiles/clocks_${view}.rpt

set FILE_IN  [open ./tempfiles/clocks_${view}.rpt r]
while {[gets $FILE_IN line] >= 0} {
    if {[regexp {\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+\S+\s+(n|y)\s+(n|y)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+} $line - CLOCK_NAME MASTER_NAME - -  DIV]} {
        set MASTER($CLOCK_NAME) "$MASTER_NAME"
        set G_DIV($CLOCK_NAME)  "${DIV}.000"
    } elseif {[regexp {\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+\S+\s+\S+\s+(n|y)\s+(n|y)\s+} $line - CLOCK_NAME PERIOD]} {
        set MASTER_PERIOD($CLOCK_NAME) "$PERIOD"
    }
}
close $FILE_IN


set FILE_IN  [open ./tempfiles/clocks_${view}.rpt r]
set FILE_OUT [open ./tempfiles/${stage}_${view}_uncertainty.tcl w]

while {[gets $FILE_IN line] >= 0} {
    if {[regexp {\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+\S+\s+(n|y)\s+(n|y)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+} $line - CLOCK_NAME MASTER_NAME - -  DIV]} {
        if {$MASTER_NAME == "-"} {
            break
        } else {
            set i "0"
            set F_DIV "1.000"
            while {$i < 10} {
                if {[array names MASTER_PERIOD $MASTER_NAME] != ""} {
                    #puts "MY_CLOCK : $CLOCK_NAME            MASTER : $MASTER_NAME"

                    set F_DIV "$F_DIV / ($G_DIV($CLOCK_NAME))"
                    set PERIOD [expr $MASTER_PERIOD($MASTER_NAME) / ($F_DIV)]
                    set UNCERTAINTY [expr $PERIOD * $UNCERT_VAR]
                    if {$UNCERTAINTY > $UNCERT_MAX_BOUND} {
                        set UNCERTAINTY $UNCERT_MAX_BOUND
                    }
                    puts $FILE_OUT "## CLOCK_NAME : $CLOCK_NAME       PERIOD : $PERIOD          - MASTER : $MASTER_NAME"
                    puts $FILE_OUT  "set_clock_uncertainty -setup $UNCERTAINTY $CLOCK_NAME"
                    break
                } else {
                    if {$MASTER_NAME == "-"} {
                        break
                    } else {
                        puts "MY_CLOCK : $CLOCK_NAME            MASTER : $MASTER_NAME"
                        set MASTER_NAME "$MASTER($MASTER_NAME)"
                        set F_DIV "$F_DIV / ( $G_DIV($CLOCK_NAME) )"
                    }
                    
                }
                incr i
            }
        }
        } elseif {[regexp {\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+\S+\s+\S+\s+(n|y)\s+(n|y)\s+} $line - CLOCK_NAME PERIOD]} {
        #set MASTER_PERIOD($CLOCK_NAME) "$PERIOD"
        set UNCERTAINTY [expr $PERIOD * $UNCERT_VAR]
        if {$UNCERTAINTY > $UNCERT_MAX_BOUND} {
            set UNCERTAINTY $UNCERT_MAX_BOUND
        }
                puts $FILE_OUT "## CLOCK_NAME : $CLOCK_NAME       PERIOD : $PERIOD"
                puts $FILE_OUT  "set_clock_uncertainty -setup $UNCERTAINTY $CLOCK_NAME"
        }
}
close $FILE_IN    


puts $FILE_OUT ""
puts $FILE_OUT "## HOLD"
# if {$PROCESS <= "16"} {
#         puts $FILE_OUT "set_clock_uncertainty -hold  0.005 \[all_clocks\]"
# } else {
#         puts $FILE_OUT "set_clock_uncertainty -hold  0.040 \[all_clocks\]"
# }


close $FILE_OUT
#exec rm ./tempfiles/clocks.rpt
set_interactive_constraint_modes [lindex [split $view _] 0]
source ./tempfiles/${stage}_${view}_uncertainty.tcl
Puts "UNCERTAINTY :: set_interactive_constraint_modes [lindex [split $view _] 0]"
Puts "UNCERTAINTY :: source ./tempfiles/${stage}_${view}_uncertainty.tcl"


}
set_interactive_constraint_modes [all_constraint_modes -active]

