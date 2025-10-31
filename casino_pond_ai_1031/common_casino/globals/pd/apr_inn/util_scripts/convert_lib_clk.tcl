
set views "func_WCL_CmaxT shift_WCL_CmaxT capture_WCL_CmaxT"
foreach a $views { 
	convert_lib_clock_tree_latencies -latency_file_prefix convert_lib_clk_ -views $a
}
if { [file exists ./convert_lib_clk_func_WCL_CmaxT.sdc] }     { set_interactive_constraint_modes func    ; source ./convert_lib_clk_func_WCL_CmaxT.sdc }
if { [file exists ./convert_lib_clk_shift_WCL_CmaxT.sdc] }    { set_interactive_constraint_modes shift   ; source ./convert_lib_clk_shift_WCL_CmaxT.sdc }
if { [file exists ./convert_lib_clk_capture_WCL_CmaxT.sdc] }  { set_interactive_constraint_modes capture ; source ./convert_lib_clk_capture_WCL_CmaxT.sdc }

set_interactive_constraint_modes [all_constraint_modes -active]

