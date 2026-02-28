create_library_set -name WCL \
	-timing [glob -type f /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/lib/WCL_all/*] \
	-aocv [glob -type f /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/lib/WCL_all_aocv_without_wireAocv/*]

create_library_set -name ML \
	-timing [glob -type f /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/lib/ML_all/*] \
	-aocv [glob -type f /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/lib/ML_all_aocv_without_wireAocv/*]

create_rc_corner -name m40c_CmaxT \
   -preRoute_res 1.00\
   -preRoute_cap 1.00\
   -postRoute_res {1.00 1.00 1.00}\
   -postRoute_cap {1.00 1.00 1.00}\
   -postRoute_xcap {1 1 1}\
   -preRoute_clkres 1.00\
   -preRoute_clkcap 1.11\
   -postRoute_clkres {1.00 1.00 1.00}\
   -postRoute_clkcap {1.11 1.11 1.11}\
   -T -40\
   -qx_tech_file /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/qrcTechfile/cworst_T/qrcTechFile

create_rc_corner -name 125c_Cmin \
   -T 125\
   -preRoute_res 1.00\
   -preRoute_cap 1.00\
   -postRoute_res {1.00 1.00 1.00}\
   -postRoute_cap {1.00 1.00 1.00}\
   -postRoute_xcap {1 1 1}\
   -preRoute_clkres 1.00\
   -preRoute_clkcap 1.10\
   -postRoute_clkres {1.00 1.00 1.00}\
   -postRoute_clkcap {1.10 1.10 1.10}\
   -qx_tech_file /home1/PROJECT/ANA38410_Rev0/PD/LAYOUT/desdir/qrcTechfile/cbest/qrcTechFile

create_delay_corner -name WCL_CmaxT\
   -library_set WCL\
   -rc_corner m40c_CmaxT

create_delay_corner -name ML_Cmin\
   -library_set ML\
   -rc_corner 125c_Cmin

create_constraint_mode -name func\
   -sdc_files "$sdc_path/$topName/func/func.sdc $sdc_path/$topName/func/mbist_add.sdc"
create_constraint_mode -name shift\
   -sdc_files "$sdc_path/$topName/shift/scan_shift.sdc"
create_constraint_mode -name capture\
   -sdc_files "$sdc_path/$topName/capture/scan_capture.sdc $sdc_path/$topName/capture/mbist_add.sdc"



create_analysis_view -name func_WCL_CmaxT \
   -constraint_mode func \
   -delay_corner WCL_CmaxT
create_analysis_view -name shift_WCL_CmaxT \
   -constraint_mode shift \
   -delay_corner WCL_CmaxT
create_analysis_view -name capture_WCL_CmaxT \
   -constraint_mode capture \
   -delay_corner WCL_CmaxT


create_analysis_view -name func_ML_Cmin \
   -constraint_mode func \
   -delay_corner ML_Cmin
create_analysis_view -name shift_ML_Cmin \
   -constraint_mode shift \
   -delay_corner ML_Cmin
create_analysis_view -name capture_ML_Cmin \
   -constraint_mode capture \
   -delay_corner ML_Cmin


set_analysis_view -setup "func_WCL_CmaxT shift_WCL_CmaxT capture_WCL_CmaxT func_ML_Cmin" -hold "func_ML_Cmin shift_ML_Cmin capture_ML_Cmin "

