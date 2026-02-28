

set all_rows_area 0
foreach a [dbShape [dbGet [dbGet -p2 top.fplan.rows.site.name CORE_7T].box] AND [dbGet top.fplan.boxes]] { 
	set llx [lindex $a 0]
	set lly [lindex $a 1]
	set urx [lindex $a 2]
	set ury [lindex $a 3]
	set all_rows_area [expr $all_rows_area + ( ($urx - $llx) * ($ury -$lly) )]
}

set softBlkg_area 0
foreach a [dbShape [dbGet [dbGet -p2 top.fplan.rows.site.name CORE_7T].box] AND [dbGet [dbGet -p top.fplan.pBlkgs.type soft].boxes]] { 
	set llx [lindex $a 0]
	set lly [lindex $a 1]
	set urx [lindex $a 2]
	set ury [lindex $a 3]
	set softBlkg_area [expr $softBlkg_area + ( ($urx - $llx) * ($ury -$lly) )]
}


set all_std_area [expr [join [dbGet [dbGet -p2 top.insts.cell.subClass core].area] +]]
set macro_area [expr [join [get_db [get_db insts -if { .base_cell.name == *SRAM* || .base_cell.name == *SROM* }] .area] +]]


set EU [expr $all_std_area / $all_rows_area ] 
set TU [expr ($all_std_area + $macro_area) / ( $all_rows_area + $macro_area ) ]
set eEU [expr $all_std_area / ( $all_rows_area - $softBlkg_area ) ] 
set eTU [expr ($all_std_area + $macro_area) / ( $all_rows_area + $macro_area - $softBlkg_area )  ]

set fo [open report/${stage}/EU_TU.rpt w]
puts  $fo [format "\n#################################################################################\n"]
puts  $fo [format " Normal    EU / TU : %3.2f%% / %3.2f%% " [expr $EU *100] [expr $TU*100] ]
puts  $fo "  -> EU = All STD area / All rows area"
puts  $fo "  -> TU = ( All STD area + Memory area ) / ( All rows area + Memory area )\n"
puts  $fo [format " Effective EU / TU : %3.2f%% / %3.2f%% " [expr $eEU *100] [expr $eTU*100] ]
puts  $fo "  -> EU = All STD area / ( All rows area - Effective softBlkgs area )"
puts  $fo "  -> TU = ( All STD areas + Memory areas ) / ( All rows area + Memory areas - Effective softBlkgs area )\n"
puts  $fo [format "#################################################################################\n"]
close $fo 


