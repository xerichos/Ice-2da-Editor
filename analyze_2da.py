#!/usr/bin/env python3
from data.twoda import load_2da

# Load the good skills.2da
data = load_2da('skills.2da')
print('Header spans:')
for i, (start, end) in enumerate(data.header_format.spans):
    width = end - start
    field = data.header_fields[i] if i < len(data.header_fields) else '???'
    print(f'  {i}: [{start}:{end}] width={width} "{field}"')

print('\nHeader raw line:')
print(repr(data.header_format.raw))

print('\nFirst data row spans:')
for i, (start, end) in enumerate(data.row_formats[0].spans):
    width = end - start
    field = data.row_fields[0][i] if i < len(data.row_fields[0]) else '???'
    print(f'  {i}: [{start}:{end}] width={width} "{field}"')

print('\nFirst data row raw line:')
print(repr(data.row_formats[0].raw))
