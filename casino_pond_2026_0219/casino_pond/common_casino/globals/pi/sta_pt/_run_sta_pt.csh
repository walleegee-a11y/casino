#!/bin/csh -f
setenv SYNOPSYS_LC_ROOT "/mnt/appl/Tools_2024/synopsys/lc/S-2021.06-SP4P"
#    1 2   3    4    5       6                  7          8                           9    10                     11
# ex) /mnt/data/prjs/ANA6714/works_sincere.baek/dsc_decode/pi___rtl-0.0_dk-0.0_tag-0.0/runs/01_IMSI_fe00_te00_pv00/sta_pt
setenv prj_name   `pwd  | awk -F / '{print $(NF-6)}'`
setenv top_design `pwd  | awk -F / '{print $(NF-4)}'`
setenv ws         `pwd  | awk -F / '{print $(NF-3)}'`
setenv run_ver    `pwd  | awk -F / '{print $(NF-1)}'`
setenv stage      `pwd  | awk -F / '{print $NF}'`

setenv db_ver     `echo $ws | awk -F ___ '{print $2}'`

# path
setenv PRJ_HOME   `pwd | sed 's;/works_.*;;g'`
setenv RUN_PATH   `pwd | sed 's;/sta_pt.*;;g'`

setenv COMMON_PATH        ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common
setenv COMMON_STA_PT      ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/common/globals/pi/sta_pt

setenv RUN_COMMON_PATH    ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common
setenv RUN_COMMON_PI      ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi
setenv RUN_COMMON_STA_PT  ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common/globals/pi/sta_pt

setenv OUTFEED_PATH       ${PRJ_HOME}/outfeeds
setenv PI_OUT_PATH        ${OUTFEED_PATH}/${top_design}/pi___${db_ver}/${run_ver}
setenv PD_OUT_PATH        ${OUTFEED_PATH}/${top_design}/pd___${db_ver}/${run_ver}
setenv PD_DONE_FILE       ${PD_OUT_PATH}/SMC.done

# backup old run data
source ${RUN_COMMON_PI}/backup_old_run.csh
#- generate ${prj_name}.${stage}.ovars.csh
${RUN_COMMON_PATH}/globals/pi/get_ovars.tcl ;# execute TCL file
source ./${prj_name}.${stage}.ovars.csh
if (-e ./${prj_name}.sta_pt.teco.csh) source ./sta_pt_teco.csh ;# for 'teco' task

#- touch
if !(${PWD} =~ "*-fe*_te*_pv*") setenv pre_post "pre"
if  (${PWD} =~ "*-fe*_te*_pv*") setenv pre_post "post"

#while (${pre_post} == "post" && ! -e ${PD_DONE_FILE} )
#    echo "`date`: waiting export (${PD_DONE_FILE})"
#    sleep 60
#end

# if ( "${pre_post}" == "post" ) then
# 
#     if ( "${sta_pt_is_flatten}" == "0" ) then
#         # Top-only
#         while ( ! -e ${PD_DONE_FILE} )
#             echo "`date`: waiting export (TOP : ${PD_DONE_FILE})"
#             sleep 60
#         end
# 
#     else if ( "${sta_pt_is_flatten}" == "1" ) then
#         # Top + Sub-blocks
#         setenv TOP_PD_DONE_FILE  ${PD_OUT_PATH}/SMC.done
#         setenv BLK_FB_RIGHT_PD_DONE_FILE ${OUTFEED_PATH}/fb_right/pd___${db_ver}/${sta_pt_sub_block_version_fb_right}/SMC.done
#         setenv BLK_FB_LEFT_PD_DONE_FILE ${OUTFEED_PATH}/fb_left/pd___${db_ver}/${sta_pt_sub_block_version_fb_left}/SMC.done
# 
#         while ( ! -e ${TOP_PD_DONE_FILE} || ! -e ${BLK_FB_RIGHT_PD_DONE_FILE} || ! -e ${BLK_FB_LEFT_PD_DONE_FILE} )
#             if ( ! -e ${TOP_PD_DONE_FILE}  ) echo "`date`: waiting export (TOP  : ${TOP_PD_DONE_FILE})"
#             if ( ! -e ${BLK_FB_RIGHT_PD_DONE_FILE} ) echo "`date`: waiting export (FB_RIGHT : ${BLK_FB_RIGHT_PD_DONE_FILE})"
#             if ( ! -e ${BLK_FB_LEFT_PD_DONE_FILE} ) echo "`date`: waiting export (FB_LEFT : ${BLK_FB_LEFT_PD_DONE_FILE})"
#             sleep 60
#         end
#     endif
# 
# endif
# 
# # ChatGPT
# set TOP_PD_DONE_FILE = ""
# 
# while ( 1 )
#     set candidates = ( ${OUTFEED_PATH}/${top_design}/pd___*/${run_ver}/SMC.done )
# 
#     if ( $#candidates == 1 ) then
#         set TOP_PD_DONE_FILE = "$candidates[1]"
#         break
#     else if ( $#candidates > 1 ) then
#         echo "`date`: ERROR - multiple TOP SMC.done found for run_ver=${run_ver}"
#         foreach f ( $candidates )
#             echo "  $f"
#         end
#         exit 1
#     endif
# 
#     echo "`date`: waiting export (TOP : pd___*/${run_ver}/SMC.done)"
#     sleep 60
# end
# 
# setenv TOP_PD_DONE_FILE "$TOP_PD_DONE_FILE"

# Gemini
if ( "${pre_post}" == "post" ) then

    if ( "${sta_pt_is_flatten}" == "0" ) then
        # Top-only
        
        # Define the wildcard pattern to search for run_ver across any db_ver
        setenv PD_DONE_SEARCH_PATTERN "${OUTFEED_PATH}/${top_design}/pd___*/${run_ver}/SMC.done"

        while ( ! -e ${PD_DONE_FILE} )
            # 1. Try to find the file using wildcard if not found yet
            set found_pd_files = ( `ls ${PD_DONE_SEARCH_PATTERN} |& grep -v "No match"` )
            
            # 2. Update path if found
            if ( $#found_pd_files >= 1 ) then
                setenv PD_DONE_FILE "$found_pd_files[1]"
            endif

            # 3. Check immediately: If file exists, break the loop to skip sleep
            if ( -e ${PD_DONE_FILE} ) break

            echo "`date`: waiting export (TOP : ${PD_DONE_FILE})"
            echo "      (Searching in: ${PD_DONE_SEARCH_PATTERN})"
            sleep 60
        end

    else if ( "${sta_pt_is_flatten}" == "1" ) then
        # Top + Sub-blocks
        setenv TOP_PD_DONE_FILE  ${PD_OUT_PATH}/SMC.done
        setenv BLK_FB_RIGHT_PD_DONE_FILE ${OUTFEED_PATH}/fb_right/pd___${db_ver}/${sta_pt_sub_block_version_fb_right}/SMC.done
        setenv BLK_FB_LEFT_PD_DONE_FILE ${OUTFEED_PATH}/fb_left/pd___${db_ver}/${sta_pt_sub_block_version_fb_left}/SMC.done

        # Define search patterns
        setenv TOP_SEARCH_PAT   "${OUTFEED_PATH}/${top_design}/pd___*/${run_ver}/SMC.done"
        setenv RIGHT_SEARCH_PAT "${OUTFEED_PATH}/fb_right/pd___*/${sta_pt_sub_block_version_fb_right}/SMC.done"
        setenv LEFT_SEARCH_PAT  "${OUTFEED_PATH}/fb_left/pd___*/${sta_pt_sub_block_version_fb_left}/SMC.done"

        while ( ! -e ${TOP_PD_DONE_FILE} || ! -e ${BLK_FB_RIGHT_PD_DONE_FILE} || ! -e ${BLK_FB_LEFT_PD_DONE_FILE} )
            
            # --- Dynamic Path Update Logic ---
            # Check TOP
            if ( ! -e ${TOP_PD_DONE_FILE} ) then
                set found_top = ( `ls ${TOP_SEARCH_PAT} |& grep -v "No match"` )
                if ( $#found_top >= 1 ) setenv TOP_PD_DONE_FILE "$found_top[1]"
            endif

            # Check FB_RIGHT
            if ( ! -e ${BLK_FB_RIGHT_PD_DONE_FILE} ) then
                set found_right = ( `ls ${RIGHT_SEARCH_PAT} |& grep -v "No match"` )
                if ( $#found_right >= 1 ) setenv BLK_FB_RIGHT_PD_DONE_FILE "$found_right[1]"
            endif

            # Check FB_LEFT
            if ( ! -e ${BLK_FB_LEFT_PD_DONE_FILE} ) then
                set found_left = ( `ls ${LEFT_SEARCH_PAT} |& grep -v "No match"` )
                if ( $#found_left >= 1 ) setenv BLK_FB_LEFT_PD_DONE_FILE "$found_left[1]"
            endif
            # ----------------------------------

            # *** CRITICAL CHANGE: Check if ALL files exist now ***
            # If all files are present, break the loop immediately to skip sleep
            if ( -e ${TOP_PD_DONE_FILE} && -e ${BLK_FB_RIGHT_PD_DONE_FILE} && -e ${BLK_FB_LEFT_PD_DONE_FILE} ) break

            if ( ! -e ${TOP_PD_DONE_FILE}  ) echo "`date`: waiting export (TOP  : ${TOP_PD_DONE_FILE})"
            if ( ! -e ${BLK_FB_RIGHT_PD_DONE_FILE} ) echo "`date`: waiting export (FB_RIGHT : ${BLK_FB_RIGHT_PD_DONE_FILE})"
            if ( ! -e ${BLK_FB_LEFT_PD_DONE_FILE} ) echo "`date`: waiting export (FB_LEFT : ${BLK_FB_LEFT_PD_DONE_FILE})"
            
            sleep 60
        end
    endif

endif

#   set RUN_STA_PT_TCL = "${RUN_COMMON_STA_PT}/run_sta_pt.tcl"
#else
#   set RUN_STA_PT_TCL = "${COMMON_STA_PT}/run_sta_pt.tcl"
#endif


#if (-e ${RUN_COMMON_STA_PT}/run_sta_pt.tcl) then
    set RUN_STA_PT_TCL = "${RUN_COMMON_STA_PT}/run_sta_pt.tcl"
#endif

##### for spread xterms #####
set screen_y = `xdpyinfo | grep dimensions | awk '{print $2}' | awk -F x '{print $2}'`

if ($screen_y > 1100) then
    set xterm_x = 100
    set xterm_y = 10
    set pixel_factor_x = 6.2
    set pixel_factor_y = 16.5
else
    set xterm_x = 70
    set xterm_y = 7
    set pixel_factor_x = 6.3
    set pixel_factor_y = 17
endif

set xterm_pixel_x = `echo $xterm_x \* $pixel_factor_x | bc | cut -d "." -f 1`
set xterm_pixel_y = `echo $xterm_y \* $pixel_factor_y | bc | cut -d "." -f 1`

set pos_x = 0
set pos_y = 20

set screen_y = `xdpyinfo | grep dimensions | awk '{print $2}' | awk -F x '{print $2}'`
set max_y = `expr $screen_y - $xterm_pixel_y`

set xterm_cmd = "xterm -fa Monospace -fs 8 -bg black -fg white -geo ${xterm_x}x${xterm_y}"
##### for spread xterms #####
foreach mode ( ${sta_pt_modes} )
    foreach corner ( ${sta_pt_corners} )
        if !(${corner} == "") then
            echo "${mode}.${corner}"

            echo "mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}"
            mkdir -p ${RUN_PATH}/sta_pt/${mode}/${corner}
            cd       ${RUN_PATH}/sta_pt/${mode}/${corner}

            mkdir -p logs
            mkdir -p reports
            mkdir -p sdc

            \cp ${RUN_STA_PT_TCL} .
            chmod +x run_sta_pt.tcl

            # :clean.csh
            echo '#! /bin/csh -f' > :clean.csh
            echo '' >> :clean.csh
            echo 'set DATE = `date "+%y%m%d_%H%M"`' >> :clean.csh
            echo 'mkdir -p .trash/${DATE}' >> :clean.csh
            echo 'foreach file (`ls -A | grep -v trash`)' >> :clean.csh
            echo '    if (! -x $file || -d $file) then' >> :clean.csh
            echo '        echo " move file to .trash/${DATE} -- $file"' >> :clean.csh
            echo '        \mv -f $file .trash/${DATE}' >> :clean.csh
            echo '    endif' >> :clean.csh
            echo 'end' >> :clean.csh
            chmod +x :clean.csh

            # restore_session.csh
            echo "#! /bin/csh -f" > :restore_session.csh
            echo "source /mnt/data/prjs/CASINO/scott/design_flow/env_selector/synopsys_env.csh" >> :restore_session.csh
            echo "setenv SYNOPSYS_LC_ROOT "/mnt/appl/Tools_2024/synopsys/lc/S-2021.06-SP4P"" >> :restore_session.csh
            echo "pt_shell -x 'restore_session session.${mode}_${corner}'" >> :restore_session.csh
            chmod +x :restore_session.csh

            # :run.csh (script for rerun)
            echo "#! /bin/csh -f" > :run.csh
            echo "setenv RUN_COMMON_PATH ${PRJ_HOME}/works_${USER}/${top_design}/${ws}/runs/${run_ver}/common" >> :run.csh
            echo "source ../../all_tools_env.csh" >> :run.csh
            echo "" >> :run.csh
            echo ":clean.csh" >> :run.csh
            echo "mkdir -p logs"    >> :run.csh
            echo "mkdir -p reports" >> :run.csh
            echo "mkdir -p sdc"     >> :run.csh
            echo "" >> :run.csh
            echo "xterm -geo 100x10 -bg black -fg white -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file logs/sta_pt.log' &" >> :run.csh
            chmod +x :run.csh

            # spread xterms
            eval "${xterm_cmd}-${pos_x}+${pos_y} -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file logs/sta_pt.log' &"
            @ pos_y = $pos_y + $xterm_pixel_y
            if ($pos_y >= $max_y) then
                set pos_y = 20
                @ pos_x = $pos_x + $xterm_pixel_x
            endif

            cd ${RUN_PATH}/sta_pt

        else
#           echo "ERROR! ${mode}.${corner}"

        endif
    end
end

# monitoring status & timing_summary
\cp ${RUN_COMMON_STA_PT}/:timing_summary.tcl .
\cp ${RUN_COMMON_STA_PT}/:check_running_status.csh .

set return_value = 0

:check_running_status.csh
if ($status != 0) set return_value = $status

:timing_summary.tcl
if ($status != 0) set return_value = $status

exit $return_value

