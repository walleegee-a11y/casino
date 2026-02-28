#!/bin/csh

# Define $pwd as the current working directory
set pwd = $cwd

# Display debug information, showing the value of $pwd (which is the current working directory)
echo "DEBUG: Replacing paths with $pwd..."

# Replace only the base path with the value of $pwd, preserving the rest of the path structure
sed -i "s|/mnt/data/prjs/CASINO/scott/casino_pond/release/[^/]*|$pwd|g" :casino.csh
sed -i "s|/mnt/data/prjs/CASINO/scott/casino_pond/release/[^/]*|$pwd|g" casino_pond/config_casino.csh


# Display debug information
echo "DEBUG: Fixing lines with odd number of quotes..."

# Temporary file to store the fixed content
set tmpfile = "tmp_file"
\rm -f $tmpfile

# Loop through each line in the file and count the quotes
foreach line ("`cat casino_pond/config_casino.csh`")
    # Count the number of quotes in the line
    set count = `echo $line | tr -cd '"' | wc -c`
    
    # Display the line and the count for debugging purposes
    echo "Line: $line"
    echo "Number of quotes: $count"
    
    # If the number of quotes is odd, append a closing quote
    if ( $count % 2 != 0 ) then
        echo "$line"'"' >> $tmpfile
    else
        echo "$line" >> $tmpfile
    endif
end

# Overwrite the original file with the fixed lines
\mv $tmpfile casino_pond/config_casino.csh

# Display debug output to confirm the fix
echo "DEBUG: Preview of the fixed lines in casino_pond/config_casino.csh:"
grep "setenv" casino_pond/config_casino.csh
