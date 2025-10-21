###############################################################################
#
#  FILE:	report_unanno_net_analysis.tcl
#
#  ABSTRACT:	This script is intended to report the analysis result for 
#		the un-annotated nets.
#		
#		pt_shell> report_unanno_net_analysis (-DMSA_slave_mode) <un-annotated net list file>
#
#  AUTHOR:	J.-R. Lee
#
#  HISTORY:	05/07/05	Release
#		05/11/21	Add the case of Input & output floating.
#		08/12/23	Display messages using 'echo' instead of 'puts'.
#		10/09/08	Report error for running this procedure before update_timing
#				in threaded multicore analysis.
#		10/10/07	Bug on variable name was fixed: _pt_version -> _pt_version_.
#		12/01/17	option 'DMSA_slave_mode' is added. if this
# 				script is run in DMSA slave mode, use this
# 				option
#               12/05/08        Bug fix related to DMSA slave mode
###############################################################################

global unanno_scr_version 
set unanno_scr_version "1.4 (2012.1.17)"

global sh_product_version _pt_version_
regexp {[A-Z]-([0-9]+\.[0-9]+)} $sh_product_version all _pt_version_

proc report_unanno_net_analysis { args } {
    global unanno_scr_version
    
    set DMSA_slave_mode false
    parse_proc_arguments -args $args results
    foreach argname [array names results] {
	switch -glob -- $argname {
	    "-DMSA*" {
	    	set DMSA_slave_mode true
	    }
	    default { set file_name $results($argname)}
	}
    }

    set threaded_multicore_flag 0
    if {$DMSA_slave_mode != "true" } {
      if { [threaded_multicore_num] > 1 } {
        set threaded_multicore_flag 1
      }
    } else {
    	echo "Info: DMSA_slave_mode(=true), skip to check threaded_multicore_num"	
    }

    echo "Reporting the analysis result for the un-annotated nets ..."
    echo "Version $unanno_scr_version"

    set fpt [open $file_name r]
    set total_net_num 0
    set drv_floating_net_num 0
    set load_floating_net_num 0
    set drv_load_floating_net_num 0
    set power_net_num 0
    set unknown_net_num 0

    # In threaded mode, the file size is 2 (the only content is just '1')
    if { $threaded_multicore_flag == 1 && [file size $file_name] < 10 } {
      echo "Error: In threaded multicore run, report_unanno_net_analysis must be run after update_timing."
      echo "       Please check followings"
      echo "       1) report_annotated_parasitics is being processed in background before update_timing."
      echo "       2) threaded multicore run"
      echo "       if both 1) and 2) are yes, Please run this procedure after update_timing."
      return 0
    }

    while { [gets $fpt line] >= 0 } {
	set token1 [lindex $line 0]
	set token2 [lindex $line 1]
	set token3 [lindex $line 2]

	if { $token3 == "(driver:" } {
	    incr total_net_num
	    set net [get_nets $token2]

	    set drv_pins [get_pins -leaf -of $net -filter "direction == out || direction == inout" -quiet]
	    set load_pins [get_pins -leaf -of $net -filter "direction == in || direction == inout" -quiet]

	    if { [sizeof_coll $drv_pins] == 0 && [sizeof_coll $load_pins] == 0 } {
		incr drv_load_floating_net_num
		continue
	    }
	    if { [sizeof_coll $drv_pins] == 0 } {
		incr drv_floating_net_num
		continue
	    } elseif { [sizeof_coll $load_pins] == 0 } {
		incr load_floating_net_num
		continue
	    } elseif { [string match "*\*Logic0\*" $token2] == 1 ||
	    	    [string match "*\*Logic1\*" $token2] == 1 } {
		incr power_net_num
		continue
	    } else {
		set power_net_flag 0
		foreach_in_collection pin $drv_pins {
		    set ref_name [get_attr -class cell [get_cell -of $pin -quiet] ref_name]
		    if {$ref_name == "**logic_one**" || $ref_name == "**logic_zero**"} {
			set power_net_flag 1
			break
		    }
		}

		if { $power_net_flag == 1 } {
		    incr power_net_num
		    continue
		}
	    }

	    incr unknown_net_num
	    set unknown_net($unknown_net_num) $token2
	}
    }
    set float_and_power_net_num [expr $drv_load_floating_net_num + $drv_floating_net_num + $load_floating_net_num + $power_net_num]

    echo ""
    echo "-------------------------------------------------------------------------"
    echo "# total unanno nets      : $total_net_num"
    echo "-------------------------------------------------------------------------"
    echo "# driver & load floating : $drv_load_floating_net_num"
    echo "# driver floating        : $drv_floating_net_num"
    echo "# load floating          : $load_floating_net_num"
    echo "# power net              : $power_net_num"
    echo "       (sum)             : $float_and_power_net_num"
    echo "-------------------------------------------------------------------------"
    echo "# unknown reason         : $unknown_net_num"
    echo "-------------------------------------------------------------------------"
    if { $unknown_net_num > 0 } {
	echo ""
        echo "For the following nets, the reason for un-annotation is not known."
	echo "So your analysis is required."
	echo ""
    }
    for { set i 1 } { [expr $i <= $unknown_net_num] } { incr i } {
	echo "$unknown_net($i)"
    }
    echo ""

}

proc threaded_multicore_num { } {
  global _pt_version_

  if { $_pt_version_ < 2009.12 } {
    return 0
  }

  redirect -variable rep { report_host_usage -ver }
  set lines [split $rep "\n"]
  redirect /dev/null { regsub -all -- {[[:space:]]+} $lines " " one_space }

  set limits_flag 0
  set threaded_core_num 1
  foreach line $one_space {
    if { $_pt_version_ >= "2010.06" } {
      if { [lrange $line 0 1] == "Usage limits" } {
        set limits_flag 1
      }

      if { $limits_flag == 1 && [lrange $line 0 1] == "(local process)" } {
        set threaded_core_num [lindex $line 6]
        break
      }
    } elseif { $_pt_version_ == "2009.12" } {
      if { [lrange $line 0 1] == "Hosts limits:" } {
        set limits_flag 1
      }

      if { $limits_flag == 1 && [lrange $line 0 3] == "** local process **" } {
        set threaded_core_num [lindex $line 6]
	break
      }
    }
  }

  return $threaded_core_num
}  
		
define_proc_attributes report_unanno_net_analysis \
    -info "Report the un-annotated net analysis result" \
    -define_args {
        {-DMSA_slave_mode "enabling DMSA_slave_mode" "" boolean optional}
	    {file_name "file of un-annotated net list" file_name string required}
    }
