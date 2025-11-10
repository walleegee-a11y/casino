
set fo [open ./report/${stage}/Vth.rpt w]


set SLVT_physical_list [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${SLVT}].isPhysOnly 1].name]
set LVT_physical_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${LVT}].isPhysOnly 1].name]
set RVT_physical_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${RVT}].isPhysOnly 1].name]
set HVT_physical_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${HVT}].isPhysOnly 1].name]


set SLVT_list [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${SLVT}].isPhysOnly 0].name]
set LVT_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${LVT}].isPhysOnly 0].name]
set RVT_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${RVT}].isPhysOnly 0].name]
set HVT_list  [dbGet [dbGet -p1 [dbGet -p2 [dbGet -p2 top.insts.cell.baseClass core].cell.name *${HVT}].isPhysOnly 0].name]


set SLVT_num [llength $SLVT_list]
set LVT_num  [llength $LVT_list]
set RVT_num  [llength $RVT_list] 
set HVT_num  [llength $HVT_list]

set SLVT_physical_num [llength $SLVT_physical_list]
set LVT_physical_num  [llength $LVT_physical_list]
set RVT_physical_num  [llength $RVT_physical_list] 
set HVT_physical_num  [llength $HVT_physical_list]


if {[string match "0x0" $SLVT_list]} { set SLVT_num 0 }
if {[string match "0x0" $LVT_list]} { set LVT_num 0 }
if {[string match "0x0" $RVT_list]} { set RVT_num 0 }
if {[string match "0x0" $HVT_list]} { set HVT_num 0 }


if {[string match "0x0" $SLVT_physical_list]} { set SLVT_physical_num 0 }
if {[string match "0x0" $LVT_physical_list]} { set LVT_physical_num 0 }
if {[string match "0x0" $RVT_physical_list]} { set RVT_physical_num 0 }
if {[string match "0x0" $HVT_physical_list]} { set HVT_physical_num 0 }


set Total_inst [expr ($SLVT_num + $LVT_num + $RVT_num + $HVT_num)]
set Total_physical_inst [expr ($SLVT_physical_num + $LVT_physical_num + $RVT_physical_num + $HVT_physical_num)]

set SLVT_ratio [format "%.2f" [expr double($SLVT_num) / double($Total_inst) * 100]]
set LVT_ratio [format "%.2f" [expr double($LVT_num) / double($Total_inst) * 100]]
set RVT_ratio [format "%.2f" [expr double($RVT_num) / double($Total_inst) * 100]]
set HVT_ratio [format "%.2f" [expr double($HVT_num) / double($Total_inst) * 100]]

puts $fo " --------------------------------------------------------------------"
puts $fo " |     VTH         |     LOGIC |      Ratio |    Physical |"
puts $fo " --------------------------------------------------------------------"
puts $fo [format " |     %-10s | %10d | %10s%% | %10d " "SLVT" ${SLVT_num} $SLVT_ratio ${SLVT_physical_num} ]
puts $fo [format " |     %-10s | %10d | %10s%% | %10d " "LVT" ${LVT_num} $LVT_ratio ${LVT_physical_num} ]
puts $fo [format " |     %-10s | %10d | %10s%% | %10d " "RVT" ${RVT_num} $RVT_ratio ${RVT_physical_num} ]
puts $fo [format " |     %-10s | %10d | %10s%% | %10d " "HVT" ${HVT_num} $HVT_ratio ${HVT_physical_num} ]
puts $fo " --------------------------------------------------------------------"
puts $fo [format " | Total Instance Count   : %-10d (%-1d)             |" $Total_inst $Total_physical_inst]
puts $fo " --------------------------------------------------------------------"


close $fo 


