"""
Template de evaluación para clasificación.
Copia, pega tu data y ajusta.

Uso: python3 scripts/eval_classification.py
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, classification_report,
                             roc_curve)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
import warnings
warnings.filterwarnings('ignore')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
# Pega tu ruta CSV aquí:
DATA_PATH = None  # ej: "data/mi_dataset.csv"
TARGET_COL = None  # ej: "target"
TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 5

# Algoritmos a evaluar (activa/desactiva según necesites)
ALGORITMOS = {
    "Regresión Logística": LogisticRegression(max_iter=1000, class_weight='balanced'),
    "Árbol Decisión": DecisionTreeClassifier(random_state=RANDOM_STATE, class_weight='balanced'),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, class_weight='balanced'),
    "SVM (RBF)": SVC(kernel='rbf', probability=True, class_weight='balanced'),
    "KNN": KNeighborsClassifier(n_neighbors=5),
}

# ─── CARGA ───────────────────────────────────────────────────────────────────
if DATA_PATH and TARGET_COL:
    print(f"Cargando {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"Shape: {df.shape}")
    print(f"Clases:\n{df[TARGET_COL].value_counts()}\n")

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # Codificar target si es texto
    if y.dtype == 'object':
        le = LabelEncoder()
        y = le.fit_transform(y)
        print("Clases:", dict(zip(le.classes_, le.transform(le.classes_))))

    # Separar numéricas para escalado
    num_cols = X.select_dtypes(include=[np.number]).columns
    cat_cols = X.select_dtypes(include=['object']).columns

    if len(cat_cols) > 0:
        print(f"Columnas categóricas detectadas: {list(cat_cols)} → aplicando one-hot")
        X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Escalar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
else:
    # ─── DATOS DE EJEMPLO ───────────────────────────────────────────────────
    print("⚠️  Usando datos de ejemplo (Iris). Edita DATA_PATH y TARGET_COL para usar tus datos.\n")
    from sklearn.datasets import load_iris, load_breast_cancer
    
    data = load_breast_cancer()
    X, y = data.data, data.target
    print(f"Dataset: breast_cancer ({X.shape[0]} muestras, {X.shape[1]} features)")
    print(f"Clases: {dict(zip(range(2), data.target_names))}\n")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

# ─── EVALUACIÓN ──────────────────────────────────────────────────────────────
print("=" * 70)
print("Resultados (test set)")
print("=" * 70)

results = []
for nombre, modelo in ALGORITMOS.items():
    modelo.fit(X_train_scaled, y_train)
    y_pred = modelo.predict(X_test_scaled)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    # AUC (solo binaria)
    auc = None
    if len(np.unique(y)) == 2 and hasattr(modelo, "predict_proba"):
        y_prob = modelo.predict_proba(X_test_scaled)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
    
    results.append({
        "Modelo": nombre,
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1": round(f1, 4),
        "AUC": round(auc, 4) if auc else "-",
    })

df_results = pd.DataFrame(results).sort_values("F1", ascending=False)
print(df_results.to_string(index=False))

# ─── MEJOR MODELO ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("Cross-validation (Stratified K-Fold) del mejor modelo")
print("=" * 70)

if len(ALGORITMOS) > 0:
    mejor_nombre = df_results.iloc[0]["Modelo"]
    mejor_modelo = ALGORITMOS[mejor_nombre]
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(mejor_modelo, X_train_scaled, y_train, cv=cv, scoring='f1_weighted')
    print(f"  {mejor_nombre}: F1 mean={scores.mean():.4f} ± {scores.std():.4f}")

print("\n✅ Done. Edita DATA_PATH y TARGET_COL para usar tus datos.")
