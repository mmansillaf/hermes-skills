# Censos Nacionales 2025 — Datos Demográficos Departamentales

## Dataset disponible

Archivo descargado manualmente desde el portal Censos 2025 del INEI (el sitio tiene WAF que bloquea scraping automatizado).

**Ruta:** `D:\Descargas\UPN-Investigacion\UPN_InclusionFinanciera_Territorial_DesarrolloLocal_Investigacion_ML-main\Estructura demográfica y envejecimiento poblacional según departamentos seleccionados del Perú 2025.xlsx`

**Hoja:** "Comparativa Departamental" (1 hoja, 38 filas incluyendo header, 12 columnas de datos)

## Columnas disponibles

| # | Columna | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | Departamento | text | Nombre del departamento (25 + Perú nacional) |
| 2 | Población total | number | Población total estimada (censada + omitida) |
| 3 | Población censada | number | Efectivamente censada |
| 4 | Población omitida | number | No censada (diferencia) |
| 5 | Hombres | number | Población masculina |
| 6 | Mujeres | number | Población femenina |
| 7 | Razón hombre-mujer | ratio | Índice de masculinidad (100 = equilibrio) |
| 8 | Edad promedio | ratio | Promedio de edad (años) |
| 9 | Edad mediana | ratio | Mediana de edad (años) |
| 10 | Personas de 60 y más años | number | Población adulta mayor absoluta |
| 11 | Porcentaje de personas de 60 y más años | percent | % de adultos mayores |
| 12 | Índice de envejecimiento | ratio | Relación adultos mayores / jóvenes |

## Carga en pandas

```python
import pandas as pd

ruta = r"D:\Descargas\UPN-Investigacion\UPN_InclusionFinanciera_Territorial_DesarrolloLocal_Investigacion_ML-main\Estructura demográfica y envejecimiento poblacional según departamentos seleccionados del Perú 2025.xlsx"

df = pd.read_excel(ruta, sheet_name="Comparativa Departamental", skiprows=6)
df = df.dropna(subset=["Departamento"])  # quitar filas vacías
df = df[df["Departamento"] != "Perú"]   # quitar total nacional

# Limpiar nombres de columnas si es necesario
df.columns = [
    "departamento", "pob_total", "pob_censada", "pob_omitida",
    "hombres", "mujeres", "razon_hm", "edad_promedio", "edad_mediana",
    "p60plus", "pct_60plus", "indice_envejecimiento"
]

# Convertir números (vienen con espacios como separadores de miles)
for col in ["pob_total", "pob_censada", "pob_omitida", "hombres", "mujeres", "p60plus"]:
    df[col] = df[col].astype(str).str.replace(" ", "").str.replace(",", ".").astype(float)
```

### Nota sobre codificación de razones y porcentajes
- `razon_hm`: usa coma decimal (97,5 = 97.5)
- `pct_60plus`: string con % (ej: "14,8%") — limpiar antes de usar
- `indice_envejecimiento`: numérico con coma decimal
- `edad_promedio` y `edad_mediana`: numéricos con coma decimal

## Lima: desagregación especial

Lima aparece como 2 filas separadas en el Excel:
- **Lima Metropolitana** (43 distritos de la provincia de Lima) — 10,129,708 hab.
- **Región Lima** (provincias de Huaura, Huarochirí, Cañete, Canta, Oyón, Yauyos, Barranca, Cajatambo) — 1,018,876 hab.

Esto suma ~11.1M para el departamento de Lima completo.

## Datos nacionales clave (2025)

| Indicador | Perú | Lima Metrop. |
|-----------|------|--------------|
| Población total | 34,157,732 | 10,129,708 |
| % 60+ años | 14.8% | 15.5% |
| Edad promedio | 34.2 | 35.9 |
| Edad mediana | 32 | 34 |
| Índice de envejecimiento | 65.2 | 82.6 |
| Razón hombre-mujer | 97.5 | 96.1 |

## Departamentos extremos

| Métrica | Máximo | Valor | Mínimo | Valor |
|---------|--------|-------|--------|-------|
| Población total | Lima Metrop. | 10,129,708 | Madre de Dios | 208,682 |
| Edad promedio | Moquegua | 36.6 | Loreto | 28.7 |
| Edad mediana | Moquegua | 36 | Loreto | 24 |
| % 60+ | Puno | 17.5% | Madre de Dios | 7.8% |
| Índice de envejecimiento | Puno | 87.7 | Madre de Dios | 27.1 |
| Razón H-M (más hombres) | Ucayali | 102.8 | Lambayeque | 95.2 |

## Uso en el pipeline de inclusión financiera

Estas variables demográficas pueden integrarse como features en el pipeline existente:

### Posibles cruces con IVCD
- **Edad promedio / mediana** → proxy de estabilidad poblacional → componente `f_rent`
- **% 60+ / Índice de envejecimiento** → riesgo demográfico → componente `h_risk`
- **Razón hombre-mujer** → proxy de migración (>100 = más hombres = posible migración laboral) → componente `g_imp`
- **Población omitida** → proxy de informalidad/zona rural → complementa `h_risk`

### Correlaciones a explorar
- `% 60+` vs `Num_CMAC` — ¿departamentos envejecidos tienen menos sucursales?
- `Edad mediana` vs `%PobrezaTotal` — ¿relación entre juventud y pobreza?
- `Razón H-M` vs `NroLineasTelefoniaMovil` — ¿migración masculina asociada a menor conectividad?

## Origen y confiabilidad

- **Fuente:** INEI — Censos Nacionales 2025: XIII de Población, VIII de Vivienda y IV de Comunidades Indígenas
- **Tipo:** Primeros Resultados (no definitivos)
- **Nivel:** Departamental (provincial y distrital aún no publicados — estimado ~6-12 meses)
- **Descargado:** 11 de junio 2026 desde dashboard web (descarga manual del Excel)
- **Bundle JS:** La SPA Angular también contiene valores similares embebidos (totalPopulation: 35,356,367 — ver discrepancia en angular-spa-extraction-via-wayback.md)
- **API:** El servicio REST con paginación (50 registros/página) está bloqueado por WAF

## Histórico disponible (para extrapolación)

Para análisis temporal o extrapolación, están disponibles los Censos 2017 a nivel distrital vía REDATAM (accesible desde inei.gob.pe/estadisticas/censos/):
- Base de Datos REDATAM - Distrital
- Base de Datos REDATAM - Manzana
- PDFs de resultados definitivos por departamento (ej: Lib1583/15ATOMO_01.pdf para Lima, 1101 páginas)
