
set_ccopt_property primary_delay_corner $cts_primary_delay_corner

# Target skew
foreach a [all_delay_corners] {
	set_ccopt_property target_skew $cts_target_skew -delay_corner $a
}

# 1. CLOCK ROUTING RULES
add_ndr -name 2W2S -width_multiplier {ME3:ME6 2} -spacing_multiplier {ME3:ME6 2} 
add_ndr -name 1W2S -spacing_multiplier {ME3:ME6 2}
 
#
#create_route_type -name top -non_default_rule 2W2S -top_preferred_layer M6 -bottom_preferred_layer M3 \
#		 -preferred_routing_layer_effort high -shield_net $gName
#create_route_type -name trunk -non_default_rule 2W2S -top_preferred_layer M6 -bottom_preferred_layer M3 \
#		 -preferred_routing_layer_effort high -shield_net $gName
#create_route_type -name leaf -non_default_rule 1W2S -top_preferred_layer M6 -bottom_preferred_layer M3 \
#		 -preferred_routing_layer_effort high 



create_route_type -name top -non_default_rule 1W2S -top_preferred_layer ME6 -bottom_preferred_layer ME3 \
		 -preferred_routing_layer_effort high 
create_route_type -name trunk -non_default_rule 1W2S -top_preferred_layer ME6 -bottom_preferred_layer ME3 \
		 -preferred_routing_layer_effort high 
create_route_type -name leaf -non_default_rule 1W2S -top_preferred_layer ME6 -bottom_preferred_layer ME3 \
		 -preferred_routing_layer_effort high 

set_ccopt_property route_type -net_type top top
set_ccopt_property route_type -net_type leaf leaf
set_ccopt_property route_type -net_type trunk trunk

# 2. SET CCOPT_PROPERTIES:
# CLOCK CELL TYPE
set_ccopt_property inverter_cells $cts_inverter_cells
set_ccopt_property buffer_cells $cts_buffer_cells
set_ccopt_property clock_gating_cells $cts_cgate_cells
#if { ${DEFINE_TRACK} == "7T" } { 
#	set_ccopt_property logic_cells "[get_db [get_db base_cells -if { .is_combinational == true && .name == *7T* && .name == CK* && .name != *D0* && .name != *D1BWP* && .name == *LVT && .is_buffer != true  && .is_inverter != true }] .name] AO*D2BWP7T35P140LVT AO*D4BWP7T35P140LVT AO*D6BWP7T35P140LVT AO*D8BWP7T35P140LVT AN4D8BWP7T35P140LVT AN4D4BWP7T35P140LVT AN4D2BWP7T35P140LVT AN3D8BWP7T35P140LVT AN3D4BWP7T35P140LVT AN3D2BWP7T35P140LVT AN2D8BWP7T35P140LVT AN2D4BWP7T35P140LVT AN2D2BWP7T35P140LVT" 
#} else {
#	set_ccopt_property logic_cells "[get_db [get_db base_cells -if { .is_combinational == true && .name == CK* && .name != *D0* && .name != *D1BWP* && .name == *LVT && .is_buffer != true  && .is_inverter != true }] .name] AO*D2BWP35P140LVT AO*D4BWP35P140LVT AO*D6BWP35P140LVT AO*D8BWP35P140LVT AN4D8BWP35P140LVT AN4D4BWP35P140LVT AN4D2BWP35P140LVT AN3D8BWP35P140LVT AN3D4BWP35P140LVT AN3D2BWP35P140LVT AN2D8BWP35P140LVT AN2D4BWP35P140LVT AN2D2BWP35P140LVT" 
#}



setUsefulSkewMode -useCells $cts_inverter_cells

set_ccopt_property target_max_trans -net_type top $cts_target_tran_top
set_ccopt_property target_max_trans -net_type trunk $cts_target_tran_trunk
set_ccopt_property target_max_trans -net_type leaf $cts_target_tran_leaf

set_ccopt_property override_minimum_max_trans_target true

set_ccopt_property primary_reporting_skew_groups_log_min_max_sinks on
set_ccopt_property skew_band_size 2
set_ccopt_property r2r_iterations 5
set_ccopt_property cluster_when_starting_skewing 1

# Locate driver to center of bbox
set_ccopt_property recluster_to_reduce_power true
set_ccopt_property remove_bufferlike_clock_logic true
set_ccopt_property merge_clock_gates true ;   # this is the CCOpt default and is redundant (but needed in CTS mode)
set_ccopt_property useful_skew_clock_gate_initial_region_restriction 200 ;   # default is 10 rows
set_ccopt_property call_cong_repair_during_final_implementation false
set_ccopt_property call_cong_repair_during_final_implementation_use_hotspots true
set_ccopt_property update_io_latency $cts_update_io_latency
 

# ETC CCOPT PROPERTIES FROM CDNS
set_ccopt_property use_inverters true
set_ccopt_property cell_density 0.80
set_ccopt_property routing_top_min_fanout 2000
set_ccopt_property extract_network_latency true
set_ccopt_property max_fanout $cts_max_fanout
set_ccopt_property auto_limit_insertion_delay_factor 1.4 ; # e.g. 1.4
set_ccopt_property pro_can_move_datapath_insts true
set_ccopt_property pro_skew_safe_drv_buffering   true;  
set_ccopt_property post_conditioning_enable_drv_fixing_by_rebuffering true; # default false
set_ccopt_property post_conditioning_enable_routing_eco true; # default false
set_ccopt_property post_conditioning_enable_skew_fixing true; # default false
set_ccopt_property post_conditioning_enable_skew_fixing_by_rebuffering false; # default false
set_ccopt_property clustering_net_skew_limit_as_proportion_of_skew_target 0.0 ;   # disable this (default setting is 1)
set_ccopt_property merge_ignore_sdc false
set_ccopt_property clock_gating_only_optimize_above_flops false
set_ccopt_property def_lock_clock_sinks_after_routing true

# Revert HE settings
set_ccopt_property ccopt_mini_clustering_levels 2
set_ccopt_property useful_skew_implement_using_wns_windows true
set_ccopt_property skew_passes_per_cluster 10
set_ccopt_property ccopt_design_localize_cppr_settings 0
set_ccopt_property min_delta_band_factor 0.5
set_ccopt_property cloning_ignore_dont_touch_sdc false ;# default is true
set_ccopt_property clone_clock_cells_with_skew_group_constraints false ;#default is true
set_ccopt_property extract_clock_generator_skew_groups false
set_ccopt_property ccopt_merge_clock_gates true


## Extra log output
#ccopt_internal_messages -on
## Speed up AAE
#setAaeTmpFile -directory ./aae_tmp

