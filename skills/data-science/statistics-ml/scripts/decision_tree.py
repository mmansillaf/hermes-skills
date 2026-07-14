"""
Decision tree interactivo para seleccionar algoritmo de ML/estadística.

Uso:
  python3 scripts/decision_tree.py          # modo interactivo
  python3 scripts/decision_tree.py --json   # output JSON para piping
"""
import argparse

def preguntar(msg, opciones):
    while True:
        print(f"\n{msg}")
        for k, v in opciones.items():
            print(f"  [{k}] {v}")
        r = input("> ").strip().lower()
        if r in opciones:
            return r
        print("Opción inválida, elige entre:", ", ".join(opciones.keys()))

def sugerir(tipo, tamaño, n_features, interpretabilidad, balanceado, linealidad, n_clases, n_etalon):
    sugerencias = []
    
    if tipo == "regresion":
        if interpretabilidad == "alta":
            if linealidad == "si":
                sugerencias.append(("Regresión Lineal (OLS)", "statsmodels", "Interpretable, rápido, necesita linealidad + normalidad de residuos"))
            sugerencias.append(("Árbol de Decisión (Regresión)", "sklearn.tree.DecisionTreeRegressor", "Interpretable, captura no-linealidades, propenso a overfitting"))
            if tamaño != "muy_pequeno":
                sugerencias.append(("Random Forest Regressor", "sklearn.ensemble.RandomForestRegressor", "Mejor precisión que árbol simple, menos interpretable"))
        else:
            sugerencias.append(("Random Forest Regressor", "sklearn.ensemble.RandomForestRegressor", "Default sólido para regresión"))
            if tamaño != "pequeno" and tamaño != "muy_pequeno":
                sugerencias.append(("XGBoost Regressor", "xgboost.XGBRegressor", "State-of-the-art en tabular, requiere tuning"))
            sugerencias.append(("SVR (RBF kernel)", "sklearn.svm.SVR", "Bueno con no-linealidad, sensible a escala"))
    
    elif tipo == "clasificacion":
        if n_clases == 2:
            if interpretabilidad == "alta":
                if n_etalon < 10:
                    sugerencias.append(("Regresión Logística", "sklearn.linear_model.LogisticRegression", "Interpretable, probabilidades calibradas, necesita features escalados"))
                sugerencias.append(("Árbol de Decisión", "sklearn.tree.DecisionTreeClassifier", "Totalmente interpretable, overfittea fácil"))
                if tamaño != "muy_pequeno":
                    sugerencias.append(("Random Forest", "sklearn.ensemble.RandomForestClassifier", "Mejor precisión, feature importance disponible"))
            else:
                if tamaño != "pequeno" and tamaño != "muy_pequeno":
                    sugerencias.append(("XGBoost / LightGBM", "xgboost.XGBClassifier / lightgbm.LGBMClassifier", "State-of-the-art, requiere tuning"))
                elif tamaño == "pequeno" or tamaño == "muy_pequeno":
                    sugerencias.append(("SVM (RBF kernel)", "sklearn.svm.SVC", "Bueno con pocos datos y muchas features"))
                sugerencias.append(("Random Forest", "sklearn.ensemble.RandomForestClassifier", "Sólido default, poco tuning necesario"))
                if not balanceado:
                    sugerencias.append(("⚠️ Datos desbalanceados → usa class_weight='balanced' o SMOTE"))
        else:
            sugerencias.append(("Random Forest / XGBoost", "multiclase", "Default para clasificación multiclase"))
            if interpretabilidad == "alta":
                sugerencias.append(("Regresión Logística (OvR)", "sklearn.linear_model.LogisticRegression(multi_class='ovr')", "Interpretable, funciona bien con features linearmente separables"))
            sugerencias.append(("KNN", "sklearn.neighbors.KNeighborsClassifier", "Simple, funciona si datos locales son informativos, sensible a escala"))
    
    elif tipo == "clustering":
        if n_clusters is not None:
            sugerencias.append(("K-Means", "sklearn.cluster.KMeans", "Rápido, requiere definir K, asume clusters esféricos"))
        else:
            sugerencias.append(("DBSCAN", "sklearn.cluster.DBSCAN", "No requiere K, detecta outliers, funciona con clusters de forma arbitraria"))
            sugerencias.append(("HDBSCAN", "hdbscan.HDBSCAN", "Mejora DBSCAN, clustering jerárquico"))
        if n_features <= 50:
            sugerencias.append(("Agglomerative Clustering", "sklearn.cluster.AgglomerativeClustering", "Jerárquico, útil para dendrogramas"))
    
    elif tipo == "reduccion":
        sugerencias.append(("PCA", "sklearn.decomposition.PCA", "Reducción lineal, máxima varianza, útil para visualización 2D/3D"))
        if interpretabilidad == "baja":
            sugerencias.append(("t-SNE", "sklearn.manifold.TSNE", "Visualización no-lineal, preserva estructura local, NO para inferencia"))
            sugerencias.append(("UMAP", "umap.UMAP", "Alternativa moderna a t-SNE, más rápido"))
        sugerencias.append(("PCA con estandarización", "", "Siempre estandarizar (StandardScaler) antes de PCA"))
    
    return sugerencias


def main():
    parser = argparse.ArgumentParser(description="Árbol de decisión para selección de algoritmo ML")
    parser.add_argument("--json", action="store_true", help="Output en JSON")
    args = parser.parse_args()
    
    if not args.json:
        print("=" * 60)
        print("  ÁRBOL DE DECISIÓN - ALGORITMOS DE ML")
        print("  Responde y te sugiero qué algoritmo usar")
        print("=" * 60)
    
    tipo = preguntar("¿Tipo de problema?", {
        "1": "Regresión (predecir valor numérico continuo)",
        "2": "Clasificación (predecir categoría/clase)",
        "3": "Clustering (agrupar datos sin etiquetas)",
        "4": "Reducción de dimensionalidad / Visualización"
    })
    map_tipo = {"1": "regresion", "2": "clasificacion", "3": "clustering", "4": "reduccion"}
    tipo = map_tipo[tipo]
    
    tamaño = preguntar("¿Tamaño del dataset?", {
        "1": "Muy pequeño (< 100 muestras)",
        "2": "Pequeño (100 - 1,000)",
        "3": "Mediano (1,000 - 50,000)",
        "4": "Grande (> 50,000)"
    })
    map_tamaño = {"1": "muy_pequeno", "2": "pequeno", "3": "mediano", "4": "grande"}
    tamaño = map_tamaño[tamaño]
    
    n_features = int(preguntar("¿Número aproximado de features (columnas)?", {
        "1": "< 10",
        "2": "10 - 100",
        "3": "100 - 1,000",
        "4": "> 1,000 (alta dimensionalidad)"
    }))
    map_features = {"1": 5, "2": 50, "3": 500, "4": 5000}
    n_features = map_features[n_features]
    
    interp = preguntar("¿Necesitas interpretabilidad (entender por qué el modelo decide)?", {
        "1": "Sí, alta (debo explicar cada predicción)",
        "2": "Media (importancia de features basta)",
        "3": "No, solo me importa la precisión"
    })
    map_interp = {"1": "alta", "2": "media", "3": "baja"}
    interp = map_interp[interp]
    
    # Preguntas específicas según tipo
    balanceado = True
    linealidad = None
    n_clases = None
    n_clusters = None
    
    if tipo in ("regresion", "clasificacion"):
        linealidad = preguntar("¿Relación features-target aproximadamente lineal?", {
            "1": "Sí, lineal",
            "2": "No sé / posiblemente no lineal"
        })
        map_linealidad = {"1": "si", "2": "no"}
        linealidad = map_linealidad[linealidad]
    
    if tipo == "clasificacion":
        n_clases = int(preguntar("¿Es clasificación binaria o multiclase?", {
            "2": "Binaria (2 clases)",
            "3": "Multiclase (3+ clases)"
        }))
        balanceado = preguntar("¿Clases balanceadas?", {
            "1": "Sí, aproximadamente iguales",
            "2": "No, hay clases muy minoritarias"
        })
        balanceado = balanceado == "1"
    
    if tipo == "clustering":
        tiene_k = preguntar("¿Sabes cuántos clusters esperas?", {
            "1": "Sí, tengo una idea del número",
            "2": "No, quiero que el algoritmo lo determine"
        })
        if tiene_k == "1":
            n_clusters = int(input("  Número estimado de clusters: "))
        else:
            n_clusters = None
    
    # Generar sugerencias
    sugerencias = sugerir(tipo, tamaño, n_features, interp, balanceado, linealidad, n_clases, n_clusters if tipo == "clustering" else None)
    
    if args.json:
        import json
        print(json.dumps({"tipo": tipo, "sugerencias": [{"algoritmo": s[0], "libreria": s[1], "nota": s[2]} for s in sugerencias]}, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 60)
        print("  🎯 ALGORITMOS SUGERIDOS")
        print("=" * 60)
        for i, (algo, lib, nota) in enumerate(sugerencias, 1):
            print(f"\n  {i}. {algo}")
            print(f"     Librería: {lib}")
            print(f"     Nota: {nota}")


if __name__ == "__main__":
    main()
