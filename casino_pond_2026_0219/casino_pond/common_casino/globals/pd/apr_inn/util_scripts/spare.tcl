proc proc_insert_spare_cells {args} {
	source ./innovus_config.tcl
        parse_proc_arguments -args $args options
        foreach arg_name [array names options] {
                switch -glob -- $arg_name {
                        "-rule"          {set rule $options(-rule)}
                        "-prefixName"    {set prefixName $options(-prefixName)}
                }
        }

        set start_time "\[START TIME\] [exec date]"
        setPlaceMode -place_detail_eco_max_distance 150
        clearDrc

        if {[dbGet -e top.fplan.pBlkgs.type soft] != "" } {
            deselectAll
            select_obj [dbGet -p top.fplan.pBlkgs.type soft ]     
            writeFPlanScript -selected -fileName dump_for_spare.tcl
            deleteSelectedFromFPlan
        }
        set placedInstsID [dbGet -e -p top.insts.pStatus placed]
        set fixedInstsID  [dbGet -e -p top.insts.pStatus fixed ]
        setInstancePlacementStatus -name * -status fixed

        ## Spare cell spec of distance (um)
        if {![info exist rule] } { set rule 150 }
        if {![info exist prefixName]} {set prefixName spare_cell_for_eco_group}
	if { $DEFINE_TRACK == "7T" } {
        	set spare(core,nonpg) [list \
					{CKBD4BWP7T35P140 1} \
					{CKBD8BWP7T35P140 1} \
					{DFCSND4BWP7T35P140 1} \
					{DFCSND4BWP7T35P140 1} \
					{INVD4BWP7T35P140 1} \
					{INVD8BWP7T35P140 1} \
					{MUX2D4BWP7T35P140 2} \
					{ND2D4BWP7T35P140 2} \
					{NR2D4BWP7T35P140 2} \
        	                        ]
	} else {
        	set spare(core,nonpg) [list \
					{CKBD4BWP35P140 1} \
					{CKBD8BWP35P140 1} \
					{DFCSND4BWP35P140 1} \
					{DFCSND4BWP35P140 1} \
					{INVD4BWP35P140 1} \
					{INVD8BWP35P140 1} \
					{MUX2D4BWP35P140 2} \
					{ND2D4BWP35P140 2} \
					{NR2D4BWP35P140 2} \
        	                        ]
	}
        set areas 0
        set cells ""
        foreach insts $spare(core,nonpg) {
            set cell [lindex $insts 0]
            specifyCellPad $cell -left 3 -right 3
            set num  [lindex $insts 1]
            set area  [expr [dbGet [dbGet -p head.libCells.name $cell].size_x] * [dbGet [dbGet -p head.libCells.name $cell].size_y] * $num]
            set areas [expr $areas + $area]
            incr i
        }
        set areas [expr ceil($areas)]
        set coreX [dbGet top.fplan.coreBox_urx]
        set coreY [dbGet top.fplan.coreBox_ury]
        set numX [expr int($coreX / $rule) + 1]
        set numY [expr int($coreY / $rule) + 1]
        set boxes ""
        for {set i 1} {$i < $numX} {incr i} {
            for {set j 1} {$j < $numY} {incr j} {
                set x [expr ($i * $rule)]
                set y [expr ($j * $rule)]
                if {[dbQuery -areas "$x $y $x $y" -objType row] != "" } {
                    lappend boxes "$x $y"
                }
            }
        }
        set cnt 1
        foreach box $boxes {
            set i 0
            foreach insts $spare(core,nonpg) {
                for {set j 0} {$j < [lindex $insts 1]} {incr j} {
                    addInst -cell [lindex $insts 0] -inst ${prefixName}${cnt}_${i}_$j -place_status placed -loc "{$box}"
                    foreach a [dbGet [dbGet -p [dbGet -p head.allCells.name [lindex $insts 0]].terms.isInput 1].name] { attachTerm ${prefixName}${cnt}_${i}_$j $a $gName }
                }
                incr i
            }
            incr cnt
        }
        deselectAll
        refinePlace -inst ${prefixName}*
        deleteCellPad *
        dbSet [dbGet top.insts.name ${prefixName}* -p].pstatus fixed
        dbSet [dbGet top.insts.name ${prefixName}* -p].dontTouch true
        if {$placedInstsID != "" } {
            dbSet $placedInstsID.pstatus placed
        }
        setPlaceMode -reset -place_detail_eco_max_distance
               if [file exist dump_for_spare.tcl] {
               source dump_for_spare.tcl
               rm -rf dump_for_spare.tcl
               }
        set end_time "\[END TIME\] [exec date]"
        Puts "\n#################################################"
        Puts "# Spare cell prefix name "
        Puts " >> ${prefixName}"
        Puts "# Spare cell coverage"
        Puts " >> $rule um"
        Puts "# num of spare cells // num of spare group"
        Puts " >> [llength [dbGet top.insts.name ${prefixName}*]] ea // [llength $boxes] groups"
        Puts "# Insertion spare cells RUNTIME"
        Puts "$start_time"
        Puts "$end_time"
        Puts "#################################################\n"
}
define_proc_arguments proc_insert_spare_cells \
        -define_args {
          {-rule "rule" "" string optional}
          {-prefixName "prefixName" "" string optional}
}

Puts "<DEFAULT VALUE> \$rule : 150 um , \$prefixName : spare_cell_for_eco_group"
Puts "<USAGE> proc_insert_spare_cells"
Puts "                  or          "
Puts "<USAGE> proc_insert_spare_cells -rule 150 -prefixName \$prefixName"
