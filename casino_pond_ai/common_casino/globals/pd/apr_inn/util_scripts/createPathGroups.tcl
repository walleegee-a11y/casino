#YMK#
reset_path_group -all
resetPathGroupOptions

	#get_cells -hierarchical  -filter "name =~ *sr_out_reg*"
set inp   [all_inputs -no_clocks]
set outp  [all_outputs]
set inp   [all_inputs -no_clocks]
set outp  [all_outputs]
set icgs  [filter_collection [all_registers] "is_integrated_clock_gating_cell == true"]
set sr [get_cells -hierarchical  -filter " name =~ *sr_out_reg* || name  =~ *ld_eno_reg* "]
set imsi_regs  [remove_from_collection [all_registers] $icgs]
set regs  [remove_from_collection $imsi_regs $sr]




# # Create IO Path Groups
group_path   -name in2reg       -from  $inp -to [all_registers] 
group_path   -name reg2out      -from [all_registers]  -to $outp
group_path   -name in2out       -from $inp   -to $outp

# # Create REG Path Groups
group_path   -name reg2reg      -from $regs -to $regs
group_path   -name reg2cgate  -from $regs -to $icgs

# # Create SR_OUT Path Groups
group_path   -name reg2sr   -from $regs -to $sr
group_path   -name sr2reg  	-from $sr -to $regs
group_path   -name sr2cgate -from $sr -to $icgs
group_path   -name sr2sr  	-from $sr -to $sr

setPathGroupOptions reg2reg -effortLevel high -weight 2 -slackAdjustment 0
setPathGroupOptions reg2cgate -effortLevel high -weight 2 -slackAdjustment 0
setPathGroupOptions reg2sr    -effortLevel high -weight 1 -slackAdjustment 0
setPathGroupOptions sr2reg    -effortLevel high -weight 1 -slackAdjustment 0
setPathGroupOptions sr2cgate  -effortLevel high -weight 1 -slackAdjustment 0
setPathGroupOptions sr2sr    -effortLevel high -weight 1 -slackAdjustment 0
setPathGroupOptions in2out -effortLevel low -weight 0 -slackAdjustment 0
setPathGroupOptions in2reg -effortLevel low -weight 0 -slackAdjustment 0
setPathGroupOptions reg2out -effortLevel low -weight 0 -slackAdjustment 0





#   ORG
#   reset_path_group -all
#   resetPathGroupOptions
#   createBasicPathGroups -expanded 
#
#   setPathGroupOptions reg2reg   -effortLevel high -weight 2 -slackAdjustment 0
#   setPathGroupOptions reg2cgate -effortLevel high -weight 2 -slackAdjustment 0
#   setPathGroupOptions in2out    -effortLevel high -weight 1 -slackAdjustment 0
#   setPathGroupOptions in2reg    -effortLevel high -weight 1 -slackAdjustment 0
#   setPathGroupOptions reg2out   -effortLevel high -weight 1 -slackAdjustment 0





