---
name: excel-consolidation
category: data-science
triggers:
  - "consolidate multiple excel sheets"
  - "merge excel files into one"
  - "remove duplicates from excel"
  - "unify columns across sheets"
  - "combine workbooks"
  - "dedup excel rows"
description: >-
  Consolidate multiple sheets or files from an Excel workbook into a single
  sheet with unified columns, removing exact duplicate rows. Handles sheets
  with different column counts, missing columns, and large datasets (100K+
  rows) efficiently.
---

# Excel Consolidation & Dedup

## When to use

- A client/partner sends a multi-sheet Excel where each sheet has the same *kind* of data but different column layouts
- Some sheets have fewer columns (e.g. missing `FECHA DE INICIO` or `MATERIA`)
- The user wants all data in one sheet, no exact duplicate rows, uniform column order
- Dataset is 10K-200K rows (fits in memory on a modern machine with openpyxl)

## Architecture pattern

```
Multi-sheet Excel
  ├── Sheet A (11 cols)
  ├── Sheet B (11 cols)
  ├── Sheet C (9 cols — missing cols 4 and 9)
  └── Sheet D (11 cols)
        ↓
  Normalize each row to 11 cols (fill missing with None)
        ↓
  Dedup by (col1, col2, ..., col11) tuple
        ↓
  Single-sheet output Excel
```

## Key steps

### 1. Understand the column layout

```python
import openpyxl
wb = openpyxl.load_workbook(input_path)
for sname in wb.sheetnames:
    ws = wb[sname]
    header = [c.value for c in ws[1]]  # or row 3 if the sheet has title rows
    print(f'{sname}: {len(header)} columns → {header}')
```

Many real-world Excel files have **title rows** (row 1 = sheet name, row 2 = blank, row 3 = actual headers). Always check by printing the first 5 rows.

### 2. Define the target column layout

```python
TARGET_COLS = [
    'COL_A', 'COL_B', 'COL_C',  # ... all columns
]
```

### 3. Map source columns to target indices

For each sheet, create a mapping dict: `{source_index: target_index}`

```python
# Example: 9-col sheet mapping to 11-col target
# source cols 0-8 map to target cols 0,1,2,3,5,6,7,8,10 (skipping 4 and 9)
MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 6, 6: 7, 7: 8, 8: 10}
```

### 4. Normalize rows

```python
def normalize(values, col_map):
    """Convert a source row to the target column format, filling missing with None."""
    row = [None] * len(TARGET_COLS)
    for src, dst in col_map.items():
        if src < len(values):
            row[dst] = values[src]
    return row
```

### 5. Skip non-data rows

Skip rows that are:
- Title/header rows (row index < 3 in many cases)
- Entirely empty (`all(v is None for v in values)`)
- Missing the key column (e.g. empty `N° EXPEDIENTE`)

### 6. Dedup strategy

```python
def row_key(row):
    """Case-insensitive, trimmed string tuple for dedup."""
    return tuple(str(v).strip().lower() if v is not None else '' for v in row)

seen = set()
unique_rows = []
for row in source_rows:
    norm = normalize(row, col_map)
    if not norm[KEY_INDEX]:  # skip rows without key value
        continue
    key = row_key(norm)
    if key not in seen:
        seen.add(key)
        unique_rows.append(norm)
```

### 7. Write output efficiently

For large datasets (50K+ rows), write in batches to avoid peak memory:

```python
wb_out = Workbook()
ws_out = wb_out.active
ws_out.append(TARGET_COLS)

batch_size = 10000
for i in range(0, len(unique_rows), batch_size):
    batch = unique_rows[i:i + batch_size]
    for row in batch:
        ws_out.append(row)

wb_out.save(output_path)
```

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Row 1 is a sheet TITLE, not the header | Check by printing rows 1-5. Skip first 2-3 rows before reading headers |
| Columns have different NAMES in different sheets | Map by position index, not by column name |
| `read_only=True` can't write | Use `read_only=True` for reading large input, never for writing. Write with normal Workbook |
| Datetime objects in cells | openpyxl preserves them as `datetime.datetime` objects — they dedup correctly because Python compares datetimes by value |
| Memory with 200K+ rows | Use `read_only=True` for reading, batch appending for writing. 133K rows × 11 cols fits in ~2GB RAM |
| String whitespace differences | `.strip()` before comparison. "MINISTERIO " and "MINISTERIO" are different strings but should be the same data |
| None vs "" vs " " | Normalize all to consistent empty value. I use `''` in the key function |
| Case differences | `.lower()` before comparison. "OSINERGMIN" vs "osirgemin" |
| File is password-protected | openpyxl cannot read password-protected files. Ask user to remove protection first |
| Merged cells in source | openpyxl reads merged cells as None in all but the top-left cell. The value only appears once |
| Encoding of non-ASCII chars | openpyxl handles UTF-8 correctly. Ensure `encoding='utf-8'` if writing CSV instead |

## Dedup semantics

The dedup removes **exact row duplicates** — rows where ALL columns have the same value. This is different from "same expediente code" dedup:

| N° EXPEDIENTE | ACTO PROCESAL | ESTADO |
|--------------|--------------|--------|
| 00001-2021 | SENTENCIA | ARCHIVO |
| 00001-2021 | SENTENCIA | ARCHIVO | ← REMOVED (exact duplicate)
| 00001-2021 | AUTO | ARCHIVO | ← KEPT (different ACTO)

If the user wants "one row per expediente" (deeper dedup), they need to specify which column to keep (e.g. latest ACTO). This is a different operation.

## Output naming convention

```
CONSOLIDADO_{original_filename}.xlsx
```

Saved in the same directory as the input file.

## Summary of counts for report

After consolidation, give the user:

```python
unique_exps = set()
for row in unique_rows:
    unique_exps.add(str(row[EXPEDIENTE_COL_INDEX]).strip())
print(f'Filas en source: {total_input_rows}')
print(f'Filas en output: {len(unique_rows)}')
print(f'Reducción: {((total_input_rows - len(unique_rows))/total_input_rows*100):.1f}%')
print(f'Expedientes únicos: {len(unique_exps)}')
```
