# data/twoda.py
from dataclasses import dataclass, field
from typing import List, Tuple
import re


@dataclass
class TwoDARow:
    raw: str
    fields: List[str]
    spans: List[Tuple[int, int]]


@dataclass
class TwoDAData:
    header_fields: List[str] = field(default_factory=list)
    row_fields: List[List[str]] = field(default_factory=list)

    header_format: TwoDARow = None
    row_formats: List[TwoDARow] = field(default_factory=list)

    version_line: str = "2DA V2.0"
    empty_lines_before_header: int = 0


def parse_raw_line(line: str) -> TwoDARow:
    spans: List[Tuple[int, int]] = []
    fields: List[str] = []

    for m in re.finditer(r"\S+", line):
        start, end = m.start(), m.end()
        spans.append((start, end))
        fields.append(line[start:end])

    return TwoDARow(raw=line, fields=fields, spans=spans)


def load_2da(path: str) -> TwoDAData:
    # Read raw bytes to detect line endings
    with open(path, "rb") as f:
        raw_data = f.read()

    # Detect line ending
    if b'\r\n' in raw_data:
        linesep = '\r\n'
        text_data = raw_data.decode('utf-8').replace('\r\n', '\n')
    else:
        linesep = '\n'
        text_data = raw_data.decode('utf-8')

    lines = text_data.splitlines()

    # Version
    if lines and lines[0].strip().startswith("2DA"):
        version = lines.pop(0).strip()
    else:
        version = "2DA V2.0"

    # Count and skip blank lines between version and header
    empty_count = 0
    while lines and not lines[0].strip():
        lines.pop(0)
        empty_count += 1

    parsed = [parse_raw_line(line) for line in lines if line.strip()]
    if not parsed:
        raise ValueError("Empty or invalid 2DA")

    header_fmt = parsed[0]
    row_fmt_list = parsed[1:]

    header_fields = header_fmt.fields.copy()
    row_fields = [r.fields.copy() for r in row_fmt_list]

    # Store the detected line ending for saving
    header_fmt._linesep = linesep
    for fmt in row_fmt_list:
        fmt._linesep = linesep

    # NOTE: no index-column fiddling here; rows stay exactly as in file.

    return TwoDAData(
        header_fields=header_fields,
        row_fields=row_fields,
        header_format=header_fmt,
        row_formats=row_fmt_list,
        version_line=version,
        empty_lines_before_header=empty_count,
    )


def save_2da(path: str, data: TwoDAData):
    # Preserve original line ending if we detected it at load time
    linesep = getattr(data.header_format, "_linesep", "\n")

    header = list(data.header_fields or [])
    rows = [list(r) for r in (data.row_fields or [])]

    # If there is no header, there's nothing sensible to write
    if not header:
        raise ValueError("Cannot save 2DA: header_fields is empty")

    n_cols = len(header)
    target_row_len = 1 + n_cols  # index + data columns

    def norm_cell(v: str) -> str:
        # In 2DA files, **** represents an empty/undefined value.
        if v is None:
            return "****"
        s = str(v)
        return "****" if s == "" else s

    # Normalize rows to the expected length: [index] + n header columns
    norm_rows = []
    for i, r in enumerate(rows):
        r = [norm_cell(x) for x in r]

        if not r:
            r = [str(i)]
        if r[0] == "****":
            r[0] = str(i)

        if len(r) < target_row_len:
            r.extend(["****"] * (target_row_len - len(r)))
        elif len(r) > target_row_len:
            r = r[:target_row_len]

        norm_rows.append(r)

    # Compute widths for real data columns (excluding index)
    col_widths = []
    for j in range(n_cols):
        maxw = len(header[j])
        for r in norm_rows:
            maxw = max(maxw, len(r[j + 1]))
        col_widths.append(maxw)

    # Index column width (for padding index values only)
    idx_width = max(1, max((len(r[0]) for r in norm_rows), default=1))

    def format_data_fields(fields_1_to_n):
        # Single-space separator, with padding to column widths.
        # (This matches the ?no extra phantom header column? requirement and prevents the drift.)
        parts = []
        for j, val in enumerate(fields_1_to_n):
            if j == n_cols - 1:
                parts.append(val)
            else:
                parts.append(val.ljust(col_widths[j]))
        return " ".join(parts)


    out_lines = []

    # Version line
    out_lines.append((data.version_line or "2DA V2.0").strip())

    # Blank lines between version and header (commonly 1)
    out_lines.extend([""] * int(getattr(data, "empty_lines_before_header", 0) or 0))

    # Header line: preserve original trailing whitespace (if any)
    hdr_suffix = trailing_suffix(data.header_format)
    out_lines.append("   " + format_data_fields([norm_cell(h) for h in header]) + hdr_suffix)

    # Data rows: preserve original trailing whitespace per row (if any)
    for i, r in enumerate(norm_rows):
        idx = r[0].ljust(idx_width)  # keep padding (no rstrip)
        if i < len(data.row_formats):
            suffix = trailing_suffix(data.row_formats[i])
        elif data.row_formats:
            suffix = trailing_suffix(data.row_formats[-1])
        else:
            suffix = ""
        out_lines.append(idx + " " + format_data_fields(r[1:]) + suffix)


    with open(path, "wb") as f:
        f.write((linesep.join(out_lines) + linesep).encode("utf-8"))

def trailing_suffix(fmt) -> str:
    # Preserve exactly what was after the last token in the original raw line (usually spaces).
    if fmt and getattr(fmt, "spans", None):
        return fmt.raw[fmt.spans[-1][1]:]
    return ""
