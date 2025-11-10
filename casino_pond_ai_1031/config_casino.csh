#! /bin/csh -f
##################################
# env   (casino - workspace)     #
##################################
unsetenv casino_*

setenv casino_prj_base                 "/mnt/data/prjs"
setenv casino_prj_name                 "ANA6716"
setenv casino_design_ver               "net-2.2"
setenv casino_dk_ver                   "dk-2.5"
setenv casino_tag                      "tag-0.0"
setenv casino_is_top                   "1"
setenv casino_top_name                 "ANA6716"
setenv casino_all_blks                 "ANA6716 fb_left fb_right"
##################################
# env   (casino/general)         #
##################################
setenv casino_pond                 "$casino_prj_base/$casino_prj_name/casino_pond"
# can be added more here ending in _py in order
setenv casino_dk_mgr_py                $casino_pond/dkm_casino.py
setenv casino_ws_mgr_py                $casino_pond/wsm_casino.py
setenv casino_flow_mgr_py              $casino_pond/fm_casino.py
setenv casino_ws_tags_py               $casino_pond/wsnv_casino.py
setenv casino_ws_tree_py               $casino_pond/treem_casino.py
setenv casino_teco_py                  $casino_pond/teco_casino.py
setenv casino_timer_py                 $casino_pond/timer_casino.py
setenv casino_rdl_py                   $casino_pond/rdl_casino.py
setenv casino_FastTrack_py             $casino_pond/ftrack_casino.py
setenv casino_hawkeye_py               $casino_pond/hawkeye_casino.py
#setenv casino_indicator_py             $casino_pond/indicator_casino.py

# tools env
setenv casino_all_tools_env            $casino_pond/all_tools_env.csh
##################################
# env   (casino/alias-csh)       #
##################################
alias csnprj    'echo "# prj_base : going to $prj_base " ; cd $prj_base'
alias csnmain   '$casino_pond/casino.py'
alias csntm     '$casino_pond/timer_casino.py'
alias csnteco   '$casino_pond/teco_casino.py'
alias csndkm    '$casino_pond/dkm_casino.py'
alias csnfm     '$casino_pond/fm_casino.py'
alias csnwsm    '$casino_pond/wsm_casino.py'
alias csnwsnv   '$casino_pond/wsnv_casino.py'
alias csnindi   '$casino_pond/indicator_casino.py'
alias csnftr    '$casino_pond/ftrack_casino.py'
alias csntree   '$casino_pond/treem_casino.py'
alias csn       'source $casino_pond/../:casino.csh' ; # CASINO text mode
alias csngui    '$casino_pond/casino_gui.py'         ; # CASINO gui mode
