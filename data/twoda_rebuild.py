# data/twoda_rebuild.py
"""
Line rebuilding functions for 2DA files.
These functions handle various strategies for rebuilding 2DA file lines
while preserving formatting and alignment.
"""
from typing import List, Tuple
from .twoda import TwoDARow, TwoDAData


def rebuild_line(fmt: TwoDARow, new_fields: List[str]) -> str:
    """Rebuild line using original field positions."""
    if not fmt.spans:
        return fmt.raw

    # For 2DA files, maintain FIXED column positions
    # Each field is placed at its original span position and truncated/padded to fit
    # This preserves the exact column alignment required by NWN

    result = list(fmt.raw)

    for (start, end), value in zip(fmt.spans, new_fields):
        # Calculate the field width
        width = end - start

        # Truncate or pad the value to fit the exact width
        field_text = value[:width].ljust(width)

        # Place the field at its original position
        for i, char in enumerate(field_text):
            result[start + i] = char

    return ''.join(result)


def rebuild_line_with_header_alignment(fmt: TwoDARow, fields: List[str], header_fmt: TwoDARow) -> str:
    """Rebuild data line aligning columns with header positions."""
    if not fields or not header_fmt.spans:
        return fmt.raw or ""

    # Create result with enough space
    max_len = max(len(fmt.raw or ""), len(header_fmt.raw or ""))
    result = [' '] * max_len

    # Copy original line content first
    if fmt.raw:
        for i, char in enumerate(fmt.raw):
            if i < len(result):
                result[i] = char

    # Index column (first field) stays at its original position
    if fields and len(fields) > 0 and fmt.spans and len(fmt.spans) > 0:
        index_span = fmt.spans[0]
        index_value = fields[0]
        orig_width = index_span[1] - index_span[0]
        index_text = index_value[:orig_width].ljust(orig_width)

        for j, char in enumerate(index_text):
            pos = index_span[0] + j
            if pos < len(result):
                result[pos] = char

    # Align data fields with header positions
    for i in range(1, len(fields)):
        if i-1 < len(header_fmt.spans):
            header_span = header_fmt.spans[i-1]
            header_start = header_span[0]

            # Get the data field value
            field_value = fields[i]

            # Determine width: use original data span width if available, otherwise header width
            if i < len(fmt.spans):
                data_span = fmt.spans[i]
                width = data_span[1] - data_span[0]
            else:
                width = header_span[1] - header_span[0]

            # Place the field at the header position
            field_text = field_value[:width].ljust(width)
            for j, char in enumerate(field_text):
                pos = header_start + j
                if pos < len(result):
                    result[pos] = char

    return ''.join(result).rstrip()


def calculate_column_widths(data: TwoDAData) -> Tuple[List[int], List[int]]:
    """Calculate the required width for header and data columns based on current content.

    Returns:
        Tuple of (header_widths, data_widths)
        header_widths: widths for header columns (14 elements)
        data_widths: widths for data columns including index (15 elements)
    """
    if not data.header_fields or not data.row_fields:
        return [], []

    header_num_cols = len(data.header_fields)  # Usually 14
    data_num_cols = max(len(row) for row in data.row_fields) if data.row_fields else 0  # Usually 15

    header_widths = [0] * header_num_cols
    data_widths = [0] * data_num_cols

    # Check header widths (skip the display index column)
    for i, field in enumerate(data.header_fields):
        header_widths[i] = max(header_widths[i], len(field))

    # Check all row widths (including index column)
    for row in data.row_fields:
        for i, field in enumerate(row):
            if i < data_num_cols:
                data_widths[i] = max(data_widths[i], len(field))

    return header_widths, data_widths


def rebuild_line_with_calculated_positions(fmt: TwoDARow, fields: List[str], column_widths: List[int]) -> str:
    """Rebuild line using calculated column positions for consistent alignment."""
    if not fields:
        return fmt.raw or ""

    result = []
    for i, value in enumerate(fields):
        if i < len(column_widths):
            width = column_widths[i]
        else:
            width = len(value)

        # Pad the value to the required width
        field_text = value.ljust(width)
        result.append(field_text)

        # Add spacing between columns (2 spaces for readability)
        if i < len(fields) - 1:
            result.append("  ")

    # Preserve original trailing whitespace
    result_str = "".join(result)

    # Append the original trailing whitespace (everything after the last non-whitespace)
    orig_line = fmt.raw or ""
    last_content_pos = len(orig_line.rstrip())
    orig_trailing = orig_line[last_content_pos:]

    # If our result is shorter than the original line, pad with original trailing whitespace
    if len(result_str) < len(orig_line):
        result_str += orig_trailing[:len(orig_line) - len(result_str)]
    elif len(result_str) > len(orig_line):
        # If longer, truncate to original length but preserve the trailing whitespace structure
        result_str = result_str[:last_content_pos] + orig_trailing

    return result_str


def rebuild_line_dynamic(fmt: TwoDARow, new_fields: List[str], column_widths: List[int], preserve_spacing: bool = False) -> str:
    """Rebuild line with smart expansion and spacing preservation.

    Args:
        fmt: The original format with spans
        new_fields: New field values
        column_widths: Required widths for expansion guidance
        preserve_spacing: If True, preserve original visual spacing when possible
    """
    if not new_fields or not fmt.spans:
        return fmt.raw or ""

    # Check if we need expansion
    needs_expansion = False
    for i, ((start, end), value) in enumerate(zip(fmt.spans, new_fields)):
        orig_width = end - start
        if len(value) > orig_width or value == "****":
            needs_expansion = True
            break

    if preserve_spacing and not needs_expansion:
        # Preserve original line exactly, including trailing whitespace
        return fmt.raw or ""
    else:
        # Dynamic expansion (either requested or needed)
        result_parts = []
        current_pos = fmt.spans[0][0] if fmt.spans else 0

        for i, ((start, end), value) in enumerate(zip(fmt.spans, new_fields)):
            orig_width = end - start

            # Determine actual field width needed
            if value == "****":
                actual_width = 4
            else:
                actual_width = max(orig_width, len(value))

            # Create field text
            if value == "****":
                field_text = "****"
            else:
                field_text = value.ljust(actual_width)

            # Add the field
            result_parts.append(field_text)

            # Calculate spacing to next field, accounting for expansion
            if i < len(fmt.spans) - 1:
                next_start = fmt.spans[i + 1][0]
                orig_spacing = next_start - end

                expansion = actual_width - orig_width
                adjusted_spacing = max(1, orig_spacing - expansion)

                result_parts.append(" " * adjusted_spacing)

        result_str = "".join(result_parts)

        # Preserve original trailing whitespace
        orig_line = fmt.raw or ""
        last_content_pos = len(orig_line.rstrip())
        orig_trailing = orig_line[last_content_pos:]

        # If our result is shorter than the original line, pad with original trailing whitespace
        if len(result_str) < len(orig_line):
            result_str += orig_trailing[:len(orig_line) - len(result_str)]
        elif len(result_str) > len(orig_line):
            # If longer, truncate to original length but preserve the trailing whitespace structure
            result_str = result_str[:last_content_pos] + orig_trailing

        return result_str

