#! /bin/csh -f

# Generate a unique identifier using the timestamp and random number
setenv UNIQUE_ID `date +%s`_`head /dev/urandom | tr -dc A-Za-z0-9 | head -c 6`

# Construct the file path using the UNIQUE_ID and the username
set username = `whoami`
set tm_stamp_path = "/tmp/tmp_tm_casino_${username}_${UNIQUE_ID}.csh"
set wsnv_stamp_path = "/tmp/tmp_wsnv_casino_${username}_${UNIQUE_ID}.csh"

$casino_pond/casino.py

# Source generated stamp files

# Find files matching the pattern in /tmp without using /dev/null
#echo "Debug: Searching files with the pattern /tmp/tmp_*_casino_${username}_${UNIQUE_ID}.csh"

# Use ls and handle the case where no files are found by checking for error code
set files = ()
if (-e /tmp/tmp_*_casino_${username}_${UNIQUE_ID}.csh) then
    set files = (`ls -1 /tmp/tmp_*_casino_${username}_${UNIQUE_ID}.csh`)
else
    echo "Info: No files found matching /tmp/tmp_*_casino_${username}_${UNIQUE_ID}.csh"
    exit 0  # Exit gracefully since no files were found
endif
# Check if any files were found
if ($#files == 0) then
    echo "Info: No files found matching /tmp/tmp_*_casino_${username}_${UNIQUE_ID}.csh"
    exit 0  # Exit gracefully since no files were found
else
    # Debugging: Print found files
    echo "Info : Found  $files"
    # Loop through the found files and ensure they are valid before sourcing
    foreach file ($files)
        if (-e "$file") then
            echo "Info : Sourcing $file"
            source "$file"
        else
            echo "Error: File not found - $file"
        endif
    end
endif
