#Global
dbSet [dbGet -p head.libCells.name *LMA].dontUse 1
dbSet [dbGet -p head.libCells.name E*M*].dontUse 1
dbSet [dbGet -p head.libCells.name *DEL*].dontUse 1
dbSet [dbGet -p head.libCells.name G*M*].dontUse 1
if {[string match "place" ${stage}] } {
dbSet [dbGet -p head.libCells.name CK*].dontUse 1
dbSet [dbGet -p head.libCells.name *M0LMA].dontUse 1
dbSet [dbGet -p head.libCells.name *M0HMA].dontUse 1
dbSet [dbGet -p head.libCells.name *M0NMB].dontUse 1
dbSet [dbGet -p head.libCells.name *M1LMA].dontUse 1
dbSet [dbGet -p head.libCells.name *M1HMA].dontUse 1
dbSet [dbGet -p head.libCells.name *M1NMB].dontUse 1
}


#
## Dont Touch
#set_db [get_db insts -if { .name == *_dont* }] .dont_touch size_ok
#
## Dont use cell lists
#set dont_use_cells " \
#  *D0BWP* \
#  *D20BWP* \
#  CK* \
#  DCCK* \
#  DEL* \
#  BUFFD1BWP* \
#  INVD1BWP* \
#"
#
#foreach dont_use_cell $dont_use_cells {
#	set_db [get_db base_cells -if { .name == $dont_use_cell && .class == core }] .dont_use true
#}
#
## ECO cells
#set_db [get_db base_cells -if { .site.name == gacore* }] .dont_use true
#
## HighEffortOptCells
#if { ${HOC_LVT} == true } {
#	setOptMode -highEffortOptCells "[get_db [ get_db base_cells -if { .dont_use == false && .name == *140LVT && .class == core } ] .name -u ]"
#	set_db [ get_db base_cells -if { .dont_use == false && .name == *140LVT && .class == core } ] .dont_use true
#} else {
#	set_db [get_db base_cells -if { .name == *140LVT && .class == core }] .dont_use true
#}
