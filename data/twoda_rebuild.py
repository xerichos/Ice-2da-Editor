# data/twoda_rebuild.py
"""
Line rebuilding functions for 2DA files.
These functions handle various strategies for rebuilding 2DA file lines
while preserving formatting and alignment.
"""
from typing import List, Tuple, Optional
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



def _orig_widths_from_spans(fmt) -> List[int]:
    """
    Derive the original per-column widths from a TwoDARow's spans.
    Assumes columns are separated by at least 1 space.
    Width for col i (non-last) is: next_start - start_i - 1
    """
    if not fmt or not getattr(fmt, "spans", None):
        return []

    widths: List[int] = []
    spans = fmt.spans

    for i, (start, end) in enumerate(spans):
        if i < len(spans) - 1:
            next_start = spans[i + 1][0]
            widths.append(max(1, next_start - start - 1))
        else:
            widths.append(max(1, end - start))

    return widths


def rebuild_line_with_header_alignment(fmt, fields: List[str], widths: List[int]) -> str:
    # Keep this for compatibility with existing imports.
    return rebuild_line_dynamic(fmt, fields, widths, preserve_spacing=True)


def calculate_column_widths(data) -> Tuple[List[int], List[int]]:
    hdr_orig = _orig_widths_from_spans(getattr(data, "header_format", None))
    row_orig = _orig_widths_from_spans(data.row_formats[0]) if getattr(data, "row_formats", None) else []

    # Determine row column count
    cols = max((len(r) for r in getattr(data, "row_fields", [])), default=0)

    # Max content length per row column (including index col at 0)
    maxlen: List[int] = [0] * cols
    for r in getattr(data, "row_fields", []):
        for c in range(cols):
            v = r[c] if c < len(r) else ""
            maxlen[c] = max(maxlen[c], len(str(v)))

    # Data widths (rows) include index column at 0
    data_widths: List[int] = [0] * cols
    for c in range(cols):
        base = maxlen[c]

        # Preserve original row layout widths where available
        if c < len(row_orig):
            base = max(base, row_orig[c])
        else:
            # New column beyond original spans: ensure at least header name length (if it maps)
            j = c - 1  # row col 1.. maps to header_fields 0..
            if c > 0 and j < len(getattr(data, "header_fields", [])):
                base = max(base, len(str(data.header_fields[j])))

        data_widths[c] = base

    # Header widths (no index column)
    header_widths: List[int] = []
    header_fields = getattr(data, "header_fields", [])

    for j, h in enumerate(header_fields):
        c = j + 1  # maps to row column
        base = max(len(str(h)), maxlen[c] if c < len(maxlen) else 0)

        # Preserve original header layout widths where available
        if j < len(hdr_orig):
            base = max(base, hdr_orig[j])

        header_widths.append(base)

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


def rebuild_line_dynamic(fmt, fields: List[str], widths: List[int],
                        preserve_spacing: bool = True, header_fmt: Optional[object] = None) -> str:
    """
    Rebuild a single 2DA line using:
    - preserved leading indentation (prefix before first token), and
    - fixed widths + single-space separators.
    """
    prefix = ""
    if preserve_spacing and fmt and getattr(fmt, "spans", None):
        prefix = fmt.raw[:fmt.spans[0][0]]

    sep = " "
    out: List[str] = [prefix]
    n = len(fields)

    for i, val in enumerate(fields):
        s = "" if val is None else str(val)
        w = widths[i] if i < len(widths) else len(s)

        if i < n - 1:
            out.append(s.ljust(w))
            out.append(sep)
        else:
            out.append(s)

    return "".join(out).rstrip()




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

