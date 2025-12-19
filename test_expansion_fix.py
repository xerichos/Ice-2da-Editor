#!/usr/bin/env python3
"""
Test the fixed expansion behavior.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da, save_2da

def test_expansion():
    """Test cell expansion behavior."""
    original_file = "cls_skill_archer.2da"
    test_file = "test_expansion_fix.2da"

    # Load and modify
    data = load_2da(original_file)
    print("Original row 0:", repr(data.row_formats[0].raw))

    # Modify to make it longer
    data.row_fields[0][1] = "SuperConcentrationAbility"
    print("Modified field:", data.row_fields[0][1])

    save_2da(test_file, data)

    # Check result
    with open(test_file, 'r') as f:
        lines = f.readlines()

    print("Result line:", repr(lines[3].rstrip()))

    # Check that expansion worked without shifting the whole line
    result_line = lines[3].strip()
    print("Starts with '0':", result_line.startswith('0'))
    print("Contains expanded content:", "SuperConcentrationAbility" in result_line)

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_expansion()
