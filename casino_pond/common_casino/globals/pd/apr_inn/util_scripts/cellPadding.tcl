
# Flop
foreach a [get_db [get_db base_cells -if { .is_flop == true }] .name] { specifyCellPad $a -left 5 -right 5 }

### # for pin density
### foreach coreCell [get_db  base_cells -if { .class == core }] {
### 	if { [expr [get_db $coreCell .num_base_pins] / [get_db $coreCell .area]] > 8 } {
### 		 specifyCellPad -left 2 -right 2 [get_db $coreCell .name]
### 	}
### }


