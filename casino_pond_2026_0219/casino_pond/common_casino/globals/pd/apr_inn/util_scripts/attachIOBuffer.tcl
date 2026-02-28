
specifyCellPad -left 3 -right 3 -top 1 -bottom 1 *

set fo [open excludeIOBuffer.tcl w ] 
foreach a [get_db [get_db designs .ports.net -if { .driver_pins.layer.name == M6 || .driver_pins.layer.name == M8 }] .name ] {
	puts $fo $a
} 
foreach a [get_db [get_db designs .ports.net -if { .load_pins.layer.name == M6 || .load_pins.layer.name == M8 }] .name  ] {
	puts $fo $a
} 
close $fo

attachIOBuffer -in BUFFD12BWP${stdTrack}35P140 -out BUFFD12BWP${stdTrack}35P140 -status fixed -baseName BOUNDARY_PD_BUF_[dbGet top.name]_ -excNetFile excludeIOBuffer.tcl

deleteCellPad * 

deselectAll
selectInst BOUNDARY_PD_BUF_*
dbSet selected.dontTouch true
deselectAll


deselectAll
selectIOPin *     
dbSet selected.net.dontTouch true
deselectAll
