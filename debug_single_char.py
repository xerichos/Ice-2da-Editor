#!/usr/bin/env python3
"""
Debug single character addition.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da, save_2da

def test_single_char():
    """Test adding a single character to a cell."""
    original_file = "cls_skill_archer.2da"
    test_file = "test_single.2da"

    # Load
    data = load_2da(original_file)
    orig_row = data.row_formats[0].raw
    print("Original row:", repr(orig_row))

    # Add single character to "Concentration"
    data.row_fields[0][1] = "ConcentrationX"  # Add one 'X'
    print("Modified field:", data.row_fields[0][1])

    save_2da(test_file, data)

    # Check result
    with open(test_file, 'r') as f:
        lines = f.readlines()

    result_row = lines[3].rstrip()  # Line 3 is first data row
    print("Result row:  ", repr(result_row))
    print("Full result: ", repr(lines[3]))

    # Compare lengths
    print(f"Original length: {len(orig_row)}")
    print(f"Result length: {len(result_row)}")
    print(f"Full result length: {len(lines[3])}")

    # Check positions of key elements
    print("\nPosition analysis:")
    print(f"Original '0' at pos 0: {orig_row[0] == '0'}")
    print(f"Result '0' at pos 0: {result_row[0] == '0'}")

    # Find where 'ConcentrationX' starts
    conc_pos = result_row.find('ConcentrationX')
    print(f"'ConcentrationX' starts at position: {conc_pos}")

    # Find where the first '1' appears after ConcentrationX
    after_conc = result_row[conc_pos + len('ConcentrationX'):]
    first_one_pos = after_conc.find('1')
    if first_one_pos != -1:
        total_one_pos = conc_pos + len('ConcentrationX') + first_one_pos
        print(f"First '1' at position: {total_one_pos}")

    # Check if positions match expectations
    expected_conc_start = 6  # From original span
    expected_first_one = 23  # Original was at 22, but shifted right by 1 due to expansion

    print("\nExpected 'ConcentrationX' at: 6")
    print(f"Expected first '1' at: {expected_first_one}")
    print(f"Actual positions correct: {conc_pos == expected_conc_start}")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_single_char()
