# data/utils.py

import re
from typing import List

def read_2da_lines(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if lines and lines[0].startswith("2DA"):
        return lines[1:]
    return lines

def parse_2da_rows(lines: List[str]) -> List[List[str]]:
    parsed = []
    for line in lines:
        if not line.strip():
            continue
        cleaned = line.rstrip()
        parts = re.split(r"\s+", cleaned.strip())
        parsed.append(parts)
    return parsed

def detect_index_column(header: List[str], rows: List[List[str]]) -> List[str]:
    if rows and len(rows[0]) == len(header) + 1:
        first = rows[0][0]
        if first == "" or first.isdigit():
            return [""] + header
    return header

def normalize_rows(header: List[str], rows: List[List[str]]) -> List[List[str]]:
    target = len(header)
    out = []
    for row in rows:
        if len(row) < target:
            row = row + [""] * (target - len(row))
        elif len(row) > target:
            row = row[:target]
        out.append(row)
    return out
