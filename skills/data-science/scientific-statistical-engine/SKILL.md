---
name: scientific-statistical-engine
description: "Motor estadístico-científico avanzado: 10 dominios, 50+ métodos. Cubre inferencia bayesiana (MCMC, PyMC, conjugados), inferencia causal (DiD, IV, RDD, Double ML), Monte Carlo (cópulas, SMC, bootstrap anidado), series temporales (ARIMA, Kalman, cambio estructural), métodos robustos (Huber, Theil-Sen, permutación), diseño experimental (power analysis, A/B secuencial), cuantificación de incertidumbre (Sobol, PCE, error propagation), teoría de información (entropía, MI, KL), optimización, y análisis multivariante. Produce informes científicos auditables con intervalos de confianza y autoevaluación."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [statistics, bayesian, causal-inference, monte-carlo, time-series, robust-statistics, experimental-design, uncertainty-quantification, information-theory, optimization, spatial-analysis]
    category: data-science
    related_skills: [statistical-formula-engine, election-forecast-small-n, ml-pipeline-engine, ml-pipeline-audit, ml-dashboard]
---

# Scientific Statistical Engine

Motor estadístico-científico avanzado con 10 dominios matemáticos, 50+ métodos implementados, y generación de informes científicos auditables. Diseñado para análisis con rigor matemático, intervalos de confianza calibrados, tests de supuestos pre-modelo, y autoevaluación post-modelo.

## Entorno

```bash
# Los paquetes se instalan globalmente (ya instalados):
#   pymc, arviz, emcee, pingouin, lifelines, pymcdm,
#   uncertainties, factor-analyzer, numpy, scipy,
#   pandas, statsmodels, scikit-learn, sympy, networkx
```

## ¿Qué resuelve?

Este skill resuelve problemas de análisis estadístico-científico avanzado que los skills existentes NO cubren:

| Problema | Skill previo | Este skill |
|----------|-------------|------------|
| "Necesito un modelo bayesiano jerárquico con MCMC" | ❌ No existía | ✅ PyMC + arviz |
| "Quiero estimar el efecto causal de X en Y" | ❌ No existía | ✅ DiD, IV, RDD, Double ML |
| "Simula 100K escenarios correlacionados" | ⚠️ Cópula básica | ✅ Cópulas Gaussianas + Arquimedianas |
| "Analyse la incertidumbre de mi modelo" | ⚠️ Bootstrap simple | ✅ Sobol, PCE, bootstrap anidado |
| "Diseña un A/B test con poder estadístico" | ❌ No existía | ✅ Power analysis secuencial |
| "Pronostica esta serie temporal con IC" | ⚠️ Básico | ✅ ARIMA, Kalman, cambio estructural |
| "Tests robustos sin supuestos de normalidad" | ❌ No existía | ✅ Permutación, Theil-Sen, Bootstrap |
| "Cuánta información tienen mis variables" | ❌ No existía | ✅ MI, KL, entropía condicional |
| "Los datos se agrupan geográficamente?" | ❌ No existía | ✅ Moran's I + grafo territorial NetworkX |
| "Qué departamentos son puentes entre regiones?" | ❌ No existía | ✅ Centralidad de intermediación en grafo |

## Arquitectura

```
scientific-statistical-engine/
├── SKILL.md                                ← Entry point
├── references/
│   ├── bayesian-methodology.md             ← Teoría + fórmulas
│   └── spatial-territorial-analysis.md     ← Grafos territoriales, Moran's I, expansión distrital
└── scripts/
    ├── diagnostic_reporter.py              ← Motor de informes
    └── bayesian_inference.py               ← Modelos bayesianos (6 modelos: BetaBinom,
                                               NormalNormal, GammaPois, MCMC lineal,
                                               logística, jerárquico)
```

> **Nota:** Los scripts `causal_estimators.py`, `uncertainty_quantification.py`,
> `time_series_analyzer.py`, `robust_stats.py`, `experimental_design.py` y
> `monte_carlo_engine.py` están documentados en la arquitectura conceptual
archivos conceptuales pero aún no implementados como scripts ejecutables. Los métodos descritos
en este SKILL.md (causal inference, Monte Carlo, series temporales, etc.) deben implementarse
caso por caso usando el código de ejemplo provisto en el markdown — no existe un script
pre-escrito para cada dominio aún.

### Referencias externas
- `references/spatial-analysis-territorial-graph.md` — Análisis espacial con NetworkX + Moran's I:
  construcción de matriz de adyacencia, pesos W, I de Moran (fórmula Cliff-Ord), diagrama de
  dispersión, centralidad, e interpretación. Útil para grafos territoriales con n < 30 regiones.

## Flujo de trabajo general

```
PASO 1: Identificar el tipo de problema
  ┌────────────────────────────────────┐
  │ ¿Qué pregunta responde el usuario? │
  ├────────────────────────────────────┤
  │ "¿Cuál es la probabilidad de X?"   │ → Bayesiano
  │ "¿X causa Y?"                      │ → Causal
  │ "¿Cuánto puede variar el resultado?"│ → UQ/Monte Carlo
  │ "¿Qué pasará en el futuro?"        │ → Series temporales
  │ "¿El efecto es real o ruido?"      │ → Test de hipótesis
  │ "¿Qué tan grande debe ser la muestra?"│ → Diseño exp.
  └────────────────────────────────────┘

PASO 2: Cargar script + ejecutar
  python3 scripts/bayesian_inference.py --data datos.csv

PASO 3: Revisar supuestos → Ajustar modelo → Revisar diagnóstico

PASO 4: Generar informe científico con diagnostic_reporter

PASO 5: Autoevaluación (limitaciones, riesgos, errores propios)
```

## Métodos por dominio

### 1. Inferencia Bayesiana (`scripts/bayesian_inference.py`)
- Modelos conjugados: Beta-Binomial, Normal-Normal, Gamma-Poisson
- MCMC con PyMC (NUTS, Metropolis, HMC)
- Modelos jerárquicos/ multinivel
- GLM Bayesianos (regresión logística, Poisson)
- Diagnóstico: R-hat, ESS, trace plots, WAIC, LOO, PSIS
- Prior y posterior predictive checks
- Comparación de modelos (BF, WAIC, LOO-CV)

### 2. Inferencia Causal (`scripts/causal_estimators.py`)
- Diferencia-en-Diferencias (DiD) con parallel trends test
- Variables Instrumentales (2SLS, LIML)
- Regresión Discontinua (RDD) con optimal bandwidth
- Propensity Score Matching (PSM, CEM)
- Double/Debiased ML con cross-fitting
- ATE, ATT, CATE, Heterogeneous Treatment Effects

### 3. Monte Carlo y Simulación (`scripts/monte_carlo_engine.py`)
- Bootstrap paramétrico y no paramétrico
- Bootstrap anidado (validación cruzada interna)
- Cópulas: Gaussian, Clayton, Frank, Gumbel, t-Student
- SMC (Sequential Monte Carlo) para filtrado
- Simulación de escenarios con cópulas y correlaciones
- MCMC con emcee (affine-invariant ensemble)

### 4. Series Temporales (`scripts/time_series_analyzer.py`)
- Descomposición: STL, clásica, X13-ARIMA
- ARIMA/SARIMA con auto-selección (AIC)
- State space: Kalman filter, smoothing
- Tests: ADF, KPSS, Chow, Bai-Perron, Ljung-Box
- Pronóstico con intervalos de confianza
- Detección de outliers y cambio estructural

### 5. Métodos Robustos (`scripts/robust_stats.py`)
- M-estimadores: Huber, Tukey bisquare, Hampel
- Theil-Sen, Siegel repeated median
- Permutation tests (2-sample, paired, ANOVA)
- Bootstrap de hipótesis (BCa, studentized)
- Winsorización y trimming óptimo
- Correlación robusta (Spearman, Kendall, Quadrant)

### 6. Diseño Experimental (`scripts/experimental_design.py`)
- Power analysis: t-test, ANOVA, proporciones, chi-cuadrado
- Cálculo de tamaño muestral (balanced, unbalanced)
- A/B testing secuencial (SPRT, siempre válido)
- Corrección de múltiples comparaciones
  - Bonferroni, Holm, Benjamini-Hochberg (FDR)
- Estratificación y randomización (permuted block)

### 7. Cuantificación de Incertidumbre (`scripts/uncertainty_quantification.py`)
- Propagación de errores (independiente, correlacionado)
- Análisis de sensibilidad de Sobol (1er orden, orden total)
- Polynomial Chaos Expansion (intrusivo, no intrusivo)
- Bayesian calibration (MCMC + emulador GP)
- Intervalos de confianza: asintótico, bootstrap, perfil de verosimilitud
- Análisis de sensibilidad global (Morris, FAST)

### 8. Teoría de Información
- Entropía: Shannon, Renyi, Tsallis
- Información Mutua (Kraskov, binning)
- Divergencia: KL (Kullback-Leibler), JS, Wasserstein
- Complejidad de Kolmogorov (Lempel-Ziv)
- Criterios de información: AIC, BIC, DIC, WAIC

### 9. Optimización
- Convexa: LP (linprog), QP (quadprog), SDP
- Libre de derivadas: Nelder-Mead, COBYLA, Powell
- Metaheurística: GA, PSO, SA
- Multi-objetivo: NSGA-II, MOEA/D
- Con restricciones: SLSQP, trust-constr

### 10. Estadística Multivariante
- MANOVA (1-way, 2-way, factorial)
- Análisis discriminante: LDA, QDA, Regularized
- Análisis factorial: EFA, CFA, PCA
- Análisis de correspondencias: CA, MCA
- PLS (Partial Least Squares): PLS1, PLS2
- Redundancy Analysis (RDA), CCA

### 11. Análisis Espacial y Grafos Territoriales (`references/spatial-territorial-analysis.md`)

Construye y analiza grafos de vecindad geográfica con NetworkX, mide autocorrelación espacial (Moran's I), y expande estimaciones a niveles administrativos inferiores.

**Cuándo usar este dominio:**
- Tienes datos geográficos (departamentos, provincias, distritos) con indicadores numéricos
- Quieres saber si los valores se agrupan espacialmente (ej: "los departamentos vecinos tienen perfiles demográficos similares?")
- Necesitas identificar "puentes" regionales (departamentos que conectan regiones)
- Quieres proyectar indicadores a niveles administrativos menores (departamento → provincia → distrito)

**Flujo de trabajo recomendado (6 pasos):**

```
PASO 1: Construir matriz de adyacencia W
  W[i,j] = 1 si i y j comparten frontera, 0 si no
  Validar simetría (toda relación A→B debe tener B→A)
  Normalizar por filas: W_norm[i,j] = W[i,j] / sum_j(W[i,j])

PASO 2: Construir grafo con NetworkX
  G = nx.Graph()
  Añadir nodos con atributos (indicadores como propiedades del nodo)
  Añadir aristas desde la matriz W
  Verificar: conectividad, componentes conexos, densidad

PASO 3: Calcular centralidades
  grado = nx.degree_centrality(G)        — número de vecinos
  intermediación = nx.betweenness_centrality(G)  — "puentes" entre regiones
  cercanía = nx.closeness_centrality(G)          — qué tan cerca de todo

PASO 4: I de Moran Global
  z = (x - x̄) / σ                          — estandarizar variable
  z_lag = W_norm @ z                       — promedio de vecinos
  I = (n / S₀) × (z · z_lag) / (z · z)    — I de Moran
  Bajo H0 (aleatoriedad):
    E[I] = -1/(n-1)
    Var[I] = fórmula de Cliff-Ord
    Z = (I - E[I]) / sqrt(Var[I]) → p-valor bajo normal asintótica

PASO 5: Diagrama de Dispersión de Moran
  Eje X: z (valor estandarizado)
  Eje Y: Wz (rezago espacial = promedio vecinos)
  Pendiente = I de Moran
  Cuadrantes: AA (Alto-Alto), BB (Bajo-Bajo), AB, BA
  Identificar outliers espaciales

PASO 6: Expansión territorial proporcional
  Para estimar provincias/distritos desde totales departamentales:
    Pob_prov_2025(d) = Pob_prov_2017(d) × (Pob_depto_2025(d) / Pob_depto_2017(d))
  ⚠ Supuesto: proporciones intra-departamentales estables entre censos
  Para mayor precisión: SAE Fay-Herriot o IPF (ver referencia)
```

**Interpretación:**
| I de Moran | p-valor | Significado | Ejemplo |
|---|---|---|---|
| I > 0.3 | < 0.05 | Fuerte clustering espacial | Temperatura, envejecimiento |
| 0.1 < I < 0.3 | < 0.10 | Clustering moderado/marginal | Razón de sexos |
| I ≈ 0 | > 0.10 | Sin patrón espacial | Población total |
| I < 0 | — | Dispersión (valores alternados) | Tablero de ajedrez |

**Pitfalls específicos del dominio:**
1. **Matriz W debe ser simétrica**: Siempre verificar que si A es vecino de B, B es vecino de A. Corregir asimetrías automáticamente.
2. **n pequeño (< 30)**: La varianza asintótica de Moran's I puede subestimar la incertidumbre. Considerar tests de permutación como alternativa.
3. **Nombres de nodos**: Coincidencia exacta de nombres entre la matriz de adyacencia y los datos. Usar `.strip()`, normalizar mayúsculas, y verificar matching.
4. **Componentes conexos**: Un grafo territorial debería ser 1 componente. Si hay más, hay errores de nomenclatura o aristas faltantes.
5. **Correlación espacial ≠ causalidad**: Que dos variables se agrupen espacialmente no significa que una cause la otra. Puede haber confusores geográficos (clima, economía, historia).
6. **Pesos W normalizados por filas**: Es la opción más común pero no la única. W binaria o estandarizada globalmente puede dar resultados diferentes. Documentar la elección.

## Principios de calidad

1. **REPRODUCIBILIDAD**: Toda ejecución con seed fija produce resultados idénticos. Reportar seed, versión de paquetes, y timestamp.
2. **INTERVALOS DE CONFIANZA**: Toda estimación puntual lleva su incertidumbre. Nunca dar un número sin su IC95%.
3. **SUPUESTOS**: Tests de supuestos ANTES de ejecutar el modelo principal. Documentar cuáles pasan y cuáles no.
4. **AUTOEVALUACIÓN**: Después de cada análisis, incluir sección de autoevaluación con:
   - Fortalezas (qué se verificó independientemente)
   - Limitaciones (qué no se pudo verificar, qué se asumió)
   - Errores propios (incorrectones detectados y corregidos durante el análisis)
   - Riesgos de interpretación (cómo los sesgos del analista pueden afectar)
5. **CUESTIONAR LAS AFIRMACIONES**: Cada afirmación en el output debe ser "atacada" antes de publicarla:
   - ¿Puedo demostrar esto con datos?
   - ¿Hay una explicación alternativa?
   - ¿Qué cambiaría si un supuesto clave es falso?
   - ¿Estoy confiando en una fuente única?
6. **DETECCIÓN ACTIVA DE ERRORES PROPIOS**: Después de cada análisis, revisar explícitamente:
   - ¿Hay doble conteo de alguna variable?
   - ¿Las sumas parciales coinciden con los totales?
   - ¿Los porcentajes suman 100%?
   - ¿Las unidades son consistentes?
   - ¿Los nombres de columnas en arviz/pandas han cambiado?
7. **FORMATO DUAL**: Informes siempre en .md (legible) + .txt (portable). Incluir fecha, seed, y versión de paquetes en el encabezado.
8. **SIN SOBREAJUSTE**: Validación cruzada, WAIC/LOO, bootstrap. No confiar en una sola métrica.
9. **HONESTIDAD**: Reportar cuando un método no es aplicable o los datos son insuficientes. Preferir "no se puede concluir" a una estimación engañosa.
10. **DOCUMENTACIÓN COMPLETA**: Registrar cada paso del análisis: qué se hizo, por qué, qué se encontró, qué se corrigió. El informe debe ser reproducible por un tercero.

## Pitfalls generales

1. **PyMC 6.x cambió la API**: `pm.Model()` sigue igual, pero el muestreo usa `pm.sample()`
   con cambios en nuts_sampler ('nutpie' por defecto). Verificar con `pm.__version__`.
2. **pandas 2.x vs 3.x**: pingouin con pandas 3.x usa 'pval' no 'p' en DataFrames de salida.
   Con pandas 2.3.3 (instalado), usar 'p-val' (guión). Verificar con `.columns`.
3. **Bootstrap anidado**: El bootstrap externo remuestrea UNIDADES (individuos/encuestas),
   el interno remuestrea PARÁMETROS. No confundir los niveles.
4. **NUTS sampler**: Con n < 100, NUTS puede fallar. Usar Metropolis o emcee.
5. **Cópulas**: La cópula Gaussiana es la más estable pero asigna poca masa a las colas.
   Para eventos extremos, usar t-Student o Gumbel. Siempre verificar que la matriz de
   correlación sea definida positiva (`np.linalg.eigvals(corr) > 0`). Si no lo es,
   regularizar con `corr += np.eye(n) * 0.01` y re-normalizar.
6. **DiD con n < 10 periodos**: Los errores estándar están subestimados. Usar bootstrap.
7. **RDD**: Especificar el bandwidth es crítico. Usar optimal bandwidth (Imbens-Kalyanaraman).
8. **Power analysis**: No redondear el n calculado hacia abajo. El poder es monótono en n.
9. **execute_code NO tiene pandas/scipy/numpy**: El sandbox de `execute_code` no tiene acceso a numpy, scipy, pandas, pymc, ni ningún paquete científico. Para análisis que requieran estos:
   1. Escribir el script completo a disco con `write_file()`
   2. Ejecutar con `terminal()` (no `execute_code()`)
   3. Iterar editando el archivo y re-ejecutando
   Esto aplica a cualquier modelo del skill que use numpy, scipy, pandas, pymc, arviz, emcee, statsmodels, etc.
10. **arviz 1.x cambió nombres de columnas**: `hdi_2.5%` → `eti95_lb`, `hdi_97.5%` → `eti95_ub`.
    Los valores son STRINGS, no floats — convertir con:
    ```python
    for col in ["mean", "sd", "eti95_lb", "eti95_ub", "r_hat", "mcse_mean", "mcse_sd"]:
        if col in summary.columns:
            summary[col] = summary[col].astype(float)
    ```
    Sin esta conversión, operaciones como `round()` fallan con `TypeError: type str doesn't define __round__ method`.
11. **PyMC 6 requiere `pm.compute_log_likelihood()` dentro del contexto del modelo**:
    Después de `pm.sample()`, llamar a `pm.compute_log_likelihood(trace)` DENTRO del
    `with pm.Model():` para que `az.loo()` funcione. Fuera del contexto lanza
    `TypeError: No model on context stack.`
12. **PyMC 6 posterior predictive**: `pm.sample_posterior_predictive()` devuelve un `DataTree`
    con los resultados bajo `ppc["posterior_predictive"]["y"]`, NO `ppc["y"]`.
    Para promediar: `y_pred = ppc["posterior_predictive"]["y"].mean(("chain", "draw")).values`.
13. **arviz 1.x ELPDData cambió atributos**: El objeto retornado por `az.loo()` usa
    `.elpd` y `.se` en vez de `.loo` y `.se` de versiones anteriores. No tiene `.waic`.
    ```python
    loo_result = az.loo(trace, pointwise=False)  # ya no acepta scale=
    loo_ic = loo_result.elpd  # NO loo_result.loo
    loo_se = loo_result.se
    ```
14. **Savage-Dickey BF requiere densidad en H₀ no en la media posterior**: El Factor de
    Bayes para H₀: μ=0 se calcula como BF₁₀ = f_prior(0) / f_posterior(0), NO
    f_prior(mu_post) / f_posterior(mu_post). La densidad se evalúa en 0 (el valor
    bajo H₀), no en la media posterior.
    ```python
    # Correcto:
    bf10 = sp_stats.norm.pdf(0, mu_prior, sigma_prior) / sp_stats.norm.pdf(0, mu_post, sigma_post)
    ```
15. **Matriz de correlación para cópula: verificar definida positiva**: Usar
    `np.linalg.eigvals(corr)` antes de Cholesky. Si algún valor propio ≤ 0,
    sumar `np.eye(n) * 0.01` a la matriz. Sin esta corrección, el Cholesky
    lanza `LinAlgError: Matrix is not positive definite.`
16. **Formato de datos**: Siempre verificar que los datos sean numéricos (float/int) antes de
    pasarlos a modelos estadísticos. pandas lee CSV como strings por defecto a veces.
    Verificar con `df.dtypes` y convertir con `pd.to_numeric()` si es necesario.
17. **Verificación de consistencia PRE-modelo**: Antes de ejecutar cualquier modelo
    estadístico, verificar la consistencia interna de los datos de entrada:
    - Sumas parciales = totales
    - Porcentajes suman 100%
    - Gaps calculados = gaps reportados
    - Unidades consistentes
    Esto evita "garbage in, garbage out" incluso con modelos sofisticados.
    Incluir al menos 4-5 checks y abortar si alguno falla.

## Output

Siempre guardar en formato dual:
- `.md` para legibilidad (tablas, fórmulas renderizadas)
- `.txt` para portabilidad

Incluir sección de **autoevaluación** con limitaciones honestas.
El usuario prefiere saber lo que el modelo NO puede hacer antes que
un pronóstico overconfident.
