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


def rebuild_line(fmt: TwoDARow, new_fields: List[str]) -> str:
    raw_list = list(fmt.raw)

    for (start, end), value in zip(fmt.spans, new_fields):
        width = end - start
        text = value.ljust(width)[:width]
        for i, ch in enumerate(text):
            raw_list[start + i] = ch

    return "".join(raw_list)


def load_2da(path: str) -> TwoDAData:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

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
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data.version_line + "\n")

        # restore blank lines between version and header
        for _ in range(data.empty_lines_before_header):
            f.write("\n")

        # header: same field count as original, so spans are safe
        header_line = rebuild_line(data.header_format, data.header_fields)
        f.write(header_line + "\n")

        # rows
        for fmt, fields in zip(data.row_formats, data.row_fields):
            line = rebuild_line(fmt, fields)
            f.write(line + "\n")
