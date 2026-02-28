################################################
# DB
################################################
set topName dsc_decode
set db_ver /mnt/data/prjs/ANA6714/db/vers/dc-0.0_dk-0.0_tag-0.0

set verilog ${db_ver}/design/v/dsc_decode_syn.v
set sdc_path ${db_ver}/design/sdc

set techLef  ${db_ver}/pdk/inno_tech/G-PD-EHV22N-GENERIC-EDI-TF-1.0_P3/22nm_EHV_8m0t2a.lef
set stdLef   [glob ${db_ver}/std/lef/*lef*]
set memLef   [glob ${db_ver}/mem/lef/*lef*]

set LIB_path ${db_ver}/*/lib

set aocv_path ${db_ver}/ocv/aocv

set setup_views "func_ss_0p72v_m40c_Cmax func_ss_0p72v_m40c_RCmax func_ss_0p72v_p125c_Cmax "
set hold_views "func_ff_0p88v_p125c_RCmax func_ff_0p88v_m40c_Cmax func_ff_0p88v_m40c_RCmin "

################################################
# Vth type
################################################
set LVT "LMB"
set RVT "NMB"
set HVT "HMA"
set SLVT "SLVT"

################################################
# Route
################################################
set topRoute "ME6"
set botRoute "ME2"
set pName VDDL ; # power name
set gName VSSL ; # ground name

################################################
# export
################################################
set base_path [join [lrange [split [pwd] "/"] 0 4] "/"]
set tag_inn [lindex [split [pwd] "/"] 7]
set run_inn [lindex [split [pwd] "/"] 9]
set tag_pi [regsub {^pd} $tag_inn "pi"]

set outfeedDirName ${base_path}/outfeeds/${topName}/${tag_inn}/${run_inn}
set pi_outfeedDirName ${base_path}/outfeeds/${topName}/${tag_pi}/${run_inn}





################################################
# options
################################################
set maxCpu 4
set DECAP_LIST_SORTED "FILE16HMA FILE16NMB FILE2HMA FILE2NMB FILE32HMA FILE32NMB FILE3HMA FILE3NMB FILE4HMA FILE4NMB FILE64HMA FILE64NMB FILE8HMA FILE8NMB"
set GFILLER_LIST_SORTED "EFILE8NMB EFILE4NMB EFILE32NMB EFILE2NMB EFILE1NMB EFILE16NMB EFILE8HMA EFILE4HMA EFILE32HMA EFILE2HMA EFILE1HMA EFILE16HMA"
set FILLER_LIST_SORTED "FIL16HMA FIL16NMB FIL1HMA FIL1NMB FIL2HMA FIL2NMB FIL32HMA FIL32NMB FIL3HMA FIL3NMB FIL4HMA FIL4NMB FIL64HMA FIL64NMB FIL8HMA FIL8NMB"

set PLACE_UNCERT_VAR 0.08 
set CTS_UNCERT_VAR 0.06
set ROUTE_UNCERT_VAR 0.03
set UNCERT_MAX_BOUND 0.50

set data_max_fanout 31
set data_max_tran 0.300
set data_max_length 600

set ecfFlow false
set usefulSkew false        
set usefulSkewPreCTS false
set usefulSkewCCOpt none  ; # enums={none standard extreme} 
set usefulSkewPostRoute false

set tieHiLoCells "TIE1NMB TIE1HMA"

set HOC_LVT false

set GBAholdOpt false
set holdFixingCellList "
BUFAM4HMA \
BUFAM4NMB \
BUFAM5HMA \
BUFAM5NMB \
BUFAM6HMA \
BUFAM6NMB \
BUFAM8HMA \
BUFAM8NMB \
BUFM4HMA \
BUFM4NMB \
BUFM5HMA \
BUFM5NMB \
BUFM6HMA \
BUFM6NMB \
BUFM8HMA \
BUFM8NMB \
"

################################################
# CTS_OPTION
################################################

set cts_primary_delay_corner  ss_0p72v_m40c_m40c_Cmax
set cts_target_skew 100ps
set cts_target_tran_top 600ps
set cts_target_tran_trunk 600ps
set cts_target_tran_leaf 500ps
set cts_max_fanout 30

set cts_top_net_length 250um
set cts_turnk_net_length 250um
set cts_leaf_net_length 250um

set cts_inverter_cells "CKINVM12LMB CKINVM16LMB CKINVM20LMB CKINVM22LMB CKINVM24LMB CKINVM26LMB CKINVM32LMB CKINVM36LMB CKINVM4LMB CKINVM6LMB CKINVM8LMB"
set cts_buffer_cells "CKBUFM12LMB CKBUFM16LMB CKBUFM20LMB CKBUFM22LMB CKBUFM24LMB CKBUFM26LMB CKBUFM32LMB CKBUFM36LMB CKBUFM4LMB CKBUFM6LMB CKBUFM8LMB"
set cts_cgate_cells "LAGCESM12LMB LAGCESM16LMB LAGCESM24LMB LAGCESM2LMB LAGCESM32LMB   LAGCESM4LMB LAGCESM6LMB LAGCESM8LMB"

set cts_update_io_latency false

################################################
# physical cell
################################################

set rowRightEndCap  FIL2HMA
set rowLeftEndCap   FIL2HMA
set tapCell WT5HMA
set tapCellRule 50

set preDecapCell FILE16HMA
set preDecapPitch 100

################################################
# powerplan
################################################
# checking narrow channel
set narrow_channel_direction_y 40
set narrow_channel_direction_x 50

# M5 stripe over memory
set M5_offset_memory_PG_stripe 1
set M5_PG_memory_width 1
set M5_PG_memory_spacing_bw_PG 0.5
set M5_memory_PG_pitch 15

# M5 stripe between memory
set M5_PG_bw_memory_width 1
set M5_PG_bw_memory_spacing_bw_PG 0.5
set M5_offset_bw_memory_PG_stripe 15

# M5 stripe over core
set M5_PG_core_width 1
set M5_PG_core_spacing_bw_PG 0.5
set M5_PG_core_pitch 15

# M6 stripe
set M6_PG_width 2.5
set M6_PG_spacing_bw_PG 0.5
set M6_PG_pitch 15

# M7 stripe 
set M7_PG_width 2.5
set M7_PG_spacing_bw_PG 0.5
set M7_PG_pitch 6

# M8 stripe 
set M8_PG_width 12
set M8_PG_spacing_bw_PG 3
set M8_PG_pitch 30

    if {[file exists ../common/flow/flow_casino.yaml]} {
    set common "../common"
    } else {
    set common "../../../common"
    }
