proc Conv_ICC_to_SOCE { ICC_ECO SOCE_ECO } {

    if { [file exists $SOCE_ECO] } {
        sh rm $SOCE_ECO
    }

    set infile [open $ICC_ECO r]
    while { [gets $infile line] != -1 } {
        set tmp [regsub -all {\[get_pins} $line {get_pins} line2]
        set tmp [regsub -all {\[get_cells} $line2 {get_cells} line3]
        set tmp [regsub -all {\[get_ports} $line3 {get_ports} line4]
        set tmp [regsub -all {\}\]} $line4 \} nline]

        if { [regexp "^#" [lindex $nline 0]] } {
            continue
        }

        if { [llength $nline] == 1 && [lindex $nline 0] == "current_instance" } {
            set c_instance ""
            continue
        }

        if { [llength $nline] == 2 && [lindex $nline 0] == "current_instance" } {
            set c_instance [lindex $nline 1]
            continue
        }

        if { $c_instance != "" } {
            if { [lindex $nline 0] == "insert_buffer" } {
                set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
                set tpin [lindex $nline $n_pin]
                set buf [lindex $nline [expr $n_pin + 1]]
                set pin "$c_instance/$tpin"
                set tmp_cell [lindex $nline [expr [lsearch -exact $nline "new_cell_names"] + 1]]
                set new_cell "$tmp_cell"
                echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
            } elseif { [lindex $nline 0] == "size_cell" } {
                set tcell [lindex $nline 1]
                set newref [lindex $nline 2]
                set cell "$c_instance/$tcell"
                echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
            } elseif { [lindex $nline 0] == "remove_buffer" } {
                set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
                set tocell [lindex $nline $n_cell]
                set cell "$c_instance/$tocell"
                echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
            }
        } else {
            if { [lindex $nline 0] == "insert_buffer" } {
                if { [lsearch -exact $nline "get_pins"] != -1 } {
                    set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
                    set tpin [lindex $nline $n_pin]
                    set buf [lindex $nline [expr $n_pin + 1]]
                    set pin "$tpin"
                    set tmp_cell [lindex $nline [expr [lsearch -exact $nline "new_cell_names"] + 1]]
                    set new_cell "$tmp_cell"
                    echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
                }
            } elseif { [lsearch -exact $nline "get_ports"] != -1 } {
                set n_pin [expr [lsearch -exact $nline "get_ports"] + 1]
                set tpin [lindex $nline $n_pin]
                set buf [lindex $nline [expr $n_pin + 1]]
                set tmp_cell [lindex $nline [expr [lsearch -exact $nline "new_cell_names"] + 1]]
                set new_cell "$tmp_cell"
                echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
            } elseif { [lindex $nline 0] == "size_cell" } {
                set tocell [lindex $nline 1]
                set newref [lindex $nline 2]
                set cell "$tocell"
                echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
            } elseif { [lindex $nline 0] == "remove_buffer" } {
                set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
                set tocell [lindex $nline $n_cell]
                set cell "$tocell"
                echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
            }
        }
    }
}
