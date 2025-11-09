"""Remove the raw EPG dump code from fetcher.py"""
import sys
from pathlib import Path

# Read the file
fetcher_path = Path(__file__).parent.parent / "src" / "epg_web" / "services" / "fetcher.py"
with open(fetcher_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 54-79 (0-indexed: 53-78)
# Line 53 is "    # Fetch EPG data\n"
# Line 79 is "    # Parse the EPG data\n"
# We want to keep everything before line 53 and from line 80 onwards
new_lines = lines[:53] + ["    # Fetch and parse the EPG data\n"] + lines[54:79] + lines[79:]

# Actually, let me re-read to check exact line numbers
print(f"Line 53 (0-indexed 52): {repr(lines[52])}")
print(f"Line 54 (0-indexed 53): {repr(lines[53])}")
print(f"Line 55 (0-indexed 54): {repr(lines[54])}")
print(f"Line 79 (0-indexed 78): {repr(lines[78])}")
print(f"Line 80 (0-indexed 79): {repr(lines[79])}")
print(f"Line 81 (0-indexed 80): {repr(lines[80])}")
print(f"Line 82 (0-indexed 81): {repr(lines[81])}")

# Remove lines 56-80 (the save block) and replace line 53+54 comment
# Line 53 (0-indexed 52) is blank
# Line 54 (0-indexed 53) is "    # Fetch EPG data\n"
# Line 55 (0-indexed 54) is "    content = await fetch_epg_data(url)\n"
# Lines 56-79 (0-indexed 55-78) is the save block
# Line 80 (0-indexed 79) is "    # Parse the EPG data\n"
# Line 81 (0-indexed 80) is "    epg_data = await parse_epg_file(content, url.lower())\n"

new_lines = (
    lines[:52] +  # Everything before the blank line before "# Fetch EPG data"
    ["\n"] +  # Keep the blank line
    ["    # Fetch and parse the EPG data\n"] +  # New comment
    [lines[54]] +  # Keep "content = await fetch_epg_data(url)"
    [lines[80]] +  # Keep "epg_data = await parse_epg_file..."
    lines[81:]  # Everything after
)

# Write back
with open(fetcher_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\nSuccessfully removed raw EPG dump code from {fetcher_path}")
