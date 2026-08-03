---
name: ml-pipeline-engine
description: "Diseñar, ejecutar, auditar y optimizar pipelines de Machine Learning con validación geoespacial. Integra sklearn, xgboost, shap, esda, geopandas, libpysal para pipelines modulares con Block CV, Moran's I y SHAP."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ml, pipeline, xgboost, shap, spatial, esda, geospatial, block-cv]
    category: data-science
---

# ML Pipeline Engine

Diseñar, ejecutar, auditar y optimizar pipelines de Machine Learning con validación geoespacial. Especializado en datos territoriales peruanos (departamentos n=25, distritos n=1,874) y small-n ML.

## Entorno

```bash
VENV="/mnt/d/Descargas/UPN-Investigacion/venv_stats_ml"
source "$VENV/bin/activate"
```

Paquetes disponibles: sklearn, xgboost, shap, esda, libpysal, geopandas, numpy, scipy, pandas, statsmodels, yellowbrick, uncertainties, scikit-opt (opcional), boruta (opcional)

## Cuándo usar este skill

- El usuario necesita diseñar un pipeline ML de principio a fin
- El usuario tiene datos geográficos y necesita validación espacial (Block CV, Moran's I)
- El usuario trabaja con datasets pequeños (n < 100, típicamente n=25 departamentos)
- El usuario pide interpretabilidad (SHAP values)
- El usuario necesita inferencia causal (Double ML)
- El usuario pide clustering territorial seguido de clasificación

## NO usar cuando

- Solo se necesita estadística clásica (regresión, tests de hipótesis) → usar statistical-formula-engine
- El usuario solo quiere explorar datos → usar jupyter-live-kernel
- El usuario pide deep learning o NLP → skills específicos

## Flujos de trabajo avanzados

### -1. PIPELINE PRELIMINAR: DESAGREGACIÓN ESPACIAL (IPF → SAE)

Antes de ejecutar ML, los datos suelen estar a nivel departamental (n=25) y deben desagregarse a nivel distrital (~1,874). Esta fase consta de 2 pasos:

**PASO -1A: Iterative Proportional Fitting (IPF)**

Distribuye totales departamentales conocidos entre distritos usando múltiples constraints (población, PBI, pobreza). No se encontró precedente en banca — es una oportunidad de contribución original.

```
Paso iterativo t:
  A^(t)_ik = A^(t-1)_ik * (T_jk / Σ_{i∈j} A^(t-1)_ik)

Donde:
  A_ik = Valor de variable k en distrito i
  T_jk = Total conocido de variable k en departamento j
  Seed inicial: población distrital (Censo 2017 o proyección)
  Convergencia: max|A^(t) / A^(t-1) - 1| < 10^-6
```

Propiedades: solución única, máxima entropía, conserva marginales exactos.

**PASO -1B: Small Area Estimation (SAE) Fay-Herriot**

Corrige las estimaciones del IPF con modelo estadístico que produce intervalos de confianza.

```
θ_i = x_i' * β + v_i + e_i

Donde:
  θ_i = Indicador en distrito i
  x_i = Covariables (población, pobreza, IDH, densidad)
  v_i = Efecto aleatorio ~ N(0, σ²_v) — heterogeneidad no observada
  e_i = Error de muestreo ~ N(0, σ²_ei) — de la encuesta
```

**CRÍTICO:** Con n=25 departamentos, σ²_v tiene CV~47% (verificado por simulación). NO usar fórmula asintótica de MSE. Usar bootstrap (1,000 remuestras) para intervalos de confianza.

Predictor BLUP:
```
θ_i_FH = γ_i * θ_i_dir + (1 - γ_i) * x_i' * β̂
γ_i = σ²_v / (σ²_v + σ²_ei)  — shrinkage factor
```

Validación: LOOCV a nivel departamental. Reportar RMSE + IC bootstrap.

Referencia: Srivastava & Kumar (2025) — única aplicación documentada de SAE para planificación de red bancaria (India).

**PASO -1C: Bootstrap anidado (SAE → ML)**

El error de SAE se propaga al ML (~17% de pérdida en R² verificada por simulación). Mitigación:

```
Para b = 1, ..., B (B=500 mínimo, 1000 recomendado):
  1. Remuestrear 25 departamentos con reemplazo
  2. Estimar SAE para distritos de la remuestra
  3. Entrenar modelo (Ridge o XGBoost) con features SAE
  4. Predecir en out-of-bag
  5. Guardar R²_b

Reportar: R²_medio, IC_95% = [percentil_2.5, percentil_97.5]
```

**NO reportar un solo R² puntual** — no refleja la incertidumbre de la desagregación espacial.

### 0. GUÍA DE ELECCIÓN DE ALGORITMO (antes de empezar)

Antes de ejecutar cualquier pipeline, responder:

| Pregunta | Si responde SÍ → |
|---|---|
| ¿n < 30 observaciones? | **COMPARAR** Ridge vs XGBoost con LOOCV. NO pre-seleccionar — XGBoost gana si hay interacciones no lineales incluso con n<30 (verificado en simulación con n=25). Ridge es baseline, XGBoost es alternativa. |
| ¿n entre 30-100? | Comparar Ridge vs XGBoost con LOOCV. XGBoost con n_estimators bajos (<100), max_depth<4. |
| ¿n > 100? | XGBoost/LightGBM estándar + CV. Ridge como baseline. |
| ¿Datos espaciales (lat/lon)? | **LOOCV es el default** para n<50. Block CV solo si los bloques están balanceados (CV<30% entre bloques). Verificar balance antes de usar Block CV. Moran's I en residuos siempre. |
| ¿Serie temporal? | Separación temporal estricta (no mezclar años) |
| ¿Target binario desbalanceado? | Usar PR-AUC (no Accuracy), scale_pos_weight |
| ¿Necesitas explicar a SBS/jurado? | SHAP obligatorio. No usar black boxes sin interpretación |

### 0.5. AUTO-ML LIGERO (Light AutoML)

Cuando no sabes qué modelo usar, ejecutar comparación rápida **siempre probando Ridge vs XGBoost** (no pre-seleccionar):

```python
def auto_model_selector(X, y, task='regression', cv_method='auto'):
    """
    Compara modelos automáticamente y recomienda el mejor.
    task: 'regression' o 'classification'
    cv_method: 'auto' → LOOCV si n<50, 5-Fold si n>=50
    **SIEMPRE compara Ridge/Logistic vs XGBoost — no preseleccionar.**
    """
    n = len(y)
    cv = LeaveOneOut() if n < 50 else 5
    
    if task == 'regression':
        models = {
            'Ridge': Ridge(alpha=1.0),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
            'XGBoost': XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
        }
        metric = 'r2'
    else:
        models = {
            'Logistic': LogisticRegression(max_iter=1000, random_state=42),
            'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
            'XGBoost': XGBClassifier(n_estimators=100, random_state=42, verbosity=0),
        }
        metric = 'roc_auc'
    
    results = {}
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring=metric)
        results[name] = {'mean': scores.mean(), 'std': scores.std()}
        print(f"  {name:15s} {metric}={scores.mean():.4f} ±{scores.std():.4f}")
    
    best = max(results, key=lambda k: results[k]['mean'])
    print(f"\n→ Recomendado: {best} ({metric}={results[best]['mean']:.4f})")
    
    # ADVERTENCIA: si Ridge y XGBoost difieren por < 5%, Ridge es preferible
    # por su interpretabilidad. Si XGBoost gana por > 10%, hay no-linealidades
    ridge_key = 'Ridge' if task == 'regression' else 'Logistic'
    xgb_key = 'XGBoost'
    if ridge_key in results and xgb_key in results:
        diff = results[xgb_key]['mean'] - results[ridge_key]['mean']
        if diff < 0.05:
            print(f"  ⚠ Diferencia Ridge-XGBoost < 5% -> preferir Ridge (interpretable)")
        elif diff > 0.10:
            print(f"  ⚠ XGBoost gana por > 10% -> hay no-linealidades reales en los datos")
    
    return results, best
```

### 0.6. HYPERPARAMETER TUNING CON OPTUNA

Optimización eficiente de hiperparámetros para datasets pequeños.

```python
import optuna
from sklearn.model_selection import cross_val_score, LeaveOneOut
from xgboost import XGBRegressor

def tune_xgboost(X, y, n_trials=50):
    """Optimiza XGBoost con Optuna + LOOCV"""
    
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 10, 200),
            'max_depth': trial.suggest_int('max_depth', 2, 6),
            'learning_rate': trial.suggest_float('lr', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample', 0.5, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 10, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-3, 10, log=True),
            'random_state': 42,
            'verbosity': 0,
        }
        model = XGBRegressor(**params)
        cv = LeaveOneOut() if len(y) < 50 else 5
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        return scores.mean()
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    
    print(f"Mejores params: {study.best_params}")
    print(f"Mejor R² LOOCV: {study.best_value:.4f}")
    return study.best_params
```

### 0.7. FEATURE ENGINEERING AUTOMÁTICO

Creación automática de features para datos territoriales.

```python
import numpy as np
import pandas as pd

def auto_features_territoriales(df, coords_cols=None, pob_col=None):
    """
    Genera features derivadas automáticamente para datos territoriales.
    """
    df = df.copy()
    features = []
    
    # Interacciones entre pares de variables económicas
    eco_cols = [c for c in df.columns if any(k in c.lower() 
                for k in ['pbi','pob','ingreso','informal','pobreza'])]
    for i, c1 in enumerate(eco_cols):
        for c2 in eco_cols[i+1:]:
            df[f'{c1}_x_{c2}'] = df[c1] * df[c2]
            features.append(f'{c1}_x_{c2}')
    
    # Ratios (per cápita)
    if pob_col and pob_col in df.columns:
        for c in eco_cols:
            if c != pob_col:
                df[f'{c}_pc'] = df[c] / df[pob_col]
                features.append(f'{c}_pc')
    
    # Log-transformaciones (para datos con sesgo)
    for c in eco_cols:
        if df[c].min() > 0:
            df[f'log_{c}'] = np.log(df[c])
            features.append(f'log_{c}')
    
    print(f"Features generadas: {len(features)}")
    return df, features

### 0.8. ENSEMBLE (STACKING)

Combinación de múltiples modelos para mejorar precisión.

```python
from sklearn.ensemble import StackingRegressor, StackingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

def stacking_model(task='regression'):
    """Stacking ensemble con 3 modelos base + meta-modelo"""
    if task == 'regression':
        base_models = [
            ('ridge', Ridge(alpha=1.0)),
            ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
            ('xgb', XGBRegressor(n_estimators=100, random_state=42, verbosity=0)),
        ]
        meta = Ridge(alpha=1.0)
        stack = StackingRegressor(estimators=base_models, final_estimator=meta, cv=5)
    else:
        base_models = [
            ('lr', LogisticRegression(max_iter=1000, random_state=42)),
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('xgb', XGBClassifier(n_estimators=100, random_state=42, verbosity=0)),
        ]
        meta = LogisticRegression(max_iter=1000, random_state=42)
        stack = StackingClassifier(estimators=base_models, final_estimator=meta, cv=5)
    
    return stack

### 0.9. PREDICCIÓN CON INTERVALOS (Conformal Prediction)

Cuando se necesita no solo el valor puntual sino un rango de confianza.

```python
def predict_with_ci(model, X_train, y_train, X_test, alpha=0.1):
    """
    Predice con intervalos de confianza usando conformal prediction.
    alpha=0.1 → 90% de confianza
    """
    from sklearn.model_selection import train_test_split
    
    # Split para calibration
    X_cal, X_val, y_cal, y_val = train_test_split(
        X_train, y_train, test_size=0.3, random_state=42)
    
    model.fit(X_cal, y_cal)
    y_val_pred = model.predict(X_val)
    residuals = np.abs(y_val - y_val_pred)
    
    # Umbral de conformidad
    n_cal = len(y_val)
    q_level = np.ceil((n_cal + 1) * (1 - alpha)) / n_cal
    q = np.quantile(residuals, q_level, method='higher')
    
    # Predicciones con intervalo
    y_pred = model.predict(X_test)
    lower = y_pred - q
    upper = y_pred + q
    
    return y_pred, lower, upper, q

# Flujos de trabajo originales

### 1. PIPELINE COMPLETO 3 ETAPAS (full pipeline)

Arquitectura del Marco Metodológico: Clustering → Clasificación → Inferencia Causal

```
ETAPA 1: Clustering territorial (no supervisado)
  - K-Means con Distancia de Haversine (coordenadas)
  - DBSCAN para detectar outliers espaciales
  - Evaluar con silhouette score + mapa geográfico
  - Salida: etiqueta de cluster para cada distrito

ETAPA 2: Clasificación supervisada (XGBoost)
  - Pipeline sklearn con StandardScaler + XGBClassifier
  - Validación: Spatial Block CV (custom splitter)
  - Métricas: F1-Score, PR-AUC (no Accuracy por desbalance)
  - Interpretación: SHAP values globales + locales

ETAPA 3: Inferencia causal (Double ML)
  - Modelo de tratamiento: RandomForest/XGBoost → predice apertura
  - Modelo de outcome: RandomForest/XGBoost → predice PBI
  - ATE = regresión de residuos
  - Requiere datos panel (varios años)
```

**Ejemplo: Pipeline completo**

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
import shap

def pipeline_3etapas(X, y, coords=None, n_clusters=4):
    """
    X: matriz de features (N distritos × M variables)
    y: target binario (1=viable, 0=no viable)
    coords: array (N × 2) de [lat, lon] para distancia Haversine
    """
    # Etapa 1: Clustering
    if coords is not None:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(coords)  # cluster por geografía
    else:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
    
    sil = silhouette_score(X, clusters) if X.shape[0] > n_clusters else None
    print(f"Silhouette: {sil:.3f}" if sil else "Muy pocos datos para silhouette")
    
    # Agregar cluster como feature
    X_aug = np.column_stack([X, clusters])
    
    # Etapa 2: XGBoost con validación
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('xgb', XGBClassifier(n_estimators=100, eval_metric='logloss', 
                              random_state=42, verbosity=0))
    ])
    
    # Nota: usar BlockCV aquí (ver workflow 2)
    pipe.fit(X_aug, y)
    
    # SHAP
    explainer = shap.TreeExplainer(pipe.named_steps['xgb'])
    X_scaled = StandardScaler().fit_transform(X_aug)
    shap_vals = explainer(X_scaled)
    
    # Feature importance
    mean_shap = np.abs(shap_vals.values).mean(axis=0)
    print(f"Top 3 features SHAP: {np.argsort(mean_shap)[-3:]}")
    
    return pipe, clusters, shap_vals
```

### 2. VALIDACIÓN GEOESPACIAL (spatial validation)

Block CV (Validación Cruzada por Bloques Geoespaciales) y Moran's I.

```
PROBLEMA: K-Fold normal mezcla distritos cercanos en train/test.
Vecinos son similares (Ley de Tobler) → fuga de información espacial
→ métricas optimistas.

SOLUCIÓN: Crear folds geográficamente separados.

PASO 1: Asignar cada muestra a un bloque geográfico
PASO 2: Heredar de BaseCrossValidator
PASO 3: Cada fold = train en N-1 bloques, test en 1 bloque separado
PASO 4: Promediar métricas de todos los folds
```

**⚠ ADVERTENCIA CRÍTICA: Verificar balance de bloques antes de usar Block CV**

Simulación con datos reales de 25 departamentos peruanos agrupados en 6 bloques (CostaN, CostaS, SierraN, SierraS, Selva, Lima):

| Bloque | Deptos | CMAC | %CMAC |
|--------|--------|------|-------|
| CostaN | 5 | 127 | 24% |
| CostaS | 4 | 81 | 15% |
| SierraN | 5 | 103 | 19% |
| SierraS | 5 | 132 | 24% |
| Selva | 3 | 23 | 4% |
| Lima | 2 | 47 | 9% |

**CV entre bloques: 47%** (ideal < 30%). Esto significa que los folds tienen tamaños muy dispares → las métricas no son comparables entre folds.

**REGLAS:**
- **Para n < 50: LOOCV es el default correcto.** Cada observación es su propio fold.
- **Block CV solo si CV entre bloques < 30%** y cada bloque tiene > 10% de los datos.
- **Alternativa:** LOOCV + Moran's I en residuos para verificar dependencia espacial no modelada.
- **NUNCA** usar Block CV sin verificar el balance primero.

**Implementación Block CV custom:**

```python
from sklearn.model_selection import BaseCrossValidator
from sklearn.model_selection import cross_val_score
import numpy as np

class SpatialBlockCV(BaseCrossValidator):
    """
    Validación cruzada por bloques geográficos.
    blocks: array-like de etiquetas de bloque (ej: 1..5 para 5 regiones)
    """
    def __init__(self, blocks, n_splits=None):
        self.blocks = np.array(blocks)
        self.unique_blocks = np.unique(self.blocks)
        if n_splits is None:
            n_splits = len(self.unique_blocks)
        self.n_splits = min(n_splits, len(self.unique_blocks))
    
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits
    
    def split(self, X, y=None, groups=None):
        # Cada fold = dejar fuera UN bloque completo
        for test_block in self.unique_blocks[:self.n_splits]:
            test_mask = self.blocks == test_block
            train_mask = ~test_mask
            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]
            yield train_idx, test_idx
    
    def _iter_test_masks(self, X=None, y=None, groups=None):
        for test_block in self.unique_blocks[:self.n_splits]:
            yield self.blocks == test_block

# EJEMPLO DE USO:
# Asignar bloques: 1=Costa Norte, 2=Costa Sur, 3=Sierra, 4=Selva
bloques = np.array([1, 1, 2, 2, 3, 3, 3, 4, 4, 4])  # 10 distritos
cv = SpatialBlockCV(bloques)
# scores = cross_val_score(modelo, X, y, cv=cv)
```

**Moran's I en residuos:**

```python
from esda.moran import Moran
import libpysal

def check_spatial_residuals(y_true, y_pred, coords, k_neighbors=5):
    """
    Verifica autocorrelación espacial en los residuos.
    Si Moran's I es significativo (p<0.05), hay dependencia espacial no modelada.
    """
    residuals = y_true - y_pred
    # Crear pesos espaciales KNN
    w = libpysal.weights.KNN.from_array(coords, k=k_neighbors)
    w.transform = 'r'
    mi = Moran(residuals, w)
    print(f"Moran's I en residuos: {mi.I:.4f} (p={mi.p_sim:.4f})")
    if mi.p_sim < 0.05:
        print("⚠ Dependencia espacial NO modelada. Considerar spatial lag/error.")
    else:
        print("✓ Residuos espacialmente independientes.")
    return mi
```

### 3. SMALL-N ML (n < 50)

Pipeline especializado para datasets pequeños como los 25 departamentos peruanos.

```
REGLAS DE ORO PARA n < 50:
  1. LOOCV (Leave-One-Out) como default — cada muestra es un fold
  2. Ridge/Lasso/ElasticNet en vez de OLS (regularización)
  3. Shapiro-Wilk para verificar normalidad (no asintótica)
  4. Bootstrap (10,000 iteraciones) para intervalos de confianza
  5. Reportar: media ± percentil 2.5-97.5%
  6. Feature selection conservadora: max 3-4 features para n=25
```

```python
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

def small_n_regression(X, y, model_type='ridge', n_bootstrap=10000):
    """Pipeline para n < 50 con bootstrap de intervalos de confianza"""
    models = {
        'ridge': Ridge(alpha=1.0),
        'lasso': Lasso(alpha=0.1),
        'elastic': ElasticNet(alpha=0.1, l1_ratio=0.5),
    }
    model = models[model_type]
    
    # LOOCV + métricas
    loo = LeaveOneOut()
    y_pred_loo = np.zeros(len(y))
    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        model.fit(X_train, y_train)
        y_pred_loo[test_idx] = model.predict(X_test)[0]
    
    r2 = r2_score(y, y_pred_loo)
    rmse = np.sqrt(mean_squared_error(y, y_pred_loo))
    print(f"LOOCV R² = {r2:.3f}, RMSE = {rmse:.3f}")
    
    # Bootstrap de intervalos
    rng = np.random.RandomState(42)
    n = len(y)
    boot_scores = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        idx = rng.choice(n, n, replace=True)
        boot_scores[i] = r2_score(y[idx], y_pred_loo[idx])
    
    ci_low = np.percentile(boot_scores, 2.5)
    ci_high = np.percentile(boot_scores, 97.5)
    print(f"R² bootstrap 95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
    
    return model, y_pred_loo, (ci_low, ci_high)
```

### 4. SHAP + INTERPRETABILIDAD (model explain)

Interpretación completa de modelos con SHAP.

```python
def explain_model(model, X, feature_names=None, sample_size=100):
    """SHAP explanation con resumen ejecutivo"""
    import shap
    
    if feature_names is None:
        feature_names = [f'X{i}' for i in range(X.shape[1])]
    
    # Detectar tipo de modelo
    explainer = shap.TreeExplainer(model)
    
    # Si hay muchas muestras, usar sample
    X_sample = X[:min(sample_size, len(X))]
    shap_values = explainer(X_sample)
    
    # Resumen
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    ranking = np.argsort(mean_abs_shap)[::-1]
    
    print("=== IMPORTANCIA SHAP (top 5) ===")
    for rank, idx in enumerate(ranking[:5], 1):
        print(f"  {rank}. {feature_names[idx]}: {mean_abs_shap[idx]:.4f}")
    
    return shap_values
```

### 5. CLUSTERING + SHAP (cluster explain)

Combina clustering territorial con interpretación por cluster.

```python
def cluster_explain(X, clusters, model, feature_names=None):
    """Interpreta cada cluster: ¿qué variables lo definen?"""
    import shap
    
    if feature_names is None:
        feature_names = [f'X{i}' for i in range(X.shape[1])]
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)
    
    for c in np.unique(clusters):
        mask = clusters == c
        cluster_shap = shap_values.values[mask].mean(axis=0)
        top_idx = np.argsort(np.abs(cluster_shap))[-3:]
        print(f"\nCluster {c} ({mask.sum()} distritos):")
        for idx in top_idx:
            direction = "+" if cluster_shap[idx] > 0 else "-"
            print(f"  {direction} {feature_names[idx]}: {cluster_shap[idx]:.4f}")
```

### 6. SESGOS Y MITIGACIÓN WMD (Weapons of Math Destruction)

Basado en Cathy O'Neil (2016) y la literatura académica (Banka & Zafar 2023 JFE, Chen & Qin 2023 MS, Fuster et al. 2022 JF, Krause & Ruesga 2020 FAccT), los modelos territoriales pueden convertirse en "armas de destrucción matemática" si cumplen 3 criterios: **Opacidad** (caja negra), **Escala** (impacto masivo), **Daño** (perjuicio auto-reforzante).

#### Sesgos documentados en modelos de inclusión financiera territorial

| Sesgo | Evidencia | Cómo se manifiesta | Mitigación |
|-------|-----------|-------------------|------------|
| **Geográfico (redlining)** | Banka & Zafar (2023) JFE | Modelo penaliza distritos remotos (distancia = alto riesgo), excluyendo sistemáticamente zonas rurales | Añadir restricción de equidad geográfica: cuota mínima por región |
| **Urbano-rural** | Chen & Qin (2023) MS | Datos de entrenamiento desbalanceados (más urbanos que rurales) → modelo menos preciso para rurales | Estratificar muestra y evaluar métricas por separado para urbano/rural |
| **Proxy discriminatorio** | Krause & Ruesga (2020) FAccT | Variables como "informalidad", "distancia a capital" o "código postal" discriminan indirectamente | Identificar proxies; no usar ninguna variable sola para decisiones críticas |
| **Confirmación** | Fuster et al. (2022) JF | Si el modelo aprende "rural = no rentable", nunca recomendará aperturas rurales → se auto-confirma | Re-evaluar periódicamente; no usar ausencia histórica como evidencia |
| **Feedback loop negativo** | O'Neil (2016) | Distrito excluido → sin datos → sin inversión → sigue excluido | Re-evaluar cada 2 años; excluir con justificación documentada |

#### Checklist obligatorio antes de desplegar un modelo territorial

```
[ ] 1. TRANSPARENCIA: ?El modelo es explicable? (SHAP, coeficientes Ridge)
[ ] 2. EQUIDAD: ?Se evaluaron métricas separadas por región/cluster?
[ ] 3. PROXIES: ?Hay variables proxy que discriminan indirectamente?
[ ] 4. HUMAN-IN-THE-LOOP: ?Cada decisión automatizada tiene revisión humana?
[ ] 5. RE-EVALUACIÓN: ?Hay un cronograma de re-evaluación periódica?
[ ] 6. VALIDACIÓN EXTERNA: ?El modelo se validó con datos fuera de muestra?
[ ] 7. DOCUMENTACIÓN: ?Cada exclusión tiene justificación documentada?
```

Si falta alguno, el modelo **NO debe desplegarse** como decisión automatizada.

## Referencia rápida

| Tarea | Función/Código |
|---|---|
| Crear bloques geográficos | `SpatialBlockCV(blocks_array)` |
| LOOCV | `LeaveOneOut()` |
| Moran's I | `Moran(residuals, spatial_weights)` |
| SHAP | `TreeExplainer(model)(X)` |
| Bootstrap CI | `np.percentile(boot_scores, [2.5, 97.5])` |
| Small-n regression | `Ridge(alpha=1.0) + LOOCV` |
| Clustering + SHAP | `cluster_explain(X, clusters, model)` |
| Pipeline 3 etapas | `pipeline_3etapas(X, y, coords)` |
| Silhouette score | `silhouette_score(X, labels)` |
| Spatial weights KNN | `libpysal.weights.KNN.from_array(coords, k=5)` |

## Referencias incluidas

| Archivo | Contenido |
|---|---|
| `references/cross-country-financial-inclusion-validation.md` | Validación internacional post-pandemia (India SAE, Turquía ML, Pakistán BLP, Brasil, Colombia, México) |
| `references/sensitivity-stability-analysis.md` | 5 técnicas de estabilidad: seed stability, RF importance, DBSCAN sweep, bootstrap co-clustering, feature ablation |
| `references/clustering-territorial-small-n.md` | Pipeline completo para clustering territorial con n=24 departamentos: feature engineering per cápita, determinación de K, estabilidad 100 seeds, perfiles con z-scores, reporte con diccionario+analogías+auto-auditoría |

## Pitfalls
2. **Verificar balance de bloques antes de Block CV.** Con 25 departamentos peruanos agrupados en 6 bloques, el CV fue 47% — demasiado desbalanceado. LOOCV es más estable.**Nunca usar K-Fold estándar con datos geoespaciales** — viola la independencia por la Ley de Tobler. Siempre usar SpatialBlockCV o LeaveOneOut.
3. **Para n=25 departamentos, LOOCV es el default correcto.** No usar K-Fold con k<25 porque los folds tendrán demasiadas observaciones correlacionadas.
4. **El error de SAE se propaga al ML (~17% de pérdida en R²).** Usar bootstrap anidado (Fase -1C) en lugar de pipeline secuencial ingenuo.
5. **SHAP puede ser lento con muchos árboles y muestras.** Si el dataset es grande (>1,000 filas), usar `shap.sample(X, K=100)` para explicar una muestra representativa.
6. **Double ML requiere datos panel (varios años por ubicación).** Con un solo corte transversal, no es posible. En ese caso, hacer solo análisis de correlación con SHAP.
7. **Clustering con Haversine requiere coordenadas en radianes.** Convertir lat/lon con `np.radians()` antes de K-Means, o usar sklearn `HaversineDistance` con `metric='haversine'` y `algorithm='brute'`.
8. **La distancia de Haversine en K-Means de sklearn requiere `algorithm='brute'`.** El algoritmo 'elkan' no soporta métricas personalizadas.
9. **Bootstrap con n=25 tiene alta varianza.** Los intervalos de confianza serán amplios. No interpretar como significancia estricta sino como rango plausible.
10. **El VIF para n=25 solo debe incluir 3-4 features máximo.** Con más variables, la relación n/p < 5 produce VIF inflados artificialmente.
11. **Moran's I espera pesos espaciales estandarizados** (`w.transform = 'r'`). Sin estandarizar, el estadístico no es comparable entre diferentes tamaños de vecindario.
12. **geopandas puede tener conflictos de dependencias.** Si `import geopandas` falla, instalar con `pip install geopandas` completo (no --no-deps).
13. **Evaluar sesgo geográfico antes de desplegar.** Un modelo que maximiza rentabilidad a corto plazo sin restricción de equidad geográfica es un WMD. Usar checklist de sección 6.
14. **Sesgo de tamaño en datos territoriales.** En datos departamentales peruanos, las variables absolutas (población, PBI, número de cajas, denuncias, efectivos PNP) están dominadas por el tamaño del departamento. Lima/Callao tiene 10× la población del siguiente. Esto produce correlaciones espurias: en el dataset de 24 deptos con 13 vars, **44 de 78 pares (56%) tenían |r| > 0.9** antes de transformar. Siempre calcular la matriz de correlación PRE-feature engineering y transformar variables absolutas a ratios per cápita antes de clusterizar.
15. **Estabilidad de K-Means con n<30.** Con 24 departamentos, K=2 puede tener solo ~60% de pares estables incluso con transformación per cápita. No confiar en una sola corrida. Ejecutar 100 seeds con n_init=1 cada una y reportar matriz de co-ocurrencia. Ver `references/clustering-territorial-small-n.md` para el patrón completo.

### 7. SENSITIVITY & STABILITY ANALYSIS

Después de entrenar cualquier modelo de clustering o clasificación,
**siempre ejecutar análisis de sensibilidad** para medir la estabilidad
de los resultados. Con n < 50 (típico en datos departamentales
peruanos), los resultados puntuales sin intervalos de confianza son
engañosos.

Cinco técnicas clave:

| Técnica | Qué mide |
|---|---|
| K-Means seed stability | ¿Cambia la partición con distinta inicialización? |
| RF importance stability | ¿El ranking de importancia es confiable? |
| DBSCAN parameter sweep | ¿Los outliers son reales o artefacto de eps? |
| Bootstrap co-clustering | ¿Dos dptos caen juntos al remuestrear? |
| Feature ablation | ¿Qué features son realmente necesarias? |

Ver implementación completa en:
`references/sensitivity-stability-analysis.md`

## Output

Siempre guardar:
- `.md` para informe legible con tablas y visualizaciones
- `.txt` para portabilidad
- Datos procesados en `data/` con README por dataset
- Modelos guardados con `joblib.dump()` o `pickle`

## Referencias incluidas

| Archivo | Contenido |
|---|---|
| `references/cross-country-financial-inclusion-validation.md` | Validación internacional post-pandemia (India SAE, Turquía ML, Pakistán BLP, Brasil, Colombia, México) |
