---
name: statistical-formula-engine
description: "Crear, ejecutar, auditar y generar fórmulas estadísticas, índices compuestos, indicadores y métricas. Integra pingouin, sympy, pymcdm, uncertainties, factor_analyzer + statsmodels para análisis estadístico completo con validación de supuestos."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [statistics, formulas, indices, pymcdm, sympy, pingouin, factor-analysis, audit]
    category: data-science
---

# Statistical Formula Engine

Motor para crear, ejecutar, auditar y generar fórmulas estadísticas, índices compuestos, indicadores y métricas. Integra 6 herramientas clave en flujos de trabajo reproducibles.

## Entorno

```bash
VENV="/mnt/d/Descargas/UPN-Investigacion/venv_stats_ml"
source "$VENV/bin/activate"
```

Paquetes disponibles: pingouin, sympy, pymcdm, uncertainties, pint, factor_analyzer, numpy, scipy, pandas, statsmodels, scikit-learn

## Cuándo usar este skill

- El usuario necesita crear o auditar una fórmula estadística (ej: U(x), IVCD, IDC, S_territorio)
- El usuario pide verificar supuestos de un modelo (normalidad, homocedasticidad, multicolinealidad)
- El usuario quiere construir un índice compuesto con pesos y validación
- El usuario pide análisis de sensibilidad de indicadores
- El usuario quiere propagación de errores en cálculos financieros
- El usuario necesita **combinar/agregar encuestas** de opinion (poll aggregation)
- El usuario pide **pronostico electoral** con datos de multiples encuestadoras
- El usuario necesita **auditar su propio modelo** (autoevaluacion critica)
- El usuario pregunta por metodos bayesianos para n pequeno

## NO usar cuando

- Solo se necesita estadística descriptiva básica → usar pandas .describe()
- El usuario pide directamente ML o modelos predictivos → usar ml-pipeline-engine
- Solo se necesita graficar → usar matplotlib/seaborn directamente
- La pregunta es puramente sobre seleccion de metodo (estadistica vs ML) → usar method-selector

## Flujos de trabajo

### 1. AUDITORÍA DE FÓRMULA (formula audit)

Carga una expresión matemática, verifica supuestos, evalúa con datos, audita correctitud.

```
PASO 1: Parsear la fórmula con sympy
  - sympy.sympify() o sympy.parsing.parse_expr()
  - Extraer variables libres
  - Verificar consistencia dimensional con pint (opcional)

PASO 2: Verificar supuestos estadísticos (si hay datos)
  - Normalidad: pingouin.normality() o scipy.stats.shapiro()
  - Homocedasticidad: pingouin.homoscedasticity() o scipy.stats.levene()
  - Multicolinealidad: statsmodels.stats.outliers_influence.variance_inflation_factor()
  - Autocorrelación: statsmodels.stats.stattools.durbin_wu()

PASO 3: Evaluar la fórmula
  - Sustituir valores con sympy.subs()
  - Calcular propagación de errores con uncertainties

PASO 4: Reporte
  - Tabla de variables con rangos válidos
  - Resultado de supuestos (pasa/no pasa)
  - Valor numérico con intervalo de confianza
```

**Ejemplo: Auditar fórmula IVCD `U(x) = w1·f_rent(x) + w2·g_imp(x) - w3·h_risk(x)`**

```python
import sympy as sp
import numpy as np
import pingouin as pg
from uncertainties import ufloat

# 1. Parsear fórmula
w1,w2,w3,f,g,h = sp.symbols('w1 w2 w3 f g h')
U = w1*f + w2*g - w3*h
print(f"Fórmula: U = {U}")
print(f"Variables: {[str(v) for v in U.free_symbols]}")

# 2. Verificar supuestos (datos de ejemplo)
np.random.seed(42)
f_data = np.random.normal(0.6, 0.15, 30)  # rentabilidad
g_data = np.random.normal(0.5, 0.20, 30)  # impacto
h_data = np.random.normal(0.2, 0.08, 30)  # riesgo
norm_f = pg.normality(f_data)
norm_g = pg.normality(g_data)
print(f"Normalidad f_rent: W={norm_f['W'].values[0]:.4f} p={norm_f['pval'].values[0]:.4f}")

# 3. Evaluar con propagación de errores
w1_v, w2_v, w3_v = 0.4, 0.35, 0.25
f_v = ufloat(0.70, 0.15)
g_v = ufloat(0.60, 0.20)
h_v = ufloat(0.25, 0.08)
U_val = w1_v*f_v + w2_v*g_v - w3_v*h_v
print(f"IVCD = {U_val}")
```

### 2. CREACIÓN DE ÍNDICE COMPUESTO (index builder)

Construye índices tipo IVCD, IDC, S_territorio con selección de método de pesos y validación.

```
PASO 1: Definir matriz de criterios (N distritos × M indicadores)
  - Normalizar: MinMaxScaler (0-1) o z-score
  - Decidir dirección: 1=maximizar, -1=minimizar

PASO 2: Seleccionar método de pesos
  - Iguales: todos los pesos = 1/M
  - Entropía: pymcdm.weighting import entropy_weight
  - AHP: pairwise comparison matrix
  - Optimización: scikit-opt (genetic algorithm) (si disponible)

PASO 3: Calcular índice con método MCDA
  - TOPSIS (pymcdm.methods.TOPSIS) — recomendado por defecto
  - VIKOR — para soluciones de compromiso
  - PROMETHEE — para ranking completo

PASO 4: Validar consistencia interna
  - Alpha de Cronbach: pingouin.cronbach_alpha() o factor_analyzer
  - KMO: factor_analyzer.calculate_kmo()
  - Bartlett: factor_analyzer.calculate_bartlett_sphericity()

PASO 5: Análisis de sensibilidad
  - Variar cada peso ±20%, medir cambio en ranking
  - Identificar variables con mayor impacto en el índice
```

**Ejemplo: Índice de Potencialidad Territorial (6 factores)**

```python
import numpy as np
import pandas as pd
from pymcdm.methods import TOPSIS
from pymcdm.weighting import entropy_weight
from pingouin import cronbach_alpha
from factor_analyzer import calculate_kmo

# 1. Matriz simulada: 5 distritos × 6 factores
data = np.array([
    [80, 70, 30, 60, 40, 65],  # Distrito A
    [60, 50, 70, 40, 30, 55],  # Distrito B
    [90, 80, 20, 70, 50, 75],  # Distrito C
    [40, 60, 50, 30, 20, 45],  # Distrito D
    [70, 65, 40, 55, 35, 60],  # Distrito E
])
factores = ['Demanda','Captacion','Competencia','Accesibilidad','Riesgo','Politica']

# 2. Tipos: demanda(+), captacion(+), competencia(-), accesibilidad(+), riesgo(-), politica(+)
types = [1, 1, -1, 1, -1, 1]

# 3. Pesos por entropía
weights = entropy_weight(data)
print(f"Pesos: {dict(zip(factores, [f'{w:.3f}' for w in weights]))}")

# 4. TOPSIS
topsis = TOPSIS()
scores = topsis(data, weights, types)
ranking = np.argsort(scores)[::-1] + 1
print(f"Scores: {[f'{s:.3f}' for s in scores]}")
print(f"Ranking: {ranking}")

# 5. Validación (si hay suficientes datos)
kmo_all, kmo_total = calculate_kmo(data)
print(f"KMO total: {kmo_total:.3f}")
```

### 3. REPORTE DE DIAGNÓSTICO ESTADÍSTICO (stat report)

Genera reporte completo de un modelo de regresión con verificación de supuestos.

```
PASO 1: Ajustar modelo (statsmodels OLS)
PASO 2: Verificar supuestos:
  - VIF < 5 (multicolinealidad baja)
  - Durbin-Watson ≈ 2 (no autocorrelación)
  - Breusch-Pagan p > 0.05 (homocedasticidad)
  - Jarque-Bera p > 0.05 (normalidad residuos)
PASO 3: Identificar violaciones y sugerir correcciones
PASO 4: Reporte estructurado en tabla
```

```python
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
import pingouin as pg
import numpy as np

def diagnostic_report(X, y, X_names=None):
    """Reporte completo de diagnóstico de regresión"""
    if X_names is None:
        X_names = [f'X{i}' for i in range(X.shape[1])]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    # VIF
    vif = [variance_inflation_factor(X, i) for i in range(X.shape[1])]
    
    # DW
    dw = durbin_watson(model.resid)
    
    # BP
    bp_test = het_breuschpagan(model.resid, X)
    
    # JB
    resid_norm = pg.normality(model.resid)
    
    print("=== REPORTE DE DIAGNÓSTICO ===")
    print(f"R² ajustado: {model.rsquared_adj:.4f}")
    print("\n--- Multicolinealidad (VIF) ---")
    for name, v in zip(['const']+X_names, vif):
        flag = '⚠ ALTO' if v > 5 else '✓ OK'
        print(f"  {name:15s}: {v:.2f}  {flag}")
    print(f"\n--- Autocorrelación ---")
    print(f"  Durbin-Watson: {dw:.3f}  {'⚠' if abs(dw-2)>0.5 else '✓'}")
    print(f"\n--- Homocedasticidad ---")
    print(f"  Breusch-Pagan: stat={bp_test[0]:.3f} p={bp_test[1]:.4f}  {'⚠' if bp_test[1]<0.05 else '✓'}")
    print(f"\n--- Normalidad residuos ---")
    print(f"  Shapiro-Wilk: W={resid_norm['W'].values[0]:.4f} p={resid_norm['pval'].values[0]:.4f}  {'⚠' if resid_norm['pval'].values[0]<0.05 else '✓'}")
    return model
```

### 4. ANÁLISIS DE SENSIBILIDAD (sensitivity)

Evalúa cómo cambia un índice/score cuando varían los pesos.

```
PASO 1: Definir índice base con pesos originales
PASO 2: Para cada peso, variar ±10%, ±20%, ±30%
PASO 3: Recalcular ranking con pesos modificados
PASO 4: Medir el cambio en posición de cada alternativa
PASO 5: Identificar qué pesos son más críticos (mayor cambio de ranking)
```

## Referencia rápida de funciones

| Tarea | Función | Paquete |
|---|---|---|
| Normalidad (Shapiro-Wilk) | `pg.normality(data)` | pingouin |
| Homocedasticidad (Levene) | `pg.homoscedasticity([a,b])` | pingouin |
| Alpha de Cronbach | `pg.cronbach_alpha(data)` | pingouin |
| VIF | `variance_inflation_factor(X,i)` | statsmodels |
| Durbin-Watson | `durbin_watson(resid)` | statsmodels |
| Breusch-Pagan | `het_breuschpagan(resid, X)` | statsmodels |
| TOPSIS | `TOPSIS()(matrix, weights, types)` | pymcdm |
| Pesos por entropía | `entropy_weights(matrix)` (de `pymcdm.weights`) | pymcdm |
| KMO | `calculate_kmo(data)` | factor_analyzer |
| Bartlett | `calculate_bartlett_sphericity(data)` | factor_analyzer |
| Parsear fórmula | `sp.sympify(expr_string)` | sympy |
| Derivada | `sp.diff(expr, var)` | sympy |
| Propagación errores | `ufloat(val, err) ± ufloat(...)` | uncertainties |
| Evaluar sympy | `expr.subs({var: val})` | sympy |

## Pitfalls

1. **pingouin con pandas 3.x**: Las columnas del DataFrame de salida usan 'pval' (no 'p'). Verificar nombres con `.columns` si hay KeyError.
2. **pymcdm requiere numpy arrays**: No acepta DataFrames de pandas directamente. Convertir con `.values` o `.to_numpy()`.
3. **sympy.sympify() es inseguro con entradas de usuario**: Si la fórmula viene de texto libre, usar `sp.parsing.parse_expr()` con medidas de seguridad.
4. **KMO requiere suficientes observaciones**: Mínimo 5 observaciones por variable. Con menos, el test falla o no es confiable.
5. **VIF en constantes**: statsmodels incluye el intercepto como columna. `variance_inflation_factor(X, 0)` es el VIF de la constante (se ignora).
6. **Propagación de errores asume independencia**: uncertainties asume que las variables son independientes. Si hay correlación, usar `ufloat_correlation()`.
7. **Pesos por entropía falla con valores cero o negativos**: Asegurar que los datos estén normalizados a (0,1] (sin ceros exactos, sumar 0.001 si es necesario).

### 5. AGREGACION DE ENCUESTAS (poll aggregation)

Combina multiples encuestas de opinion en un pronostico con
incertidumbre calibrada. Adecuado para n < 30 polls.

Ver metodologia completa en `references/poll-aggregation-methodology.md`.

```
PASO 1: Estimar house effects (sesgo sistematico por encuestadora)
  - Diferencia de cada encuestadora vs el promedio general
  - Corregir diferencias restando el house effect

PASO 2: Bootstrap a nivel de encuesta (NO de individuo)
  - Remuestrear las ENCUESTAS con reemplazo (n_polls, no n_entrevistas)
  - Ponderar por tamano de muestra (polls grandes pesan mas)
  - 10,000 repeticiones → distribucion bootstrap

PASO 3: Propagar incertidumbre de parametros secundarios
  - Voto blanco/nulo como distribucion (no valor fijo)
  - Participacion como distribucion (no valor fijo)
  - Simular 100,000 escenarios combinados

PASO 4: Bayesian Model Averaging
  - 4+ modelos con distintas especificaciones (ventana temporal,
    filtro de calidad, ajuste historico)
  - Promediar distribuciones con pesos iguales (default)
  - Reportar el rango, no un valor puntual

PASO 5: Autoevaluacion
  - Preguntar: ¿es robusto? (cambia al variar supuestos?)
  - Preguntar: ¿IC realistas? (no subestimados por DEFF)
  - Preguntar: ¿sesgo del investigador? (modelo "favorito" como base?)
```

**Ejemplo: Pronostico electoral segunda vuelta Peru 2026**

```python
import numpy as np

# 15 encuestas: (diferencia Keiko-Roberto pp, n, encuestadora)
polls = np.array([
    [(51.4-48.6), 1204, 0],  # Ipsos
    [(52.9-47.1), 1501, 1],  # Datum
    # ... 13 mas
])

# Bootstrap a nivel de encuesta (DEFF correction)
N_BOOT = 10000
boot = np.zeros(N_BOOT)
for b in range(N_BOOT):
    idx = np.random.choice(len(polls), len(polls), replace=True)
    w = polls[idx, 1] / polls[idx, 1].sum()
    boot[b] = np.average(polls[idx, 0], weights=w)

p_victoria = (boot > 0).mean()
ic_95 = np.percentile(boot, [2.5, 97.5])

# ⚠ NUNCA usar n_entrevistas como n_observaciones
# Incorrecto: scipy.stats.beta(alfa+total_votos, beta+total_no_votos)
# Correcto:  bootstrap sobre polls
```

## Pitfalls adicionales (poll aggregation)

8. **DEFF ignorado**: Tratar 19,513 entrevistas como 19,513 obs independientes
   es el error mas comun. Cada ENCUESTA es un cluster. El tamano efectivo
   de muestra NO es la suma de entrevistas, sino el numero de polls.
9. **Overconfidence por modelo unico**: Si 4 especificaciones distintas dan
   resultados incompatibles (Keiko 51% vs Roberto 53%), no hay "modelo base".
   Usar Bayesian Model Averaging.
10. **Decimales espurios**: Con n < 30 polls, NO reportar decimales (51.11%).
    Redondear a enteros (51%).
11. **Sesgo del investigador**: El modelo que el investigador "prefiere" no
    es el modelo "base". Todos son igualmente validos. Reportarlos todos.
12. **Autoevaluacion obligatoria**: Despues de construir el modelo, auditarlo.
    Documentar limitaciones con honestidad. El usuario valora mas la verdad
    sobre las limitaciones que un pronostico overconfident.

---

### 6. DESAGREGACIÓN ESPACIAL (IPF + SAE)

Cuando los datos están a nivel departamental (n=25) y se necesitan a nivel distrital (~1,874).

#### 5.1 Iterative Proportional Fitting (IPF)

Distribuye totales conocidos usando múltiples constraints. Única solución que maximiza entropía.

```
Paso t: A^(t)_ik = A^(t-1)_ik * (T_jk / Σ_i A^(t-1)_ik)

Donde:
  A_ik = Valor de variable k en distrito i
  T_jk = Total conocido en departamento j
  Seed: población distrital como starting point
  Convergencia: |A^(t)/A^(t-1) - 1| < 10^-6
```

**Validación:** Verificar que los marginales se conservan exactamente. RMSE < 0.1%.

#### 5.2 SAE Fay-Herriot con Bootstrap

El modelo Fay-Herriot estima indicadores para áreas pequeñas:

```
θ_i_FH = γ_i * θ_i_dir + (1 - γ_i) * x_i' * β̂

γ_i = σ²_v / (σ²_v + σ²_ei)  — shrinkage factor
```

**⚠ CRÍTICO:** Con n=25, σ²_v tiene CV~47% (verificado por simulación). **NO usar fórmula asintótica de MSE.** Usar bootstrap:

```python
import numpy as np

def sae_bootstrap(X, theta_dir, sig2_e, n_bootstrap=1000):
    """SAE Fay-Herriot con bootstrap para intervalos de confianza."""
    n = len(theta_dir)
    boot_estimates = np.zeros((n_bootstrap, n))
    
    for b in range(n_bootstrap):
        # Remuestrear departamentos
        idx = np.random.choice(n, n, replace=True)
        X_boot = X[idx]
        theta_boot = theta_dir[idx]
        sig2_boot = sig2_e[idx]
        
        # Estimar sigma2_v por REML (simplificado)
        from sklearn.linear_model import Ridge
        m = Ridge(alpha=1.0)
        m.fit(X_boot, theta_boot)
        resid = theta_boot - m.predict(X_boot)
        sig2_v_est = max(0.001, np.var(resid) - np.mean(sig2_boot))
        
        # Predictor FH
        gamma = sig2_v_est / (sig2_v_est + sig2_boot)
        theta_fh = gamma * theta_boot + (1 - gamma) * m.predict(X_boot)
        boot_estimates[b] = theta_fh
    
    # Intervalos de confianza
    ci_low = np.percentile(boot_estimates, 2.5, axis=0)
    ci_high = np.percentile(boot_estimates, 97.5, axis=0)
    theta_mean = boot_estimates.mean(axis=0)
    
    return theta_mean, ci_low, ci_high
```

**Referencia:** Srivastava & Kumar (2025) — SAE para inclusión financiera en India.

#### 5.3 Propagación de errores (bootstrap anidado)

El error del SAE se propaga al modelo ML (~17% de pérdida en R²). Mitigación:

```
Para b = 1, ..., B:
  1. Bootstrap de departamentos (Fase SAE)
  2. Estimar indicadores distritales
  3. Entrenar modelo predictivo (Ridge o XGBoost)
  4. Evaluar en out-of-bag
  5. Guardar métrica

Reportar: R² medio ± IC 95% (NO un valor puntual)
```

Extrae datos de los cuadros estadísticos del INEI (formato Excel multi-hoja con cabeceras anidadas).

Ver `references/inei-excel-processing.md` para patrones completos y script de extracción probado.

```
PASO 1: Identificar estructura del Excel
  - pd.ExcelFile() para listar hojas
  - read_excel(skiprows=6) como default para cabeceras INEI

PASO 2: Normalizar nombres de departamento
  - unicodedata.normalize('NFKD') para acentos (Áncash vs Ancash)
  - Filtrar filas agregadas (Valor Agregado, Derechos, PBI total)

PASO 3: Renombrar columnas con años como nombres
  - Columnas "Unnamed" → años (2007..2024)
  - Notar sufijos P/ (preliminar) y E/ (estimado)

PASO 4: Extraer indicadores derivados
  - PBI per cápita = PBI / población
  - Crecimiento acumulado = (Valor_final / Valor_inicial) - 1
  - Participación % = (PBI_depto / PBI_nacional) * 100
```

## Referencias incluidas

| Archivo | Contenido |
|---|---|
| `references/inei-excel-processing.md` | Patrones de procesamiento de Excel del INEI: skiprows, acentos, notacion P/E/, Lima desagregado |
| `references/poll-aggregation-methodology.md` | Metodologia completa para agregar encuestas: DEFF, house effects, bootstrap a nivel cluster, BMA, autoevaluacion |

## Output

Siempre guardar en formato dual:
- `.md` para legibilidad (tablas, formulas renderizadas)
- `.txt` para portabilidad

Incluir en el informe una seccion de **limitaciones** con honestidad.
El usuario prefiere saber lo que el modelo NO puede hacer antes que
un pronostico overconfident.
