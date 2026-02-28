###  
###  deselectAll
###  selectPGPin -layer M9
###  
###  set fo [open ${outfeedDirName}/${stage}/edtext.tcl w]
###  foreach a [dbGet selected.name  -u] {
###  	set llx [lindex [lindex [dbGet [dbGet -p selected.name $a].rect] 0] 0]
###  	set lly [lindex [lindex [dbGet [dbGet -p selected.name $a].rect] 0] 1]
###  	set urx [lindex [lindex [dbGet [dbGet -p selected.name $a].rect] 0] 2]
###  	set ury [lindex [lindex [dbGet [dbGet -p selected.name $a].rect] 0] 3]
###  	set ptx [expr $llx + (($urx - $llx)/2)]
###  	set pty [expr $lly + (($ury - $lly)/2)]
###  	puts $fo "LAYOUT TEXT $a $ptx $pty 139.0 [dbGet top.name]_TOP"
###  }
###  close $fo
###  deselectAll
### 

deselectAll
select_bump
set fo [open ${outfeedDirName}/${stage}/label_on.tcl w]
puts $fo "set input_gds \"OUTPUT\""
puts $fo "set TOP_MODULE \"ANA38410_TOP\""
puts $fo "set LL \[layout create \$input_gds -dt_expand\]"
foreach a [dbGet selected] {
	puts $fo "\$LL create text \$TOP_MODULE 126.0 [expr [dbGet $a.pt_x]+49.1]u [expr [dbGet $a.pt_y]+49.1]u [dbGet $a.terms.name]"
}
puts $fo "\$LL delete layer 5"
puts $fo "\$LL oasisout \"OUTPUT\""
puts $fo "exit"
close $fo 

deselectAll
select_bump
set fo [open ${outfeedDirName}/${stage}/EDTEXT w]
foreach a [dbGet selected] {
	puts $fo "LAYOUT TEXT [dbGet $a.terms.name] [expr [dbGet $a.pt_x]+49.1] [expr [dbGet $a.pt_y]+49.1] 126.0 ANA384010_TOP"
}
close $fo 
deselectAll




