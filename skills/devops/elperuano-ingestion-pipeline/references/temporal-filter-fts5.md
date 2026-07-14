# Temporal Filter (Year + Month) for FTS5 Queries

## Problem
Temporal queries like "normas del año 2020" match via FTS5 on any mention
of the year in texto_completo, not just norms published in that year.

## Solution
Filter `AND fecha_publicacion LIKE 'YYYY%'` in the FTS5 query.
Implemented in api_rest.py lines 817-837.

## Results
| Query | Without | With filter |
|-------|---------|-------------|
| "normas setiembre 2024" | 18,104 | 1,193 |
| "presupuesto 2027" | 3 (FP) | 0 |
| "normas 2010" | 3 (FP) | 0 |
