#################################################################################################
##                                                                                             ##
## SAMSUNG ELECTRONICS RESERVES THE RIGHT TO CHANGE PRODUCTS, INFORMATION AND SPECIFICATIONS   ##
## WITHOUT NOTICE.                                                                             ##
##                                                                                             ##
## No part of this publication may be reproduced, stored in a retrieval system, or transmitted ##
## in any form or by any means, electric or mechanical, by photocopying, recording,            ##
## or otherwise, without the prior written consent of Samsung. This publication is intended    ##
## for use by designated recipients only. This publication contains confidential information   ##
## (including trade secrets) of Samsung protected by Competition Law, Trade Secrets Protection ## 
## Act and other related laws, and therefore may not be, in part or in whole, directly or      ##
## indirectly publicized, distributed, photocopied or used (including in a posting on the      ##
## Internet where unspecified access is possible) by any unauthorized third party. Samsung     ##
## reserves its right to take any and all measures both in equity and law available to it and  ##
## claim full damages against any party that misappropriates Samsung?s trade secrets and/or   ##
## confidential information                                                                    ##
##                                                                                             ##
## All brand names, trademarks and registered trademarks belong to their respective owners.    ##
##                                                                                             ##
## 2016 Samsung Electronics Co., Ltd. All rights reserved                                      ##
##                                                                                             ##
#################################################################################################
############################################################################################
##   Conversion of the ICC ECO script to the SOC Encounter ECO script                     ##
##                                                                                        ##
##   Developer: H.S. Park (hs09.park@samsung.com)                                         ## 
##              DT Team, S. LSI Division, Samsung Electronics Co.,Ltd.                    ##
##   Release Date: 2012.07.30                                                             ##
##                                                                                        ##
##   How to convert icc eco tcl to soc encounter tcl <<<                                  ##
##   pt_shell> remote_execute {source $PATH/icc_eco_to_soce_eco.tcl}                      ##
##   pt_shell> remote_execute {Conv_ICC_to_SOCE eco_output.icc.tcl eco_output.soce.tcl}   ##  
############################################################################################

proc Conv_ICC_to_SOCE { ICC_ECO SOCE_ECO } {
	
	if { [file exists $SOCE_ECO] } {
		sh rm $SOCE_ECO
	}
		
	set infile [open $ICC_ECO r]
	while { [gets $infile line] != -1 } {
	        set tmp [regsub -all {\[get_pins} $line {get_pins} line2]
		set tmp [regsub -all {\[get_cells} $line2 {get_cells} line3]
		set tmp [regsub -all {\[get_ports} $line3 {get_ports} line4]
		set tmp [regsub -all {\}\]} $line4 \} nline]
		

		if { [regexp "^#" [lindex $nline 0]] } {
			continue
		}
		if { [llength $nline] == 1 && [lindex $nline 0] == "current_instance" } {
			set c_instance ""
			continue
		} 
		if { [llength $nline] == 2 && [lindex $nline 0] == "current_instance" } {
			set c_instance [lindex $nline 1]
			continue
		}
		if { $c_instance != ""} {
			if { [lindex $nline 0] == "insert_buffer" } {
				set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
				set tpin [lindex $nline $n_pin]
				set buf  [lindex $nline [expr $n_pin + 1]]
				set pin "$c_instance/$tpin"
				set tmp_cell [lindex $nline [expr [lsearch -exact $nline "-new_cell_names"] + 1]]
				set new_cell "$tmp_cell"
				echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
			} elseif { [lindex $nline 0] == "size_cell" } {
				set tcell 	[lindex $nline 1]
				set newref  [lindex $nline 2]
				set cell "$c_instance/$tcell"
				echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
			} elseif { [lindex $nline 0] == "remove_buffer" } {
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set tcell   [lindex $nline $n_cell]
				set cell $c_instance/$tcell
				echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
			}
		} else {
			if { [lindex $nline 0] == "insert_buffer" } {
				if { [lsearch -exact $nline "get_pins"] != -1 } {
					set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
					set tpin [lindex $nline $n_pin]
					set buf  [lindex $nline [expr $n_pin + 1]]
					set pin "$tpin"
					set tmp_cell [lindex $nline [expr [lsearch -exact $nline "-new_cell_names"] + 1]]
					set new_cell "$tmp_cell"
					echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
				} elseif { [lsearch -exact $nline "get_ports"] != -1 } {
					set n_pin [expr [lsearch -exact $nline "get_ports"] + 1]
					set tpin [lindex $nline $n_pin]
					set buf  [lindex $nline [expr $n_pin + 1]]
					set pin "$tpin"
					set tmp_cell [lindex $nline [expr [lsearch -exact $nline "-new_cell_names"] + 1]]
					set new_cell "$tmp_cell"
					echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
				}
			} elseif { [lindex $nline 0] == "size_cell" } {
				set tcell 	[lindex $nline 1]
				set newref  [lindex $nline 2]
				set cell "$tcell"
				echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
			} elseif { [lindex $nline 0] == "remove_buffer" } {
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set tcell   [lindex $nline $n_cell]
				set cell $tcell
				echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
			}
		}
	}
}	
