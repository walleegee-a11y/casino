set of [open viewDefinitionFile.tcl w] ;

#puts  "ex) Enter DK Path : /mnt/data/prjs/ANA6710P/INNOVUS/ANA6710P/db/vers/20240905_FINAL"
#puts  "Enter DK Path : "
#flush stdout
#gets stdin dk
#
#puts  "ex) Enter setup_view list: aa bb "
#puts  "Enter setup_view list: "
#flush stdout
#gets stdin setup_views 
#
#
#puts  "ex) Enter hold_view list: aa bb cc "
#puts  "Enter hold_view list: "
#flush stdout
#gets stdin hold_views


#set dk /mnt/data/prjs/ANA6714/db/vers/20241028
#set aocv /mnt/data/prjs/ANA6714/db/imported/pdk/20241024/ocv/aocv
#
#
#set setup_views "func_ss_0p72v_m40c_Cmax func_ss_0p72v_m40c_RCmax func_ss_0p72v_p125c_Cmax "
#set hold_views "func_ff_0p88v_p125c_RCmax func_ff_0p88v_m40c_Cmax func_ff_0p88v_m40c_RCmin "

########

#Test2
set all_corner [concat $setup_views $hold_views]

set all_mode {}
set all_process {}
set all_voltage {}
set all_temperature {}
set all_rc_corner {}
set all_lib_set {}

    foreach view $all_corner {
        set split_view [split $view "_"]
        set mode [lindex $split_view 0]
        set process [lindex $split_view 1]
        set voltage [lindex $split_view 2]
        set temperature [lindex $split_view 3]
        set rc_corner [lindex $split_view 4]


        set lib_set "[lindex $split_view 1]_[lindex $split_view 2]_[lindex $split_view 3]"
        set Temperature_rc_corner "[lindex $split_view 3]_[lindex $split_view 4]"



        
        if {[lsearch -exact $all_mode $mode] == -1} {
            lappend all_mode $mode

        puts $of "create_constraint_mode -name $mode -sdc_files [exec find $sdc_path -name "*${mode}*"]"

        }
        if {[lsearch -exact $all_lib_set $lib_set] == -1} {
            lappend all_lib_set $lib_set

        puts $of "create_library_set -name $lib_set -timing \[glob -type f ${LIB_path}/${lib_set}/*lib* \] -aocv \[glob $aocv_path/${lib_set}/*.aocv\]"
        }
        if {[lsearch -exact $all_rc_corner $Temperature_rc_corner] == -1} {
            lappend all_rc_corner $Temperature_rc_corner

        puts $of "create_rc_corner -name $Temperature_rc_corner  \\"
        puts $of "  -preRoute_res 1.00 \\"
        puts $of "  -preRoute_cap 1.00 \\"
        puts $of "  -postRoute_res {1.00 1.00 1.00} \\"
        puts $of "  -postRoute_cap {1.00 1.00 1.00} \\"
        puts $of "  -postRoute_xcap {1 1 1} \\"
        puts $of "  -preRoute_clkres 1.00 \\"
        puts $of "  -preRoute_clkcap 1.00 \\"
        puts $of "  -postRoute_clkres {1.00 1.00 1.00} \\"
        puts $of "  -postRoute_clkcap {1.00 1.00 1.00} \\"
        puts $of "  -T [string map {m - c "" p ""} $temperature]  \\"
        puts $of "  -qx_tech_file \[glob -type f ${qrc_path}/${rc_corner}/qrcTechFile \]"

        }
    }



#make Delay Corner & make View


foreach lib $all_lib_set {
    foreach rc $all_rc_corner {
        puts $of "create_delay_corner -name ${lib}_${rc} -library_set $lib -rc_corner $rc"
        foreach mode $all_mode {

                    set split_lib [split $lib "_"]
                    set split_rc [split $rc "_"]
                set lib_tem [lindex $split_lib 2]
                set rc_tem [lindex $split_rc 0]
                set rc_name [lindex $split_rc 1]
                if {$rc_tem == $lib_tem} {
                puts $of "create_analysis_view -name ${mode}_${lib}_${rc_name} -constraint_mode ${mode} -delay_corner ${lib}_${rc}"
                }

            }
    }
}
puts $of "set_analysis_view -setup \"${setup_views}\" -hold \"${hold_views}\""



close $of

puts "Mode List: $all_mode"
puts "Libset List: $all_lib_set"
puts "Rccorner List: $all_rc_corner"




