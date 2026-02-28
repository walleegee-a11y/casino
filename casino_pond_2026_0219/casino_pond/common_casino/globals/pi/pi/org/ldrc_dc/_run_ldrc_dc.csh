#! /bin/csh -f
###############################################
#- Set Environment 
###############################################
#clean-up
rm -rf LDRC_DC_*

#make directories
mkdir -p logs
mkdir -p reports
mkdir -p netlist

#run_ldrc_dc.tcl
\cp -rf ../common/globals/pi/${stage}/run_ldrc_dc.tcl .
dc_shell -f run_ldrc_dc.tcl -output_log_file ./logs/ldrc.log
