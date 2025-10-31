#!/usr/bin/bash
# Script to diagnose encoding issues in dashboard.py

FILE="./hawkeye_casino/gui/dashboard.py"

echo "=== Checking first 20 bytes of file ==="
head -c 20 "$FILE" | od -A x -t x1z -v

echo ""
echo "=== Checking for non-ASCII characters ==="
grep --color='auto' -P -n "[^\x00-\x7F]" "$FILE" | head -20

echo ""
echo "=== File encoding detection ==="
file -i "$FILE"

echo ""
echo "=== First 3 lines of file ==="
head -3 "$FILE"

