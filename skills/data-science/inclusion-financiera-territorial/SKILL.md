---
name: inclusion-financiera-territorial
description: "Marco metodologico completo para analisis de inclusion financiera territorial con ML, SAE e IPF. Enfoque en CMAC peruanas y distritos fuera de Lima. Incluye simulaciones, prevencion de sesgos (WMD) y validacion internacional."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [financial-inclusion, cmac, peru, sae, ipf, ml, spatial, bias]
    category: data-science
---

# Inclusión Financiera Territorial — Marco Metodológico

## ¿Qué resuelve?

Proporciona un pipeline completo y validado para determinar qué distritos fuera de Lima tienen potencial para inclusión financiera que genere desarrollo económico, usando CMAC (Cajas Municipales de Ahorro y Crédito) como caso de estudio.

## Advertencia metodológica crítica

Las simulaciones (100 remuestras bootstrap) muestran que **ningún método de desagregación es intrínsecamente superior**. La combinación SAE+IPF+ML mejora la precisión ~1-3% vs. métodos simples, pero esta mejora NO es siempre estadísticamente significativa. El valor real está en:
1. Intervalos de confianza (no valores puntuales)
2. Equidad geográfica (no solo replicar población)
3. Defendibilidad académica (metodología publicable)
4. Simulación de escenarios (qué-pasaría-si)

## Pipeline metodológico

### Fase -1: Backtest departamental (OBLIGATORIO)

Antes de cualquier desagregación, validar con datos reales a nivel departamental.

```python
# Datos: Base de datos 1 (nivel departamento).xlsx (25 deptos, 16 variables)
# Target: Num_CMAC por departamento
# Features: Poblacion_18_70, %PobrezaTotal, NroLineasTelefoniaMovil, etc.

from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_score
from xgboost import XGBRegressor, XGBClassifier

# Comparar Ridge vs XGBoost con LOOCV
# Si Ridge R2 > 0.3: modelo lineal es suficiente
# Si XGBoost gana por >10%: hay no-linealidades reales
# Si ambos R2 < 0.3: repensar features o el problema
```

### Fase 0: IPF para desagregación distrital

**Analogía:** "Repartir la torta considerando peso, edad y metabolismo de cada persona, no solo el peso."

```python
def desagregar_ipf(total_depto, depto_idx, variables_dict, n_iter=8):
    """
    IPF con múltiples constraints.
    variables_dict: {'nombre': array_distrital}
    Constraints tipicos: poblacion, PBI_pc, inverso_pobreza
    """
    est = np.ones(len(depto_idx))
    for d in range(num_deptos):
        mask = depto_idx == d
        idx = np.where(mask)[0]
        n = len(idx)
        if n == 0 or total_depto[d] == 0:
            est[idx] = 0
            continue
        w = np.ones(n)
        for _ in range(n_iter):
            for nombre, arr in variables_dict.items():
                vals = arr[idx]
                if nombre == 'inversa_pobreza':
                    vals = np.clip(1 - vals, 0.01, 1.0)
                suma = (w * vals).sum()
                if suma > 0:
                    w = w * total_depto[d] * vals / suma
        est[idx] = w
    return np.nan_to_num(est, nan=0.0)
```

### Fase 1: SAE Fay-Herriot con bootstrap

**Analogía:** "Cuando dos médicos dan diagnósticos diferentes, el especialista confía más en el que tiene más experiencia en ese tipo de caso."

```python
def sae_fay_herriot(est_directa, depto_idx, features, num_deptos, n_bootstrap=1000):
    """
    SAE con bootstrap para intervalos de confianza.
    est_directa: estimacion IPF
    features: covariables a nivel distrital
    """
    from sklearn.linear_model import Ridge
    
    # Promedios departamentales
    feat_depto = np.zeros((num_deptos, features.shape[1]))
    theta_dir = np.zeros(num_deptos)
    for d in range(num_deptos):
        mask = depto_idx == d
        if mask.sum() > 0:
            feat_depto[d] = features[mask].mean(axis=0)
            theta_dir[d] = est_directa[mask].mean()
    
    # Regresion
    ridge = Ridge(alpha=1.0).fit(feat_depto, theta_dir)
    theta_reg = ridge.predict(feat_depto)
    
    # sigma2_v
    resid = theta_dir - theta_reg
    sig2_v = max(0.01, np.var(resid) - np.var(theta_dir)*0.05)
    
    # NOTA: CV de sigma2_v con n=25 es ~47%. Usar bootstrap.
    # NO confiar en formula asintotica del MSE.
    
    # Predictor Fay-Herriot
    est_sae = np.zeros(len(depto_idx))
    for d in range(num_deptos):
        mask = depto_idx == d
        n = mask.sum()
        if n == 0: continue
        frac = np.clip(est_directa[mask], 0.01, None)
        frac = frac / frac.sum()
        sig2_e = np.var(frac) / n if n > 1 else 0.5
        gamma = sig2_v / (sig2_v + sig2_e)
        theta_fh = gamma * theta_dir[d] + (1 - gamma) * theta_reg[d]
        est_sae[mask] = frac * max(0, theta_fh * n)
    
    return np.nan_to_num(est_sae, nan=0.0)
```

### Fase 2: Bootstrap anidado (SAE + ML)

Validación realista que propaga el error de SAE al ML:

```python
def bootstrap_anidado(X, y, depto_idx, n_boot=100):
    """
    Loop externo: bootstrap de departamentos
    Loop interno: LOOCV para calibrar modelo
    Reportar: AUC medio + IC 95%
    """
    aucs_base, aucs_sae = [], []
    for b in range(n_boot):
        boot_d = np.random.choice(num_deptos, num_deptos, replace=True)
        train = np.zeros(len(y), dtype=bool)
        for d in boot_d: train |= (depto_idx == d)
        test = ~train
        if test.sum() < 10 or y[test].sum() < 2: continue
        
        # Re-estimar SAE en bootstrap
        # ... (codigo SAE aqui)
        
        # Entrenar y evaluar
        m1 = LogisticRegression().fit(X[train], y[train])
        auc_base.append(roc_auc_score(y[test], m1.predict_proba(X[test])[:,1]))
        
        X_sae = np.column_stack([X[train], sae_boot[train]])
        m2 = LogisticRegression().fit(X_sae, y[train])
        auc_sae.append(roc_auc_score(y[test], m2.predict_proba(X_sae)[:,1]))
    
    return auc_base, auc_sae
```

### Fase 3: Ranking con intervalos

```python
# Ranking final: ordenar por mediana del IVCD bootstrap
# Clasificar:
#   IVCD_2.5% > 0.40 → GO (seguro)
#   IVCD_97.5% < 0.20 → NO-GO (seguro)
#   Otros → ZONA DE DECISIÓN (análisis adicional)
```

## IVCD: Índice de Viabilidad Comercial y Desarrollo

```
IVCD(i) = w1 * f_rent(i) + w2 * g_imp(i) - w3 * h_risk(i)

Donde:
  f_rent = 0.25*Pob_norm + 0.20*PBI_pc_norm + 0.20*MYPE_norm + 0.15*Vol_com_norm + 0.10*Edu_norm + 0.10*Internet_norm
  g_imp  = 0.30*(1-Pobreza_norm) + 0.25*IDH_norm + 0.25*MYPE_norm + 0.20*Acceso_vial_norm
  h_risk = 0.35*Informalidad_norm + 0.25*(1-Densidad_CMAC_norm) + 0.20*Dist_capital_norm + 0.20*(1-Cobertura_4G_norm)

  w1 = 0.31 (rentabilidad)
  w2 = 0.16 (impacto desarrollo)  ← MÍNIMO 0.25 si hay riesgo de sesgo geográfico
  w3 = 0.53 (riesgo)
```

## Prevención de sesgos (WMD)

Basado en Cathy O'Neil (2016): "Armas de destrucción matemática"

### 3 criterios WMD a evitar

| Criterio | Qué significa | Cómo evitarlo |
|----------|--------------|---------------|
| Opacidad | Caja negra: el afectado no sabe cómo se decide | Publicar fórmula IVCD + SHAP + coeficientes |
| Escala | Impacto masivo: afecta a miles | Cada recomendación NO es decisión automática |
| Daño | Perjuicio real a vulnerables | g_imp con peso mínimo 0.25 + revisión humana |

### Sesgos documentados

| Sesgo | Evidencia | Mitigación |
|-------|-----------|------------|
| Redlining geográfico | Banka & Zafar (2023) | Cuota mínima por cluster |
| Proxy discriminatorio | Krause & Ruesga (2020) | Informalidad NO usada sola |
| Feedback loop | O'Neil (2016) | Re-evaluar excluidos cada 2 años |
| Sesgo urbano | Chen & Qin (2023) | Estratificar 50% urbano / 50% rural |

### Reglas de oro

1. **Human-in-the-loop**: Cada NO-GO requiere revisión manual
2. **Transparencia total**: Todas las fórmulas y pesos son públicos
3. **Validación externa**: Backtest con datos históricos obligatorio
4. **Equidad geográfica**: Cada cluster debe tener al menos 1 recomendado en top 20

## Validación internacional

| Método | País que lo usa | Referencia |
|--------|----------------|------------|
| SAE para inclusión financiera | India | Srivastava & Kumar (2025) |
| ML para sucursales (AutoML) | Turquía (Ziraat Bank) | Met et al. (2023) IEEE Access |
| GIS+ML selección ubicaciones | Pakistán | Ashraf et al. (2025) |
| Branch Licensing Policy | Pakistán | SBP Annual Reports 2021-2025 |
| Corresponsales bancarios | Brasil (Caixa Aqui) | 400,000+ puntos |

## Errores comunes y mitigaciones

| Error | Consecuencia | Corrección |
|-------|-------------|------------|
| Usar XGBoost con n=25 sin comparar con Ridge | Sobreajuste no detectado | Comparar ambos con LOOCV |
| Asumir IPF siempre superior | RMSE puede empeorar | Probar 3 métodos y seleccionar |
| No propagar error SAE al ML | IC95% subestimados | Bootstrap anidado obligatorio |
| Ignorar sesgo geográfico | WMD: excluir rurales | g_imp peso mínimo 0.25 |
| Ranking sin intervalos | Falsos positivos | Ranking bootstrap |

## Explicación detallada de los 18 algoritmos

Cuando se requiera explicar los algoritmos del pipeline, usar el formato estructurado documentado en `references/explicacion-algoritmos-formato.md`:

- Cada técnica: **razón de aplicación** + **supervisado/no/no-ML** + **fórmula clave** + **analogía concreta del dominio CMAC/Perú** + **ejemplo numérico** + **precisión documentada**
- Acompañar con diagramas Excalidraw (ver referencias externas en Papers/)
- Entregar en formato .md (tablas) + .txt (texto plano)
- Incluir auto-auditoría al final con cada afirmación verificada contra fuente documental

Los 18 algoritmos clasificados:
  - **NO-ML (6):** IPF, Proporcional Simple, IVCD, AHP, Moran's I/LISA, Huff, MCLP
  - **NO SUPERVISADO (1):** K-Means + Haversine
  - **SUPERVISADO (9):** SAE Fay-Herriot, Ridge, XGBoost, Random Forest, Double ML, Regresión Logística, CART, Boruta + SHAP post-hoc

## Scripts de referencia

Los scripts de simulación están en la carpeta Papers/ con prefijo _:
- `_simulacion_final.py` — Versión completa con analogías
- `_auditoria_critica_v2.py` — Validación de supuestos
- `_investigacion_busqueda_v3.py` — Búsqueda en APIs académicas
- `_demostracion_sesgos.py` — 4 pruebas estadísticas de sesgo (proxy, geográfico, error, feedback)

## Referencias incluidas

| Archivo | Contenido |
|---------|-----------|
| `references/demostracion-sesgos-4-pruebas.md` | Demostración matemática de 4 sesgos: variables proxy, IVCD geográfico, error desigual, feedback loop |
| `references/validacion-internacional-postpandemia.md` | Comparación 6 países: evolución sucursales vs agentes 2020-2024, metodologías documentadas |
| `references/explicacion-algoritmos-formato.md` | Formato estructurado para explicar 18 algoritmos (razón, clasificación, fórmula, analogía, ejemplo, precisión) + diagramas Excalidraw asociados en Papers/ |
| `references/censos-2025-data-source.md` | Dataset Censos 2025 INEI: 25 deptos × 12 indicadores demográficos. Ruta del Excel descargado, columnas, carga en pandas, departamentos extremos, y cruces propuestos con el pipeline IVCD. |

## Visualización y presentación de resultados

### Dashboard HTML interactivo (Plotly)

Cuando se requiera un dashboard visual tipo Power BI para presentar resultados de clustering/ML a stakeholders, usar el patrón self-contained HTML con Plotly.js (CDN):

```html
<!-- Patrón base: dark theme corporativo, Plotly vía CDN -->
<!DOCTYPE html>
<html lang="es">
<head>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  /* Tokens visuales */
  :root {
    --bg: #0d1117;
    --surface: #161b22;
    --text: #f0f6fc;
    --text2: #8b949e;
    --border: #30363d;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --cluster0: #f85149;
    --cluster1: #3fb950;
    --cluster2: #58a6ff;
  }
  body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }
  .chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
</style>
</head>
<body>
  <!-- KPIs, gráficos, mapa -->
  <script>
    // Data como array de objetos JS (embedido, no fetch)
    // Plotly.newPlot('id', traces, layout, options)
  </script>
</body>
</html>
```

**7 visualizaciones recomendadas para un dashboard de inclusión financiera (v3 — 6 variables):**

| # | Visualización | Tipo Plotly | Datos | Propósito |
|---|---|---|---|---|
| 1 | KPIs (4 tarjetas) | HTML/CSS | Resumen (n, clusters, factor #1, brecha) | Visión general inmediata |
| 2 | Ranking departamentos | Barras | Oficinas_por_100k por depto, coloreado por cluster | Jerarquía visual |
| 3 | Perfil de clusters | Radar polar | Promedio de 6 indicadores normalizados por cluster | Comparación multidimensional |
| 4 | PCA scatter | Scatter 2D | PC1 vs PC2 con etiquetas | Estructura / outliers |
| 5 | Importancia de variables | Barras horizontales | RF feature importance | Factor clave |
| 6 | Relación bivariada | Scatter + tamaño | Oficinas vs Depósitos, tamaño = ingreso | Hipótesis directa |
| 7 | Matriz de correlaciones | Heatmap | Pearson entre 6 variables | Multicolinealidad |

**Versión v4 (11 variables):** El proyecto evolucionó a `pipeline_clustering_v4.py` que usa 11 variables (incluye PBI_pc, Denuncias_x_100k_hab, PNP_x_100k_hab) con K=2. Ver skill `ml-dashboard` y su referencia `feature-engineering-per-capita-pattern.md` para el patrón de transformación absoluto → per cápita aplicado.

**Patrón de layout en Plotly (dark theme):**
```javascript
const layout = (title='') => ({
  paper_bgcolor: '#161b22',
  plot_bgcolor: '#161b22',
  font: { family: 'Inter, sans-serif', color: '#8b949e', size: 11 },
  margin: { l: 50, r: 20, t: 30, b: 50 },
  xaxis: { gridcolor: '#21262d', zerolinecolor: '#30363d', color: '#8b949e' },
  yaxis: { gridcolor: '#21262d', zerolinecolor: '#30363d', color: '#8b949e' },
});
```

### Integración con Power BI

**Opción 1 — CSV directo (2 clics):**
1. Power BI Desktop > Obtener datos > Texto/CSV
2. Seleccionar `v3_resultados_clustering.csv`
3. Marcar `Cluster` como categoría, `DPTO_KEY` como geografía
4. Crear mapa coroplético (requiere shapes del Perú descargables de INEI o Github)

**Opción 2 — Excel fuente:**
1. Power BI Desktop > Obtener datos > Excel
2. Seleccionar `Basededatos3.xlsx`
3. Aplicar clusters desde CSV como tabla de referencia (JOIN por departamento)

**Opción 3 — Script Python dentro de Power BI (avanzado):**
1. Power BI > Obtener datos > Script de Python
2. Ejecutar el pipeline `analisis_v3_basededatos3.py` directamente
3. Power BI consume los resultados como tabla

**Limitaciones de Power BI en este proyecto:**
- Power BI Desktop no tiene API CLI para generar .pbix programáticamente
- Los mapas departamentales requieren shapes externos (formato TopoJSON/Shapefile)
- Random Forest / PCA / clustering no existen como visualizaciones nativas en Power BI — se ejecutan en Python antes de importar
- Alternativa: dashboard HTML autónomo (ver arriba) se abre en cualquier navegador y no requiere licencia Power BI

### Referencia visual

Ver `references/dashboard-ejemplo.md` para el archivo dashboard HTML completo generado en sesión (8 junio 2026) con datos del proyecto V3.

## Referencias clave

1. Srivastava & Kumar (2025). Spatial heterogeneity in women's financial inclusion in India: SAE. VeriXiv.
2. Met, Erkoc & Seker (2023). AutoML for Bank Branches. IEEE Access.
3. O'Neil, C. (2016). Weapons of Math Destruction. Crown Books.
4. Banka & Zafar (2023). Algorithmic Redlining in Banking. J. Financial Economics.
5. Chen & Qin (2023). Geographic Bias in Algorithmic Decision-Making. Management Science.
6. Iwara (2024). Optimizing PoS agent banking. J. Accounting and Finance.
7. Ashraf et al. (2025). GIS and ML for Site Selection in Pakistan.
8. Huwaida & Ubaidillah (2024). saePseudo: SAE Package. CRAN.
9. Maehara et al. (2024). Predicting Financial Inclusion in Peru: ML. JRFM.
10. Izaguirre (2025). Spatial downscaling of survey data. Spatial Economic Analysis.
