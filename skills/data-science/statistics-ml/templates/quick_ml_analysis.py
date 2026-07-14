#!/usr/bin/env python3
"""
quick_ml_analysis.py — Template de análisis rápido de ML.

Uso desde el skill:
  1. Copia a tu proyecto
  2. Ajusta CSV_PATH y TARGET_COLUMN
  3. Ejecuta: python quick_ml_analysis.py

Entrena y evalúa automáticamente 5 algoritmos sobre un dataset CSV:
  - Regresión Logística (baseline)
  - Árbol de Decisión
  - Random Forest
  - KNN
  - SVM (RBF kernel)

Requiere: scikit-learn, pandas, numpy, matplotlib
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    f1_score, accuracy_score
)
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════
# CONFIGURACIÓN — AJUSTA ESTO
# ═══════════════════════════════════════════
CSV_PATH = "datos.csv"       # Ruta a tu CSV
TARGET_COLUMN = "target"      # Nombre de la columna objetivo
TEST_SIZE = 0.2               # Proporción test
RANDOM_STATE = 42
# ═══════════════════════════════════════════


def main():
    print("═" * 60)
    print("QUICK ML ANALYSIS")
    print("═" * 60)
    
    # 1. Cargar datos
    print(f"\n📂 Cargando: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"   Shape: {df.shape}")
    print(f"   Columnas: {list(df.columns)}")
    
    # 2. Separar features y target
    y = df[TARGET_COLUMN]
    X = df.drop(columns=[TARGET_COLUMN])
    
    # Codificar target si es texto
    if y.dtype == 'object':
        le = LabelEncoder()
        y = le.fit_transform(y)
        print(f"   Clases: {list(le.classes_)}")
    
    # 3. Detectar columnas no numéricas
    non_numeric = X.select_dtypes(exclude=['int64', 'float64']).columns
    if len(non_numeric) > 0:
        print(f"   ⚠️ Columnas no numéricas detectadas: {list(non_numeric)}")
        print(f"   Se eliminarán. Considera OneHotEncoder para categóricas.")
        X = X.select_dtypes(include=['int64', 'float64'])
    
    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE,
        stratify=y if len(np.unique(y)) <= 10 else None
    )
    print(f"\n📊 Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
    print(f"   Features: {X_train.shape[1]}")
    print(f"   Clases: {len(np.unique(y))}")
    
    # 5. Algoritmos a probar
    models = {
        "LogisticRegression": LogisticRegression(
            max_iter=2000, class_weight='balanced', random_state=RANDOM_STATE
        ),
        "DecisionTree": DecisionTreeClassifier(
            max_depth=5, min_samples_leaf=5, random_state=RANDOM_STATE
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            class_weight='balanced', n_jobs=-1, random_state=RANDOM_STATE
        ),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM_RBF": SVC(
            kernel='rbf', C=1.0, gamma='scale',
            class_weight='balanced', random_state=RANDOM_STATE
        ),
    }
    
    # 6. Evaluar cada uno
    results = []
    is_binary = len(np.unique(y)) == 2
    
    print("\n" + "═" * 60)
    print("RESULTADOS")
    print("═" * 60)
    
    for name, clf in models.items():
        # Pipeline con escalado (KNN y SVM lo necesitan)
        needs_scaler = name in ("KNN", "SVM_RBF", "LogisticRegression")
        
        if needs_scaler:
            pipe = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        else:
            pipe = Pipeline([('clf', clf)])
        
        # CV
        cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring='f1_macro')
        
        # Train final
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='macro')
        
        print(f"\n{'─'*40}")
        print(f"🔹 {name}")
        print(f"{'─'*40}")
        print(f"   CV F1 (macro): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        print(f"   Test Accuracy: {acc:.3f}")
        print(f"   Test F1 (macro): {f1:.3f}")
        
        if is_binary:
            try:
                if hasattr(pipe, 'predict_proba'):
                    y_proba = pipe.predict_proba(X_test)[:, 1]
                    auc = roc_auc_score(y_test, y_proba)
                    print(f"   AUC-ROC: {auc:.3f}")
            except:
                pass
        
        results.append({
            'modelo': name,
            'cv_f1_mean': cv_scores.mean(),
            'cv_f1_std': cv_scores.std(),
            'test_accuracy': acc,
            'test_f1_macro': f1,
        })
    
    # 7. Tabla comparativa
    print("\n" + "═" * 60)
    print("TABLA COMPARATIVA")
    print("═" * 60)
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('test_f1_macro', ascending=False)
    print(df_results.to_string(index=False))
    
    # 8. Recomendación
    print("\n" + "═" * 60)
    best = df_results.iloc[0]
    print(f"✅ MEJOR MODELO: {best['modelo']}")
    print(f"   Test F1: {best['test_f1_macro']:.3f} | CV F1: {best['cv_f1_mean']:.3f}")
    print("═" * 60)


if __name__ == "__main__":
    main()
