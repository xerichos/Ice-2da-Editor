# data/twoda_rebuild.py
"""
Line rebuilding functions for 2DA files.
These functions handle various strategies for rebuilding 2DA file lines
while preserving formatting and alignment.
"""
from typing import List, Tuple
from .twoda import TwoDARow, TwoDAData


def rebuild_line(fmt: TwoDARow, new_fields: List[str], header_fmt: TwoDARow = None) -> str:
    """Rebuild line allowing fields to expand by compressing inter-field whitespace first."""
    if not fmt.spans:
        return fmt.raw

    # Rebuild line with whitespace compression for field expansion

    orig_line = fmt.raw
    result_parts = []

    for i, ((start, end), value) in enumerate(zip(fmt.spans, new_fields)):
        if i == 0:
            # Spaces before first field
            spaces_before = start
        else:
            # Spaces between this field and previous
            prev_end = fmt.spans[i-1][1]
            orig_spaces = start - prev_end

            # Check if previous field expanded
            prev_value = new_fields[i-1]
            prev_orig_end = fmt.spans[i-1][1]
            prev_orig_start = fmt.spans[i-1][0]
            prev_expansion = len(prev_value) - (prev_orig_end - prev_orig_start)

            # Compress whitespace by the amount of previous expansion
            spaces_before = max(1, orig_spaces - prev_expansion)

        result_parts.append(' ' * spaces_before)
        result_parts.append(value)

    # Add everything after the last field
    if fmt.spans:
        last_end = fmt.spans[-1][1]
        result_parts.append(orig_line[last_end:])

    result_str = ''.join(result_parts)

    return result_str


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

            # Place the field at the header position, allowing expansion
            field_len = len(field_value)
            expansion_needed = field_len - width

            if expansion_needed > 0:
                # Need to expand - shift subsequent content
                shift_start = header_start + width
                shift_amount = expansion_needed

                # Make room for the expanded field
                new_result = result[:shift_start] + [' '] * shift_amount + result[shift_start:]
                result = new_result

            # Place the field
            for j, char in enumerate(field_value):
                pos = header_start + j
                if pos < len(result):
                    result[pos] = char

    # Preserve original trailing whitespace
    result_str = ''.join(result)
    orig_line = fmt.raw or ""
    last_content_pos = len(orig_line.rstrip())
    orig_trailing = orig_line[last_content_pos:]

    # Ensure we have at least the original trailing whitespace
    if len(result_str) < len(orig_line):
        result_str += orig_trailing[:len(orig_line) - len(result_str)]
    elif len(result_str) > len(orig_line):
        # If longer, truncate to original length but preserve the trailing whitespace structure
        result_str = result_str[:last_content_pos] + orig_trailing

    return result_str


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


def rebuild_line_with_expansion(fmt: TwoDARow, fields: List[str], header_fmt: TwoDARow) -> str:
    """Rebuild data line allowing expansion that shifts subsequent columns."""
    if not fields or not header_fmt.spans:
        return fmt.raw or ""

    # Create result with enough space
    max_len = len(fmt.raw or "") + sum(len(field) for field in fields)
    result = [' '] * max_len

    # Copy original line content first
    if fmt.raw:
        for i, char in enumerate(fmt.raw):
            if i < len(result):
                result[i] = char

    # Track current position offset due to expansions
    offset = 0

    # Index column (first field) stays at its original position
    if fields and fmt.spans:
        index_span = fmt.spans[0]
        index_value = fields[0]
        orig_width = index_span[1] - index_span[0]
        index_text = index_value[:orig_width].ljust(orig_width)

        for j, char in enumerate(index_text):
            pos = index_span[0] + j
            if pos < len(result):
                result[pos] = char

    # Align data fields with header positions, but allow expansion
    for i in range(1, len(fields)):
        if i-1 < len(header_fmt.spans):
            header_span = header_fmt.spans[i-1]
            header_start = header_span[0]

            # Apply current offset to the header position
            actual_start = header_start + offset

            # Get the data field value
            field_value = fields[i]

            # Place the field at the offset position
            for j, char in enumerate(field_value):
                pos = actual_start + j
                if pos < len(result):
                    result[pos] = char

            # Calculate how much this field expanded beyond the header width
            header_width = header_span[1] - header_span[0]
            actual_width = len(field_value)
            expansion = max(0, actual_width - header_width)
            offset += expansion

    # Trim and preserve trailing whitespace
    result_str = ''.join(result).rstrip()

    # Preserve original trailing whitespace pattern
    orig_line = fmt.raw or ""
    last_content_pos = len(orig_line.rstrip())
    orig_trailing = orig_line[last_content_pos:]

    if orig_trailing:
        result_str += orig_trailing

    return result_str


def rebuild_line_with_calculated_positions(fmt: TwoDARow, fields: List[str], column_widths: List[int]) -> str:
    """Rebuild line using calculated column positions for consistent alignment."""
    if not fields:
        return fmt.raw or ""

    # For 2DA expansion, create a line that accommodates the calculated widths
    # Position fields at cumulative positions based on column widths
    total_width = sum(column_widths)
    result = [' '] * (total_width + 10)  # Extra space for safety

    current_pos = 0
    for i, value in enumerate(fields):
        if i < len(column_widths):
            width = column_widths[i]
        else:
            width = len(value)

        # Place the field, allowing it to be longer than the allocated width
        actual_len = len(value)
        for j, char in enumerate(value):
            pos = current_pos + j
            if pos < len(result):
                result[pos] = char

        # Move to next column position (maintain minimum spacing)
        current_pos += max(width, actual_len)

    # Trim and preserve original trailing whitespace
    result_str = ''.join(result).rstrip()

    # Preserve original trailing whitespace pattern
    orig_line = fmt.raw or ""
    last_content_pos = len(orig_line.rstrip())
    orig_trailing = orig_line[last_content_pos:]

    if orig_trailing:
        result_str += orig_trailing

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

    # Check if we need expansion or content changed
    needs_expansion = False
    content_changed = False
    for i, ((start, end), value) in enumerate(zip(fmt.spans, new_fields)):
        orig_width = end - start
        if len(value) > orig_width or value == "****":
            needs_expansion = True
            break
        # Check if content actually changed
        orig_value = fmt.fields[i] if i < len(fmt.fields) else ""
        if value != orig_value:
            content_changed = True

    if preserve_spacing and len(new_fields) == len(fmt.spans):
        # For headers/data with preserve_spacing, use rebuild_line which now handles expansion
        return rebuild_line(fmt, new_fields)
    else:
        # For cases where we don't want to preserve spacing, use calculated positions
        # Calculate widths based on content
        widths = []
        for value in new_fields:
            if value == "****":
                widths.append(4)
            else:
                widths.append(len(value))

        return rebuild_line_with_calculated_positions(fmt, new_fields, widths)

