# Temporal Filter Gap

## Problem

Query "normas del año 2020" returns confidence 0.72 (false positive). Root cause: FTS5 searches for "2020" in `texto_completo` and finds norms from 2021-2025 that MENTION "2020" in their text. The temporal intent (filter by `fecha_publicacion`) is not applied.

Example: "Aprueban los Estados Financieros del Año Fiscal 2020" = published 2021-03-31, but matches FTS5 query for "2020".

## Solution (not yet implemented)

When query classifier detects Type C (TEMPORAL), extract year with regex `\b(20\d{2})\b` and add SQL filter:

```python
# In search_sqlite or hybrid search:
if query_type == 'C':
    year_match = re.search(r'\b(20\d{2})\b', question)
    if year_match:
        year = year_match.group(1)
        sql_query += f" AND fecha_publicacion LIKE '{year}%'"
```

This way, a query for "normas del año 2020" would add `AND fecha_publicacion LIKE '2020%'` - and since the DB has no 2020 norms, results = 0, confidence stays low.

## Status
Not yet implemented. Requires ~15 lines in `api_rest.py` search function.
