---
name: time-series-forecasting
description: "Proyectar indicadores económicos a años futuros usando regresión lineal por entidad, ARIMA, Prophet y validación con LOOCV. Especializado en series cortas (n<25 años) y datos departamentales peruanos."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [forecasting, time-series, projection, regression, ARIMA, small-n]
---

# Time Series Forecasting

Proyectar indicadores económicos (PBI, pobreza, etc.) a años futuros. Optimizado para series departamentales peruanas cortas (2007-2024 = 18 puntos).

## Entorno

```bash
VENV="/mnt/d/Descargas/UPN-Investigacion/venv_stats_ml"
source "$VENV/bin/activate"
```

## Cuándo usar

- El usuario necesita proyectar un indicador a 2025, 2026 o más allá
- Hay datos históricos disponibles (mínimo 5-10 años)
- Se necesita comparar métodos (lineal vs. ARIMA vs. ML)
- Contexto: PBI departamental, pobreza, densidad financiera

## Cuándo NO usar

- El usuario necesita un modelo causal (usar ml-pipeline-engine)
- Hay menos de 3 puntos de datos (no alcanza para tendencia)
- El usuario pide escenarios contra-fácticos (usar statistical-formula-engine)

## Métodos disponibles (orden de recomendación)

### Método 1: Regresión Lineal Simple (default para n=18)

Por cada entidad (departamento), ajustar PBI ~ año. Simple, interpretable, funciona bien para tendencias lineales.

```python
from sklearn.linear_model import LinearRegression
import numpy as np

anos = np.array(range(2007, 2025)).reshape(-1, 1)  # [2007..2024]
valores = df_departamento.values  # PBI año a año
modelo = LinearRegression().fit(anos, valores)
proy_2025 = modelo.predict([[2025]])[0]
proy_2026 = modelo.predict([[2026]])[0]
r2 = r2_score(valores, modelo.predict(anos))
```

**Ventaja:** Simple, R² alto (>0.85) para series con tendencia clara
**Desventaja:** No captura ciclos ni quiebres estructurales (ej: COVID-2020)

### Método 2: Regresión con dummies post-COVID

Agrega variable binaria para 2020 (caída) y 2021 (rebote).

```python
X = np.column_stack([anos.ravel(),
    [1 if a==2020 else 0 for a in anos],  # dummy caida
    [1 if a==2021 else 0 for a in anos]])  # dummy rebote
```

### Método 3: ARIMA (para series con autocorrelación)

Si los residuos de la regresión lineal muestran autocorrelación (Durbin-Watson ≠ 2).

```python
from statsmodels.tsa.arima.model import ARIMA
# Orden pequeño para n<20: ARIMA(1,1,0) o ARIMA(0,1,1)
modelo = ARIMA(valores, order=(1,1,0)).fit()
proy = modelo.forecast(steps=2)
```

### Método 4: XGBoost LOOCV (cuando hay features adicionales)

```python
from xgboost import XGBRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score, mean_absolute_error

# Features: PBI en anos clave + indicadores auxiliares
X = np.column_stack([pbi_2007, pbi_2010, pbi_2015, pbi_2020])
y = crecimiento_07_24  # target

y_pred = np.zeros(len(y))
for tr, te in LeaveOneOut().split(X):
    m = XGBRegressor(n_estimators=50, max_depth=2, random_state=42, verbosity=0)
    m.fit(X[tr], y[tr])
    y_pred[te] = m.predict(X[te])[0]
```

## Validación

| Método | Métrica | Threshold esperado |
|---|---|---|
| Regresión lineal | R² | >0.80 (series con tendencia) |
| LOOCV | MAE | <10% del valor medio |
| ARIMA | AIC | Comparativo entre órdenes |
| Bootstrap | CI 95% | Intervalo percentil 2.5-97.5% |

## Proyección de totales

```python
# Sumar proyecciones individuales para obtener total nacional
total_2025 = sum(proyecciones[depto][0] for depto in deptos)
total_2026 = sum(proyecciones[depto][1] for depto in deptos)
crecimiento = ((total_2025 / total_2024) - 1) * 100
```

## Pitfalls

1. **COVID-2020 rompe la tendencia lineal** en muchos departamentos. Si el modelo lineal da R² < 0.70, revisar si incluir dummy 2020-2021 mejora el ajuste.
2. **Madre de Dios y Pasco** tienen R² muy bajo (<0.10) porque su PBI real no creció en 17 años. Para estos, la proyección lineal es poco confiable.
3. **Moquegua** tiene alta volatilidad por minería (caídas y picos). Usar mediana móvil o suavizado antes de proyectar.
4. **Nunca proyectar más allá de 3 años** con n=18 — el error crece geométricamente.
6. **ARIMA necesita estacionariedad** — si la serie tiene tendencia, diferenciar (d=1) antes de modelar.
7. **El MAE de XGBoost LOOCV suele ser alto** (30-40pp) con n<25 porque cada fold entrena con solo 22 datos.

## Referencias

- `references/peru-departmental-projections.md` — Proyecciones reales de PBI departamental 2025-2026 con tabla completa, ranking de métodos y departamentos con baja confiabilidad.

