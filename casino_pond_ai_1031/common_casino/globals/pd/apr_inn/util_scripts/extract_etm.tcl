


if {![file exists ./TEMP_SPEF]} { exec mkdir ./TEMP_SPEF }

extractRC
foreach a [all_rc_corners ] { rcOut  -rc_corner $a  -spef ./TEMP_SPEF/$a.spef.gz } 

set_global timing_extract_model_aocv_mode graph_based
set_global timing_extract_model_write_min_max_clock_tree_path 1
set_global timing_extract_model_preserve_clock_name_as_internal_pin false

set setupView [all_analysis_views -type setup]
set holdView [all_analysis_views -type hold]

foreach view [all_analysis_views] {
	set_analysis_view -setup $view -hold $view
	if { [regexp _ML_ $view] } {
		spefIn -rc_corner 125c_Cmin ./TEMP_SPEF/125c_Cmin.spef.gz
	} elseif { [regexp _WCL_ $view] } {
		spefIn -rc_corner m40c_CmaxT ./TEMP_SPEF/m40c_CmaxT.spef.gz
        }
	do_extract_model -view $view ./report/${stage}/[dbGet top.name].${view}.lib
}

set rcLists "WCL_CmaxT ML_Cmin"
foreach a $rcLists {
set_global timing_library_no_exist_mismatch_pin_cap  1
merge_model_timing -mode_group pd_etm -modes "func shift capture" -library_file "report/${stage}/[dbGet top.name].func_${a}.lib report/${stage}/[dbGet top.name].shift_${a}.lib report/${stage}/[dbGet top.name].capture_${a}.lib" -outfile ./report/${stage}/[dbGet top.name].merge.${a}.lib
}


set_analysis_view -setup $setupView -hold $holdView
rm -rf ./TEMP_SPEF


