# Sensitivity & Stability Analysis for ML Clustering Projects

## ¿Por qué hacer análisis de sensibilidad?

Un modelo ML produce resultados puntuales. El análisis de sensibilidad
responde: **¿cuán confiables son esos resultados?**

Para proyectos de clustering territorial (K-Means, DBSCAN) con n < 50
observaciones, la sensibilidad es crítica porque:

- La inicialización aleatoria de K-Means produce particiones diferentes
- Random Forest tiene estocasticidad en la selección de features
- DBSCAN depende fuertemente del parámetro eps
- Pequeños cambios en los datos de entrada cambian las asignaciones
- Cada feature tiene un peso distinto en la segmentación

## 1. Estabilidad K-Means (semilla aleatoria)

Evalúa si la partición cambia según la inicialización.

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

N_SEEDS = 100
K_FINAL = 3
asignaciones = np.zeros((N_SEEDS, len(X_original)), dtype=int)

for i in range(N_SEEDS):
    km = KMeans(n_clusters=K_FINAL, random_state=i, n_init=30)
    asignaciones[i] = km.fit_predict(X_original)

# Comparar todas vs referencia (seed=42)
labels_ref = asignaciones[42 % N_SEEDS]
ari_vs_ref = [adjusted_rand_score(labels_ref, asignaciones[i])
              for i in range(N_SEEDS)]
print(f"ARI promedio: {np.mean(ari_vs_ref):.4f} ± {np.std(ari_vs_ref):.4f}")
```

### ⚠ Label switching (cambio de rótulos)

K-Means asigna etiquetas 0, 1, 2 arbitrariamente. Dos semillas pueden
producir la MISMA partición con diferente numeración. ARI (Adjusted Rand
Index) es invariante a permutaciones, pero para comparar asignaciones
directamente hay que alinear las etiquetas.

```python
from scipy.optimize import linear_sum_assignment

def alinear_etiquetas(labels_ref, labels_objetivo):
    """
    Re-numera labels_objetivo para maximizar coincidencias con labels_ref.
    Usa Hungarian algorithm para resolver el label switching.
    """
    k = max(labels_ref.max(), labels_objetivo.max()) + 1
    match_cost = np.zeros((k, k))
    for u in range(k):
        for v in range(k):
            match_cost[u, v] = ((labels_ref == u) & (labels_objetivo == v)).sum()
    # Hungarian maximizando coincidencias
    _, cols = linear_sum_assignment(-match_cost)
    mapeo = dict(zip(cols, range(k)))
    return np.array([mapeo[l] for l in labels_objetivo])
```

### Interpretación
| ARI | Significado |
|---|---|
| > 0.95 | Muy estable — cluster confiable |
| 0.70 - 0.95 | Moderadamente estable |
| < 0.70 | Inestable — revisar K o features |

## 2. Estabilidad Random Forest (importancia de variables)

Mide qué tan confiables son los rankings de importancia.

```python
N_SEEDS_RF = 50
importancias = []

for i in range(N_SEEDS_RF):
    rf = RandomForestRegressor(n_estimators=200, random_state=i, max_depth=5)
    rf.fit(X_rf, y_rf)
    importancias.append(rf.feature_importances_)

importancias = np.array(importancias)

for j, feat in enumerate(FEATURES_RF):
    media = importancias[:, j].mean()
    std = importancias[:, j].std()
    cv = std / media  # Coeficiente de variación
    print(f"{feat:<35} {media:.4f} ± {std:.4f}  (CV={cv:.2f})")
```

CV bajo (< 0.10) = variable confiable. CV alto (> 0.20) = interpretar
con cautela.

## 3. Sensibilidad DBSCAN (parámetros eps y min_samples)

DBSCAN es muy sensible a eps. Una exploración sistemática es obligatoria.

```python
eps_range = np.arange(0.5, 4.0, 0.25)
min_samples_range = [2, 3, 4, 5]

for ms in min_samples_range:
    n_outliers, n_clusters = [], []
    for eps in eps_range:
        db = DBSCAN(eps=eps, min_samples=ms)
        labels = db.fit_predict(X_scaled)
        n_outliers.append((labels == -1).sum())
        n_clust = len(set(labels)) - (1 if -1 in labels else 0)
        n_clusters.append(n_clust)
    # Graficar ambas curvas
```

Buscar una **zona de meseta** donde n_outliers y n_clusters se
estabilicen. Si no hay meseta, DBSCAN no es el algoritmo adecuado.

## 4. Bootstrap co-clustering (estabilidad de asignaciones)

Remuestrea con reemplazo y mide qué tan seguido dos observaciones
caen juntas en el mismo cluster.

```python
from sklearn.utils import resample

N_BOOTSTRAP = 100
n_muestras = len(df_original)
co_ocurrencia = np.zeros((n_muestras, n_muestras))
n_veces_juntos = np.zeros((n_muestras, n_muestras))

for i in range(N_BOOTSTRAP):
    idx = np.array(resample(range(n_muestras), random_state=i,
                            n_samples=n_muestras))
    X_boot = X_original[idx]
    km = KMeans(n_clusters=K_FINAL, random_state=i, n_init=20)
    labels_boot = km.fit_predict(X_boot)

    for a in range(n_muestras):
        for b in range(a + 1, n_muestras):
            pos_a = np.flatnonzero(idx == a)
            pos_b = np.flatnonzero(idx == b)
            if len(pos_a) > 0 and len(pos_b) > 0:
                n_veces_juntos[a, b] += 1
                if labels_boot[pos_a[0]] == labels_boot[pos_b[0]]:
                    co_ocurrencia[a, b] += 1

prob = co_ocurrencia / n_veces_juntos  # matriz de probabilidad
```

Interpretación: dos observaciones con prob > 80% son robustas. Entre
40-60% hay ambigüedad.

## 5. Ablación de features (impacto en clustering)

Elimina una feature a la vez y mide cómo cambia la calidad del cluster.

```python
FEATURES_MODELO = ['feat1', 'feat2', ...]
sil_base = silhouette_score(X_scaled, labels_base)

for i, feat in enumerate(FEATURES_MODELO):
    features_abl = [f for j, f in enumerate(FEATURES_MODELO) if j != i]
    X_abl = StandardScaler().fit_transform(df[features_abl].values)
    km = KMeans(n_clusters=K_FINAL, random_state=42, n_init=30)
    labels = km.fit_predict(X_abl)
    sil = silhouette_score(X_abl, labels)
    ari = adjusted_rand_score(labels_base, labels)
    print(f"Excluir {feat:<30}: Silhouette={sil:.4f} ({'▼' if sil<sil_base else '▲'}) ARI={ari:.4f}")
```

La feature más crítica = la que más reduce silhouette al eliminarla.

## Cuándo aplicar cada técnica

| Técnica | Cuándo usarla | Costo computacional |
|---|---|---|
| Seed stability | Siempre en K-Means | Bajo (100 seeds) |
| RF importance stability | Siempre en RF | Bajo (50 seeds) |
| DBSCAN parameter sweep | Siempre en DBSCAN | Muy bajo |
| Bootstrap co-clustering | Cuando n < 100 | Medio (100 iter x n²) |
| Feature ablation | Para seleccionar features | Bajo (1 iter por feature) |
