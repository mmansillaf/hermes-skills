"""
Template de evaluación para regresión.
Copia, pega tu data y ajusta.

Uso: python3 scripts/eval_regression.py
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (mean_squared_error, mean_absolute_error, r2_score,
                             explained_variance_score)
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
import warnings
warnings.filterwarnings('ignore')

# ─── CONFIG ──────────────────────────────────────────────────────────────────
DATA_PATH = None  # "data/mi_dataset.csv"
TARGET_COL = None  # "target"
TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 5

ALGORITMOS = {
    "Regresión Lineal (OLS)": LinearRegression(),
    "Ridge (L2)": Ridge(alpha=1.0),
    "Lasso (L1)": Lasso(alpha=0.01, max_iter=10000),
    "Árbol Decisión": DecisionTreeRegressor(random_state=RANDOM_STATE),
    "Random Forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, random_state=RANDOM_STATE),
    "SVR (RBF)": SVR(kernel='rbf'),
}

# ─── CARGA ───────────────────────────────────────────────────────────────────
if DATA_PATH and TARGET_COL:
    print(f"Cargando {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]
    print(f"Shape: {df.shape}, Target: {y.describe()}\n")
else:
    print("⚠️  Usando datos de ejemplo (diabetes). Edita DATA_PATH y TARGET_COL.\n")
    from sklearn.datasets import load_diabetes
    data = load_diabetes()
    X, y = data.data, data.target
    print(f"Dataset: diabetes ({X.shape[0]} muestras, {X.shape[1]} features)")
    print(f"Target: mean={y.mean():.1f}, std={y.std():.1f}\n")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ─── EVALUACIÓN ─────────────────────────────────────────────────────────────
print("=" * 70)
print("Resultados (test set)")
print("=" * 70)

results = []
for nombre, modelo in ALGORITMOS.items():
    modelo.fit(X_train_scaled, y_train)
    y_pred = modelo.predict(X_test_scaled)
    
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    ev = explained_variance_score(y_test, y_pred)
    
    results.append({
        "Modelo": nombre,
        "R²": round(r2, 4),
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4),
        "EV": round(ev, 4),
    })

df_results = pd.DataFrame(results).sort_values("R²", ascending=False)
print(df_results.to_string(index=False))

# CV del mejor modelo
print("\n" + "=" * 70)
print("Cross-validation del mejor modelo")
print("=" * 70)
mejor_nombre = df_results.iloc[0]["Modelo"]
mejor_modelo = ALGORITMOS[mejor_nombre]
cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
scores = cross_val_score(mejor_modelo, X_train_scaled, y_train, cv=cv, scoring='r2')
print(f"  {mejor_nombre}: R² CV mean={scores.mean():.4f} ± {scores.std():.4f}")

print("\n✅ Done.")
