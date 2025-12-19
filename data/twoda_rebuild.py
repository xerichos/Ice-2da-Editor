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
            # Normal case: align with corresponding header span
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
        else:
            # Extra fields beyond header spans - place them after the last header
            if header_fmt.spans:
                last_header_end = header_fmt.spans[-1][1]
                # Add spacing before extra fields
                current_pos = max(last_header_end + 1, len(result))

                # Extend result if needed
                if current_pos + len(fields[i]) > len(result):
                    result.extend([' '] * (current_pos + len(fields[i]) - len(result)))

                # Place the extra field
                for j, char in enumerate(fields[i]):
                    pos = current_pos + j
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


def rebuild_line_dynamic(fmt: TwoDARow, new_fields: List[str], column_widths: List[int], preserve_spacing: bool = False, header_fmt: TwoDARow = None) -> str:
    """Rebuild line with smart expansion and spacing preservation.

    Args:
        fmt: The original format with spans
        new_fields: New field values
        column_widths: Required widths for expansion guidance
        preserve_spacing: If True, preserve original visual spacing when possible
    """
    if not new_fields:
        return fmt.raw or ""

    # If we don't have format spans, fall back to calculated positions
    if not fmt.spans:
        widths = []
        for value in new_fields:
            if value == "****":
                widths.append(4)
            else:
                widths.append(len(value))
        return rebuild_line_with_calculated_positions(fmt, new_fields, widths)

    # Handle case where we have more fields than spans (columns were added)
    if len(new_fields) > len(fmt.spans):
        # For lines with extra columns, try to align based on existing structure
        # Create an extended format by adding spans for new columns
        extended_fmt = extend_format_for_new_columns_smart(fmt, new_fields, column_widths, header_fmt)
        return rebuild_line(extended_fmt, new_fields)
    elif len(new_fields) < len(fmt.spans):
        # Handle case where columns were removed - use only the spans we need
        truncated_fmt = TwoDARow(
            raw=fmt.raw,
            fields=fmt.fields[:len(new_fields)] if fmt.fields else [],
            spans=fmt.spans[:len(new_fields)]
        )
        return rebuild_line(truncated_fmt, new_fields)
    else:
        # Normal case: same number of fields and spans
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

        if preserve_spacing:
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


def extend_format_for_new_columns_smart(fmt: TwoDARow, new_fields: List[str], column_widths: List[int], header_fmt: TwoDARow = None) -> TwoDARow:
    """Smartly extend format spans to accommodate newly added columns.

    This tries to maintain the visual structure by using header positions when available,
    or analyzing spacing patterns from existing spans.
    """
    if len(new_fields) <= len(fmt.spans):
        return fmt

    # If we have a header format, try to align with it
    if header_fmt and len(new_fields) <= len(header_fmt.spans) + 1:  # +1 for index column
        # Use header positions to determine data column positions
        extended_spans = []
        extended_fields = []

        # Index column (first field) - keep original position if available
        if fmt.spans:
            extended_spans.append(fmt.spans[0])
            extended_fields.append(new_fields[0])
        else:
            # Default position for index column
            extended_spans.append((2, 2 + len(new_fields[0])))
            extended_fields.append(new_fields[0])

        # Add spans based on header positions for data columns
        for i in range(1, len(new_fields)):
            if i-1 < len(header_fmt.spans):
                header_span = header_fmt.spans[i-1]
                # Use header start position, but adjust width based on data
                start = header_span[0]
                field_width = len(new_fields[i])
                end = start + field_width
                extended_spans.append((start, end))
                extended_fields.append(new_fields[i])
            else:
                # Extra fields beyond header spans - place at end
                if extended_spans:
                    last_end = extended_spans[-1][1]
                    start = last_end + 1
                    end = start + len(new_fields[i])
                    extended_spans.append((start, end))
                    extended_fields.append(new_fields[i])

        # Create raw line
        max_len = max(extended_spans[-1][1] + 10 if extended_spans else 50, len(fmt.raw or ""))
        result_parts = [' '] * max_len

        # Copy original content if available
        if fmt.raw:
            for j, char in enumerate(fmt.raw):
                if j < len(result_parts):
                    result_parts[j] = char

        # Place fields at their span positions
        for (start, end), field_value in zip(extended_spans, extended_fields):
            for j, char in enumerate(field_value):
                pos = start + j
                if pos < len(result_parts):
                    result_parts[pos] = char

        raw_line = ''.join(result_parts).rstrip()

        return TwoDARow(
            raw=raw_line,
            fields=extended_fields,
            spans=extended_spans
        )

    # Fallback: use original logic for cases where header alignment isn't available
    # Start with the original spans
    extended_spans = list(fmt.spans)
    extended_fields = list(fmt.fields) if fmt.fields else []

    # Find the end position of the last original span
    last_end = 0
    if extended_spans:
        last_end = extended_spans[-1][1]

    # Analyze spacing pattern from existing spans
    if len(extended_spans) >= 2:
        # Calculate average spacing between columns
        spacings = []
        for i in range(1, len(extended_spans)):
            spacing = extended_spans[i][0] - extended_spans[i-1][1]
            spacings.append(spacing)

        avg_spacing = sum(spacings) / len(spacings) if spacings else 2
        # Use a reasonable spacing (not too compressed)
        spacing = max(1, int(avg_spacing))
    else:
        spacing = 1  # Default minimal spacing

    # Add spans for the new columns
    current_pos = last_end
    for i in range(len(fmt.spans), len(new_fields)):
        field_value = new_fields[i]

        # Use column width if available, otherwise use field length
        if i < len(column_widths) and column_widths[i] > 0:
            width = max(len(field_value), column_widths[i])
        else:
            width = len(field_value)

        # Add spacing before the new field
        current_pos += spacing

        start = current_pos
        end = start + width
        extended_spans.append((start, end))
        extended_fields.append(field_value)

        current_pos = end

    # Create a new raw line that represents the extended format
    max_len = current_pos + 10
    result_parts = [' '] * max_len

    # Copy original content if available
    if fmt.raw:
        for j, char in enumerate(fmt.raw):
            if j < len(result_parts):
                result_parts[j] = char

    # Add the new fields
    for (start, end), field_value in zip(extended_spans[len(fmt.spans):], new_fields[len(fmt.spans):]):
        for j, char in enumerate(field_value):
            pos = start + j
            if pos < len(result_parts):
                result_parts[pos] = char

    raw_line = ''.join(result_parts).rstrip()

    return TwoDARow(
        raw=raw_line,
        fields=extended_fields,
        spans=extended_spans
    )

