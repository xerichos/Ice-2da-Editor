#!/usr/bin/env python3
"""
Test script to verify whitespace preservation in 2DA files.
"""
import sys
import os

# Add the data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from data.twoda import load_2da, save_2da

def test_whitespace_preservation():
    """Test that loading and saving a 2DA file preserves whitespace correctly."""
    test_file = "test_whitespace.2da"
    output_file = "test_output.2da"

    # Load the original file
    print(f"Loading {test_file}...")
    data = load_2da(test_file)

    # Save it back
    print(f"Saving to {output_file}...")
    save_2da(output_file, data)

    # Compare the files
    print("Comparing files...")

    with open(test_file, 'rb') as f1, open(output_file, 'rb') as f2:
        original = f1.read()
        saved = f2.read()

    if original == saved:
        print("? SUCCESS: Whitespace preserved perfectly!")
        return True
    else:
        print("? FAILURE: Whitespace not preserved!")
        print("Differences:")

        # Show line-by-line differences
        orig_lines = original.decode('utf-8', errors='replace').splitlines()
        saved_lines = saved.decode('utf-8', errors='replace').splitlines()

        for i, (orig, sav) in enumerate(zip(orig_lines, saved_lines)):
            if orig != sav:
                print(f"Line {i+1}:")
                print(f"  Original: {repr(orig)}")
                print(f"  Saved:    {repr(sav)}")
                break

        # Show the first few differing bytes
        for i, (a, b) in enumerate(zip(original, saved)):
            if a != b:
                print(f"First difference at byte {i}: {a:02x} vs {b:02x}")
                break

        return False

def test_content_modification():
    """Test that whitespace is preserved when content is modified."""
    test_file = "test_modified.2da"
    output_file = "test_modified_output.2da"

    print(f"\nTesting content modification with {test_file}...")

    # Load the file
    data = load_2da(test_file)

    # Modify some content to be longer
    if data.row_fields and len(data.row_fields[0]) > 1:
        # Change "Concentration" to "SuperConcentration" to test expansion
        data.row_fields[0][1] = "SuperConcentration"
        print("Modified first skill name to test expansion handling")

    # Save it back
    save_2da(output_file, data)

    # Load the saved file and check if the change was preserved
    data2 = load_2da(output_file)

    if data2.row_fields[0][1] == "SuperConcentration":
        print("? SUCCESS: Content modification preserved!")
        return True
    else:
        print("? FAILURE: Content modification not preserved!")
        return False

if __name__ == "__main__":
    success1 = test_whitespace_preservation()
    success2 = test_content_modification()
    sys.exit(0 if (success1 and success2) else 1)
