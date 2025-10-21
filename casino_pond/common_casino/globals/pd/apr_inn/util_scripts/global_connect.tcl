
clearGlobalNets

# STD & Memory
globalNetConnect VDD09_DIG -pin VDD -type pgpin -all ; # pg std cells
globalNetConnect VSSD_CORE -pin VSS -type pgpin -all ; # pg std cells
globalNetConnect VDD09_DIG -pin VDDPE -type pgpin -all ; # pg mem cells
globalNetConnect VDD09_DIG -pin VDDCE -type pgpin -all ; # pg mem cells
globalNetConnect VDD09_DIG -pin VDDE -type pgpin -all ; # pg mem cells
globalNetConnect VSSD_CORE -pin VSSE -type pgpin -all ; # pg mem cells

# tiehi & tielo
globalNetConnect VDD09_DIG -type tiehi -all
globalNetConnect VSSD_CORE -type tielo -all

# UPI
set cellName UPITX18CH_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect VDD09_PLL_TX   -singleInstance $instName -type pgpin -verbose -override -pin       VDD08_PLL
   globalNetConnect VDD09D_TX      -singleInstance $instName -type pgpin -verbose -override -pin       VDD08D_TX
   globalNetConnect VDD12A_PRE_TX  -singleInstance $instName -type pgpin -verbose -override -pin   VDD12A_PRE_TX
   globalNetConnect VDD12A_TX      -singleInstance $instName -type pgpin -verbose -override -pin       VDD12A_TX
   globalNetConnect VDD18_PLL_TX   -singleInstance $instName -type pgpin -verbose -override -pin       VDD18_PLL
   globalNetConnect VDD18_TX       -singleInstance $instName -type pgpin -verbose -override -pin        VDD18_TX
   globalNetConnect VSSD_CORE      -singleInstance $instName -type pgpin -verbose -override -pin             VSS
   globalNetConnect VSS_PLL_TX     -singleInstance $instName -type pgpin -verbose -override -pin         VSS_PLL
   globalNetConnect VSS18_TX       -singleInstance $instName -type pgpin -verbose -override -pin        VSS18_TX
   globalNetConnect VSSA_TX        -singleInstance $instName -type pgpin -verbose -override -pin         VSSA_TX
   globalNetConnect VSSD_TX        -singleInstance $instName -type pgpin -verbose -override -pin         VSSD_TX
   #globalNetConnect REXT_UPI       -singleInstance $instName -type pgpin -verbose -override -pin            EXTR
}

# MIPI
set cellName MIPIRX4CH_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect VDD09_MIPI  -singleInstance $instName -type pgpin -verbose -override -pin   VDD08_MIPI
   globalNetConnect VDD12_MIPI  -singleInstance $instName -type pgpin -verbose -override -pin   VDD12_MIPI
   globalNetConnect VSS_MIPI    -singleInstance $instName -type pgpin -verbose -override -pin   VSS
   globalNetConnect VSSD_CORE    -singleInstance $instName -type pgpin -verbose -override -pin   VSSC
}

# PLL
set cellName PLLTS22ULPAFRAC2
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      if { [lindex [split $a /] end] == "UPI_PLL" } {
         globalNetConnect VDD18_PLL_TX	 -singleInstance $a -type pgpin -verbose -override -pin   VDDHV	
         globalNetConnect VDD09_PLL_TX	 -singleInstance $a -type pgpin -verbose -override -pin   VDDPOST	
         globalNetConnect VDD09_PLL_TX	 -singleInstance $a -type pgpin -verbose -override -pin   VDDREF	
         globalNetConnect VSS_PLL_TX	 -singleInstance $a -type pgpin -verbose -override -pin   VSS	
      } 
      if { [lindex [split $a /] end] == "SSCG_DPLL" } {
         globalNetConnect VDD18_DPLL	 -singleInstance $a -type pgpin -verbose -override -pin   VDDHV	
         globalNetConnect VDD09_DPLL	 -singleInstance $a -type pgpin -verbose -override -pin   VDDPOST	
         globalNetConnect VDD09_DPLL	 -singleInstance $a -type pgpin -verbose -override -pin   VDDREF	
         globalNetConnect VSS_DPLL	 -singleInstance $a -type pgpin -verbose -override -pin   VSS	
      } 
      if { [lindex [split $a /] end] == "SSCG_PLL" } {
         globalNetConnect VDD18_MPLL	 -singleInstance $a -type pgpin -verbose -override -pin  VDDHV	
         globalNetConnect VDD09_MPLL	 -singleInstance $a -type pgpin -verbose -override -pin  VDDPOST	
         globalNetConnect VDD09_MPLL	 -singleInstance $a -type pgpin -verbose -override -pin  VDDREF	
         globalNetConnect VSS_MPLL	 -singleInstance $a -type pgpin -verbose -override -pin  VSS	
      }
   }
}


# EDP
set cellName A38410_EDPRX4CH_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect VDD18VCO_EDP  -singleInstance $instName  -type pgpin -verbose -override -pin VDVCO_EDP
   globalNetConnect VDD09_EDP	  -singleInstance $instName  -type pgpin -verbose -override -pin VDD08_EDP
   globalNetConnect VDD18_EDP	  -singleInstance $instName  -type pgpin -verbose -override -pin VDD18_EDP
   globalNetConnect VSS_EDP	  -singleInstance $instName  -type pgpin -verbose -override -pin VSS_EDP	 
   globalNetConnect VSSD_CORE	  -singleInstance $instName  -type pgpin -verbose -override -pin VSSL	 
   globalNetConnect VSSD_CORE	  -singleInstance $instName  -type pgpin -verbose -override -pin VSSR	 
   #globalNetConnect REXT_EDP	  -singleInstance $instName  -type pgpin -verbose -override -pin REXT	 
}

# OSC
set cellName A38409_RCOSC_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect   VDD09_DIG       -singleInstance $instName -type pgpin -verbose -override -pin  VDD0V8	  
   globalNetConnect   VDD18_OSC       -singleInstance $instName -type pgpin -verbose -override -pin  VDD1V8	  
   globalNetConnect   VSS_OSC         -singleInstance $instName -type pgpin -verbose -override -pin  VSS	  
   globalNetConnect   OSC_VLD08O      -singleInstance $instName -type pgpin -verbose -override -pin  OSC_VLD08O
}

# POR
set cellName A38407_POR_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect  VDD09_DIG     -singleInstance  $instName  -type pgpin -verbose -override -pin VDD0V8	
   globalNetConnect  VDD18_POR     -singleInstance  $instName  -type pgpin -verbose -override -pin VDD1V8	
   globalNetConnect  VSS_POR       -singleInstance  $instName  -type pgpin -verbose -override -pin VSS	
}

# efuse / ESD
# globalNetConnect  VQPS_FUSE1         -singleInstance    -type pgpin -verbose -override -pin      VQPS	
# globalNetConnect  VSS                -singleInstance    -type pgpin -verbose -override -pin      VSS	
# globalNetConnect  VQPS_FUSE2         -singleInstance    -type pgpin -verbose -override -pin      VQPS	
# globalNetConnect  VSS                -singleInstance    -type pgpin -verbose -override -pin      VSS	

# efuse
set cellName TEF22ULP8X32HD18_PHRM
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   globalNetConnect   VDD09_DIG	       -singleInstance  clk_ctrl/u_bisr_ctrl/efuse       -type pgpin -verbose -override -pin VDD	
   globalNetConnect   VQPS_FUSE1       -singleInstance  clk_ctrl/u_bisr_ctrl/efuse       -type pgpin -verbose -override -pin VQPS	
   globalNetConnect   VSSD_CORE	       -singleInstance  clk_ctrl/u_bisr_ctrl/efuse       -type pgpin -verbose -override -pin VSS	
   globalNetConnect   VDD09_DIG	       -singleInstance  clk_ctrl/u_osc_efuse_ctrl/efuse  -type pgpin -verbose -override -pin VDD	
   globalNetConnect   VQPS_FUSE2       -singleInstance  clk_ctrl/u_osc_efuse_ctrl/efuse  -type pgpin -verbose -override -pin VQPS	
   globalNetConnect   VSSD_CORE	       -singleInstance  clk_ctrl/u_osc_efuse_ctrl/efuse  -type pgpin -verbose -override -pin VSS	
}

# DDR PHY master
set cellName dwc_ddrphymaster_top
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instName [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   globalNetConnect   VDD18_DDR   -singleInstance  $instName  -type pgpin -verbose -override -pin VAA	
   globalNetConnect   VDD09_DIG   -singleInstance  $instName  -type pgpin -verbose -override -pin VDD	
   globalNetConnect   VDD12_AC    -singleInstance  $instName  -type pgpin -verbose -override -pin VDDQ	
   globalNetConnect   VSSD_CORE   -singleInstance  $instName  -type pgpin -verbose -override -pin VSS	
}

# DDR PHY acx
set cellName dwc_ddrphyacx4_top_ew
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instNames [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   foreach instName $instNames {
   globalNetConnect   VDD09_DIG      -singleInstance $instName   -type pgpin -verbose -override -pin VDD	
   globalNetConnect   VDD12_AC       -singleInstance $instName   -type pgpin -verbose -override -pin VDDQ	
   globalNetConnect   VSSD_CORE      -singleInstance $instName   -type pgpin -verbose -override -pin VSS	
   }
}

# DDR PHY dyte
set cellName dwc_ddrphydbyte_top_ns
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instNames [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   foreach instName $instNames {
   globalNetConnect    VDD09_DIG	      -singleInstance $instName   -type pgpin -verbose -override -pin VDD	
   globalNetConnect    VDD12_DBYTE	      -singleInstance $instName   -type pgpin -verbose -override -pin VDDQ	
   globalNetConnect    VSSD_CORE	      -singleInstance $instName   -type pgpin -verbose -override -pin VSS	
   }
}

# DDR PHY dwc_ddrphy_decapvddq_ns
set cellName dwc_ddrphy_decapvddq_ns
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instNames [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   foreach instName $instNames {
   globalNetConnect    VDD12_DBYTE	      -singleInstance $instName   -type pgpin -verbose -override -pin VDDQ	
   globalNetConnect    VSSD_CORE	      -singleInstance $instName   -type pgpin -verbose -override -pin VSS	
   }
}

# DDR PHY dwc_ddrphy_decapvddq_ew
set cellName dwc_ddrphy_decapvddq_ew
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   set instNames [dbGet [dbGet -p2 top.insts.cell.name $cellName].name]
   foreach instName $instNames {
   globalNetConnect    VDD12_AC 	      -singleInstance $instName   -type pgpin -verbose -override -pin VDDQ	
   globalNetConnect    VSSD_CORE	      -singleInstance $instName   -type pgpin -verbose -override -pin VSS	
   }
}

# custom IO
if { [dbGet -p3 top.insts.cell.pgTerms.name *PST] != "0x0" } {
   deselectAll
   select_obj  [dbGet -p3 top.insts.cell.pgTerms.name *PST]
   foreach a [dbGet selected] {

      if { [dbGet $a.name u_mem_core/*] != "0x0" } {                    set side L ; # for LEFT-BOTTOM side
      } elseif { [dbGet top.name mem_core_wrap] != "0x0" } {            set side L ; # for LEFT-BOTTOM side
      } elseif { [dbGet $a.pt_y] < 2000 } {                             set side B ; # for BOTTOM side
      } else {                                                          set side T ; # for TOP side
      }     
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VDDPST" } { globalNetConnect  VDD18_DIG_${side}  -singleInstance $instName   -type pgpin -verbose -override -pin VDDPST   }
         if { $b == "VSSPST" } { globalNetConnect  VSSD_IO_${side}    -singleInstance $instName   -type pgpin -verbose -override -pin VSSPST   }
         if { $b == "VDDEOS" } { globalNetConnect  VDDEOS_${side}     -singleInstance $instName   -type pgpin -verbose -override -pin VDDEOS   }
         #if { $b == "POC" }    { globalNetConnect  POC_${side}        -singleInstance $instName   -type pgpin -verbose -override -pin POC      }
         if { $b == "VSS" }    { globalNetConnect  VSSD_CORE          -singleInstance $instName   -type pgpin -verbose -override -pin VSS      }
         if { $b == "VDD" }    { globalNetConnect  VDD09_DIG          -singleInstance $instName   -type pgpin -verbose -override -pin VDD      }
      }
   }
}
deselectAll

# DTI
set cellName dti_tm22ulp_18v33vcfs_prot_s
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   deselectAll
   selectInstByCellName dti*
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSS"  } { globalNetConnect  VSSD_CORE    -singleInstance $instName   -type pgpin -verbose -override -pin VSS   }
         if { $b == "VDD"  } { globalNetConnect  VDD09_DIG    -singleInstance $instName   -type pgpin -verbose -override -pin VDD   }
         if { $b == "VDDO" } { globalNetConnect  VDD33_DIG    -singleInstance $instName   -type pgpin -verbose -override -pin VDDO  }
      }
   }
}
deselectAll

# DPLL IO
set cellName PLLTS22ULPAFRAC2
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      if { [lindex [split $a /] end] == "SSCG_DPLL" } {
         deselectAll
         select_obj  [get_db insts -if { .name == *_DPLL_* && .base_cell.class != core && .base_cell.name == P* }]
         foreach a [dbGet selected] {
            set instName [dbGet $a.name]
            foreach b [dbGet $a.cell.pgTerms.name] {
               if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
               if { $b == "TAVSS"  }    { globalNetConnect  VSS_DPLL      -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
               if { $b == "VSSA"   }    { globalNetConnect  VSS_DPLL      -singleInstance $instName   -type pgpin -verbose -override -pin VSSA    }
               if { $b == "TAVDD"  }    { globalNetConnect  VDD18_DPLL    -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
               if { $b == "VDD08A" }    { globalNetConnect  VDD09_DPLL    -singleInstance $instName   -type pgpin -verbose -override -pin VDD08A  }
               }
         }
      }
   }
}
deselectAll

# MPLL IO
set cellName PLLTS22ULPAFRAC2
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      if { [lindex [split $a /] end] == "SSCG_PLL" } {
         deselectAll
         select_obj  [get_db insts -if { .name == *_MPLL_* && .base_cell.class != core && .base_cell.name == P* }]
         foreach a [dbGet selected] {
            set instName [dbGet $a.name]
            foreach b [dbGet $a.cell.pgTerms.name] {
               if { $b == "VDD18A"  }   { globalNetConnect  VDD18_MPLL    -singleInstance $instName   -type pgpin -verbose -override -pin VDD18A   }
               if { $b == "VSSA"   }    { globalNetConnect  VSS_MPLL      -singleInstance $instName   -type pgpin -verbose -override -pin VSSA    }
               if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
               if { $b == "TAVSS"  }    { globalNetConnect  VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
               if { $b == "TAVDD"  }    { globalNetConnect  VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
               if { $b == "VDD08A" }    { globalNetConnect  VDD09_MPLL    -singleInstance $instName   -type pgpin -verbose -override -pin VDD08A  }
               }
         }
      }
   }
}
deselectAll

# OSC IO
set cellName A38409_RCOSC_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      deselectAll
      select_obj  [get_db insts -if { .name == *_OSC_* && .base_cell.class != core && .base_cell.name == P* }]
      selectInstByCellName PDBA12F70
      foreach a [dbGet selected] {
         set instName [dbGet $a.name]
         foreach b [dbGet $a.cell.pgTerms.name] {
            if { $b == "VSS"     }    { globalNetConnect   VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
            if { $b == "TAVSS"   }    { globalNetConnect   VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
            if { $b == "TAVDD"   }    { globalNetConnect   VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD    }
            if { $b == "AIO"     }    { globalNetConnect   OSC_VLD08O    -singleInstance $instName   -type pgpin -verbose -override -pin AIO  }
            }
      }
   }
}
deselectAll

# POR IO
set cellName A38407_POR_T22ULP_A00
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      deselectAll
      select_obj  [get_db insts -if { .name == *_POR_* && .base_cell.class != core && .base_cell.name == P* }]
      foreach a [dbGet selected] {
         set instName [dbGet $a.name]
         foreach b [dbGet $a.cell.pgTerms.name] {
            if { $b == "VDD18A"  }   { globalNetConnect  VDD18_POR     -singleInstance $instName   -type pgpin -verbose -override -pin VDD18A   }
            if { $b == "VSSA"   }    { globalNetConnect  VSS_POR       -singleInstance $instName   -type pgpin -verbose -override -pin VSSA    }
            if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
            if { $b == "TAVSS"  }    { globalNetConnect  VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
            if { $b == "TAVDD"  }    { globalNetConnect  VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
            }
      }
   }
}
deselectAll

# efuse IO
set cellName TEF22ULP8X32HD18_PHRM
if { [dbGet top.insts.cell.name $cellName] != "0x0" } {
   foreach a [dbGet [dbGet -p2 top.insts.cell.name $cellName].name] {
      deselectAll
      select_obj  [get_db insts -if { .name == *_FUSE1_* && .base_cell.class != core && .base_cell.name == P* }]
      foreach a [dbGet selected] {
         set instName [dbGet $a.name]
         foreach b [dbGet $a.cell.pgTerms.name] {
            if { $b == "VDD18A"  }   { globalNetConnect  VQPS_FUSE1   -singleInstance $instName   -type pgpin -verbose -override -pin VDD18A   }
            if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
            if { $b == "TAVSS"  }    { globalNetConnect  VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
            if { $b == "TAVDD"  }    { globalNetConnect  VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
            }
      }
      deselectAll
      select_obj  [get_db insts -if { .name == *_FUSE2_* && .base_cell.class != core && .base_cell.name == P* }]
      foreach a [dbGet selected] {
         set instName [dbGet $a.name]
         foreach b [dbGet $a.cell.pgTerms.name] {
            if { $b == "VDD18A"  }   { globalNetConnect  VQPS_FUSE2   -singleInstance $instName   -type pgpin -verbose -override -pin VDD18A   }
            if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
            if { $b == "TAVSS"  }    { globalNetConnect  VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
            if { $b == "TAVDD"  }    { globalNetConnect  VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
            }
      }
      deselectAll
      selectInst VSSD_CORE_517_EX
      selectInst VSSD_CORE_518_EX
      selectInst VDD09_DIG_519_EX
      selectInst VDD09_DIG_520_EX
      selectInst VSSD_CORE_521_EX
      selectInst VSSD_CORE_522_EX
      foreach a [dbGet selected] {
         set instName [dbGet $a.name]
         foreach b [dbGet $a.cell.pgTerms.name] {
            if { $b == "VDD08A" }   { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin VDD08A   }
            if { $b == "VSSA"   }   { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin VSSA   }
            if { $b == "VSS"    }    { globalNetConnect  VSSD_CORE     -singleInstance $instName   -type pgpin -verbose -override -pin VSS     }
            if { $b == "TAVSS"  }    { globalNetConnect  VSS_OSC       -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS   }
            if { $b == "TAVDD"  }    { globalNetConnect  VDD18_OSC     -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD   }
            }
      }
   }
}
deselectAll

# for top only
if { [dbGet top.insts.cell.name mem_core_wrap] != "0x0" } {
	foreach a [dbGet [dbGet -p top.insts.cell.name mem_core_wrap].pgTerms.name] {
		globalNetConnect  $a  -singleInstance u_mem_core   -type pgpin -verbose -override -pin $a
	}
}
if { [dbGet top.insts.cell.name input_core] != "0x0" } {
	foreach a [dbGet [dbGet -p top.insts.cell.name input_core].pgTerms.name] {
		globalNetConnect  $a  -singleInstance u_input_core   -type pgpin -verbose -override -pin $a
	}
}

# CLAMP
set lists "PCLAMPEC_V_G PCLAMPEC_H_G"
deselectAll
selectInstByCellName $lists
foreach instName [dbGet selected.name] {
	globalNetConnect  VDD09_DIG  -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD
	globalNetConnect  VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD
}
deselectAll

# additional PAD
set cellLists "PRCUTA2E PVDDA08PRC_V PVSSAXXPC PVSSA08PRC_V PVSSA08PRC_H PFILLERA20 PVDDA08PRC_H"
deselectAll
foreach a $cellLists { if { [dbGet top.insts.cell.name $a] != "0x0" } { selectInstByCellName $a } }
 if { [dbGet selected.name] != "0x0" } {
    foreach a [dbGet selected] {
       set instName [dbGet $a.name]
       if { ([dbGet $a.name u_mem_core/*] != "0x0") || ([dbGet $a.name u_input_core/*] != "0x0") } {
          foreach b [dbGet $a.cell.pgTerms.name] {
             if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  VSS  }
             if { $b == "TACVSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVSS  }
             if { $b == "TACVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD  }
             if { $b == "TAVSS" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  TAVSS  }
             if { $b == "TAVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TAVDD  }
             if { $b == "VSSA" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  VSSA  }
             }
      } elseif { [dbGet $a.pt_y] < 2000 } {
          foreach b [dbGet $a.cell.pgTerms.name] {
             if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  VSS  }
             if { $b == "TACVSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVSS  }
             if { $b == "TACVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD  }
             if { $b == "TAVSS" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  TAVSS  }
             if { $b == "TAVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TAVDD  }
             if { $b == "VSSA" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  VSSA  }
             }
      }
    }
 }
 deselectAll

# PCORNEREA
set cellLists PCORNEREA
deselectAll
foreach a $cellLists { if { [dbGet top.insts.cell.name $a] != "0x0" } { selectInstByCellName $a } }
 if { [dbGet selected.name] != "0x0" } {
    foreach a [dbGet selected] {
       set instName [dbGet $a.name]
       foreach b [dbGet $a.cell.pgTerms.name] {
          if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  VSS  }
          if { $b == "TACVSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVSS  }
          if { $b == "TACVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD  }
          if { $b == "TAVSS" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  TAVSS  }
          if { $b == "TAVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TAVDD  }
          if { $b == "VSSA" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  VSSA  }
          }
    }
 }
 deselectAll

### # input_core
### set instlists "u_input_core/P_VDD09_DIG_R01_ADD P_CORNER_RB u_input_core/P_VDD09_DIG_B49_ADD u_input_core/P_VDD09_DIG_B50_ADD u_input_core/P_VDD09_DIG_B51_ADD u_input_core/P_VDD09_DIG_B52_ADD u_input_core/P_VSSD_CORE_B53_ADD u_input_core/P_VSSD_CORE_B54_ADD u_input_core/P_VSSD_CORE_B55_ADD u_input_core/P_VSSD_CORE_B56_ADD u_input_core/P_VDD09_DIG_B57_ADD u_input_core/P_VDD09_DIG_B58_ADD"
### deselectAll
### selectInst $instlists
### if { [dbGet selected.name] != "0x0" } {
###    foreach a [dbGet selected] {
###       set instName [dbGet $a.name]
###       foreach b [dbGet $a.cell.pgTerms.name] {
###          if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  VSS  }
###          if { $b == "TACVSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVSS  }
###          if { $b == "TACVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD  }
###          if { $b == "TAVSS" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  TAVSS  }
###          if { $b == "TAVDD" }    { globalNetConnect  VDD09_DIG   -singleInstance $instName   -type pgpin -verbose -override -pin  TAVDD  }
###          if { $b == "VSSA" }    { globalNetConnect   VSSD_CORE  -singleInstance $instName   -type pgpin -verbose -override -pin  VSSA  }
###          }
###    }
### }
### deselectAll

# IP CLAMP !!!
deselectAll
selectInst OSC_PCLAMPE_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_OSC   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD18_OSC   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll
selectInst MPLL_VDD18_PCLAMPE_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_MPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD18_MPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll
selectInst MPLL_VDD08_PCLAMPEC_V_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_MPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD09_MPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll
selectInst POR_PCLAMPE_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_POR   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD18_POR   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll
selectInst u_pads/P_VDDQ_ESD
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin VSS }
         if { $b == "VQPS" }    { globalNetConnect  VQPS_FUSE2   -singleInstance $instName   -type pgpin -verbose -override -pin VQPS  }
         }
   }
}
deselectAll
selectInst P_VDDQ_ESD_0
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSS" }    { globalNetConnect  VSSD_CORE   -singleInstance $instName   -type pgpin -verbose -override -pin VSS }
         if { $b == "VQPS" }    { globalNetConnect  VQPS_FUSE1   -singleInstance $instName   -type pgpin -verbose -override -pin VQPS }
         }
   }
}
deselectAll
selectInst DPLL_VDD08_PCLAMPEC_H_G
selectInst ANA38410_DPLL_VDD08_PCLAMPEC_H_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD09_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll
selectInst DPLL_VDD18_PCLAMPE_G
selectInst ANA38410_ANA38410_DPLL_VDD18_PCLAMPE_G
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "VSSESD" }    { globalNetConnect  VSS_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VSSESD }
         if { $b == "VDDESD" }    { globalNetConnect  VDD18_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin VDDESD }
         }
   }
}
deselectAll


deselectAll
selectInst "FFN_PFILLERD_memCore_3_7 FFN_PFILLERD_memCore_3_6 FFN_PFILLERD_memCore_3_5 FFN_PFILLERD_memCore_3_4 FFN_PFILLERD_memCore_3_3 FFN_PFILLERD_memCore_3_2 FFN_PFILLERD_memCore_3_1 FFN_PFILLERD_memCore_3_0 FFN_PFILLERD_memCore_2_2 FFN_PFILLERD_memCore_2_1 FFN_PFILLERD_memCore_2_0 FFN_PFILLERD_memCore_1_0 FFN_PFILLERD_memCore_0_6 FFN_PFILLERD_memCore_0_5 FFN_PFILLERD_memCore_0_4 FFN_PFILLERD_memCore_0_3 FFN_PFILLERD_memCore_0_2 FFN_PFILLERD_memCore_0_1 FFN_PFILLERD_memCore_0_0"
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "TAVSS" }    { globalNetConnect  VSS_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS }
         if { $b == "TAVDD" }    { globalNetConnect  VDD18_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD }
         if { $b == "TACVSS" }    { globalNetConnect  VSS_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin TACVSS }
         if { $b == "TACVDD" }    { globalNetConnect  VDD18_DPLL   -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD}
         }
   }
}
deselectAll

globalNetConnect  VSSD_CORE  -singleInstance   FFN_add_PVSSAXXPC_0 -type pgpin -verbose -override -pin VSSA
globalNetConnect  VSS_OSC  -singleInstance   FFN_add_PVSSAXXPC_0 -type pgpin -verbose -override -pin TAVSS
globalNetConnect  VDD18_OSC  -singleInstance   FFN_add_PVSSAXXPC_0 -type pgpin -verbose -override -pin TAVDD

globalNetConnect  VDD09_DIG  -singleInstance   FFN_add_PVDDA08PC_V_0 -type pgpin -verbose -override -pin VDD08A
globalNetConnect  VSS_OSC  -singleInstance     FFN_add_PVDDA08PC_V_0 -type pgpin -verbose -override -pin TAVSS
globalNetConnect  VDD18_OSC  -singleInstance   FFN_add_PVDDA08PC_V_0 -type pgpin -verbose -override -pin TAVDD

deselectAll
selectInst "FFN_add_PFILLERA_1 VQPS_FUSE2_515_EX VQPS_FUSE2_516_EX VSSD_CORE_517_EX VSSD_CORE_518_EX VDD09_DIG_519_EX VDD09_DIG_520_EX VSSD_CORE_521_EX VSSD_CORE_522_EX VSS_POR_512_EX FFN_add_PFILLERA_5 FFN_add_PFILLERA_6 FFN_add_PFILLERA_7 FFN_add_PFILLERA_8_0 FFN_add_PFILLERA_8_1 FFN_add_PFILLERA_8_2 FFN_add_PFILLERA_8_3 FFN_add_PFILLERA_8_4 FFN_add_PFILLERA_8_5 FFN_add_PFILLERA_8_6 FFN_add_PFILLERA_8_7 FFN_add_PFILLERA_8_8 FFN_add_PFILLERA_9_0 FFN_add_PFILLERA_9_1 FFN_add_PFILLERA_9_2 FFN_add_PFILLERA_9_3 FFN_add_PFILLERA_9_4 FFN_add_PFILLERA_9_5 FFN_add_PFILLERA_9_6 FFN_add_PFILLERA_9_7 FFN_add_PFILLERA_9_8 FFN_add_PFILLERA_9_9 FFN_add_PFILLERA_9_10 FFN_add_PFILLERA_9_11 FFN_add_PFILLERA_9_12 FFN_add_PFILLERA_9_13 VQPS_FUSE1_513_EX VQPS_FUSE1_514_EX FFN_add_PFILLERA_2 FFN_add_PFILLERA_3 FFN_add_PFILLERA_4_0 FFN_add_PFILLERA_4_1 VSS_POR_511_EX VDD18_POR_509_EX VDD18_POR_510_EX FFN_add_PFILLERA_0 VDD18_MPLL_503_EX VDD18_MPLL_504_EX VSS_MPLL_505_EX VDD09_MPLL_506_EX VDD09_MPLL_507_EX VSS_MPLL_508_EX FFN_ADD_PFILLERA20_003 FFN_ADD_PFILLERA20_002 FFN_ADD_PFILLERA20_001 FFN_ADD_PFILLERA20_000"
if { [dbGet selected.name] != "0x0" } {
   foreach a [dbGet selected] {
      set instName [dbGet $a.name]
      foreach b [dbGet $a.cell.pgTerms.name] {
         if { $b == "TAVSS" }    { globalNetConnect  VSS_POR   -singleInstance $instName   -type pgpin -verbose -override -pin TAVSS }
         if { $b == "TAVDD" }    { globalNetConnect  VDD18_POR   -singleInstance $instName   -type pgpin -verbose -override -pin TAVDD }
         if { $b == "TACVSS" }    { globalNetConnect  VSS_POR   -singleInstance $instName   -type pgpin -verbose -override -pin TACVSS }
         if { $b == "TACVDD" }    { globalNetConnect  VDD18_POR  -singleInstance $instName   -type pgpin -verbose -override -pin  TACVDD}
         }
   }
}
deselectAll


# checking
set fo [open ./report/Error_globalNetConnect.tcl w]
foreach instList [ get_db insts -if { .base_cell.class  != "core" } ] {
	if { [get_db $instList .base_cell.pg_base_pins] != "" } {
		if { [get_db $instList .pg_pins] == "" } {
			puts "ERROR Inst : No PG connection for $instList"
			puts $fo "ERROR Inst : No PG connection for $instList"
		} else {
			foreach a [get_db $instList .pg_pins.] {
				if { [get_db $a .net] == ""  } {
					if { [get_db $a -if { .name != "*/POC" } ] != "" } {
						puts "ERROR Pin : No PG connection for $a"
						puts $fo "ERROR Pin : No PG connection for $a"
                                   	}
				}
			}
		}
	}
}
close $fo


