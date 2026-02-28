#IMSI

####

deselectAll
select_obj  [get_db insts -if { \
   .place_status == fixed && \
   .base_cell.name != *SRAM* && \
   .base_cell.class != core && \
   .base_cell.class != core_spacer && \
   .base_cell.class != core_welltap \
}]

setEcoMode -reset 
setEcoMode -honorDontTouch false -honorDontUse false -honorFixedNetWire false -honorFixedStatus false -refinePlace false -updateTiming false
setOptMode -preserveModuleFunction true
setOptMode -addPortAsNeeded false
setEcoMode -batchMode true

set i 0
set allPins ""
set fo [open error_PD_BUF.tcl w]

foreach a [get_db selected .pins -if { \
   .net.num_connections != 1 && \
   .net.name != "" && \
   .net.name != VDDL && \
   .net.name != VSSL && \
   .net.name != VDDAWO && \
   .net.driver_ports.name == "" && \
   .net.load_ports.name == "" && \
   .layer.name != AL_RDL && \
   .net.skip_routing != true\
}] {
   if { [get_db $a .net.drivers] != "" } {
      ecoAddRepeater -term [get_db $a .name] -cell BUFM8NMB -loc [get_db $a .location] -name [lindex [split [get_db $a .cell_name ] /] end]_PD_BUF_${i}
      lappen allPins [get_db $a .name]
      incr i
   } else {
      puts $fo [get_db $a .name]
   }
}
setOptMode -preserveModuleFunction false
setOptMode -addPortAsNeeded true

setEcoMode -reset 
close $fo


deselectAll
selectInst *PD_BUF*     
specifyCellPad -left 3 -right 3 -top 1 -bottom 1 *
setPlaceMode -place_detail_eco_max_distance 999
refinePlace -inst [dbGet selected.name ]
deselectAll

setPlaceMode -reset -place_detail_eco_max_distance
deleteCellPad *  

deselectAll
selectInst *PD_BUF*
dbSet selected.dontTouch true
dbSet selected.pstatus fixed
deselectAll

deselectAll
selectPin $allPins
dbSet selected.net.dontTouch true
deselectAll
