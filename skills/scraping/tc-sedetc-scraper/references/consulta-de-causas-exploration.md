# Consulta de Causas — TC's Legacy Case Search System

## Overview

The TC has a second case-search system at `https://www.tc.gob.pe/consultas-de-causas/`
that predates the SEDETC portal. It contains historical cases (at least from 2020
onwards) that are NOT available through the SEDETC API.

## Stack Analysis

| Component | Detail |
|-----------|--------|
| CMS | **WordPress** (wp-json endpoints visible) |
| Page ID | `/wp-json/wp/v2/pages/122` |
| Frontend | Bootstrap 4, jQuery, DataTables 1.10.19 |
| Pagination | bootpag 1.0.7 |
| Validation | jQuery Validate 1.17 |
| Data | Server-side via DataTables AJAX |

## Forms

Two search forms exist on the page:

### Form 1: BÚSQUEDA TC (id="form_causas")
- Fields: `n_exp` (número de expediente), `anio` (año), `tipo_expediente` (select), demandante, demandado, ponente
- Button: `btn_consultar` → triggers DataTables AJAX server-side processing
- Action: Submits via JS, no `<form action>` attribute

### Form 2: BÚSQUEDA PJ (id="form_causas2")
- Connects to Poder Judicial's database by PJ case number
- Separate system

## Quick Search Endpoint

Found in `theme.js` line 273:
```javascript
$('#buscador_x_num_exp').click(function(event) {
    window.location = './consultas-de-causas/detalles-consulta/?action=index_expedientes&a_exp=&num_exp=' + cnum_ex + '&datos_deman=' + datos_dem;
});
```

This endpoint returns a full HTML page with case details:
```
https://www.tc.gob.pe/consultas-de-causas/detalles-consulta/?action=index_expedientes&a_exp=2022&num_exp=&datos_deman=
```

## What Works

### Individual Case Details (by ID)
```
https://www.tc.gob.pe/consultas-de-causas/detalles-consulta?id_exp=481876
```
Returns full case detail page with:
- Nro. expediente, fecha de ingreso, colegiado, ponente
- Resoluciones publicadas (PDF + HTML links)
- Audiencias públicas
- Vista de causas

### PDF Links Found on Detail Pages
All link to `tc.gob.pe/jurisprudencia/{year}/{expediente}.pdf` — same pattern
as SEDETC. Verified working for cases from 2022, 2023.

## What Does NOT Work

### Direct Page-based Search
Trying `?anio=2022` or POST with form data returns the search page without results.
The search uses DataTables server-side processing, which means the AJAX call
goes to WordPress's `admin-ajax.php` with a custom action. The exact action name
could not be determined without browser automation.

### Old System (181.177.234.6)
The legacy system at IP `181.177.234.6/buscarRes/public/resolucionjur` is
blocked/inaccessible (connection refused or timed out).

## Strategy to Scrape

To extract older cases, you'll need:

1. **Browser automation** (Selenium/undetected_chromedriver) to:
   - Load the page `https://www.tc.gob.pe/consultas-de-causas/`
   - Fill year field, click CONSULTAR
   - Intercept the DataTables AJAX call to find the actual endpoint
   - Paginate through all results for each year

2. **Extract expediente numbers** from the DataTable rows

3. **Verify PDFs** at `https://tc.gob.pe/jurisprudencia/{year}/{expediente}.pdf`

4. **Download** using the same pattern as the SEDETC scraper

## Limitations

- WordPress site — fragile to updates and plugin changes
- DataTables server-side — pagination state may use POST parameters
- No rate limit information available (untested at scale)
- The system shows "2,365 resoluciones publicadas en el presente año (2026)"
  on the publicadas-en-el-dia page, suggesting significant volume per year
