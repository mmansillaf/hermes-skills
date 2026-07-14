---
name: statistics-ml
description: "Guía práctica de estadística y machine learning clásico: regresión lineal, logística, árboles, random forest, KNN, SVM, K-Means, PCA, Naive Bayes. Incluye árbol de decisión algorítmica, preprocesamiento, métricas de evaluación y templates reutilizables en sklearn/statsmodels."
tags:
  - estadistica
  - machine-learning
  - sklearn
  - regresion
  - clasificacion
  - clustering
  - pca
  - python
  - data-science
---

# Statistics & ML — Guía Práctica

Skill para manejar, evaluar, discernir y desarrollar problemas de estadística y machine learning clásico. Orientado a producción y análisis, no a teoría pura.

---

## 1. Árbol de Decisión — ¿Qué algoritmo usar?

### ¿Tienes datos etiquetados (variable objetivo)?

**SÍ → Supervisado**

| Si tu objetivo es... | Prueba con... |
|---|---|
| Predecir un **número** (precio, temperatura, score) | **Regresión Lineal** (relación lineal) → **Random Forest Regressor / XGBoost** (relaciones no lineales) |
| Predecir una **categoría binaria** (sí/no, fraude/no fraude) | **Regresión Logística** (interpretable, baseline) → **SVM** (márgenes claros) → **Random Forest** (no lineal) |
| Predecir **múltiples categorías** (tipo de documento, clase de norma) | **Random Forest / XGBoost** → **KNN** (pocos features, dataset chico) |
| Datos con **ruido o outliers** | **Árboles de Decisión / Random Forest** (robustos a outliers) |
| Necesitas **interpretabilidad** (explicar predicciones) | **Regresión Lineal / Logística** → **Árbol de Decisión** (reglas visibles) |
| Pocos datos (< 1000 muestras) | **Regresión Lineal / KNN / Naive Bayes** (evitar deep learning) |
| Muchos features (> columnas que filas) | **Regresión Regularizada (Ridge/Lasso)** → **PCA + clasificador** |

**NO → No Supervisado**

| Si quieres... | Prueba con... |
|---|---|
| Agrupar datos similares sin etiquetas | **K-Means** (rápido, clusters esféricos) → **DBSCAN** (clusters irregulares, detecta outliers) |
| Reducir dimensionalidad (muchas columnas) | **PCA** (lineal, preserva varianza) → **t-SNE / UMAP** (visualización) |
| Encontrar patrones en texto/documentos | **NMF / LDA** (topic modeling) |
| Detectar anomalías/outliers | **Isolation Forest** → **DBSCAN** → **One-Class SVM** |

### Consideraciones previas:

1. **Escalar los datos**: SVM, KNN, K-Means, PCA, Regresión Lineal REQUIEREN escalado. Árboles/Random Forest NO.
2. **Balance de clases**: En clasificación con clases desbalanceadas, usar **class_weight='balanced'** o **SMOTE** (imbalanced-learn).
3. **Data Leakage**: NO escalar/transformar antes del split train/test. Usar Pipeline de sklearn.
4. **Overfitting**: Validación cruzada (cross_val_score), regularización (Ridge/Lasso para regresión), poda para árboles.

---

## 2. Fichas Técnicas por Algoritmo

### 2.1 Regresión Lineal
- **Tipo**: Supervisado — Regresión
- **Cuándo usarlo**: Relación aproximadamente lineal entre features y target. Baseline obligatorio.
- **Cuándo NO**: Relaciones no lineales, muchas features correlacionadas entre sí (multicolinealidad), outliers fuertes.
- **Preprocesamiento**: Escalar (StandardScaler), detectar y tratar multicolinealidad (VIF), evaluar residuos (deben ser normales y homocedásticos).
- **Hiperparámetros clave**: `fit_intercept`, `normalize` (deprecated, usar Pipeline en su lugar).
- **Variantes**: Ridge (L2), Lasso (L1), ElasticNet (L1+L2) — para regularización.
- **Métricas**: R², RMSE, MAE, MAPE.
- **Código mínimo**:
  ```python
  from sklearn.linear_model import LinearRegression
  from sklearn.pipeline import Pipeline
  from sklearn.preprocessing import StandardScaler
  
  model = Pipeline([
      ('scaler', StandardScaler()),
      ('reg', LinearRegression())
  ])
  model.fit(X_train, y_train)
  y_pred = model.predict(X_test)
  ```

### 2.2 Regresión Logística
- **Tipo**: Supervisado — Clasificación binaria (extensible a multiclase)
- **Cuándo usarlo**: Clasificación binaria interpretable, baseline para problemas de clasificación, probabilidades calibradas.
- **Cuándo NO**: Relaciones no lineales complejas sin ingeniería de features, muchas categorías (>100).
- **Preprocesamiento**: Escalar features (obligatorio), one-hot encoding para categóricas.
- **Hiperparámetros clave**: `C` (inverso de regularización — menor C = más regularización), `penalty='l2'/'l1'/'elasticnet'`, `class_weight='balanced'`.
- **Métricas**: Accuracy, Precision, Recall, F1-score, AUC-ROC, Matriz de Confusión.
- **Código mínimo**:
  ```python
  from sklearn.linear_model import LogisticRegression
  from sklearn.metrics import classification_report, ConfusionMatrixDisplay
  
  model = LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000)
  model.fit(X_train, y_train)
  y_pred = model.predict(X_test)
  print(classification_report(y_test, y_pred))
  ConfusionMatrixDisplay.from_estimator(model, X_test, y_test)
  ```

### 2.3 Árboles de Decisión
- **Tipo**: Supervisado — Clasificación y Regresión
- **Cuándo usarlo**: Necesitas interpretabilidad (reglas visibles), datos con relaciones no lineales, features mixtas (numéricas + categóricas sin escalar).
- **Cuándo NO**: Datos muy grandes (>100K filas), necesitas alta precisión sin ensemble (los árboles solos overfitean), muchas features ruidosas.
- **Preprocesamiento**: NO requiere escalado ni normalización. Maneja outliers bien.
- **Hiperparámetros clave**: `max_depth` (controla overfitting — empezar con 3-5), `min_samples_split`, `min_samples_leaf`, `max_features`.
- **Métricas**: Accuracy/F1 (clasificación), RMSE/R² (regresión), importance de features.
- **Código mínimo**:
  ```python
  from sklearn.tree import DecisionTreeClassifier, plot_tree
  
  model = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10)
  model.fit(X_train, y_train)
  # Ver reglas
  plot_tree(model, feature_names=feature_names, class_names=classes, filled=True)
  # Importancia de features
  for name, imp in zip(feature_names, model.feature_importances_):
      print(f"{name}: {imp:.3f}")
  ```

### 2.4 Random Forest
- **Tipo**: Supervisado — Clasificación y Regresión (Ensemble)
- **Cuándo usarlo**: Problema complejo sin mucha tuning, mejor accuracy que árbol simple, robusto a overfitting, feature importance confiable.
- **Cuándo NO**: Necesitas explicar predicción individual (no es interpretable como un árbol), datasets muy grandes (>100K × >100 features → es lento), datos con clases extremadamente desbalanceadas.
- **Preprocesamiento**: NO requiere escalado. Maneja missing values (con `SimpleImputer` primero).
- **Hiperparámetros clave**: `n_estimators` (100-1000 — más árboles = mejor pero más lento), `max_depth` (None = hojas puras → puede overfitean), `min_samples_leaf`, `max_features='sqrt'` (clasificación) / `'log2'` (regresión).
- **Métricas**: OOB Score (error out-of-bag — no necesita test set extra), feature importance.
- **Código mínimo**:
  ```python
  from sklearn.ensemble import RandomForestClassifier
  
  model = RandomForestClassifier(n_estimators=200, max_depth=10, 
                                  min_samples_leaf=5, oob_score=True,
                                  class_weight='balanced', n_jobs=-1)
  model.fit(X_train, y_train)
  print(f"OOB Score: {model.oob_score_:.3f}")
  # Top features
  importances = sorted(zip(feature_names, model.feature_importances_), 
                       key=lambda x: x[1], reverse=True)[:10]
  ```

### 2.5 K-Nearest Neighbors (KNN)
- **Tipo**: Supervisado — Clasificación y Regresión (no paramétrico)
- **Cuándo usarlo**: Dataset pequeño (<10K), fronteras de decisión no lineales, baseline simple, problema donde la similitud local importa.
- **Cuándo NO**: Dataset grande (es lento en inferencia — calcula distancia con TODOS los puntos), muchas features (>20 sin PCA),features en diferentes escalas.
- **Preprocesamiento**: **OBLIGATORIO** escalar (StandardScaler o MinMaxScaler). PCA para reducir dimensionalidad. Balancear clases.
- **Hiperparámetros clave**: `n_neighbors` (3-15 — probar con grid), `weights='uniform'/'distance'`, `metric='euclidean'/'manhattan'/'cosine'`.
- **Métricas**: Accuracy/F1 (clasificación), RMSE (regresión).
- **Código mínimo**:
  ```python
  from sklearn.neighbors import KNeighborsClassifier
  from sklearn.model_selection import GridSearchCV
  
  params = {'n_neighbors': [3, 5, 7, 9, 11], 'weights': ['uniform', 'distance']}
  grid = GridSearchCV(KNeighborsClassifier(), params, cv=5)
  grid.fit(X_train_scaled, y_train)
  print(f"Best k={grid.best_params_['n_neighbors']}")
  ```

### 2.6 Support Vector Machines (SVM)
- **Tipo**: Supervisado — Clasificación (SVC) y Regresión (SVR)
- **Cuándo usarlo**: Dataset mediano (<50K), fronteras de decisión claras, alta dimensionalidad (funciona bien con muchos features), problemas donde el margen entre clases es importante.
- **Cuándo NO**: Dataset grande (escala O(n²) o peor), muchas clases, necesitas probabilidades calibradas (con `probability=True` es aún más lento), features sin escalar.
- **Preprocesamiento**: **OBLIGATORIO** escalar (StandardScaler). Datos limpios, sin outliers extremos.
- **Hiperparámetros clave**: `C` (trade-off margen vs error de clasificación — alto = margen estrecho), `kernel='rbf'/'linear'/'poly'/'sigmoid'`, `gamma` (para RBF/poly — controla influencia de un solo ejemplo).
- **Métricas**: Accuracy/F1, Matriz de Confusión.
- **⚠️ Pitfall**: SVM con kernel RBF tiene 3 hiperparámetros (C, gamma, kernel) que interactúan — siempre usar GridSearchCV.
- **Código mínimo**:
  ```python
  from sklearn.svm import SVC
  from sklearn.model_selection import GridSearchCV
  
  params = {'C': [0.1, 1, 10, 100], 'gamma': ['scale', 'auto', 0.01, 0.001]}
  grid = GridSearchCV(SVC(kernel='rbf', class_weight='balanced'), params, cv=5)
  grid.fit(X_train_scaled, y_train)
  print(f"Best: {grid.best_params_}")
  ```

### 2.7 K-Means
- **Tipo**: No Supervisado — Clustering
- **Cuándo usarlo**: Agrupar datos sin etiquetas, segmentación de clientes, compresión de imágenes, pre-procesamiento para reducir datos.
- **Cuándo NO**: Clusters no esféricos (forma de media luna, anidados), datos con outliers fuertes, dimensiones muy altas sin reducir primero, no sabes cuántos clusters esperar.
- **Preprocesamiento**: **OBLIGATORIO** escalar (StandardScaler). PCA para visualizar clusters en 2D.
- **Hiperparámetros clave**: `n_clusters` (el más importante — usar codo o silhouette score), `init='k-means++'` (default, recomendado), `n_init=10`.
- **Métricas**: Inertia (suma de distancias intra-cluster — decrece con más clusters), Silhouette Score (mejor cerca de 1), Davies-Bouldin Index.
- **Determinar K**:
  ```python
  from sklearn.cluster import KMeans
  from sklearn.metrics import silhouette_score
  
  inertias, sil_scores = [], []
  K_range = range(2, 11)
  for k in K_range:
      km = KMeans(n_clusters=k, random_state=42, n_init=10)
      labels = km.fit_predict(X_scaled)
      inertias.append(km.inertia_)
      sil_scores.append(silhouette_score(X_scaled, labels))
  # Elegir k donde inertia baja marcadamente o silhouette es máximo
  ```

### 2.8 PCA (Principal Component Analysis)
- **Tipo**: No Supervisado — Reducción de Dimensionalidad
- **Cuándo usarlo**: Demasiadas features (>20), visualizar datos de alta dimensionalidad en 2D/3D, eliminar ruido, preprocesar para otros algoritmos (especialmente KNN, SVM).
- **Cuándo NO**: Datos con estructura no lineal (usar t-SNE o UMAP), necesitas interpretar componentes (los componentes son combinaciones lineales abstractas), features con escalas muy diferentes sin escalar.
- **Preprocesamiento**: **OBLIGATORIO** escalar (StandardScaler — fundamental, si no PCA se sesga por la escala de cada feature).
- **Hiperparámetros clave**: `n_components` (número de componentes, o fracción de varianza explicada como `0.95`), `whiten=True` (útil si luego usas algoritmos que asumen varianza unitaria).
- **Métricas**: Varianza explicada acumulada (curva scree), ratio de varianza por componente.
- **Código mínimo**:
  ```python
  from sklearn.decomposition import PCA
  
  pca = PCA(n_components=0.95)  # mantener 95% de varianza
  X_pca = pca.fit_transform(X_scaled)
  print(f"Dimensiones originales: {X_scaled.shape[1]}")
  print(f"Dimensiones reducidas: {X_pca.shape[1]}")
  print(f"Varianza explicada: {sum(pca.explained_variance_ratio_):.3f}")
  ```

---

## 3. Evaluación — Tabla Rápida

| Problema | Clasificación | Regresión | Clustering |
|---|---|---|---|
| **Métrica principal** | Accuracy, F1 (si desbalanceado) | RMSE, MAE, R² | Silhouette Score, Inertia |
| **Validación** | StratifiedKFold | KFold | No hay ground truth — usar criterios internos |
| **Overfitting** | Train vs Test gap | Train vs Test gap | Más clusters = menos error aparente |
| **Feature importance** | RandomForest, PermutationImportance | Coeficientes (lineal), RF | PCA loadings |

### ¿Qué test estadístico según el caso?

| Pregunta | Test |
|---|---|
| ¿Dos grupos tienen medias diferentes? | t-test (2 grupos), ANOVA (>2 grupos) |
| ¿Hay relación entre dos variables numéricas? | Correlación Pearson / Spearman |
| ¿Una variable categórica afecta a una numérica? | ANOVA o Kruskal-Wallis (no paramétrico) |
| ¿La distribución observada difiere de la esperada? | Chi-cuadrado |
| ¿Los residuos del modelo son normales? | Shapiro-Wilk o QQ-plot |

---

## 4. Pipeline Mínimo para Producción

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import pandas as pd

# 1. Cargar
df = pd.read_csv('datos.csv')
X = df.drop('target', axis=1)
y = df['target']

# 2. Split ANTES de cualquier transformación
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. Preprocesamiento
num_features = X.select_dtypes(include=['int64', 'float64']).columns
cat_features = X.select_dtypes(include=['object', 'category']).columns

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), num_features),
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
])

# 4. Modelo
model = Pipeline([
    ('prep', preprocessor),
    ('clf', RandomForestClassifier(
        n_estimators=200, max_depth=10, 
        class_weight='balanced', n_jobs=-1
    ))
])

# 5. Evaluación
scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1_macro')
print(f"CV F1: {scores.mean():.3f} ± {scores.std():.3f}")

model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
```

---

## 5. Pitfalls Comunes

- ❌ **Escalar después del split** — Siempre fit en train, transform en train+test.
- ❌ **Usar accuracy con clases desbalanceadas** — Usar F1, Precision-Recall, o AUC-ROC.
- ❌ **Ignorar multicolinealidad en regresión lineal** — Coeficientes se vuelven inestables.
- ❌ **Asumir normalidad sin verificar** — No todos los tests/métodos lo requieren.
- ❌ **Sobre-interpretar p-valores** — Con muestras grandes, cualquier diferencia mínima es "significativa".
- ❌ **No setear random_state** — Resultados no reproducibles.
- ❌ **Olvidar que PCA es lineal** — Si los datos tienen estructura no lineal, PCA captura poco.

---

## 6. Auditoría de Proyectos ML: Documento vs Datos

Cuando un proyecto ML tiene dos artefactos — un **documento de metodología** (Word/PDF) y una **base de datos** (Excel/CSV) — audita la consistencia entre ellos antes de modelar.

### Checklist

| # | Qué verificar | Cómo detectarlo |
|---|---|---|
| 1 | **Variables derivadas prometidas pero no implementadas** | El doc lista ratios/features calculados que **no existen** en el Excel |
| 2 | **Conteo de observaciones inconsistente** | El doc dice "N registros" pero el Excel tiene más/menos filas |
| 3 | **Multicolinealidad no cuantificada** | Variables absolutas con r > 0.90 entre sí (población ↔ líneas móviles, PEA ↔ población). Verificar con matriz de correlación. |
| 4 | **Outlier crítico no tratado** | El doc menciona "se revisará" sin especificar acción concreta. Detectar con IQR method. |
| 5 | **Métrica de evaluación incorrecta o incompleta** | Clasificación supervisada → F1, AUC-ROC. Clustering → Silhouette, Davies-Bouldin, Inertia. NO mezclar. |
| 6 | **Múltiples estados de limpieza** | Data Inicial (cruda) vs Data Final (limpia). Verificar a qué hoja se refiere el doc. |

### Procedimiento

```
1. Extraer TODAS las variables y transformaciones del documento
2. Listar TODAS las columnas reales del Excel (cada hoja)
3. Cruzar: cada variable prometida ¿existe? cada variable real ¿se usa?
4. Calcular correlaciones entre variables absolutas
5. Identificar outliers por variable (IQR)
6. Confirmar que el conteo de observaciones coincide
7. Verificar que métricas corresponden al tipo de modelo
```

### ⚠️ Pitfall: Feature engineering en el doc, raw data en el Excel

El proyecto describe ratios y transformaciones sofisticadas pero esas columnas no existen en los datos. El modelo se entrenaría con variables incorrectas. La auditoría debe detectar esto antes de modelar.

### ⚠️ Pitfall: No confundir listas ilustrativas con variables afirmadas

Cuando el documento usa frases como *"Entre estas variables **pueden considerarse**..."* o *"tales como..."* o *"por ejemplo..."*, se trata de una **lista ilustrativa de variables potenciales**, no una afirmación de que esas columnas existan en la base de datos. Marcar esto como inconsistencia es un falso positivo que desvía la auditoría. Para detectar una verdadera inconsistencia, buscar afirmaciones en presente o futuro concreto: *"la base contiene..."*, *"se trabajará con..."*, *"las variables seleccionadas son..."*.

### ⚠️ Pitfall: IQR oculta outliers dominantes

Si una observación (ej. Lima/Callao) es 10-30x el promedio en TODAS las variables, el IQR estándar lo subestima porque el propio outlier infla Q3 y el IQR. Usar **comparación con la media del resto** (ratio de dominancia):

```
dom_val = df.loc[mask_dominante, col].values[0]
resto_mean = df.loc[~mask_dominante, col].mean()
ratio = dom_val / resto_mean  # > 5x = dominio extremo

Si la observación dominante es 10-30x el promedio del resto en TODAS las variables, indica que el modelo clusterizará alrededor de ella. Soluciones: (a) eliminar temporalmente la observación y modelar el resto, (b) winsorizar (capar) los valores extremos, o (c) usar variables relativas (ratios) que atenúan el efecto del tamaño.
```

### Deliverables de la auditoría

Cuando se complete, entregar:

1. **Informe en .md** (markdown con tablas)
2. **Informe en .txt** (texto plano, ancho fijo)
3. **Documento Word auditado** (.docx con sufijo "- AUDITADO") con observaciones intercaladas en color:
   - 🔴 Rojo = Crítico · 🟠 Naranja = Alto · 🔵 Azul = Mejora · 🟢 Verde = Bien

No modificar el original. El Word auditado es copia con anotaciones.

Ver: `references/project-audit-checklist.md`

---

## 7. Scripts Ejecutables

El skill incluye scripts reutilizables en `scripts/`:

| Script | Descripción | Uso |
|---|---|---|
| `scripts/decision_tree.py` | CLI interactivo: responde preguntas sobre tu problema y sugiere el mejor algoritmo | `python3 <path>/scripts/decision_tree.py` |
| `scripts/eval_classification.py` | Template completo: entrena y evalúa 5 clasificadores (RegLog, DT, RF, SVM, KNN) con métricas + CV | `python3 <path>/scripts/eval_classification.py` |
| `scripts/eval_regression.py` | Template: evalúa 7 regresores (OLS, Ridge, Lasso, DT, RF, GB, SVR) | `python3 <path>/scripts/eval_regression.py` |
| `scripts/eval_clustering.py` | Template: K-Means, DBSCAN, Agglomerative, GMM + PCA + t-SNE con métricas | `python3 <path>/scripts/eval_clustering.py` |

Encuentra la ruta del skill con: `skill_view('statistics-ml')` y busca `skill_dir` en el output.

---

## Referencias Locales

Los siguientes PDFs están en `/home/usuario/Escritorio/PyCode/UPN/TrabajoInclusionFinaciera/Papers/Statics/`:

- `Introduction to Machine Learning with Python ( PDFDrive.com )-min.pdf` — sklearn práctico, todos los algoritmos clásicos
- `MachineLearningTomMitchell.pdf` — Tom Mitchell. Teoría clásica de ML
- `Online_Statistics_Education.pdf` — Curso completo de estadística (190+ entradas de TOC)
- `all-of-statistics.pdf` — Wasserman. Estadística teórica avanzada
- `Basic statistics_ Dr J ANITHA.pdf` — Estadística descriptiva básica
- `MACHINE LEARNING(R17A0534).pdf` — Apuntes de ML con temario completo

Repos de referencia explorados:
- github.com/shsarv/Machine-Learning-Projects — 26 proyectos end-to-end
- github.com/TannerGilbert/Machine-Learning-Explained — teoría + código
- github.com/vineetjohn/machine-learning-algorithms — implementaciones from scratch
