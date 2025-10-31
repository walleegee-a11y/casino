# : ################################################
# : # DB
# : ################################################
# : set topName dsc_decode
# : set db_ver /mnt/data/prjs/ANA6716/dbs/vers/net-0.0_dk-0.0_tag-0.0
# :
# : set verilog ${db_ver}/design/v/dsc_decode_syn.v
# : set sdc_path ${db_ver}/design/sdc
# :
# : set techLef  ${db_ver}/pdk/inno_tech/G-PD-EHV22N-GENERIC-EDI-TF-1.0_P3/22nm_EHV_8m0t2a.lef
# : set stdLef   [glob ${db_ver}/std/lef/*lef*]
# : set memLef   [glob ${db_ver}/mem/lef/*lef*]
# :
# : set LIB_path ${db_ver}/*/lib
# :
# : set aocv_path ${db_ver}/pdk/ocv/aocv
# : set qrc_path ${db_ver}/pdk/qrc_tech
# :
# : set setup_views "func_ss_0p72v_m40c_Cmax func_ss_0p72v_m40c_RCmax func_ss_0p72v_p125c_Cmax "
# : set hold_views "func_ff_0p88v_p125c_RCmax func_ff_0p88v_m40c_Cmax func_ff_0p88v_m40c_RCmin "
# :
# :
# :     if {[file exists ../common/flow/flow_casino.yaml]} {
# :     set common "../common"
# :     } else {
# :     set common "../../../common"
# :     }
# :


# : ################################################
# : # Vth type
# : ################################################
# : set LVT "LMB"
# : set RVT "NMB"
# : set HVT "HMA"
# : set SLVT "SLVT"
# :
# : ################################################
# : # Design Option
# : ################################################
# : set maxCpu 4
# : set topRoute "ME6"
# : set botRoute "ME2"
# : set pName VDDL ; # power name
# : set gName VSSL ; # ground name
# : set UNCERT_MAX_BOUND 0.50
# :
# : ################################################
# : # export
# : ################################################
# : set base_path [join [lrange [split [pwd] "/"] 0 4] "/"]
# : set tag_inn [lindex [split [pwd] "/"] 7]
# : set run_inn [lindex [split [pwd] "/"] 9]
# : set tag_pi [regsub {^pd} $tag_inn "pi"]
# :
# : set outfeedDirName ${base_path}/outfeeds/${topName}/${tag_inn}/${run_inn}
# : set pi_outfeedDirName ${base_path}/outfeeds/${topName}/${tag_pi}/${run_inn}





################################################
# init Option
################################################
#TieCell
    set tieHiLoCells "TIE1NMB TIE1HMA"

#Endcap
    set rowRightEndCap  FIL2HMA
    set rowLeftEndCap   FIL2HMA

#Well tap
    set tapCell WT5HMA
    set tapCellRule 50

#Pre decap
    set preDecapCell FILE16HMA
    set preDecapPitch 100

#Power Plan
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


################################################
# Place
################################################
set PLACE_UNCERT_VAR 0.08
set data_max_fanout 31
set data_max_tran 0.300
set data_max_length 600
set ecfFlow false
set usefulSkew false
set usefulSkewPreCTS false
set HOC_LVT false


################################################
# cts
################################################
set CTS_UNCERT_VAR 0.06
set usefulSkewCCOpt none  ; # enums={none standard extreme}

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
# route
################################################
set ROUTE_UNCERT_VAR 0.03
set usefulSkewPostRoute false
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
# chipfinish
################################################

#Finish Cell
    set DECAP_LIST_SORTED "FILE16HMA FILE16NMB FILE2HMA FILE2NMB FILE32HMA FILE32NMB FILE3HMA FILE3NMB FILE4HMA FILE4NMB FILE64HMA FILE64NMB FILE8HMA FILE8NMB"
    set GFILLER_LIST_SORTED "EFILE8NMB EFILE4NMB EFILE32NMB EFILE2NMB EFILE1NMB EFILE16NMB EFILE8HMA EFILE4HMA EFILE32HMA EFILE2HMA EFILE1HMA EFILE16HMA"
    set FILLER_LIST_SORTED "FIL16HMA FIL16NMB FIL1HMA FIL1NMB FIL2HMA FIL2NMB FIL32HMA FIL32NMB FIL3HMA FIL3NMB FIL4HMA FIL4NMB FIL64HMA FIL64NMB FIL8HMA FIL8NMB"

;##########################################################################
;#- PI
;##########################################################################
set ovars(pi,default_pvt) "ss_0p72v_m40c" ;# string

;##########################################################################
;#- lec_fm
;##########################################################################
## TODO(ANA6716) For blk lec
set ovars(lec_fm,user_ref) ""
set ovars(lec_fm,user_imp) ""

## TODO(ANA6716) Fix error (Add bbox variable) & For blk lec
set ovars(lec_fm,top_only) "0" ;# boolean: < 0 | 1 >

#set ovars(lec_fm,bbox) ""
set ovars(lec_fm,bbox_1) ""
set ovars(lec_fm,bbox_2) ""

## TODO(ANA6716) For flatten lec
set ovars(lec_fm,is_flatten) "1" ;# boolean: < 0 | 1 >

set ovars(lec_fm,reference,top_net)   "/mnt/data/prjs/ANA6716/dbs/interface/from_customer/12_20251017_NET/ANA6716_UMC22eHV_7T_pre0a_topo.scaniso2b.v" ;# ref_path
set ovars(lec_fm,reference,sub_net_1) "/mnt/data/prjs/ANA6716/dbs/interface/from_customer/09_20251013_FB_NET/ANA6716_release_251013/fb_right_UMC22eHV_7T_pre0c_topo.scaniso2.v" ;# ref_path
set ovars(lec_fm,reference,sub_net_2) "/mnt/data/prjs/ANA6716/dbs/interface/from_customer/09_20251013_FB_NET/ANA6716_release_251013/fb_left_UMC22eHV_7T_pre0c_topo.scaniso2.v" ;# ref_path

set ovars(lec_fm,sub_block_version,fb_right) "01_net-08_CHANNEL_3um-fe00_te00_pv00"
set ovars(lec_fm,sub_block_version,fb_left)  "01_net-08_CHANNEL_3um-fe00_te00_pv00"

set ovars(lec_fm,implementation,top_net)   "${PD_OUT_PATH}/netlist/${top_design}.v" ;# imp_path 
set ovars(lec_fm,implementation,sub_net_1) "${OUTFEED_PATH}/fb_right/pd___${db_ver}/$ovars(lec_fm,sub_block_version,fb_right)/netlist/fb_right.v" ;# imp_path 
set ovars(lec_fm,implementation,sub_net_2) "${OUTFEED_PATH}/fb_left/pd___${db_ver}/$ovars(lec_fm,sub_block_version,fb_left)/netlist/fb_left.v" ;# imp_path 


;##########################################################################
;#- sta_pt
;##########################################################################
set SYNOPSYS_LC_ROOT /mnt/appl/Tools_2024/synopsys/lc/S-2021.06-SP4P ;# TODO

set ovars(sta_pt,sub_block_list) ""
set ovars(sta_pt,sub_block_location_file) "/mnt/data/prjs/ANA6716/works_rachel.han/sub_block_location.info"
set ovars(sta_pt,sub_block_version,fb_right) "01_net-08_CHANNEL_3um-fe00_te00_pv00"
set ovars(sta_pt,sub_block_version,fb_left)  "01_net-08_CHANNEL_3um-fe00_te00_pv00"

set ovars(sta_pt,is_flatten) "1" ;# boolean: < 0 | 1 >
set ovars(sta_pt,hpdf_level) "top" ;# string: < top | intermediate | bottom >
set ovars(sta_pt,gen_sdf)    "0" ;# boolean: < 0 | 1 >
set ovars(sta_pt,hack_sdf)   "0" ;# boolean: < 0 | 1 >
set ovars(sta_pt,pba)        "path" ;# list: < none | path | exhaustive >

set ovars(sta_pt,extra_setup_uncert)        "0.000" ;# float
set ovars(sta_pt,extra_hold_uncert)         "0.000" ;# float

set ovars(sta_pt,modes)      [list func misn ssft scap] ;# list: < misn | func | bist | ssft | scap | socc >
#set ovars(sta_pt,modes)      [list  misn] ;# list: < misn | func | bist | ssft | scap | socc >
#set ovars(sta_pt,corners)    [list \
#                                    ss_0p72v_p125c_cmax_setup \
#                                    ss_0p72v_p125c_cmin_setup \
#                                    ss_0p72v_p125c_rcmax_setup \
#                                    ss_0p72v_m40c_cmax_setup \
#                                    ss_0p72v_m40c_cmin_setup \
#                                    ss_0p72v_m40c_rcmin_setup \
#                                    ss_0p72v_p125c_cmax_hold \
#                                    ss_0p72v_p125c_cmin_hold \
#                                    ss_0p72v_p125c_rcmax_hold \
#                                    ss_0p72v_m40c_cmax_hold \
#                                    ss_0p72v_m40c_cmin_hold \
#                                    ss_0p72v_m40c_rcmin_hold \
#                                    ff_0p88v_p125c_cmax_hold \
#                                    ff_0p88v_p125c_cmin_hold \
#                                    ff_0p88v_p125c_rcmax_hold \
#                                    ff_0p88v_m40c_cmax_hold \
#                                    ff_0p88v_m40c_cmin_hold \
#                                    ff_0p88v_m40c_rcmin_hold \
#                                    tt_0p80v_p25c_typical \
#                           ]

#- Pre
set ovars(sta_pt,corners)    [list \
                                    ff_0p88v_p125c_rcmax \
                                    ss_0p72v_m40c_cmax \
                           ]
;##########################################################################
;#- dmsa
;##########################################################################
set ovars(dmsa,debug)          "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,save_session)   "1" ;# boolean: < 0 | 1 >

set ovars(dmsa,teco,physical_aware) "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,physical_mode)  "open_site" ;# string: < none | open_site | occuepied_site >
                                               ;# ${phy_mode} would be gated by ${phy_mode} as below:
                                               ;# run_sta_pt.tcl) if { !${phy_aware} } { set phy_mode "none" }
set ovars(dmsa,teco,pba)            "path" ;# string: < none | path | exhaustive | ml_exhaustive >

set ovars(dmsa,teco,fix_leakage)    "0" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_mttv)       "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_max_cap)    "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_noise)      "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_setup)      "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_hold)       "1" ;# boolean: < 0 | 1 >

set ovars(dmsa,teco,target_groups) [list dec_clk]               ;# list: < dec_clk | clk >
set ovars(dmsa,teco,except_groups) [list IN2OUT IN2REG REG2OUT] ;# list: < clocks_described_in_SDC | **async_default** | **clock_gating_default** | IN2OUT | IN2REG | REG2OUT >
                                                           ;# only the groups excluding the listed ones are assigned using the `-group` option.
                                                           ;#  If both options are specified, `target_group` excluding `except_group` is assigned using the `-group` option.
                                                           ;#  Both options are applicable only to the `fix_eco_timing` command.

set ovars(dmsa,teco,slack_lesser_than)  "" ;# float:
set ovars(dmsa,teco,slack_greater_than) "" ;# float:
                                      ;#  To fix setup timing violations with slack between 0 and -0.2, you can use the following options:
                                      ;#   -> fix_eco_timing -type setup -slack_lesser_than 0 -slack_greater_than -0.2
                                      ;#  Both options are applicable only to the `fix_eco_timing` command.

set ovars(dmsa,teco,modes)      [list func] ;# list: < misn | func | bist | ssft | scap | socc >
set ovars(dmsa,teco,corners)    [list \
                                    ss_0p72v_p125c_cmax_setup \
                                    ss_0p72v_p125c_cmin_setup \
                                    ss_0p72v_p125c_rcmax_setup \
                                    ss_0p72v_m40c_cmax_setup \
                                    ss_0p72v_m40c_cmin_setup \
                                    ss_0p72v_m40c_rcmin_setup \
                                    ss_0p72v_p125c_cmax_hold \
                                    ss_0p72v_p125c_cmin_hold \
                                    ss_0p72v_p125c_rcmax_hold \
                                    ss_0p72v_m40c_cmax_hold \
                                    ss_0p72v_m40c_cmin_hold \
                                    ss_0p72v_m40c_rcmin_hold \
                                    ff_0p88v_p125c_cmax_hold \
                                    ff_0p88v_p125c_cmin_hold \
                                    ff_0p88v_p125c_rcmax_hold \
                                    ff_0p88v_m40c_cmax_hold \
                                    ff_0p88v_m40c_cmin_hold \
                                    ff_0p88v_m40c_rcmin_hold \
                                    tt_0p80v_p25c_typical \
                           ];# list : <\
                                   | ss_0p72v_p125c_cmax_setup \
                                   | ss_0p72v_p125c_cmin_setup \
                                   | ss_0p72v_p125c_rcmax_setup \
                                   | ss_0p72v_m40c_cmax_setup \
                                   | ss_0p72v_m40c_cmin_setup \
                                   | ss_0p72v_m40c_rcmin_setup \
                                   | ss_0p72v_p125c_cmax_hold \
                                   | ss_0p72v_p125c_cmin_hold \
                                   | ss_0p72v_p125c_rcmax_hold \
                                   | ss_0p72v_m40c_cmax_hold \
                                   | ss_0p72v_m40c_cmin_hold \
                                   | ss_0p72v_m40c_rcmin_hold \
                                   | ff_0p88v_p125c_cmax_hold \
                                   | ff_0p88v_p125c_cmin_hold \
                                   | ff_0p88v_p125c_rcmax_hold \
                                   | ff_0p88v_m40c_cmax_hold \
                                   | ff_0p88v_m40c_cmin_hold \
                                   | ff_0p88v_m40c_rcmin_hold \
                                   | tt_0p80v_p25c_typical >



set ovars(dmsa,pre_source) "dmsa_pre_source.tcl" ;# string: file name
set ovars(dmsa,dont_touch) "dmsa_dont_touch.tcl" ;# string: file name
set ovars(dmsa,dont_use)   [list */GH* */*AM* */*M0*]

set ovars(dmsa,filler_cells) [list \
                                        FILE16HMA FILE16NMB FILE2HMA FILE2NMB FILE32HMA FILE32NMB FILE3HMA FILE3NMB FILE4HMA FILE4NMB FILE64HMA FILE64NMB FILE8HMA FILE8NMB \
                                        EFILE8NMB EFILE4NMB EFILE32NMB EFILE2NMB EFILE1NMB EFILE16NMB EFILE8HMA EFILE4HMA EFILE32HMA EFILE2HMA EFILE1HMA EFILE16HMA \
                                        FIL16HMA FIL16NMB FIL1HMA FIL1NMB FIL2HMA FIL2NMB FIL32HMA FIL32NMB FIL3HMA FIL3NMB FIL4HMA FIL4NMB FIL64HMA FIL64NMB FIL8HMA FIL8NMB \
                             ]

set ovars(dmsa,drc,invs)   [list CKINVM8NMB CKINVM12NMB CKINVM16NMB]
set ovars(dmsa,drc,bufs)   [list BUFM4NMB BUFM8NMB BUFM12NMB BUFM16NMB BUFM20NMB]
set ovars(dmsa,setup,bufs) [list BUFM2NMB BUFM3NMB BUFM4NMB BUFM5NMB BUFM6NMB BUFM8NMB BUFM12NMB BUFM16NMB BUFM20NMB]
set ovars(dmsa,hold,bufs)  [list \
                                        BUFM2HMA BUFM3HMA BUFM4HMA BUFM5HMA BUFM6HMA BUFM8HMA \
                                        BUFM2NMB BUFM3NMB BUFM4NMB BUFM5NMB BUFM6NMB BUFM8NMB \
                                        DEL1M2HMA DEL1M4HMA DEL1M8HMA DEL2M2HMA DEL2M4HMA DEL2M8HMA DEL3M2HMA DEL3M4HMA DEL3M8HMA DEL4M2HMA DEL4M4HMA DEL4M8HMA \
                                        DEL1M2NMB DEL1M4NMB DEL1M8NMB DEL2M2NMB DEL2M4NMB DEL2M8NMB DEL3M2NMB DEL3M4NMB DEL3M8NMB DEL4M2NMB DEL4M4NMB DEL4M8NMB \
                           ]

