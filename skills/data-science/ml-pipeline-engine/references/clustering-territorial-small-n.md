# Clustering Territorial con Small-n (n=24 departamentos)

## Cuándo usar este patrón

- Tienes datos a nivel de departamentos/regiones peruanos (n≈24)
- 10-15 variables que mezclan indicadores financieros, demográficos, sociales
- Necesitas segmentar territorios para expansión de servicios financieros
- El objetivo es clustering no supervisado (K-Means) con reporte interpretable

## Problema típico: sesgo de tamaño

En datos territoriales, las variables absolutas (población, PBI, número de
cajas, denuncias, líneas móviles, conexiones de internet, efectivos PNP)
están dominadas por el tamaño del departamento. **Lima/Callao concentra
10× la población del siguiente departamento** — esto crea correlaciones
espurias entre variables que simplemente miden "qué tan grande es el
departamento".

**Verificación:** calcular la matriz de correlación. Si >50% de los pares
tienen |r| > 0.9, el sesgo de tamaño está presente. En el dataset de
24 departamentos peruanos con 13 variables, **44 de 78 pares (56%)
tenían correlación > 0.9** antes de transformar.

## Pipeline comprobado

### Fase 1: Feature Engineering (per cápita + estructura)

Transformar variables absolutas a indicadores relativos:

| Variable absoluta | Indicador derivado | Fórmula | Unidad |
|---|---|---|---|
| Num_Cajas | Cajas_x_100k_adultos | =Num_Cajas / Pob18_70 × 100,000 | Cajas / 100k adultos |
| Depositos_Cajas_PEN_MM | Depositos_x_adulto | =Depositos × 1e6 / Pob18_70 | S/. / adulto |
| NroLineasTelefoniaMovil | Lineas_x_hab | =Lineas / PobTotal | Líneas / hab |
| Conexión_Internet_Fijo | Internet_x_100k_hab | =Internet / PobTotal × 100,000 | Conex. / 100k hab |
| Denuncias_2024 | Denuncias_x_100k_hab | =Denuncias / PobTotal × 100,000 | Denunc. / 100k hab |
| Num_PNP_2026 | PNP_x_100k_hab | =PNP / PobTotal × 100,000 | Efect. / 100k hab |
| PBI_miles_PEN | PBI_pc | =PBI / PobTotal | Miles S/. / hab |
| Poblacion_18_70, PobTotal | Prop_Adultos | =Pob18_70 / PobTotal | Proporción (0-1) |
| PEA_ocupada, PEA_no_ocupada | Ratio_PEA_Ocupada | =PEA_oc / (PEA_oc + PEA_no_oc) | Proporción (0-1) |
| Ingreso_Prom_PEN_2024 | (sin transformar) | — | S/. / mes |
| NBI_%_2024 | (sin transformar) | — | % |

**Resultado:** 11 indicadores transformados que capturan intensidad,
no tamaño. Normalizar con StandardScaler.

### Fase 2: Determinación de K (Elbow + 3 métricas)

Evaluar K=2..8 con 4 métricas:

| Métrica | Criterio | Confiable en n<30 |
|---------|----------|------------------|
| Silhouette Score | Mayor = mejor | ✅ Sí |
| Davies-Bouldin Index | Menor = mejor | ⚠️ Parcial |
| Calinski-Harabasz | Mayor = mejor | ⚠️ Parcial |
| Inertia (Elbow) | Punto de inflexión | ⚠️ Subjetivo |

Para n=24, **Silhouette es la más confiable**. Si dos valores de K
tienen Silhouette casi iguales (diferencia < 0.01), reportar ambas como
alternativas. Ejemplo real: K=2 (S=0.3369) y K=3 (S=0.3349) — diferencia
de 0.002, prácticamente empatadas.

### Fase 3: Análisis de estabilidad (100 seeds)

**Obligatorio para n<30.** K-Means con distintas inicializaciones puede
producir particiones diferentes.

```python
import numpy as np
from sklearn.cluster import KMeans

n_runs = 100
n = len(dept_names)
co_occurrence = np.zeros((n, n))

for seed in range(n_runs):
    km = KMeans(n_clusters=best_k, random_state=seed, n_init=1, max_iter=500)
    labels = km.fit_predict(X_scaled)
    for i in range(n):
        for j in range(i+1, n):
            if labels[i] == labels[j]:
                co_occurrence[i, j] += 1

co_pct = co_occurrence / n_runs * 100

# Clasificar pares
stable = sum(1 for i in range(n) for j in range(i+1, n)
             if co_pct[i, j] >= 90 or co_pct[i, j] <= 10)
total = n * (n-1) // 2
print(f"Pares estables: {stable}/{total} ({stable/total*100:.1f}%)")

# Pares inestables (zona de ambigüedad)
unstable_pairs = []
for i in range(n):
    for j in range(i+1, n):
        if 10 < co_pct[i, j] < 90:
            unstable_pairs.append((dept_names[i], dept_names[j], co_pct[i, j]))
```

**Interpretación:**
- >80% estables → partición robusta
- 50-80% estables → moderadamente estable, reportar con cautela
- <50% estables → revisar K o feature engineering

### Fase 4: Perfiles de cluster con z-scores

Después de obtener los clusters, interpretar usando desviación respecto
a la media global (z-score simplificado):

```python
for c in range(n_clusters):
    mask = labels == c
    subset = df_features.iloc[mask]
    print(f"Cluster {c} ({mask.sum()} deptos):")
    for var in model_vars:
        mean_val = subset[var].mean()
        global_mean = df_features[var].mean()
        global_std = df_features[var].std()
        z = (mean_val - global_mean) / global_std if global_std > 0 else 0
        arrow = "↑↑" if z > 1 else "↑" if z > 0.3 else "→" if z > -0.3 else "↓" if z > -1 else "↓↓"
        print(f"  {var:30s}: {mean_val:.4f} (z={z:+.2f}) {arrow}")
```

### Fase 5: PCA para visualización

```python
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
print(f"Varianza explicada: PC1={pca.explained_variance_ratio_[0]:.1%}, "
      f"PC2={pca.explained_variance_ratio_[1]:.1%}, "
      f"Total={pca.explained_variance_ratio_.sum():.1%}")

# Cargas (loadings) para interpretar componentes
loadings = pca.components_
for i, v in enumerate(model_vars):
    print(f"{v:30s} PC1={loadings[0,i]:+.4f} PC2={loadings[1,i]:+.4f}")
```

### Fase 6: Reporte con diccionario + analogías + auto-auditoría

Estructura del reporte:

1. **Resumen ejecutivo** — tabla con K óptimo, silhouette, estabilidad, varianza PCA
2. **Diccionario de datos** — tabla con variable, descripción, unidad, fuente, año
   - Separar variables originales de derivadas
   - Incluir fórmula de cada derivada
3. **EDA** — resumen descriptivo + matriz de correlación + hallazgos clave
4. **Feature engineering** — qué transformaciones y por qué
5. **Determinación de K** — tabla comparativa K=2..8 con 4 métricas
6. **Asignación de clusters** — lista de departamentos por cluster
7. **Perfiles de cluster** — centroides con z-scores y flechas (↑↓)
8. **Estabilidad** — co-occurrence matrix, pares estables/inestables
9. **Alternativas** — K=2 vs K=3, cuándo elegir cada una
10. **Analogías** — ejemplos cotidianos para cada concepto técnico
11. **Limitaciones** — n pequeño, estabilidad limitada, heterogeneidad interna
12. **Auto-auditoría** — errores detectados y corregidos durante el análisis

## Resultados conocidos (dataset peruano, 24 deptos, 13 vars)

| K | Silhouette | Pares estables | Cluster 0 | Cluster 1 | Cluster 2 |
|---|---|---|---|---|---|
| 2 | 0.337 | 59% | 16 "Interior" | 8 "Desarrollados" | — |
| 3 | 0.335 | 56% | 16 "Interior" | 3 "Frontera" | 5 "Alto desarrollo" |
| 4 | 0.329 | 48% | 16 "Interior" | — | Lima como singleton |

**Cluster 0** ("Interior con potencial"): Amazonas, Ancash, Apurimac,
Ayacucho, Cajamarca, Cusco, Huancavelica, Huanuco, Junin, La Libertad,
Loreto, Pasco, Piura, Puno, San Martin, Ucayali.

**Cluster 1** (K=2, "Ejes desarrollados"): Arequipa, Ica, Lambayeque,
Lima/Callao, Madre de Dios, Moquegua, Tacna, Tumbes.

## Sesgos a mitigar

1. **Efecto Lima**: Incluso después de transformación per cápita, Lima
   sigue siendo outlier (10× población). Monitorear su influencia en PCA.
2. **NBI como variable independiente**: Es la única variable con r<0.20
   contra las demás — captura una dimensión única de vulnerabilidad.
   No eliminarla aunque parezca "incorrelacionada".
3. **Heterogeneidad interna**: Departamentos como Cusco mezclan turismo
   de lujo con pobreza rural extrema. El clustering departamental es
   una agregación — no refleja la diversidad interna.
