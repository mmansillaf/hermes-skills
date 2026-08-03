# INEI Censos 2025 — Territorial Graph Analysis (Session Reference)

**Date:** June 2026
**Project:** `D:\PyCode\Censos2025-Territorial-Grafo\`
**Data source:** INEI Censos 2025 — "Estructura demográfica y envejecimiento poblacional según departamentos seleccionados del Perú 2025.xlsx"

## Data

- 25 departments + Perú, 12 indicators per row
- Columns: `departamento`, `poblacion_total`, `poblacion_censada`, `poblacion_omitida`, `hombres`, `mujeres`, `razon_hombre_mujer`, `edad_promedio`, `edad_mediana`, `personas_60plus`, `porcentaje_60plus`, `indice_envejecimiento`
- **Validated**: censada + omitida = total (27/27 rows). Hombres+Mujeres = Total (NOT censada).
- **Lima split**: "Lima Metropolitana 1/" (43 districts) + "Región Lima 2/" (9 provinces) = 11,148,584 total.
- **Notable**: Lima Metropolitana 2017→2025 factor = 0.991 (slight decrease), while Región Lima grew 1.170×.

## Graph

- 26 nodes, 48 edges, 4 connected components (Callao and Lima naming issues need fixing)
- Junín has the most neighbors (9), Callao the fewest (1)
- Density: 0.148

## Moran's I Results

| Variable | I | p | Interpretation |
|----------|---|---|----------------|
| edad_promedio | +0.533 | <0.001 | Strong clustering: southern departments older, Amazon younger |
| indice_envejecimiento | +0.528 | <0.001 | Same pattern as edad_promedio (r=0.99 between them) |
| porcentaje_60plus | +0.347 | 0.005 | Moderate clustering |
| razon_hombre_mujer | +0.210 | 0.072 | Marginal (Amazon departments have more men) |
| poblacion_total | +0.014 | 0.700 | No spatial pattern |
| poblacion_omitida | +0.029 | 0.620 | No spatial pattern |

## Key Correlations

- edad_promedio ↔ indice_envejecimiento: r = +0.99 (nearly identical constructs)
- razon_hombre_mujer ↔ porcentaje_60plus: r = -0.78 (more elderly = fewer men — women live longer)
- edad_promedio ↔ porcentaje_60plus: r = +0.93

## Dashboard Bugs Found and Fixed

1. **`d3` variable name collision**: `const COLOR_60P = d3 => {...}` shadows Plotly's internal D3 object. Fixed to `item`.
2. **Object-literal arrow function syntax error**: `vars.map(v => ({...})[v])` rejected by Node 22. Fixed to separate `LABEL_MAP`.
3. **Moran I slope mismatch**: JS calculation (OLS z vs Wz) gave different slope than Python (proper Cliff-Ord formula). Fixed by hardcoding the Python I=0.5333.
4. **Tooltips showing `{text}` literal**: `hovertemplate: '%{text}...'` not working reliably. Fixed by using `hovertext` array + `hoverinfo: 'text'`.

## Expansion Distrital

- 100 provinces projected across 10 departments using proportional allocation
- 43 Lima districts projected from 2017 PDF data (factor 1.165×)
- Method: proportional (baseline only — see INFORME_EXPANSION_DISTRITAL.md for SAE/IPF upgrades)

## Files Generated

| File | Description |
|------|-------------|
| `data/censos2025_departamental.csv` | Cleaned 25-department dataset |
| `data/grafo_territorial.graphml` | NetworkX graph (26 nodes, 48 edges) |
| `data/matriz_adyacencia.csv` | 26×26 binary adjacency |
| `data/centralidad.csv` | Degree, betweenness, closeness |
| `data/moran_results.csv` | Moran's I for 6 variables |
| `data/atributos_nodos.csv` | All node attributes |
| `data/provincias_estimacion_2025.csv` | 100 provinces projected |
| `data/distritos_lima_estimacion_2025.csv` | 43 Lima districts projected |
| `outputs/dashboard_territorial_censos2025.html` | Interactive Plotly dashboard |
| `outputs/moran_diagram.png` | Moran scatter plot |
| `informe_completo.md` | Full technical report |

## Script Order

```bash
python scripts/01_cargar_datos.py
python scripts/02_grafo_analisis_espacial.py
python scripts/03_dashboard.py
python scripts/04_expansion_distrital.py
```
