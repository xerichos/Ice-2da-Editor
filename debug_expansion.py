#!/usr/bin/env python3
"""
Debug expansion behavior.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da
from data.twoda_rebuild import rebuild_line_dynamic

# Load the file
data = load_2da("cls_skill_archer.2da")

print("Header fields:", data.header_fields)
print("Header spans:", [span for span in data.header_format.spans])

# Test header expansion
print("\n=== HEADER TEST ===")
modified_header = list(data.header_fields)
modified_header[1] = "SuperConcentrationAbility"
print("Modified header fields:", modified_header)

header_widths = [len(f) for f in modified_header]
print("Header widths:", header_widths)

result_header = rebuild_line_dynamic(data.header_format, modified_header, header_widths, preserve_spacing=True)
print("Header result:", repr(result_header))

# Test data row
print("\n=== DATA ROW TEST ===")
print("Original data row 0:", data.row_fields[0])
print("Data row spans:", [span for span in data.row_formats[0].spans])

modified_row = list(data.row_fields[0])
modified_row[1] = "SuperConcentrationAbility"
print("Modified data row:", modified_row)

data_widths = [len(f) for f in modified_row]
print("Data widths:", data_widths)

result_row = rebuild_line_dynamic(data.row_formats[0], modified_row, data_widths, preserve_spacing=True)
print("Data row result:", repr(result_row))
