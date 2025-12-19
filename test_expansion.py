#!/usr/bin/env python3
"""
Test expansion handling for 2DA files.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da, save_2da

def test_expansion():
    """Test that cells can expand and shift subsequent columns."""
    original_file = "cls_skill_archer.2da"
    test_file = "test_expansion.2da"

    # Load the file
    data = load_2da(original_file)

    # Modify a cell to be much longer to test expansion
    print("Original data:")
    for i, row in enumerate(data.row_fields[:3]):
        print(f"  Row {i}: {row}")

    if data.row_fields and len(data.row_fields[0]) > 1:
        # Make the skill name very long
        data.row_fields[0][1] = "SuperConcentrationAbility"  # Much longer than original
        print(f"\nModified row 0, field 1 to: {data.row_fields[0][1]}")

    print("\nData after modification:")
    for i, row in enumerate(data.row_fields[:3]):
        print(f"  Row {i}: {row}")

    # Save it
    save_2da(test_file, data)

    # Check the result
    with open(test_file, 'r') as f:
        lines = f.readlines()

    print("\nHeader line (line 2):")
    print(repr(lines[2].rstrip()))
    print("\nFirst data line (line 3, modified):")
    print(repr(lines[3].rstrip()))

    # Check that the long content is preserved in the first data row
    first_data_line = lines[3].strip()
    if "SuperConcentrationAbility" in first_data_line:
        print("? Long content preserved in data row")
    else:
        print("? Long content truncated in data row")

    # Check that subsequent columns are shifted
    # The '1' (SkillIndex) should appear after the long skill name
    parts = first_data_line.split("SuperConcentrationAbility")
    if len(parts) > 1 and "1" in parts[1]:
        print("? Subsequent columns properly shifted")
    else:
        print("? Subsequent columns not shifted correctly")

    # Check that the overall structure is maintained
    if first_data_line.startswith('0') and '1' in first_data_line and first_data_line.endswith('1'):
        print("? Row structure maintained")
    else:
        print("? Row structure broken")

    # Don't clean up for debugging
    # if os.path.exists(test_file):
    #     os.remove(test_file)

if __name__ == "__main__":
    test_expansion()
