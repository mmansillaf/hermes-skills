# Dashboard de Inclusión Financiera — Ejemplo de referencia

**Generado en:** Sesión 8 junio 2026
**Proyecto:** UPN_InclusionFinanciera_Territorial_DesarrolloLocal_Investigacion_ML
**Datos:** v3_resultados_clustering.csv (24 departamentos, 3 clusters)

## Archivo generado

`dashboard_inclusion_financiera.html` — HTML autónomo con Plotly.js vía CDN.

**Ubicación original:** D:\Descargas\UPN-Investigacion\UPN_InclusionFinanciera_Territorial_DesarrolloLocal_Investigacion_ML-main\dashboard_inclusion_financiera.html

## Estructura del dashboard

### KPIs (4 tarjetas HTML/CSS)
| KPI | Valor | Fuente |
|-----|-------|--------|
| Departamentos analizados | 24 | Basededatos3.xlsx |
| Clusters identificados | 3 | K-Means + Silhouette + Dendrograma |
| Factor #1 de inclusión | Oficinas/100k (69.6%) | Random Forest |
| Brecha Cluster 0 vs 1 | 3.1× (depósitos per cápita) | Promedios cluster |

### Visualizaciones (8 gráficos Plotly)

1. **Mapa de clusters** — Barras agrupadas horizontales, todos los dptos ordenados por cluster, eje X = Oficinas_por_100k
2. **Ranking oficinas** — Barras verticales, coloreado por cluster, etiqueta con valor numérico
3. **Perfil cluster (radar)** — 6 variables normalizadas [0,1] por cluster: Oficinas_100k, Depósitos_cápita, Ingreso_prom, Internet_100k, Tasa_Empleo, Bajo_NBI
4. **PCA scatter** — PC1 (45.7%) vs PC2 (25.7%), etiquetas de departamento, colores de cluster
5. **Random Forest importancia** — Barras horizontales: Oficinas (69.6%) > Ingreso (12.2%) > NBI (9.7%) > Empleo (4.7%) > Internet (3.8%)
6. **Oficinas vs Depósitos** — Scatter con tamaño de marcador = Ingreso_prom, coloreado por cluster
7. **Matriz de correlaciones** — Heatmap 6×6, escala azul oscuro a azul brillante
8. **Boxplot distribución** — Oficinas_por_100k por cluster con media ± SD

### Tema visual
- Fondo oscuro (GitHub-dark inspired: `#0d1117`)
- Superficies `#161b22`, bordes `#30363d`
- Fuente: Inter (Google Fonts)
- Colores cluster: rojo `#f85149`, verde `#3fb950`, azul `#58a6ff`
- Sin barra de herramientas Plotly (`displayModeBar: false`)

## Cómo regenerar

```python
import pandas as pd

# Datos
df = pd.read_csv('v3_resultados_clustering.csv')

# Mismas columnas necesarias:
# DPTO_KEY, Cluster, Oficinas_por_100k, Depositos_por_Capita,
# NBI_%_2024, Ingreso_Prom_PEN_2024, Tasa_Empleo,
# Internet_por_100k, PCA1, PCA2

# Exportar a JS inline
data_js = df.to_dict(orient='records')
```

## Lecciones de la sesión

- El CSV `v3_resultados_clustering.csv` es la fuente ideal para cualquier BI — ya tiene clusters, PCA y todos los indicadores
- Power BI Desktop no tiene CLI, así que dashboard HTML autónomo es la mejor opción cuando se necesita sin licencia PBI
- Plotly + Inter + dark theme produce un resultado profesional sin necesidad de herramientas de diseño
- El diseño "GitHub-dark" funciona bien para datos peruanos (neutral, profesional, sin sesgo de color)
