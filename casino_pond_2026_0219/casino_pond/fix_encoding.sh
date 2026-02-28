#!/usr/bin/bash
# Script to fix encoding issues in dashboard.py

SOURCE_FILE="./hawkeye_casino/gui/dashboard.py"
BACKUP_FILE="${SOURCE_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "=== Fixing encoding issues in dashboard.py ==="
echo "Creating backup: $BACKUP_FILE"
cp "$SOURCE_FILE" "$BACKUP_FILE"

echo "Converting file to UTF-8 and adding encoding declaration..."

# Method 1: Try to convert from common encodings to UTF-8
if command -v iconv &> /dev/null; then
    # Try Latin-1 first (0xa1 is valid in Latin-1)
    if iconv -f LATIN1 -t UTF-8 "$SOURCE_FILE" > "${SOURCE_FILE}.tmp" 2>/dev/null; then
        echo "# -*- coding: utf-8 -*-" > "${SOURCE_FILE}.new"
        cat "${SOURCE_FILE}.tmp" >> "${SOURCE_FILE}.new"
        mv "${SOURCE_FILE}.new" "$SOURCE_FILE"
        rm "${SOURCE_FILE}.tmp"
        echo "? Fixed using Latin-1 to UTF-8 conversion"
    else
        # Try removing non-ASCII characters
        echo "# -*- coding: utf-8 -*-" > "${SOURCE_FILE}.new"
        LC_ALL=C sed 's/[\x80-\xFF]//g' "$SOURCE_FILE" >> "${SOURCE_FILE}.new"
        mv "${SOURCE_FILE}.new" "$SOURCE_FILE"
        echo "? Fixed by removing non-ASCII characters"
    fi
else
    # Fallback: Use Python to clean the file
    python3 << 'EOF'
import sys

source_file = "./hawkeye_casino/gui/dashboard.py"

try:
    # Try reading with various encodings
    content = None
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            with open(source_file, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"? Successfully read file with {encoding} encoding")
            break
        except:
            continue

    if content is None:
        # Last resort: read as binary and replace bad bytes
        with open(source_file, 'rb') as f:
            raw = f.read()
        content = raw.decode('utf-8', errors='ignore')
        print("? Read file with error handling (some characters may be lost)")

    # Add encoding declaration if not present
    if not content.startswith('# -*- coding:'):
        content = '# -*- coding: utf-8 -*-\n' + content

    # Write back as UTF-8
    with open(source_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"? Fixed and saved as UTF-8")
    sys.exit(0)

except Exception as e:
    print(f"? Error: {e}")
    sys.exit(1)
EOF
fi

echo ""
echo "=== Verification ==="
file -i "$SOURCE_FILE"
head -3 "$SOURCE_FILE"
echo ""
echo "Backup saved at: $BACKUP_FILE"

