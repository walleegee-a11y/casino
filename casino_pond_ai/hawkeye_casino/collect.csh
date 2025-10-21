#!/usr/bin/csh

# Create/reset the output file
rm -f ./prj_hawkeye_full_dump.txt

foreach f (`find . -type f | grep -v "__pycache__" | egrep -v '\.sw[a-z]$'`)
    echo "===== FILE: $f =====" >> ./prj_hawkeye_full_dump.txt
    cat $f >> ./prj_hawkeye_full_dump.txt
    echo "\n" >> ./prj_hawkeye_full_dump.txt
end

