# TC Consulta de Causas — WordPress/DataTables Scraping Pattern

## Overview

The TC Peru has a WordPress-based system at `tc.gob.pe/consultas-de-causas/` that predates the SEDETC Nuxt.js portal. It uses jQuery DataTables with server-side processing to list and paginate expedientes. Unlike the SEDETC API (REST JSON), this system returns HTML tables and requires no JavaScript execution — the search parameters work via GET.

## Key Discovery

The search URL was found by inspecting the browser's form submission, which revealed a GET-based endpoint:

```
https://www.tc.gob.pe/consultas-de-causas/?bus=tc&action=search
  &n_exp=&a_exp={YEAR}&tip_exp=&demdt=&demdo=&ponte=&cod=&pagina={PAGE}
```

## Data Characteristics

| Year | Expedientes | Pages (20/page) |
|------|-------------|-----------------|
| 2026 | 114 | 6 |
| 2025 | 316 | 16 |
| 2024 | 257 | 13 |
| 2023 | 253 | 13 |
| 2022 | 275 | 14 |
| 2021 | 207 | 11 |
| 2020 | 121 | 7 |
| 2019 | 256 | 13 |
| 2018 | 251 | 13 |

## Search Results Parsing

The search results table uses `<th scope="row">` for expediente numbers (not `<td>`). The `id_exp` link is in the last `<td>`:

```html
<tr>
  <th scope="row" data-title="Nro. Expediente">00001-2022-AA</th>
  <td data-title="Demandante">...</td>
  <td data-title="Demandado">...</td>
  <td data-title="Nro. PJ">...</td>
  <td><a href="detalles-consulta?id_exp=476993">Ver</a></td>
</tr>
```

**Parsing rule**: Match both `<td>` and `<th>` cells. The `id_exp` is in the last cell's link, not in the expediente cell.

```python
all_cells = re.findall(r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>', row, re.DOTALL)
exp_match = re.search(r'(\d{5}-\d{4}-[A-Z]+)', all_cells[0])
id_match = re.search(r'detalles-consulta\?id_exp=(\d+)', row)
```

## Detail Page Parsing

The detail page (`detalles-consulta?id_exp=N`) has a "Resoluciones y Sentencias Publicadas" table with 6 columns:

| Col | Header |
|-----|--------|
| 0 | Tipo de Resolución |
| 1 | Fecha de Public. Web |
| 2 | Public. Diario El Peruano |
| 3 | Fallo |
| 4 | Ver Publicación (PDF link) |
| 5 | Ver Publicación (Formato HTML) |

**Parsing**: PDF link is in cell [4], HTML link in cell [5]. The PDF URLs may contain spaces:

```
https://www.tc.gob.pe/jurisprudencia/2023/00001-2022-AA Resolucion.pdf
```

**Fix**: Normalize filenames with `re.sub(r'\s+', ' ', filename)`.

## PDF URL Pattern

```
https://www.tc.gob.pe/jurisprudencia/{PUB_YEAR}/{EXPEDIENTE}.pdf
```

The `PUB_YEAR` comes from the detail page (publication date), not from the expediente number. An expediente from 2021 may publish in 2022, so the PDF is stored under `/2022/`.

## HTML Version Available

Each resolution also has an HTML version:
```
https://www.tc.gob.pe/jurisprudencia/{PUB_YEAR}/{EXPEDIENTE}.htm
```

## Known Issues

- **Pagination parameter `pagina=N` is 1-indexed.** Page 1 returns records 1-20, page 2 returns 21-40, etc.
- **No auth required.** All endpoints are public GET requests.
- **No rate limit detected.** Safe to use 0.3s delay between requests (3 req/s).
- **Connection pool exhaustion**: 24 parallel workers on `requests.Session()` triggers "Connection pool is full" warnings. Either increase pool size or use individual `requests.get()` calls for downloads.
- **Total counts per year are approximate.** The HTML shows `total: N` in the pagination section.
- **Some expedientes have no resoluciones.** These are cases still in process, not yet resolved. The detail page will have no "Resoluciones y Sentencias Publicadas" table.

## Differences from SEDETC API

| Aspect | SEDETC API | Consulta de Causas |
|--------|-----------|-------------------|
| Framework | Nuxt.js (Vue SPA) | WordPress + jQuery |
| Data format | JSON via REST API | HTML tables |
| Coverage | Nov 2023 → present | 2018 → present (sparser) |
| Indexing | Each fundamento jurídico as entry | Each expediente once |
| Auth | None | None |
| Pagination | `?page=N` (GET) | `?pagina=N` (GET) |
| Items per page | 10 | 20 |
| Total catalog | ~10,000 | ~2,300 unique exp |
