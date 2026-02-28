#################################################################################################
##                                                                                             ##
## SAMSUNG FOUNDRY RESERVES THE RIGHT TO CHANGE PRODUCTS, INFORMATION AND SPECIFICATIONS       ##
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
## claim full damages against any party that misappropriates Samsung's trade secrets and/or    ##
## confidential information                                                                    ##
##                                                                                             ##
## All brand names, trademarks and registered trademarks belong to their respective owners.    ##
##                                                                                             ##
## 2016-2018 Samsung Foundry                                                                   ##
##                                                                                             ##
#################################################################################################
##                                                                                             ##
## Title                : icc_eco_to_soce_physical.tcl                                         ##
## Description          : Conversion of the ICC ECO script to the SOC Encounter ECO script     ##
## Process              : Any SEC process                                                      ##
## Author               : CJ Bae                                                               ##
## Initial Release Date : Nov. 30, 2014                                                        ##
## Last Update Date     : Jun. 30, 2015                                                        ##
## Script Version       : V1.00                                                                ##
## Tool Version         : SEC guided PrimeTime version                                         ##
## Usage                :                                                                      ##
##       pt_shell> remote_execute {source $PATH/icc_eco_to_soce_eco.tcl}                       ##
##       pt_shell> remote_execute {Conv_ICC_to_SOCE eco_output.icc.tcl eco_output.soce.tcl}    ##  
#################################################################################################
proc Conv_ICC_to_SOCE_pa { ICC_ECO SOCE_ECO } {
	
	if { [file exists $SOCE_ECO] } {
		sh rm $SOCE_ECO
	}
		
	set infile [open $ICC_ECO r]
	while { [gets $infile line] != -1 } {
		regsub -all {\[get_pins} $line {get_pins} line
		regsub -all {\[get_cells} $line {get_cells} line
		regsub -all {\[get_net} $line {get_net} line
		regsub -all {\}\]} $line \} nline
		

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

## for sub instance 
		if { $c_instance != ""} {

            set icc2_cmd [lindex $nline 0]
        
			if { ${icc2_cmd} == "insert_buffer" } {
                set prev_cmd ${icc2_cmd}
				set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
				set tpin [lindex $nline $n_pin]
				set buf  [lindex $nline [expr $n_pin + 1]]
				set pin "$c_instance/$tpin"
				set tmp_cell [lindex $nline [expr [lsearch -exact $nline "-new_cell_names"] + 1]]
				set new_cell "$tmp_cell"
				set num_set_cl 0
				#echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
				if { [lsearch -exact $nline "-location"] } {
					set n_location [expr [lsearch -exact $nline "-location"] + 1]
					#echo "placeInstance $c_instance/$new_cell [lindex [lindex $nline $n_location] 0] [lindex [lindex $nline $n_location] 1] -placed" >> $SOCE_ECO
				}

				set n_orient [expr [lsearch -exact $nline "-orientation"] + 1]
				set t_orient [lindex $nline $n_orient]

				switch $t_orient {
					N {
						set c_orient R0
					}
					S {
						set c_orient R180
					}
					W {
						set c_orient R90
					}
					E {
						set c_orient R270
					}
					FN {
						set c_orient MY
					}
					FS {
						set c_orient MX
					}
					FW {
						set c_orient MX90
					}
					FE {
						set c_orient MY90
					}
				}
# scott
     echo "ecoAddRepeater -term $pin -cell $buf -name $new_cell -loc \{ [lindex [lindex $nline $n_location] 0] [lindex [lindex $nline $n_location] 1] \} -bufOrient $c_orient " >> $SOCE_ECO

			} elseif { ${icc2_cmd} == "size_cell" } {
                set prev_cmd ${icc2_cmd}
				set tcell 	[lindex $nline 1]
				set newref  [lindex $nline 2]
				set cell "$c_instance/$tcell"
				set num_set_cl 0
				#echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
			} elseif { ${icc2_cmd} == "remove_buffer" } {
                set prev_cmd ${icc2_cmd}
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set tcell   [lindex $nline $n_cell]
				set cell $c_instance/$tcell
				set num_set_cl 0
				echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
			} elseif { ${icc2_cmd} == "add_buffer_on_route" } {
                set prev_cmd ${icc2_cmd}
				set n_cell [expr [lsearch -exact $nline "get_net"] + 2]
# scott : debug
#puts "DBG 1 : $n_cell"
				set start_pin [lindex $nline $n_cell]
# scott : debug
#puts "DBG 2 : $start_pin"

				set num_set_cl 0
				
				set start_cell [get_cells -of $c_instance/$start_pin]
				set n_cell [expr [lsearch -exact $nline "-user_specified_buffers"] + 1]
				set t_cells [lindex $nline $n_cell]
					
				set t_names ""
				set t_refs ""
				set t_locs ""

				for { set t 0} { $t < [expr [llength $t_cells]/5] } {incr t} {
#					set t_names [concat $t_names [lindex $t_cells [expr $t*5]]]
#					set t_refs [concat $t_refs [lindex $t_cells [expr $t*5+1]]]
#					set t_locs [concat $t_locs "\{[lindex $t_cells [expr $t*5+2]]"]
#					set t_locs [concat $t_locs "[lindex $t_cells [expr $t*5+3]]\}"]
					set t_names [lindex $t_cells [expr $t*5]]
					set t_refs  [lindex $t_cells [expr $t*5+1]]
					set t_locs "[lindex $t_cells [expr $t*5+2]]"
					set t_locs [concat $t_locs "[lindex $t_cells [expr $t*5+3]]"]
					echo "ecoAddRepeater -net \[get_attribute \[get_net -of $c_instance/$start_pin\] full_name\] -name \{$t_names\} -cell \{$t_refs\} -offLoadAtLoc \{$t_locs\}" >> $SOCE_ECO
					set t_names ""
					set t_refs ""
					set t_locs ""
				}		

#				echo "ecoAddRepeater -net \[get_attribute \[get_net -of $c_instance/$start_pin\] name\] -name \{$t_names\} -cell \{$t_refs\} -loc \{$t_locs\}" >> $SOCE_ECO

			} elseif { ${icc2_cmd} == "set_cell_location" } {
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set t_cell [lindex $nline $n_cell]
				set n_cor  [expr [lsearch -exact $nline "-coordinates"] + 1]
				set t_x_cor [lindex [lindex $nline $n_cor] 0]
				set t_y_cor [lindex [lindex $nline $n_cor] 1]
				set n_orient [expr [lsearch -exact $nline "-orientation"] + 1]
				set t_orient [lindex $nline $n_orient]

				switch $t_orient {
					N {
						set c_orient R0
					}
					S {
						set c_orient R180
					}
					W {
						set c_orient R90
					}
					E {
						set c_orient R270
					}
					FN {
						set c_orient MY
					}
					FS {
						set c_orient MX
					}
					FW {
						set c_orient MX90
					}
					FE {
						set c_orient MY90
					}
				}


				if { $num_set_cl == 0 } {
		            if { $c_instance != ""} {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $c_instance/$t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                        switch -exact ${prev_cmd} {
                            size_cell {
				                echo "ecoChangeCell -inst $c_instance/$t_cell -cell $newref" -loc \{ $t_x_cor $t_y_cor \} -orient \{ $c_orient \} >> $SOCE_ECO
                            }
                            add_buffer_on_route {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $c_instance/$t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                            }
                            default { }
                        }
                    } else {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                        switch -exact ${prev_cmd} {
                            size_cell {
				                echo "ecoChangeCell -inst $t_cell -cell $newref" -loc \{ $t_x_cor $t_y_cor \} -orient \{ $c_orient \} >> $SOCE_ECO
                            }
                            add_buffer_on_route {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                            }
                            default { }
                        }
                    }
				}
				incr num_set_cl
			}

## for top instance
		} else {

            set icc2_cmd [lindex $nline 0]

			if { ${icc2_cmd} == "insert_buffer" } {
                set prev_cmd ${icc2_cmd}
				set n_pin [expr [lsearch -exact $nline "get_pins"] + 1]
				set tpin [lindex $nline $n_pin]
				set buf  [lindex $nline [expr $n_pin + 1]]
				set pin "$tpin"
				set tmp_cell [lindex $nline [expr [lsearch -exact $nline "-new_cell_names"] + 1]]
				set new_cell "$tmp_cell"
				set num_set_cl 0
				#echo "AddBuf {$pin} $buf 1 $new_cell" >> $SOCE_ECO
				if { [lsearch -exact $nline "-location"] } {
					set n_location [expr [lsearch -exact $nline "-location"] + 1]
					#echo "placeInstance $new_cell [lindex [lindex $nline $n_location] 0] [lindex [lindex $nline $n_location] 1] -placed " >> $SOCE_ECO
				}

				set n_orient [expr [lsearch -exact $nline "-orientation"] + 1]
				set t_orient [lindex $nline $n_orient]

				switch $t_orient {
					N {
						set c_orient R0
					}
					S {
						set c_orient R180
					}
					W {
						set c_orient R90
					}
					E {
						set c_orient R270
					}
					FN {
						set c_orient MY
					}
					FS {
						set c_orient MX
					}
					FW {
						set c_orient MX90
					}
					FE {
						set c_orient MY90
					}
					default {
						set c_orient R0
					}
				}
# scott
     echo "ecoAddRepeater -term $pin -cell $buf -name $new_cell -loc \{ [lindex [lindex $nline $n_location] 0] [lindex [lindex $nline $n_location] 1] \} -bufOrient $c_orient " >> $SOCE_ECO

			} elseif { ${icc2_cmd} == "size_cell" } {
                set prev_cmd ${icc2_cmd}
				set tcell 	[lindex $nline 1]
				set newref  [lindex $nline 2]
				set cell "$tcell"
				set num_set_cl 0
				#echo "ecoChangeCell -inst $cell -cell $newref" >> $SOCE_ECO
			} elseif { ${icc2_cmd} == "remove_buffer" } {
                set prev_cmd ${icc2_cmd}
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set tcell   [lindex $nline $n_cell]
				set cell $tcell
				set num_set_cl 0
				echo "ecoDeleteRepeater -inst $cell" >> $SOCE_ECO
			} elseif { ${icc2_cmd} == "add_buffer_on_route" } {
                set prev_cmd ${icc2_cmd}
				set n_cell [expr [lsearch -exact $nline "get_net"] + 2]
# scott : debug
puts "DBG 1 : $n_cell"
				set start_pin [lindex $nline $n_cell]
# scott : debug
puts "DBG 2 : $start_pin"

				set num_set_cl 0

				if { [get_pins -quiet $start_pin] == "" && [get_ports -quiet $start_pin] == "" } {

# scott : debug
#puts "DBG 4 : $num_set_cl"
# scott modified
					#puts "SEC-Error: No pins or ports matched $start_pins"
					puts "SEC-Error: No pins or ports matched start_pins : $start_pin"
				}

# scott : debug
#puts "DBG 4 : $start_pin"
				set start_cell [get_cells -of $start_pin]
				set n_cell [expr [lsearch -exact $nline "-user_specified_buffers"] + 1]
				set t_cells [lindex $nline $n_cell]
					
				set t_names ""
				set t_refs ""
				set t_locs ""

				for { set t 0} { $t < [expr [llength $t_cells]/5] } {incr t} {
					#set t_names [concat $t_names [lindex $t_cells [expr $t*5]]]
					#set t_refs [concat $t_refs [lindex $t_cells [expr $t*5+1]]]
					#set t_locs [concat $t_locs "\{[lindex $t_cells [expr $t*5+2]]"]
					#set t_locs [concat $t_locs "[lindex $t_cells [expr $t*5+3]]\}"]
					set t_names [lindex $t_cells [expr $t*5]]
					set t_refs [lindex $t_cells [expr $t*5+1]]
					set t_locs "[lindex $t_cells [expr $t*5+2]]"
					set t_locs [concat $t_locs "[lindex $t_cells [expr $t*5+3]]"]
					echo "ecoAddRepeater -net \[get_attribute \[get_net -of $start_pin\] name\] -name \{$t_names\} -cell \{$t_refs\} -offLoadAtLoc \{$t_locs\}" >> $SOCE_ECO

					set t_names ""
					set t_refs ""
					set t_locs ""
				}		

				#echo "ecoAddRepeater -net \[get_attribute \[get_net -of $start_pin\] name\] -name \{$t_names\} -cell \{$t_refs\} -loc \{$t_locs\}" >> $SOCE_ECO


			} elseif { ${icc2_cmd} == "set_cell_location" } {
				set n_cell [expr [lsearch -exact $nline "get_cells"] + 1]
				set t_cell [lindex $nline $n_cell]
				set n_cor  [expr [lsearch -exact $nline "-coordinates"] + 1]
				set t_x_cor [lindex [lindex $nline $n_cor] 0]
				set t_y_cor [lindex [lindex $nline $n_cor] 1]
				set n_orient [expr [lsearch -exact $nline "-orientation"] + 1]
				set t_orient [lindex $nline $n_orient]

				switch $t_orient {
					N {
						set c_orient R0
					}
					S {
						set c_orient R180
					}
					W {
						set c_orient R90
					}
					E {
						set c_orient R270
					}
					FN {
						set c_orient MY
					}
					FS {
						set c_orient MX
					}
					FW {
						set c_orient MX90
					}
					FE {
						set c_orient MY90
					}
				}
				if { $num_set_cl == 0 } {
		            if { $c_instance != ""} {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $c_instance/$t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                        switch -exact ${prev_cmd} {
                            size_cell {
				                echo "ecoChangeCell -inst $c_instance/$t_cell -cell $newref" -loc \{ $t_x_cor $t_y_cor \} -orient \{ $c_orient \} >> $SOCE_ECO
                            }
                            add_buffer_on_route {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $c_instance/$t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                            }
                            default { }
                        }
                    } else {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                        switch -exact ${prev_cmd} {
                            size_cell {
				                echo "ecoChangeCell -inst $t_cell -cell $newref" -loc \{ $t_x_cor $t_y_cor \} -orient \{ $c_orient \} >> $SOCE_ECO
                            }
                            add_buffer_on_route {
                        #echo "placeInstance \[get_attribute \[get_cells -hierarchical -filter \"full_name =~ $t_cell\"\] full_name\] $t_x_cor $t_y_cor $c_orient -placed" >> $SOCE_ECO
                            }
                            default { }
                        }

                    }
				}
				incr num_set_cl
			}
		}
	}
}	


# temp
#source /home1/PROJECT/ANA38410_Rev0/PI/4_Postlayout/sta/common/vth_rpt.TSMC22ULP.tcl
#vth_rpt > Vth_Ratio_${what}.rpt
