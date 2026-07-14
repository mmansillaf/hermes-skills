# Algorithm Taxonomy — Reference from Local PDFs & Repos

Taxonomía de algoritmos extraída del material local en `/home/usuario/Escritorio/PyCode/UPN/TrabajoInclusionFinaciera/Papers/Statics/`.

## Fuentes principales

| PDF | Capítulos/Secciones relevantes |
|---|---|
| Introduction to ML with Python (O'Reilly) | Ch.2 Supervised Learning (KNN, Linear Models, Naive Bayes, Decision Trees, Ensembles, SVM, Neural Nets) — Ch.3 Unsupervised (PCA, NMF, t-SNE, K-Means, Agglomerative, DBSCAN) |
| Online Statistics Education | Ch.1-5 (Descriptive, Probability, Distributions) — Ch.7 (Normal Distributions) — Ch.12-14 (Correlation, Regression, ANOVA) |
| MACHINE LEARNING(R17A0534) | Decision Trees (ID3, CART), Linear/Logistic Regression, SVM (Linear/Non-linear/Kernel), KNN, K-Means, Random Forest, AdaBoost, EM, Gaussian Mixture Models |

## Algoritmos por familia

### Modelos Geométricos
- K-Nearest Neighbors — distancia euclidiana/manhattan, basado en instancias
- Linear models (Regresión Lineal, Logística, SVM lineal) — hiperplanos de separación
- SVM con kernel — mapas a espacio de alta dimensionalidad

### Modelos Lógicos
- Decision Trees (ID3, CART) — partición booleana del espacio
- Random Forest — ensemble de árboles con bagging
- Rule models — IF-THEN rules

### Modelos Probabilísticos
- Naive Bayes — teorema de Bayes con independencia condicional
- Gaussian Mixture Models — EM algorithm
- Regresión Logística — odds ratios, likelihood

### Modelos de Agrupamiento (No Supervisado)
- K-Means — centroides, minimiza inercia
- DBSCAN — densidad, detecta outliers
- Agglomerative Clustering — jerárquico bottom-up

### Reducción de Dimensionalidad
- PCA — varianza máxima, componentes ortogonales
- NMF — descomposición no negativa (textos/images)
- t-SNE — visualización no lineal (preserva vecindad local)

## Referencia cruzada de repos

| Repo | Cubre | Útil para |
|---|---|---|
| shsarv/Machine-Learning-Projects (26 projects) | CNN, SVM, RF, XGBoost, KNN, ARIMA, Prophet, LSTM, NLP, K-Means | Ejemplos end-to-end con datasets reales |
| vineetjohn/machine-learning-algorithms | Implementaciones from scratch: Linear/Logistic/Bayesian/Regularized regression, KNN, GMM, HMM, Gaussian Processes | Entender matemática interna |
| TannerGilbert/Machine-Learning-Explained | Teoría + código: ML algorithms, ensemble methods, activation functions, optimizers, metrics | Aprendizaje conceptual |
