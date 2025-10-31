#! /usr/bin/csh -f

# get mode & corner list
set mode_corner_list = `find -maxdepth 2 -mindepth 2 -type d | egrep "\w+_\w+v_\w+c_" | awk -F / '{print $(NF-1)"/"$NF}'`

# check touch file name
set done_file_read_design   = "READ_DESIGN_DONE"
set done_file_read_sdc      = "READ_SDC_DONE"
set done_file_update_timing = "UPDATE_TIMING_DONE"
set done_file_save_session  = "SAVE_SESSION_DONE"
set done_file_report        = "REPORT_DONE"
set done_file_sta_finish    = "STA_PT_DONE"

set done_list = ($done_file_read_design $done_file_read_sdc $done_file_update_timing $done_file_save_session $done_file_report $done_file_sta_finish)

# set font color & font type
set text_bold   = "`tput bold`"
set reset_color = "`tput sgr0`"
set orange_color   = "`tput setaf 202`"
set red_color   = "`tput setaf 9`"
set blue_color  = "`tput setaf 33`"
set green_color = "`tput setaf 2`"

@ limit_count = $#done_list * $#mode_corner_list

set return_value = 0

while (1)
    set total_done_count = 0
    clear
    echo "############################################################################################################"
    echo "# run path : `pwd`"
    echo "############################################################################################################"
    echo ""

    printf "$text_bold"
    printf " %-6s         %-20s | %-15s %-15s %-15s %-15s %-15s %-15s %-15s\n" MODE CORNER read_design read_sdc update_timing save_session report sta_done Error_code
    printf "-------------------------------------+---------------------------------------------------------------------------------------------------------------------\n"
    printf "$reset_color"
    
    foreach mode_corner ($mode_corner_list)
        set mode   = `echo "$mode_corner" | cut -d / -f 1`
        set corner = `echo "$mode_corner" | cut -d / -f 2`

        eval set ${mode}_${corner}_done_count = 0
        set running_flag = 1

        printf "%s %-8s %-26s |%s " $text_bold $mode $corner $reset_color

# check done file
        foreach done ($done_list)
            if (-e ./$mode/$corner/$done) then
                eval set ${mode}_${corner}_${done} = "done"
                eval printf "%s%-15s%s\ " \$green_color \${${mode}_${corner}_${done}} \$reset_color 
                eval @ ${mode}_${corner}_done_count ++
            else if ($running_flag == 1) then
                eval set ${mode}_${corner}_${done} = "running"
                eval printf "%s%-15s%s\ " \$blue_color \${${mode}_${corner}_${done}} \$reset_color
                set running_flag = 0
            else
                eval set ${mode}_${corner}_${done} = "stand-by"
                eval printf "%s%-15s%s\ " \$orange_color \${${mode}_${corner}_${done}} \$reset_color
            endif
        end

# check error code & mode_corner_done_count
        set abnormal_error_file = `find ./$mode/$corner -name ":ABNORMAL_ERROR_*" | awk -F / '{print $4}'`
        if ($#abnormal_error_file >= 1) then
            printf "%s%-15s%s " $red_color $abnormal_error_file $reset_color
            eval set ${mode}_${corner}_done_count = "$#done_list"
            set return_value = 1
        else 
            printf "-"
        endif

# add to total_done_count
        eval @ total_done_count += \${${mode}_${corner}_done_count}
        echo ""
    end

# Check if all STA jobs are completed (either done or errored)
    set completed_jobs = 0
    foreach mode_corner_check ($mode_corner_list)
        set mode_check   = `echo "$mode_corner_check" | cut -d / -f 1`
        set corner_check = `echo "$mode_corner_check" | cut -d / -f 2`

        # Check for STA_PT_DONE file (success) or error file (failure)
        set error_check = `find ./$mode_check/$corner_check -name ":ABNORMAL_ERROR_*" |& grep -v "^find:"`
        if (-e ./$mode_check/$corner_check/STA_PT_DONE || "$error_check" != "") then
            @ completed_jobs++
        endif
    end

    # Exit when all jobs are completed (success or failure)
    if ($completed_jobs >= $#mode_corner_list) then
        break
    else
        sleep 1m
    endif
end

# Ensure return_value is set (default to 0 if not set during loop)
if (! $?return_value) then
    set return_value = 0
endif

sleep 5s
echo ""
echo " DDDDDD    OOOOOO   NN    N  EEEEEEE     SSSSSSS TTTTTTTT  AAAAA  "
echo " DD   DD  OO    OO  NNN   N  EE          SS         TT    AA   AA "
echo " DD   DD  OO    OO  N NN  N  EEEEE       SSSSSSS    TT    AAAAAAA "
echo " DD   DD  OO    OO  N  NN N  EE               SS    TT    AA   AA "
echo " DDDDDD    OOOOOO   N   NNN  EEEEEEE     SSSSSSS    TT    AA   AA "
echo ""
sleep 5s