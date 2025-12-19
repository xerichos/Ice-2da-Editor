#!/usr/bin/env python3
"""
Comprehensive test to verify column insertion alignment fix
"""
from data.twoda import load_2da, save_2da
import os

def test_column_insertion_alignment():
    """Test that column insertion maintains proper alignment"""

    print("=== LOADING REFERENCE FILE ===")
    data = load_2da('skills ref.2da')

    print(f"Original header fields ({len(data.header_fields)}): {data.header_fields}")
    print(f"Original data row 0 ({len(data.row_fields[0])}): {data.row_fields[0][:8]}...")

    print("\n=== SIMULATING COLUMN INSERTION ===")
    # Based on the broken newest file, insert 'Header' between 'Icon' and 'Untrained'
    # Header position: after 'Icon' (position 3) -> insert at position 4
    # Data position: after index + header position -> insert at position 5

    header_insert_pos = 4  # Insert 'Header' at position 4 in header_fields
    data_insert_pos = 5    # Insert data at position 5 in row_fields

    data.header_fields.insert(header_insert_pos, 'Header')

    # Add the new data column to all rows
    for row in data.row_fields:
        row.insert(data_insert_pos, '****')

    print(f"After insertion - header fields ({len(data.header_fields)}): {data.header_fields}")
    print(f"After insertion - data row 0 ({len(data.row_fields[0])}): {data.row_fields[0][:9]}...")

    print("\n=== SAVING TEST FILE ===")
    save_2da('current_output.2da', data)

    print("=== COMPARING WITH BROKEN FILE ===")

    # Read the saved file
    with open('current_output.2da', 'r') as f:
        current_lines = f.readlines()

    # Read the broken file
    with open('Skills broken newest.2da', 'r') as f:
        broken_lines = f.readlines()

    print("Current header:")
    print(repr(current_lines[2].strip()))
    print("\nBroken header:")
    print(repr(broken_lines[2].strip()))
    print(f"\nHeaders match: {current_lines[2].strip() == broken_lines[2].strip()}")

    print("\nCurrent data line 1:")
    print(repr(current_lines[3].strip()))
    print("\nBroken data line 1:")
    print(repr(broken_lines[3].strip()))
    print(f"\nData lines match: {current_lines[3].strip() == broken_lines[3].strip()}")

    print("\nCurrent data line 2:")
    print(repr(current_lines[4].strip()))
    print("\nBroken data line 2:")
    print(repr(broken_lines[4].strip()))
    print(f"\nData lines 2 match: {current_lines[4].strip() == broken_lines[4].strip()}")

    # Check alignment by comparing positions
    if len(current_lines) > 3 and len(broken_lines) > 3:
        current_data = current_lines[3].strip()
        broken_data = broken_lines[3].strip()

        # Check key alignment points
        alignment_checks = [
            ('AllClassesCanUse', 'AllClassesCanUse'),
            ('Category', 'Category'),
            ('MaxCR', 'MaxCR'),
            ('Constant', 'Constant'),
            ('HostileSkill', 'HostileSkill')
        ]

        print("\n=== ALIGNMENT CHECK ===")
        for header_text, data_hint in alignment_checks:
            if header_text in current_lines[2] and header_text in broken_lines[2]:
                current_pos = current_lines[2].find(header_text)
                broken_pos = broken_lines[2].find(header_text)
                match = current_pos == broken_pos
                print(f"{header_text}: Current pos={current_pos}, Broken pos={broken_pos}, Match={match}")

    # Clean up
    if os.path.exists('current_output.2da'):
        os.remove('current_output.2da')

    return current_lines[2].strip() == broken_lines[2].strip() and current_lines[3].strip() == broken_lines[3].strip()

if __name__ == "__main__":
    success = test_column_insertion_alignment()
    print(f"\n=== TEST RESULT: {'PASS' if success else 'FAIL'} ===")
