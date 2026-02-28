#!/usr/bin/tclsh

set TARGET_DIR  [pwd]
set OUTPUT_FILE "${TARGET_DIR}/merged_skew_final.rpt"

puts "Info: Searching for reports in $TARGET_DIR ..."

set ORDERED_CORNERS {
    "ss_0p72v_p125c_rcmax_setup"
    "ss_0p72v_m40c_cmax_setup"
    "ss_0p72v_p125c_rcmax_hold"
    "ss_0p72v_m40c_cmax_hold"
    "ff_0p88v_p125c_rcmax_hold"
    "ff_0p88v_p125c_cmin_hold"
    "ff_0p88v_p125c_cmax_hold"
    "ff_0p88v_m40c_cmin_hold"
}

set report_files [glob -nocomplain "${TARGET_DIR}/*_total_skew.rpt"]

if {[llength $report_files] == 0} {
    puts "Error: No *_total_skew.rpt files found in $TARGET_DIR"
    exit 1
}

foreach file_path $report_files {
    set file_name [file tail $file_path]
    if { [regexp {^(.*)_total_skew\.rpt$} $file_name match corner_name] } {
        set FILE_MAP($corner_name) $file_path
    }
}

puts "Info: Target Corner Order - $ORDERED_CORNERS"

catch {unset PINS_MAP}
catch {unset DATA}

foreach corner $ORDERED_CORNERS {
    if { ![info exists FILE_MAP($corner)] } {
        puts "Warning: File for corner '$corner' not found. Filling with '-'"
        continue
    }

    set rpt_file $FILE_MAP($corner)
    puts "Reading $rpt_file ..."
    
    set fin [open $rpt_file r]
    while {[gets $fin line] >= 0} {
        if { [string match "*:*" $line] && ([string match "* min *" $line] || [string match "* max *" $line]) } {
            
            set clean_line [regexp -all -inline {\S+} $line]
            
            if {[llength $clean_line] >= 5} {
                set pin_name [lindex $clean_line 0]
                set type     [lindex $clean_line 2]
                set val      [lindex $clean_line 4]
                
                set PINS_MAP($pin_name) 1
                
                if { ![info exists DATA($pin_name,$corner,min)] } { set DATA($pin_name,$corner,min) "-" }
                if { ![info exists DATA($pin_name,$corner,max)] } { set DATA($pin_name,$corner,max) "-" }
                
                if { $type == "min" } {
                    set DATA($pin_name,$corner,min) $val
                } elseif { $type == "max" } {
                    set DATA($pin_name,$corner,max) $val
                }
            }
        }
    }
    close $fin
}

set PIN_LIST [lsort -dictionary [array names PINS_MAP]]
set fout [open $OUTPUT_FILE w]


proc print_header {fout corners} {
    puts -nonewline $fout [format "%-30s | %-5s" "Pin Name" "Type"]
    foreach corner $corners {
        puts -nonewline $fout [format " | %-25s" $corner]
    }
    puts $fout ""
    puts $fout [string repeat "=" [expr 40 + 28 * [llength $corners]]]
}

print_header $fout $ORDERED_CORNERS

foreach pin $PIN_LIST {
    puts -nonewline $fout [format "%-30s | %-5s" $pin "min"]
    foreach corner $ORDERED_CORNERS {
        if { [info exists DATA($pin,$corner,min)] } {
            puts -nonewline $fout [format " | %-25s" $DATA($pin,$corner,min)]
        } else {
            puts -nonewline $fout [format " | %-25s" "-"]
        }
    }
    puts $fout ""
}

foreach pin $PIN_LIST {
    puts -nonewline $fout [format "%-30s | %-5s" $pin "max"]
    foreach corner $ORDERED_CORNERS {
        if { [info exists DATA($pin,$corner,max)] } {
            puts -nonewline $fout [format " | %-25s" $DATA($pin,$corner,max)]
        } else {
            puts -nonewline $fout [format " | %-25s" "-"]
        }
    }
    puts $fout ""
}

close $fout
puts "Info: Merging Complete. Output file: $OUTPUT_FILE"
