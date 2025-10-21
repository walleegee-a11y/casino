


if { $ecfFlow == "false" } {
	# create/source clock tree spec:
	create_ccopt_clock_tree_spec -keep_all_sdc_clocks -filename ./ccopt.spec
	source ./ccopt.spec
	
#IMSI
#	foreach ct [get_ccopt_clock_trees *] {
#	  Puts "   INFO    >> setting max length constraints for clock tree : $ct"
#	  set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type top ${cts_top_net_length} ;   # limit the top   net length - confirmed value for this technology and library
#	  set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type trunk ${cts_turnk_net_length} ;   # limit the trunk net length - confirmed value for this technology and library
#	  set_ccopt_property max_source_to_sink_net_length -clock_tree $ct -net_type leaf ${cts_leaf_net_length} ;   # limit the leaf  net length - confirmed value for this technology and library
#	}
#}

set_ccopt_property cts_debug_output_db_dir debug_cts_dbs
set_ccopt_property debug_output_db_step_list {"Clustering"}

saveDesign ./dbs/pre_cts.enc   
