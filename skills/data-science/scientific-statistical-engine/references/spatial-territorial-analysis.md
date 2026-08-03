# Análisis Espacial y Grafos Territoriales — Referencia Práctica

**Caso concreto:** Censos Nacionales 2025 (INEI, Perú) — 25 departamentos, 12 indicadores demográficos.
**Stack:** Python 3.12, NetworkX 3.x, NumPy, Pandas, SciPy, Plotly.
**Repositorio ejemplo:** `D:\PyCode\Censos2025-Territorial-Grafo\` (informe completo en `informe_completo.md`).

---

## 1. Matriz de Adyacencia (Vecindad Geográfica)

```python
adjacency = {
    "Amazonas": ["Cajamarca", "San Martín", "La Libertad", "Loreto"],
    "Áncash": ["La Libertad", "Huánuco", "Lima Región", "Junín"],
    # ... los 25 departamentos
}

# Validar simetría
asymmetric = []
for d, vecinos in adjacency.items():
    for v in vecinos:
        if d not in adjacency.get(v, []):
            asymmetric.append((d, v))

# Corregir automáticamente
for d, v in asymmetric:
    adjacency.setdefault(v, []).append(d)
```

**Regla:** Siempre validar simetría — las fronteras son bidireccionales.

## 2. Grafo con NetworkX

```python
import networkx as nx

G = nx.Graph()

# Añadir nodos con atributos demográficos
for _, row in df.iterrows():
    attrs = {col: float(row[col]) for col in numeric_cols if pd.notna(row[col])}
    G.add_node(row['departamento'], **attrs)

# Añadir aristas
for dept, vecinos in adjacency.items():
    for v in vecinos:
        if dept in G and v in G:
            G.add_edge(dept, v)

# Métricas del grafo
print(f"Nodos: {G.number_of_nodes()}")
print(f"Aristas: {G.number_of_edges()}")
print(f"¿Conexo?: {nx.is_connected(G)}")
print(f"Densidad: {nx.density(G):.3f}")
print(f"Componentes: {nx.number_connected_components(G)}")
```

## 3. Centralidades

```python
centralidad = {
    "grado": nx.degree_centrality(G),
    "intermediacion": nx.betweenness_centrality(G),
    "cercania": nx.closeness_centrality(G)
}

# Identificar "puentes" (alta intermediación)
top_puentes = sorted(centralidad["intermediacion"].items(), key=lambda x: -x[1])[:3]
# Ejemplo real: Ucayali (0.212), La Libertad (0.204), Junín (0.204)
```

## 4. I de Moran Global

```python
def morans_i(valores, W):
    """W = matriz de pesos normalizada por filas"""
    n = len(valores)
    z = valores - np.mean(valores)
    z_lag = W @ z
    
    numerador = n * np.sum(z * z_lag)
    denominador = np.sum(z**2) * np.sum(W)
    if denominador == 0:
        return 0, 0, 1.0
    
    I = numerador / denominador
    
    # Varianza (Cliff-Ord)
    S0 = np.sum(W)
    S1 = 0.5 * np.sum((W + W.T)**2)
    S2 = np.sum((np.sum(W, axis=1) + np.sum(W, axis=0))**2)
    
    EI = -1 / (n - 1)
    VI = (n**2 * S1 - n * S2 + 3 * S0**2) / (S0**2 * (n**2 - 1)) - EI**2
    
    if VI <= 0:
        return I, 0, 1.0
    
    ZI = (I - EI) / np.sqrt(VI)
    p_valor = 2 * (1 - stats.norm.cdf(abs(ZI)))
    
    return I, ZI, p_valor
```

**Interpretación de resultados reales (Censos 2025, n=26):**

| Variable | I de Moran | p-valor | Interpretación |
|---|---|---|---|
| Edad promedio | +0.53 | < 0.001 | Clustering fuerte: sur envejecido, selva joven |
| Índice de envejecimiento | +0.53 | < 0.001 | Misma tendencia |
| % 60+ | +0.35 | 0.005 | Clustering moderado |
| Razón H-M | +0.21 | 0.072 | Marginal |
| Población total | +0.01 | 0.700 | Sin patrón espacial |

## 5. Diagrama de Dispersión de Moran

```python
import matplotlib.pyplot as plt

z = (valores - np.mean(valores)) / np.std(valores)
z_lag = W @ z

fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(z, z_lag, c='steelblue', s=80, alpha=0.7)

# Anotar puntos extremos
for i, node in enumerate(nodes):
    if abs(z[i]) > 1.0 or abs(z_lag[i]) > 1.0:
        ax.annotate(node, (z[i], z_lag[i]), fontsize=7)

# Línea de regresión (pendiente = I de Moran)
slope = I
x_line = np.linspace(min(z), max(z), 100)
ax.plot(x_line, slope * x_line, 'r--', alpha=0.7, label=f'I = {slope:.4f}')

# Cuadrantes
ax.axhline(0, color='gray', ls='--', alpha=0.5)
ax.axvline(0, color='gray', ls='--', alpha=0.5)
```

## 6. Expansión Territorial Proporcional

```python
# Porcentaje de cada provincia dentro de su depto (Censo anterior)
pesos = pob_prov_2017 / pob_depto_2017

# Aplicar a totales del nuevo censo
pob_prov_2025 = pesos * pob_depto_2025
```

**Limitación:** Asume proporciones constantes entre censos. No captura migración diferencial, nuevas urbanizaciones, o cambios de límites.

## 7. Validaciones críticas

Antes de ejecutar cualquier análisis espacial:

1. ✅ **Simetría de W** — toda relación A→B implica B→A
2. ✅ **Sumas parciales = totales** — población censada + omitida = total
3. ✅ **Hombres + Mujeres** — debe cuadrar con población total
4. ✅ **n > 3** — Moran's I requiere al menos 4 observaciones
5. ✅ **Componentes conexos** — deben ser 1 (si no, revisar nombres)
6. ✅ **Matriz W definida positiva** — para análisis avanzados

## 8. Errores comunes detectados en la práctica

| Error | Síntoma | Solución |
|---|---|---|
| Nombre de nodo no coincide | Componentes conexos > 1 | Normalizar: `.strip()`, quitar notas al pie |
| W asimétrica | Sesgo en I de Moran | Validar y corregir automáticamente |
| n < 30 | p-valores optimistas | Reportar, considerar permutaciones |
| Población H+M ≠ censada | Columnas mal interpretadas | H+M = total, no censada. Verificar etiquetas INEI |

## 9. Referencias

- Cliff, A.D. & Ord, J.K. (1981). *Spatial Processes: Models & Applications*
- Anselin, L. (1995). "Local Indicators of Spatial Association — LISA"
- INEI (2025). Censos Nacionales 2025 — Primeros Resultados
- Proyecto ejemplo: `D:\PyCode\Censos2025-Territorial-Grafo\`
