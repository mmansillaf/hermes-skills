"""
Template de clustering y reducción de dimensionalidad.
Uso: python3 scripts/eval_clustering.py
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import warnings
warnings.filterwarnings('ignore')

# ─── CONFIG ──────────────────────────────────────────────────────────────────
DATA_PATH = None  # "data/mi_dataset.csv"
RANDOM_STATE = 42
N_CLUSTERS = 3  # Ajusta según tu problema

# ─── CARGA ───────────────────────────────────────────────────────────────────
if DATA_PATH:
    print(f"Cargando {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    X = df.select_dtypes(include=[np.number]).dropna()
    print(f"Shape: {X.shape}")
else:
    print("⚠️  Usando datos de ejemplo (blobs). Edita DATA_PATH.\n")
    from sklearn.datasets import make_blobs
    X, _ = make_blobs(n_samples=500, n_features=5, centers=4, random_state=RANDOM_STATE)
    N_CLUSTERS = 4
    print(f"Dataset sintético: {X.shape[0]} muestras, {X.shape[1]} features, {N_CLUSTERS} centros\n")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ─── CLUSTERING ──────────────────────────────────────────────────────────────
print("=" * 70)
print("Evaluación de Clustering")
print("=" * 70)

algoritmos = {
    "K-Means (K={})".format(N_CLUSTERS): KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10),
    "Agglomerative (K={})".format(N_CLUSTERS): AgglomerativeClustering(n_clusters=N_CLUSTERS),
    "DBSCAN (eps=0.5)": DBSCAN(eps=0.5, min_samples=5),
    "Gaussian Mixture (K={})".format(N_CLUSTERS): GaussianMixture(n_components=N_CLUSTERS, random_state=RANDOM_STATE),
}

results = []
for nombre, modelo in algoritmos.items():
    labels = modelo.fit_predict(X_scaled)
    n_clusters_found = len(set(labels) - {-1})
    n_noise = list(labels).count(-1)
    
    sil = silhouette_score(X_scaled, labels) if n_clusters_found > 1 else None
    db = davies_bouldin_score(X_scaled, labels) if n_clusters_found > 1 else None
    ch = calinski_harabasz_score(X_scaled, labels) if n_clusters_found > 1 else None
    
    results.append({
        "Algoritmo": nombre,
        "Clusters": n_clusters_found,
        "Ruido": n_noise,
        "Silhouette": round(sil, 4) if sil else "N/A",
        "Davies-Bouldin": round(db, 4) if db else "N/A",
        "CH Index": f"{ch:.1f}" if ch else "N/A",
    })

df_results = pd.DataFrame(results)
print(df_results.to_string(index=False))

# ─── PCA: Varianza explicada ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("PCA - Varianza explicada")
print("=" * 70)
pca = PCA().fit(X_scaled)
cum_var = np.cumsum(pca.explained_variance_ratio_)
for i, (var, cum) in enumerate(zip(pca.explained_variance_ratio_[:10], cum_var[:10]), 1):
    print(f"  PC{i}: var={var:.3f}  acum={cum:.3f}")
print(f"  Componentes para 95% varianza: {np.argmax(cum_var >= 0.95) + 1}")

# ─── t-SNE: Visualización 2D ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("t-SNE (visualización 2D)")
print("=" * 70)
tsne = TSNE(n_components=2, random_state=RANDOM_STATE, perplexity=30)
X_tsne = tsne.fit_transform(X_scaled)
print(f"  t-SNE completado. Shape: {X_tsne.shape}")
print(f"  Rango X: {X_tsne[:,0].min():.2f} a {X_tsne[:,0].max():.2f}")
print(f"  Rango Y: {X_tsne[:,1].min():.2f} a {X_tsne[:,1].max():.2f}")

print("\n✅ Done.")
