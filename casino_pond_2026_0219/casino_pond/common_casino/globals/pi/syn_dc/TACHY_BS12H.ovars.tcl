set ovars(pi,default_pvt)  "ss_0p72v_m40c"
set ovars(pi,nd2_area)     "0.294" ;# ND2M1NMB 22nm UMC NAND 2 - input cell   

;##########################################################################
;#- syn_dc
;##########################################################################
set ovars(syn_dc,design_format)          "rtl"
set ovars(syn_dc,is_flatten)  "0" ;# boolean: < 0 | 1 >
set ovars(syn_dc,is_dft)      "0" ;# boolean: < 0 | 1 >
set ovars(syn_dc,is_upf)      "0" ;# boolean: < 0 | 1 >
set ovars(syn_dc,is_mcmm)     "0" ;# boolean: < 0 | 1 >
set ovars(syn_dc,target_library) [list \
                            u022lschv08bdhg_072c-40_ssg_ccs.db   \
                            u022lschv08bdlag_072c-40_ssg_ccs.db  \
                            u022lschv08bdlecg_072c-40_ssg_ccs.db \
                            u022lschv08bdrag_072c-40_ssg_ccs.db  \
                            u022lschv08bdrecg_072c-40_ssg_ccs.db \
                            u022lschv08l7bhg_072c-40_ssg_ccs.db  \
                       ]

set ovars(syn_dc,ckg_positive)    "LAGCESM2NMB" 
set ovars(syn_dc,ckg_negative)    "" 
set ovars(syn_dc,mem_ref_name)    "TS*N12FFCLL*"

set ovars(syn_dc,user_dont_use)   "user_dont_use.tcl"   ;# string: file name
set ovars(syn_dc,user_dont_touch) "user_dont_touch.tcl" ;# string: file name
set ovars(syn_dc,library_dont_use_pre_compile_list) "" ;#Tcl file for customized don't use list before first compile
;##########################################################################
;#- lec_fm
;##########################################################################
set ovars(lec_fm,user_ref) "" ;# string: file name
set ovars(lec_fm,user_imp) "" ;# string: file name
set ovars(lec_fm,bbox)     "" ;# string: file name

;##########################################################################
;#- sta_pt
;##########################################################################
set SYNOPSYS_LC_ROOT /mnt/appl/Tools_2024/synopsys/lc/S-2021.06-SP4P ;# TODO

set ovars(sta_pt,is_flatten) "0" ;# boolean: < 0 | 1 >
set ovars(sta_pt,gen_sdf)    "0" ;# boolean: < 0 | 1 >
set ovars(sta_pt,hack_sdf)   "0" ;# boolean: < 0 | 1 >
set ovars(sta_pt,pba)        "path" ;# list: < none | path | exhaustive >

set ovars(sta_pt,extra_setup_uncert)        "0.000" ;# float
set ovars(sta_pt,extra_hold_uncert)         "0.000" ;# float

set ovars(sta_pt,modes)      [list func] ;# list: < misn | func | bist | ssft | scap | socc >
#set ovars(sta_pt,corners)    [list \
#									ss_0p72v_p125c_cmax_setup \
#									ss_0p72v_p125c_cmin_setup \
#									ss_0p72v_p125c_rcmax_setup \
#									ss_0p72v_m40c_cmax_setup \
#									ss_0p72v_m40c_cmin_setup \
#									ss_0p72v_m40c_rcmin_setup \
#									ss_0p72v_p125c_cmax_hold \
#									ss_0p72v_p125c_cmin_hold \
#									ss_0p72v_p125c_rcmax_hold \
#									ss_0p72v_m40c_cmax_hold \
#									ss_0p72v_m40c_cmin_hold \
#									ss_0p72v_m40c_rcmin_hold \
#									ff_0p88v_p125c_cmax_hold \
#									ff_0p88v_p125c_cmin_hold \
#									ff_0p88v_p125c_rcmax_hold \
#									ff_0p88v_m40c_cmax_hold \
#									ff_0p88v_m40c_cmin_hold \
#									ff_0p88v_m40c_rcmin_hold \
#									tt_0p80v_p25c_typical \
#						   ]

set ovars(sta_pt,corners)    [list \
									ss_0p72v_m40c_cmax \
						   ]
;##########################################################################
;#- dmsa
;##########################################################################
set ovars(dmsa,debug)          "0" ;# boolean: < 0 | 1 >
set ovars(dmsa,save_session)   "0" ;# boolean: < 0 | 1 >
set ovars(dmsa,pba)            "path" ;# string: < none | open_site | occuepied_site >
set ovars(dmsa,is_flatten)     "0" ;# boolean: < 0 | 1 >

set ovars(dmsa,teco,physical_aware) "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,physical_mode)  "open_site" ;# string: < none | open_site | occuepied_site >

set ovars(dmsa,teco,fix_leakage)    "0" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_mttv)       "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_max_cap)    "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_noise)      "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_setup)      "1" ;# boolean: < 0 | 1 >
set ovars(dmsa,teco,fix_hold)       "1" ;# boolean: < 0 | 1 >

set ovars(dmsa,teco,target_groups) [list dec_clk]               ;# list: < dec_clk | clk >
set ovars(dmsa,teco,except_groups) [list IN2OUT IN2REG REG2OUT] ;# list: < dec_clk | clk | **async_default** | **clock_gating_default** | IN2OUT | IN2REG | REG2OUT >

set ovars(dmsa,teco,slack_lesser_than)  "" ;# float
set ovars(dmsa,teco,slack_greater_than) "" ;# float 

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
								] ;# list: < ss_0p72v_p125c_cmax_setup | ss_0p72v_p125c_cmin_setup | ss_0p72v_p125c_rcmax_setup \
                                           | ss_0p72v_m40c_cmax_setup  | ss_0p72v_m40c_cmin_setup  | ss_0p72v_m40c_rcmin_setup \
                                           | ss_0p72v_p125c_cmax_hold  | ss_0p72v_p125c_cmin_hold  | ss_0p72v_p125c_rcmax_hold \
                                           | ss_0p72v_m40c_cmax_hold   | ss_0p72v_m40c_cmin_hold   | ss_0p72v_m40c_rcmin_hold \
                                           | ff_0p88v_p125c_cmax_hold  | ff_0p88v_p125c_cmin_hold  | ff_0p88v_p125c_rcmax_hold \
                                           | ff_0p88v_m40c_cmax_hold   | ff_0p88v_m40c_cmin_hold   | ff_0p88v_m40c_rcmin_hold \
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

