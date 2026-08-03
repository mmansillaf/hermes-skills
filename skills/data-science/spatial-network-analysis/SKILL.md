---
name: spatial-network-analysis
description: Build and analyze spatial networks from geographic adjacency — construct NetworkX graphs from region boundaries, assign demographic/economic attributes to nodes, calculate centrality and autocorrelation (Moran's I), and produce interactive Plotly dashboards. Designed for territorial research with census, financial, or administrative data at department/province/district level.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [networkx, spatial, moran, geography, adjacency, graph, network-analysis, dashboard, peru]
    category: data-science
    related_skills: [scientific-statistical-engine, ml-dashboard, ml-pipeline-engine, inclusion-financiera-territorial]
---

# Spatial Network Analysis

Build and analyze spatial networks from geographic adjacency — construct NetworkX graphs from region boundaries, assign demographic/economic attributes to nodes, calculate centrality and autocorrelation (Moran's I), and produce interactive Plotly dashboards.

## When to use

| Trigger | Example |
|---------|---------|
| "Quiero analizar cómo se relacionan los departamentos geográficamente" | Cruzar datos censales con vecindad territorial |
| "¿Los indicadores se agrupan espacialmente?" | Moran's I sobre edad, ingresos, pobreza |
| "¿Qué regiones son puentes entre otras?" | Centralidad de intermediación en el grafo |
| "Necesito un dashboard territorial interactivo" | HTML con grafo force-directed + heatmap + tabla |
| "Estimar datos a nivel de provincia/distrito desde totales departamentales" | Asignación proporcional |

## Core workflow

```
1. Datos departamentales  →  cargar + validar consistencia
2. Matriz de adyacencia   →  definir vecindad geográfica (quién limita con quién)
3. NetworkX graph          →  nodos = regiones, aristas = frontera, atributos = indicadores
4. Centralidad             →  grado, intermediación, cercanía
5. Autocorrelación espacial → I de Moran global (pesos W normalizados por filas)
6. Dashboard               →  Plotly: grafo, Moran, centralidad, correlaciones, tabla
7. Expansión sub-regional  →  asignación proporcional desde censo anterior
```

## Detailed steps

### 1. Build the adjacency matrix

Define `adjacency: dict[str, list[str]]` — each key is a region, each value is its list of geographic neighbors. **Validate symmetry**: if A lists B as neighbor, B must also list A. Auto-fix asymmetries found.

```python
adjacency = {
    "Amazonas": ["Cajamarca", "San Martín", "La Libertad", "Loreto"],
    # ...
}

# Validate symmetry
for d, vecinos in adjacency.items():
    for v in vecinos:
        if d not in adjacency.get(v, []):
            adjacency.setdefault(v, []).append(d)  # auto-fix
```

**Stats to report:** min neighbors, max neighbors, average, density.

### 2. Construct NetworkX graph with node attributes

```python
import networkx as nx
import pandas as pd

G = nx.Graph()

# Add nodes with demographic/economic attributes
for _, row in df.iterrows():
    dept = row['departamento']
    if dept == 'Perú':
        continue
    attrs = {col: float(row[col]) for col in numeric_cols if pd.notna(row[col])}
    G.add_node(dept, **attrs)

# Add edges
for dept, vecinos in adjacency.items():
    for v in vecinos:
        if dept in G and v in G:
            G.add_edge(dept, v)

# Properties to report
nx.is_connected(G)            # Is the graph a single component?
nx.number_connected_components(G)
nx.density(G)
```

### 3. Centrality analysis

```python
centrality = {
    "grado": nx.degree_centrality(G),
    "intermediacion": nx.betweenness_centrality(G),
    "cercania": nx.closeness_centrality(G),
}
```

- **Degree**: number of neighbors (which regions border the most others)
- **Betweenness**: how often a node lies on the shortest path between two others (regions that act as "bridges")
- **Closeness**: how quickly a node can reach all others (how centrally located)

### 4. Global Moran's I (spatial autocorrelation)

Build a **row-normalized spatial weights matrix W**:

```python
n = len(nodes_list)
W = np.zeros((n, n))
for i, d1 in enumerate(nodes_list):
    for j, d2 in enumerate(nodes_list):
        if G.has_edge(d1, d2):
            W[i, j] = 1
W_norm = W / W.sum(axis=1, keepdims=True)  # row-normalize
```

**Moran's I formula**: I = (n / S₀) · (zᵀ W z) / (zᵀ z) where z = standardized values.

```python
def morans_i(valores, W):
    n = len(valores)
    z = valores - np.mean(valores)
    z_lag = W @ z
    numerador = n * np.sum(z * z_lag)
    denominador = np.sum(z**2) * np.sum(W)
    I = numerador / denominador if denominador != 0 else 0
    
    # Variance under H0 (Cliff-Ord formula)
    S0 = np.sum(W)
    S1 = 0.5 * np.sum((W + W.T)**2)
    S2 = np.sum((np.sum(W, axis=1) + np.sum(W, axis=0))**2)
    EI = -1 / (n - 1)
    VI = (n**2 * S1 - n * S2 + 3 * S0**2) / (S0**2 * (n**2 - 1)) - EI**2
    ZI = (I - EI) / np.sqrt(VI) if VI > 0 else 0
    p_valor = 2 * (1 - norm.cdf(abs(ZI)))
    
    return I, ZI, p_valor
```

**Interpretation:**
| I value | p-value | Meaning |
|---------|---------|---------|
| I > 0, p < 0.05 | Significant | Neighbors have similar values (clustering) |
| I ≈ 0, p > 0.05 | Not significant | Random spatial distribution |
| I < 0, p < 0.05 | Significant | Neighbors have opposite values (dispersion) |

**Important**: With small n (< 30), the asymptotic variance may be underestimated. Report both I and p-value, and note the sample size limitation.

### 5. Dashboard visualization

Use the `ml-dashboard` skill's patterns for Plotly. Key chart types for spatial networks:

| Chart | Plotly type | Data |
|-------|-------------|------|
| **Force-directed graph** | Scatter (lines + markers) | Edge coordinates + node positions from 100-iteration repulsion-attraction simulation |
| **Moran scatter plot** | Scatter + regression line | z-scores (x) vs spatial lag Wz (y), slope = I |
| **Centrality bars** | Bar (horizontal) | Sorted by degree/betweenness/closeness |
| **Correlation heatmap** | Heatmap (triangular) | Pearson r between all indicator pairs |
| **Data table** | HTML table | All regions with attributes + neighbors |

**CRITICAL Plotly pitfalls (from ml-dashboard skill):**
- **NEVER name a variable `d3`** — it shadows Plotly's internal D3 and silently breaks all charts
- **Separate lookup objects** instead of `array.map(v => ({...})[v])` — JS engine inconsistency
- **Use `hovertext` + `hoverinfo: 'text'`** instead of `hovertemplate: '%{text}...'` for reliable tooltips

### 6. Proportional sub-region allocation

When detailed sub-region data (province, district) is unavailable for the current year, estimate using:

```python
factor = pob_departamento_2025 / pob_departamento_2017
pob_provincia_2025_est = pob_provincia_2017 * factor
```

**Assumption**: intra-departmental proportions remain stable between censuses. This is a baseline method — document it as such. For more rigorous estimation, use SAE Fay-Herriot or IPF (see `inclusion-financiera-territorial` skill).

**Must document limitations**:
- Does not capture differential migration
- Does not capture new urbanization
- Does not capture pandemic effects on specific sub-regions
- Does not capture boundary changes

## Pitfalls

1. **Graph disconnected components**: When names in the adjacency matrix don't exactly match node names (e.g., "Lima Metropolitana 1/" has trailing characters), the edge won't connect. Normalize names before adding edges.
2. **Moran's I with n < 30**: The Cliff-Ord asymptotic variance may be unreliable. Report p-value but note the limitation. The bootstrap permutation test is more robust for small n.
3. **Row-normalized W vs binary W**: Row-normalization changes the interpretation of Moran's I — it becomes the slope of the regression of z on the average of neighbors' z, not the sum. Document which normalization you use.
4. **Connectivity completeness**: Verify every node in the graph has at least one neighbor that actually exists. Islands (nodes with no edges) inflate centrality metrics for other nodes.
5. **Excel number formatting**: INEI exports use spaces as thousands separators and commas as decimals. Clean with `str.replace(" ", "").str.replace(",", ".")` before `pd.to_numeric()`.
6. **Validation: censada + omitida = total**: Always check this. If it fails, the column interpretation is wrong. Also verify hombres + mujeres match the total, not just the censada population.

## Output

Always produce:
- `data/` — processed CSV/XLSX, adjacency matrix, graph attributes
- `outputs/` — dashboard HTML, PNG diagnostic plots
- `scripts/` — numbered pipeline scripts (01_load, 02_graph, 03_dashboard, 04_expansion)
- `informe_completo.md` — full technical report with data dictionary, glossary, and self-evaluation

## References

See `references/session-inei-censos2025.md` for the concrete implementation against INEI Censos 2025 data (25 departments, 12 indicators, 48 edges).
