#!/usr/bin/env python3
"""
Debug script to understand how column insertion works at the model level
"""
from gui.table_model import TwoDATableModel

def debug_model_insertion():
    """Debug column insertion at the table model level"""

    # Create model and load data like the application does
    model = TwoDATableModel()

    # Set up data like the file loader does
    from data.twoda import load_2da
    data = load_2da('skills ref.2da')
    header = [""] + data.header_fields  # Add empty index header
    rows = data.row_fields

    model.set_data(header, rows)

    print("=== BEFORE INSERTION ===")
    print(f"Model header ({len(model._header)}): {model._header}")
    print(f"Model row 0 ({len(model._rows[0])}): {model._rows[0][:8]}...")

    # Insert column at position 5 (after "Icon" which is at position 4 in the model)
    # This simulates inserting to the right of the Icon column
    insert_pos = 5
    print(f"\nInserting column at position {insert_pos}")

    model.insertColumns(insert_pos, 1)

    # Manually set the inserted header to "Header" to match the broken file
    model._header[insert_pos] = "Header"

    # Manually set the inserted data to **** to match the broken file
    for row in model._rows:
        row[insert_pos] = "****"

    print("\n=== AFTER INSERTION ===")
    print(f"Model header ({len(model._header)}): {model._header}")
    print(f"Model row 0 ({len(model._rows[0])}): {model._rows[0][:9]}...")

    # Extract data like the save process does
    extracted_header, extracted_rows = model.extract_data()
    print(f"\nExtracted header: {extracted_header}")
    print(f"Extracted header[1:] (saved): {extracted_header[1:]}")
    print(f"Extracted rows[0]: {extracted_rows[0][:9]}...")

    # Create data structure for saving
    save_data = data  # Copy original
    save_data.header_fields = extracted_header[1:]  # Skip empty index header
    save_data.row_fields = extracted_rows

    # Save and check result
    from data.twoda import save_2da
    save_2da('debug_model_output.2da', save_data)

    print("\n=== SAVED FILE CONTENT ===")
    with open('debug_model_output.2da', 'r') as f:
        lines = f.readlines()
        print("Header line:")
        print(repr(lines[2].strip()))
        print("Data line 1:")
        print(repr(lines[3].strip()))

    # Compare with broken file
    print("\n=== COMPARISON WITH BROKEN ===")
    with open('Skills broken newest.2da', 'r') as f:
        broken_lines = f.readlines()
        print("Broken header:")
        print(repr(broken_lines[2].strip()))
        print("Broken data 1:")
        print(repr(broken_lines[3].strip()))

        match = (lines[2].strip() == broken_lines[2].strip() and
                lines[3].strip() == broken_lines[3].strip())
        print(f"\nMatches broken file: {match}")

    # Don't clean up for debugging
    print("\nDebug file saved as 'debug_model_output.2da'")

if __name__ == "__main__":
    debug_model_insertion()
