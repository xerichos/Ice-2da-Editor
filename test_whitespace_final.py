#!/usr/bin/env python3
"""
Final test to verify whitespace preservation works correctly.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da, save_2da

def test_whitespace_preservation():
    """Test that whitespace is preserved correctly."""
    original_file = "cls_skill_archer.2da"
    test_file = "test_whitespace_final.2da"

    # Load and save
    data = load_2da(original_file)
    save_2da(test_file, data)

    # Compare byte by byte
    with open(original_file, 'rb') as f1, open(test_file, 'rb') as f2:
        orig = f1.read()
        saved = f2.read()

    if orig == saved:
        print("? SUCCESS: Perfect whitespace preservation!")
        return True
    else:
        print("? FAILURE: Whitespace not preserved")
        return False

def test_trailing_whitespace():
    """Test that lines with extra trailing spaces are preserved."""
    original_file = "cls_skill_archer.2da"
    test_file = "test_trailing.2da"

    # Load and save
    data = load_2da(original_file)
    save_2da(test_file, data)

    # Check specific lines with extra trailing spaces
    with open(original_file, 'rb') as f1, open(test_file, 'rb') as f2:
        orig_lines = f1.read().split(b'\n')
        test_lines = f2.read().split(b'\n')

    success = True
    # Check lines that should have extra trailing spaces (16 and 21 in 1-indexed)
    check_lines = [15, 20]  # 0-indexed

    for line_idx in check_lines:
        if line_idx < len(orig_lines) and line_idx < len(test_lines):
            orig_line = orig_lines[line_idx]
            test_line = test_lines[line_idx]

            orig_spaces = len(orig_line) - len(orig_line.rstrip())
            test_spaces = len(test_line) - len(test_line.rstrip())

            print(f"Line {line_idx+1}: orig={orig_spaces} spaces, test={test_spaces} spaces")

            if orig_spaces != test_spaces:
                print(f"  MISMATCH: Expected {orig_spaces} trailing spaces, got {test_spaces}")
                success = False

    return success

if __name__ == "__main__":
    success1 = test_whitespace_preservation()
    success2 = test_trailing_whitespace()

    # Clean up
    for f in ["test_whitespace_final.2da", "test_trailing.2da"]:
        if os.path.exists(f):
            os.remove(f)

    sys.exit(0 if (success1 and success2) else 1)
