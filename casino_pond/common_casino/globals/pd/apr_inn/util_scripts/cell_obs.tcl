
# For DRC

if { ${stage} == "place" } {
   add_cell_obs -cell FA1OPTCD1BWP${stdTrack}30P140HVT -layer M2 -rects "2.495 0.675 2.500 0.725" -spacing 0
   add_cell_obs -cell FA1OPTCD1BWP${stdTrack}30P140HVT -layer M2 -rects "2.005 0.675 2.010 0.725" -spacing 0
   add_cell_obs -cell FA1OPTCD1BWP${stdTrack}35P140 -layer M2 -rects "2.495 0.675 2.500 0.725" -spacing 0
   add_cell_obs -cell FA1OPTCD1BWP${stdTrack}35P140 -layer M2 -rects "2.005 0.675 2.010 0.725" -spacing 0
} else {
   delete_cell_obs -cells FA1OPTCD1BWP${stdTrack}30P140HVT -layers M2   
   delete_cell_obs -cells FA1OPTCD1BWP${stdTrack}35P140 -layers M2
}
