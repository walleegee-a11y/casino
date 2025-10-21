
deselectAll
selectNet  [get_ccopt_clock_tree_nets -net_types trunk]
selectNet  [get_ccopt_clock_tree_nets -net_types top]
set instLists ""
set fo [open ./report/${stage}/ccopt_clock_tree_cells_fixing.tcl w]
if { $DEFINE_TRACK == "7T" } {
foreach a [dbGet -p2 [dbGet -p2 selected.instTerms.inst.cell.subClass core].cell.name *HVT] {
   if { [dbGet head.allCells.name [string map {"BWP7T30P140HVT" "BWP7T35P140LVT"} [dbGet $a.cell.name]]] ==  "0x0" } {
      puts $fo "# ERROR [dbGet $a.name] [dbGet $a.cell.name]"
   } else { 
      puts $fo "ecoChangeCell -inst [dbGet $a.name] -cell [string map {"BWP7T30P140HVT" "BWP7T35P140LVT"} [dbGet $a.cell.name]] ; # org Cell [dbGet $a.cell.name]"
      lappend instLists [dbGet $a.name]
   }
}
foreach a [dbGet -p2 [dbGet -p2 selected.instTerms.inst.cell.subClass core].cell.name *140] {
   if { [dbGet head.allCells.name [string map {"BWP7T35P140" "BWP7T35P140LVT"} [dbGet $a.cell.name]]] ==  "0x0" } {
      puts $fo "# ERROR [dbGet $a.name] [dbGet $a.cell.name]"
   } else { 
      puts $fo "ecoChangeCell -inst [dbGet $a.name] -cell [string map {"BWP7T35P140" "BWP7T35P140LVT"} [dbGet $a.cell.name]] ; # org Cell [dbGet $a.cell.name]"
      lappend instLists [dbGet $a.name]
   }
}
} else {
foreach a [dbGet -p2 [dbGet -p2 selected.instTerms.inst.cell.subClass core].cell.name *HVT] {
   if { [dbGet head.allCells.name [string map {"BWP30P140HVT" "BWP35P140LVT"} [dbGet $a.cell.name]]] ==  "0x0" } {
      puts $fo "# ERROR [dbGet $a.name] [dbGet $a.cell.name]"
   } else { 
      puts $fo "ecoChangeCell -inst [dbGet $a.name] -cell [string map {"BWP30P140HVT" "BWP35P140LVT"} [dbGet $a.cell.name]] ; # org Cell [dbGet $a.cell.name]"
      lappend instLists [dbGet $a.name]
   }
}
foreach a [dbGet -p2 [dbGet -p2 selected.instTerms.inst.cell.subClass core].cell.name *140] {
   if { [dbGet head.allCells.name [string map {"BWP35P140" "BWP35P140LVT"} [dbGet $a.cell.name]]] ==  "0x0" } {
      puts $fo "# ERROR [dbGet $a.name] [dbGet $a.cell.name]"
   } else { 
      puts $fo "ecoChangeCell -inst [dbGet $a.name] -cell [string map {"BWP35P140" "BWP35P140LVT"} [dbGet $a.cell.name]] ; # org Cell [dbGet $a.cell.name]"
      lappend instLists [dbGet $a.name]
   }
}
}
close $fo
deselectAll

setEcoMode -reset 
setEcoMode -honorDontTouch false -honorDontUse false -honorFixedNetWire false -honorFixedStatus false -refinePlace false -updateTiming false
setEcoMode -batchMode true
source ./report/${stage}/ccopt_clock_tree_cells_fixing.tcl
setEcoMode -reset 

deselectAll
selectInst $instLists
dbSet selected.pstatus placed
refinePlace -inst "$instLists" 
dbSet selected.pstatus fixed
deselectAll


deselectAll
selectNet  [get_ccopt_clock_tree_nets -net_types trunk]
selectNet  [get_ccopt_clock_tree_nets -net_types top]
set fo [open ./report/${stage}/ccopt_clock_tree_cells.rpt w]
foreach a [dbGet selected.instTerms.inst.cell.name  -u] { puts $fo $a}
close $fo
deselectAll



