# Spatial Analysis on Territorial Graphs (NetworkX + Moran's I)

## When to use this
When you have geographic regions (departments, provinces, districts) with numeric attributes and need to quantify whether similar values cluster spatially.

## Workflow

### 1. Build adjacency matrix (neighbor relationships)
```python
import networkx as nx
G = nx.Graph()
# Add nodes with demographic attributes
G.add_node("DeptA", poblacion=100000, indice_envejecimiento=65.2)
# Add edges for shared borders (symmetry enforced)
G.add_edge("DeptA", "DeptB")
# Verify symmetry
for d, vecinos in adjacency.items():
    for v in vecinos:
        if d not in adjacency.get(v, []):
            adjacency[v].append(d)  # auto-correct
```

### 2. Build spatial weights matrix W
```python
nodes_list = list(G.nodes())
n = len(nodes_list)
W = np.zeros((n, n))
for i, d1 in enumerate(nodes_list):
    for j, d2 in enumerate(nodes_list):
        if G.has_edge(d1, d2):
            W[i, j] = 1
# Row-normalize (W_ij / sum(W_i))
row_sums = W.sum(axis=1, keepdims=True)
row_sums[row_sums == 0] = 1
W_norm = W / row_sums
```

### 3. Compute Moran's I
```python
def morans_i(valores, W):
    n = len(valores)
    z = valores - np.mean(valores)
    z_lag = W @ z
    numerador = n * np.sum(z * z_lag)
    denominador = np.sum(z**2) * np.sum(W)
    if denominador == 0:
        return 0, 0, 1
    I = numerador / denominador
    # Variance under H0 (Cliff-Ord formula)
    S0 = np.sum(W)
    S1 = 0.5 * np.sum((W + W.T)**2)
    S2 = np.sum((np.sum(W, axis=1) + np.sum(W, axis=0))**2)
    EI = -1 / (n - 1)
    VI = (n**2 * S1 - n * S2 + 3 * S0**2) / (S0**2 * (n**2 - 1)) - EI**2
    if VI <= 0: return I, 0, 1.0
    ZI = (I - EI) / np.sqrt(VI)
    p_valor = 2 * (1 - stats.norm.cdf(abs(ZI)))
    return I, ZI, p_valor
```

### 4. Interpret results
| I de Moran | p-valor | Meaning |
|------------|---------|---------|
| > 0 | < 0.05 | Positive spatial autocorrelation (clusters) |
| ≈ 0 | > 0.10 | Random spatial distribution |
| < 0 | < 0.05 | Negative spatial autocorrelation (dispersion) |

### 5. Moran scatter plot
X-axis: standardized variable z = (x - mean)/std
Y-axis: spatial lag Wz (average of neighbors)
Slope of regression line = I de Moran

### 6. Centrality metrics (NetworkX)
```python
nx.degree_centrality(G)       # Number of neighbors (normalized)
nx.betweenness_centrality(G)  # How often node is on shortest paths ("bridges")
nx.closeness_centrality(G)    # How close node is to all others
```

## Pitfalls
- **Row-normalized W is standard** but not the only option. Binary W or global standardization give different I values. Document which you use.
- **n < 30**: Moran's I asymptotic normality is questionable. Use permutation tests for p-values when n < 30.
- **Symmetry**: Adjacency MUST be bidirectional (if A neighbors B, B neighbors A). Validate programmatically.
- **Connected components**: Moran's I assumes the graph is connected. Disconnected components (naming mismatches, islands) bias results toward zero.
- **Moran's I ≠ causation**: Spatial autocorrelation does not prove one region causes its neighbors' values. Confounders (shared climate, economy, history) produce the same pattern.

## Reference
- Cliff, A.D. & Ord, J.K. (1981). *Spatial Processes: Models & Applications*.
- Anselin, L. (1995). "Local Indicators of Spatial Association — LISA". *Geographical Analysis*.
