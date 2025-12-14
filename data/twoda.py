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
    from .twoda_rebuild import calculate_column_widths, rebuild_line_dynamic
    
    # Calculate dynamic column widths based on current content
    header_widths, data_widths = calculate_column_widths(data)

    # Get line ending from original format
    linesep = getattr(data.header_format, '_linesep', '\n')

    with open(path, "wb") as f:  # Write as bytes to preserve line endings
        # Version line
        f.write((data.version_line + linesep).encode('utf-8'))

        # Restore blank lines between version and header
        for _ in range(data.empty_lines_before_header):
            f.write(linesep.encode('utf-8'))

        # Header: preserve visual formatting but allow expansion
        header_line = rebuild_line_dynamic(data.header_format, data.header_fields, header_widths, preserve_spacing=True)
        f.write((header_line + linesep).encode('utf-8'))

        # Rows: allow dynamic expansion with proper spacing
        for fmt, fields in zip(data.row_formats, data.row_fields):
            line = rebuild_line_dynamic(fmt, fields, data_widths, preserve_spacing=False)
            f.write((line + linesep).encode('utf-8'))
