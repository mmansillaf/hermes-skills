---
name: method-selector
description: "Guia de decision para elegir entre aritmetica comun, estadistica clasica y Machine Learning segun el tipo de problema, cantidad de datos, objetivo del analisis y contexto del proyecto."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [methodology, decision-guide, statistics, ml, arithmetic, small-n]
    category: data-science
---

# Method Selector — ¿Cuándo usar Aritmética, Estadística o ML?

Guía de decisión para elegir el método correcto según el tipo de problema, cantidad de datos, objetivo y restricciones del contexto peruano (datos departamentales n=25, distritales n=1,874).

## Árbol de decisión rápido

```
¿Tienes datos?
├── NO → Búsqueda bibliográfica, marco teórico, fuentes secundarias
│
└── SÍ → ¿Cuántas observaciones?
    │
    ├── n < 10 → Solo ARITMÉTICA (promedios, sumas, tasas)
    │   Ej: 3 años de PBI, 5 distritos piloto
    │
    ├── 10 ≤ n < 100 → ESTADÍSTICA CLÁSICA + ML restringido
    │   Ej: 25 departamentos, 50 provincias
    │   Métodos: LOOCV, Ridge, Spearman, Bootstrap
    │   NO: deep learning, K-Fold estándar, redes neuronales
    │
    ├── 100 ≤ n < 1,000 → ESTADÍSTICA + ML intermedio
    │   Ej: 200 distritos, 500 agencias
    │   Métodos: XGBoost, RF, K-Fold, SHAP, Block CV
    │
    └── n ≥ 1,000 → ML completo + validación estándar
        Ej: 1,874 distritos, datos a nivel manzana
        Métodos: XGBoost, LightGBM, Deep Learning, CV estándar
```

## Matriz de decisión por objetivo

### Objetivo: Describir (¿qué pasó?)

| Situación | Método | Herramienta |
|---|---|---|
| Resumir datos | Aritmética | Media, mediana, suma, tasa, proporcion |
| Comparar 2 grupos | Estadística | t-test, Mann-Whitney, Levene |
| Comparar 3+ grupos | Estadística | ANOVA, Kruskal-Wallis |
| Distribucion de datos | Estadística | Shapiro-Wilk, asimetria, curtosis |
| Cambio temporal simple | Aritmética | Variacion %, diferencia absoluta |
| Ranking simple | Aritmética | Ordenamiento, percentiles |

### Objetivo: Relacionar (¿qué se asocia con qué?)

| Situación | n < 30 | n 30-100 | n > 100 |
|---|---|---|---|
| 2 variables continuas | Spearman rank | Pearson/Spearman | Pearson + scatter |
| 1 continua + 1 categorica | U-Mann-Whitney | ANOVA/t-test | ANOVA + post-hoc |
| Muchas variables vs 1 target | Ridge (LOOCV) | RF + LOOCV | XGBoost + SHAP |
| Relacion espacial | Moran's I (n>20) | Moran's I + LISA | Moran's I + LISA |

### Objetivo: Predecir (¿qué pasará?)

| Situación | n < 30 | n 30-100 | n > 100 |
|---|---|---|---|
| Serie temporal simple | Tendencia lineal | Ridge + tendencia | ARIMA, Prophet |
| Clasificación binaria | NO RECOMENDADO | Ridge logístico + LOOCV | XGBoost + CV |
| Regresión numérica | NO RECOMENDADO | Ridge/ElasticNet + Bootstrap | RF, XGBoost, LightGBM |
| Cluster geográfico | K-Means (k<3) | K-Means + silhouette | DBSCAN, HDBSCAN |

### Objetivo: Prevenir sesgos algorítmicos (¿esto es un WMD?)

**Basado en Cathy O'Neil (2016) — Weapons of Math Destruction**

Antes de desplegar cualquier modelo, verificar estos 3 criterios:

| Criterio WMD | Pregunta de control | Riesgo si no se verifica |
|---|---|---|
| **Opacidad** | ¿El modelo es explicable? ¿SHAP, coeficientes, o caja negra? | El afectado no puede apelar ni entender la decisión |
| **Escala** | ¿El modelo afecta a muchas personas/territorios? | Un error se replica masivamente |
| **Daño** | ¿El modelo excluye sistemáticamente a vulnerables? | Desigualdad auto-reforzante (feedback loop) |

**Pruebas estadísticas mínimas para detectar sesgo:**

| Prueba | Qué mide | Cómo se hace | Umbral de alerta |
|--------|----------|-------------|------------------|
| **Proxy test** | Si variables predictoras son proxies de características protegidas | Correlación de Pearson entre cada variable y ruralidad/género/etc. | r > 0.5 = proxy potencial |
| **Equidad geográfica** | Si el modelo favorece sistemáticamente regiones | IVCD medio por cluster. Prueba t entre cluster favorecido vs perjudicado | p < 0.05 = sesgo significativo |
| **Error desigual** | Si el modelo se equivoca más en ciertos grupos | Error absoluto medio separado por grupo | Error_grupo > 3x Error_referencia |
| **Feedback loop** | Si el modelo replica desigualdades históricas | Simular N periodos: P(acceso_t) vs P(acceso_t-1) | Cambio < 5% en 5 periodos = estancamiento |

**Referencia:** Banka & Zafar (2023) JFE — Algorithmic Redlining in Banking. Chen & Qin (2023) MS — Geographic Bias. Krause & Ruesga (2020) FAccT — Fairness in Financial Inclusion.

### Objetivo: Explicar con causalidad (¿por qué pasó?)

| Método | Cuando usarlo |
|---|---|
| Correlación | Nunca para causalidad. Solo exploración |
| Regresión con controles | n > 20 por variable independiente |
| Double ML | n > 100 con datos panel (3+ periodos) |
| Diff-in-Diff | n > 50 con grupo control |
| Experimento (A/B) | Siempre que sea posible (gold standard) |

### Objetivo: Construir índice compuesto

| n de indicadores | Método de pesos | Validación |
|---|---|---|
| 3-5 | Iguales o juicio experto | Analisis de sensibilidad |
| 5-10 | TOPSIS, Entropia, AHP | Cronbach alpha, KMO |
| 10+ | PCA, Factor Analysis | Bartlett, KMO, varianza explicada |

## Reglas de oro para el contexto peruano

#### Dimensión territorial peruana (n=25 departamentos, n=1,874 distritos)

### n=25 departamentos (small-n)
- ✅ **SIEMPRE COMPARAR Ridge vs XGBoost con LOOCV** — NO pre-seleccionar. Simulación con n=25 muestra que XGBoost puede superar a Ridge cuando hay interacciones no lineales (100% de victoria en datos con interacciones).
- ✅ **LOOCV** (Leave-One-Out) como validación default
- ✅ **Bootstrap** para intervalos de confianza
- ✅ **Ridge/ElasticNet** para regresión (regularización)
- ✅ **Comparar Ridge vs XGBoost** — no pre-seleccionar. Simulación con n=25 muestra que XGBoost puede superar a Ridge cuando hay interacciones no lineales.
- ✅ **XGBoost con n_estimators ≤ 50, max_depth ≤ 3** para evitar sobreajuste
- ✅ **Spearman** para correlaciones (no paramétrico)
- ✅ **Shapiro-Wilk** para normalidad (potente en n pequeño)
- ❌ K-Fold con k<25 (folds pequeños, alta varianza)
- ❌ Deep learning (necesita >1,000 muestras)
- ❌ Random Forest con n_estimators > 100 (sobreajuste)

### n=1,874 distritos
- ✅ **Block CV** para validación geoespacial
- ✅ **XGBoost/LightGBM** mejor rendimiento
- ✅ **SHAP** para interpretabilidad
- ✅ **Moran's I** para dependencia espacial
- ✅ **Spatial Lag/Error** si hay autocorrelación residual
- ❌ Regresión OLS con 1,874 variables dummy (Lima vs resto)
- ❌ Ignorar autocorrelación espacial (Ley de Tobler)

## Ejemplos de aplicación

### Ejemplo 1: "¿Qué departamento creció más?"
-> Aritmética pura. Variación %: (PBI_2024/PBI_2007 - 1) * 100.
NO necesita estadística ni ML.

### Ejemplo 2: "¿El PBI base determina el crecimiento futuro?"
-> Estadística. Correlacion de Spearman entre PBI_2007 y crecimiento.
Con n=24 departamentos y distribucion no normal, Spearman > Pearson.

### Ejemplo 3: "Proyectar PBI 2025-2026 por departamento"
-> ML restringido. Ridge regression con LOOCV para 18 periodos.
Deep learning seria overkill y sobreajuste.

### Ejemplo 4: "Predecir que distritos seran viables para agencia CMAC"
-> ML completo. XGBoost + Block CV + SHAP.
n=1,874 distritos, 50+ variables, validacion geoespacial obligatoria.

### Ejemplo 5: "Construir un Indice de Desarrollo Financiero"
-> Indice compuesto. TOPSIS + pesos por entropia + Cronbach alpha.
Combina estadistica (validacion) con MCDA (indexacion).

### Ejemplo 6: "¿Abrir una agencia genera desarrollo economico?"
-> Causalidad. Double ML o Diff-in-Diff con datos panel.
Correlacion simple no responde esta pregunta.

## Checklist de elección de método

Antes de elegir, responde:

1. ¿Cuántas observaciones tengo? (n = __)
   - n < 10 → SOLO ARITMÉTICA
   - n 10-100 → Estadística clásica
   - n > 100 → ML viable

2. ¿Mi objetivo es describir, predecir o explicar causalmente?
   - Describir → Aritmética o Estadística
   - Predecir → ML
   - Causal → Experimentos, Double ML, Diff-in-Diff

3. ¿Tengo datos espaciales (lat/lon)?
   - SÍ → La validación debe ser geoespacial (Block CV, Moran's I)
   - NO → Validación estándar

4. ¿Necesito interpretabilidad?
   - SÍ (regulatorio SBS, tesis) → SHAP, LIME, coeficientes
   - NO (solo precision) → Black box (XGBoost, LightGBM)

5. ¿Es para un paper/tesis o para producción?
   - Paper → Estadística clásica (p-valores, intervalos) + SHAP
   - Producción → ML (precision, F1-score) + monitoreo

6. ¿Mi audiencia entiende ML?
   - SÍ → Usar ML con interpretabilidad
   - NO → Estadística clásica (regresión, correlación)

7. **¿Podría mi modelo ser un WMD (Weapon of Math Destruction)?** (NUEVO)
   - ¿El modelo es opaco? → Añadir SHAP o coeficientes interpretables
   - ¿El modelo opera a escala masiva? → Añadir revisión humana
   - ¿El modelo daña a vulnerables? → Añadir restricciones de equidad
   - ¿Hay variables proxy? (correlacionan r>0.5 con característica protegida) → Remover o combinar
   - ¿El error del modelo es mayor para ciertos grupos? → Estratificar, recalibrar
   - Si respondiste SÍ a cualquier pregunta de esta sección, el modelo requiere mitigación antes de desplegarse.

## Pitfalls frecuentes

1. **Usar ML cuando n < 30**: Cualquier modelo con >5 features sobreajusta.
   Solución: Ridge regression o estadística descriptiva.
2. **Usar Pearson cuando los datos no son normales**: Pearson asume normalidad
   bivariada. Con outliers, Spearman da mejores resultados.
3. **K-Fold en datos espaciales**: Fuga de información entre folds vecinos.
   Solución: Spatial Block CV.
4. **Confundir correlación con causalidad**: El ML predice bien pero no explica
   por qué. Double ML o experimentos para causalidad.
5. **Sobreinterpretar p-valores con n pequeño**: Con n=25, un p=0.06 puede ser
   relevante aunque no sea "significativo" al 5%. Reportar tamaño del efecto.
6. **Data leakage temporal**: Mezclar datos de 2007-2024 sin separar train/test
   por año. Usar ventanas temporales.
7. **Normalizar sin verificar distribución**: Para datos log-normales (como PBI),
   aplicar log() antes de estandarizar.

## Reglas de oro adicionales (absorbido de statistics-vs-ml-decision)

1. **n=24 departamentos → siempre LOOCV.** K-Fold con k<24 tiene demasiada varianza. Nunca separar train/test fijo — pierdes 1/3 de tus datos.
2. **n=24 → máximo 3-4 variables en el modelo.** Regla n/5 = 4.8 ≈ 4 features. Con más, sobreajuste garantizado.
3. **Datos departamentales → siempre verificar autocorrelación espacial (Moran's I).** Los departamentos vecinos tienden a comportarse similar (Ley de Tobler).
4. **PBI no es normal → mediana en vez de media, Spearman en vez de Pearson.** Como mostró el test de normalidad (Shapiro-Wilk p=0.04).
5. **XGBoost con n=24 → R² negativo en LOOCV es normal.** Esperado. Con 23 datos de train, el modelo no generaliza. Usar Ridge o regresión lineal simple en su lugar.
6. **Índices compuestos (TOPSIS) → validar con KMO.** Si KMO < 0.5, las variables no comparten suficiente varianza para combinarse en un índice.
7. **Proyecciones a futuro → no más de 3 años con n=18 (2007-2024).** El error de proyección crece cuadráticamente.
8. **Si el R² de regresión lineal es < 0.70 → hay quiebre estructural (ej: COVID, minería).** Revisar gráficamente, no confiar en la proyección.
9. **Outliers (z > 2.5) → investigar antes de eliminar.** Apurímac (+296%) es real (minería Las Bambas). Pasco (-4%) también es real (crisis minera). Eliminarlos sesgaría el análisis.
10. **El mejor modelo es el más simple que funciona.** Para PBI departamental, regresión lineal por depto (R² medio >0.85) supera a XGBoost LOOCV (R² = -0.33).

### Tabla rápida según n (granularidad fina)

| n | Recomendado | No recomendado | Ejemplo Perú |
|---|---|---|---|
| 5-25 | Regresión lineal, Ridge, LOOCV, Bootstrap, Shapiro-Wilk | XGBoost, RF, Deep Learning, K-Fold | 24 departamentos |
| 25-50 | Ridge/Lasso, árbol pequeño, stepwise | Ensemble grande, redes | Provincias de un depto |
| 50-200 | RF, XGBoost básico, K-Fold(5) | Deep Learning, AutoML | Distritos de una provincia |
| 200-1,000 | XGBoost, RF, SHAP, K-Fold(10) | Redes profundas (>3 capas) | Muestra de ENAHO |
| 1,000+ | Cualquier método | Ninguno (depende del problema) | Censos INEI |

## Referencias

- Burnham & Anderson (2002): Model Selection and Multimodel Inference
- Hastie, Tibshirani & Friedman (2009): Elements of Statistical Learning
- Meyer et al. (2019): "Spatial cross-validation" (Ecological Informatics)
- Ley de Tobler: "Everything is related to everything else, but near things
  are more related than distant things"
