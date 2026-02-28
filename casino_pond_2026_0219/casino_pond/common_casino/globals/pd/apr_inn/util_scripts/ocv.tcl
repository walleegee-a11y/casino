#set RVT_add  [get_object_name [get_lib_cells u028lschv09bdraec_099c-40_ffg/*NMB]]
#set HVT_add  [get_object_name [get_lib_cells u028lschv09bdhec_099c-40_ffg/*HMA]]
#set HVT_add2 [get_object_name [get_lib_cells u028lschv09l7bh_099c-40_ffg/*HMA]]
#
#set RVT [get_object_name [get_object_name [get_lib_cells u028lschv09bdra_099c-40_ffg/*NMB]]
#set LVT [get_object_name [get_object_name [get_lib_cells u028lschv09bdl_099c-40_ffg/*LMA]]
#set HVT [get_object_name [get_object_name [get_lib_cells u028lschv09bdh_099c-40_ffg/*HMA]]

reset_timing_derate
set RVT_derate [dbGet head.libCells.name *$RVT]
set LVT_derate [dbGet head.libCells.name *$LVT]
set HVT_derate [dbGet head.libCells.name *$HVT]

set all_corner [concat $setup_views $hold_views]


set BST ""
set BST_TI ""
set WST_TI "" 
set WST ""


foreach corner $all_corner {
    if {[string match *ss* $corner] && [string match *p* $corner]} {
        lappend WST $corner
    } elseif {[string match *ss* $corner] && [string match *m* $corner]} {
        lappend WST_TI $corner
    } elseif {[string match *ff* $corner] && [string match *m* $corner]} {
        lappend BST $corner
    } elseif {[string match *ff* $corner] && [string match *p* $corner]} {
        lappend BST_TI $corner
    }
}


foreach BST_dc $BST {
set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -early -[expr 0.0216 + 0.0007] $HVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -early -[expr 0.0216 + 0.00061] $RVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -early -[expr 0.0216 + 0.0005] $LVT_derate

set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.0007] $HVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.00061] $RVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.0005] $LVT_derate

set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -late [expr 0.0216 + 0.0007] $HVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -late [expr 0.0216 + 0.00061] $RVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -data -add -late [expr 0.0216 + 0.0005] $LVT_derate

set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -late [expr 0.0211 + 0.0007] $HVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -late [expr 0.0211 + 0.00061] $RVT_derate
set_timing_derate -delay_corner $BST_dc -cell_delay -clock -add -late [expr 0.0211 + 0.0005] $LVT_derate


    set_timing_derate -delay_corner $BST_dc -net_delay -data -add -late 0.085
    set_timing_derate -delay_corner $BST_dc -net_delay -clock -add -late 0.085
    set_timing_derate -delay_corner $BST_dc -net_delay -data -add -early -0.085
    set_timing_derate -delay_corner $BST_dc -net_delay -clock -add -early -0.085


}



foreach BST_TI_dc $BST_TI {
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -early -[expr 0.0216 + 0.00058] $HVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -early -[expr 0.0216 + 0.00055] $RVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -early -[expr 0.0216 + 0.00047] $LVT_derate

set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.00058] $HVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.00055] $RVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -early -[expr 0.0211 + 0.00047] $LVT_derate

set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -late [expr 0.0216 + 0.00058] $HVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -late [expr 0.0216 + 0.00055] $RVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -data -add -late [expr 0.0216 + 0.00047] $LVT_derate

set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -late [expr 0.0211 + 0.00058] $HVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -late [expr 0.0211 + 0.00055] $RVT_derate
set_timing_derate -delay_corner $BST_TI_dc -cell_delay -clock -add -late [expr 0.0211 + 0.00047] $LVT_derate


    set_timing_derate -delay_corner $BST_TI_dc -net_delay -data -add -late 0.085
    set_timing_derate -delay_corner $BST_TI_dc -net_delay -clock -add -late 0.085
    set_timing_derate -delay_corner $BST_TI_dc -net_delay -data -add -early -0.085
    set_timing_derate -delay_corner $BST_TI_dc -net_delay -clock -add -early -0.085

}


foreach WST_dc $WST {
set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -early -[expr 0.0196 + 0.00104] $HVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -early -[expr 0.0196 + 0.0009] $RVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -early -[expr 0.0196 + 0.00069] $LVT_derate

set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.00104] $HVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.0009] $RVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.00069] $LVT_derate

set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -late [expr 0.0196 + 0.00104] $HVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -late [expr 0.0196 + 0.0009] $RVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -data -add -late [expr 0.0196 + 0.00069] $LVT_derate

set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -late [expr 0.0194 + 0.00104] $HVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -late [expr 0.0194 + 0.0009] $RVT_derate
set_timing_derate -delay_corner $WST_dc -cell_delay -clock -add -late [expr 0.0194 + 0.00069] $LVT_derate

    set_timing_derate -delay_corner $WST_dc -net_delay -data -add -late 0.085
    set_timing_derate -delay_corner $WST_dc -net_delay -clock -add -late 0.085
    set_timing_derate -delay_corner $WST_dc -net_delay -data -add -early -0.085
    set_timing_derate -delay_corner $WST_dc -net_delay -clock -add -early -0.085
}


foreach WST_TI_dc $WST_TI {
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -early -[expr 0.0196 + 0.00195] $HVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -early -[expr 0.0196 + 0.00132] $RVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -early -[expr 0.0196 + 0.00084] $LVT_derate

set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.00195] $HVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.00132] $RVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -early -[expr 0.0194 + 0.00084] $LVT_derate

set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -late [expr 0.0196 + 0.00195] $HVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -late [expr 0.0196 + 0.00132] $RVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -data -add -late [expr 0.0196 + 0.00084] $LVT_derate

set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -late [expr 0.0194 + 0.00195] $HVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -late [expr 0.0194 + 0.00132] $RVT_derate
set_timing_derate -delay_corner $WST_TI_dc -cell_delay -clock -add -late [expr 0.0194 + 0.00084] $LVT_derate

    set_timing_derate -delay_corner $WST_TI_dc -net_delay -data -add -late 0.085
    set_timing_derate -delay_corner $WST_TI_dc -net_delay -clock -add -late 0.085
    set_timing_derate -delay_corner $WST_TI_dc -net_delay -data -add -early -0.085
    set_timing_derate -delay_corner $WST_TI_dc -net_delay -clock -add -early -0.085



}


#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.103 + 0.020] ${7t_hvt_cells}  
#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.074 + 0.009] ${7t_rvt_cells}  
#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.056 + 0.006] ${7t_lvt_cells}  
#   
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.036 + 0.001] ${7t_hvt_cells} 
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.026 + 0.005] ${7t_rvt_cells} 
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.019 + 0.007] ${7t_lvt_cells} 
#
#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.097 + 0.018] ${9t_hvt_cells}  
#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.071 + 0.008] ${9t_rvt_cells}  
#set_timing_derate -delay_corner WCL_CmaxT -cell_delay -add -early -[expr 0.054 + 0.005] ${9t_lvt_cells}  
#   
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.035 + 0.001] ${9t_hvt_cells}  
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.025 + 0.005] ${9t_rvt_cells}  
#set_timing_derate -delay_corner ML_Cmin -cell_delay -add -late [expr 0.018 + 0.007] ${9t_lvt_cells}  
#
#
#   set_timing_derate -delay_corner WCL_CmaxT -net_delay  -add -late 0.06
#   set_timing_derate -delay_corner WCL_CmaxT -net_delay  -add -early -0.06
#   set_timing_derate -delay_corner ML_Cmin -net_delay  -add -late 0.085
#
##if { $stage == "place" } { set_timing_derate -delay_corner WCL_CmaxT -net_delay  -add -late -data 0.05 }
