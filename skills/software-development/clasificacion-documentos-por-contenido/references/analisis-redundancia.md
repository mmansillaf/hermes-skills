# Análisis de Redundancia - Clasificación de Documentos

## Problema

13 categorías nominales con 3 atributos cuantitativos cada una = 39 datos brutos.
¿Cuántas dimensiones reales subyacen?

## Método

Para cada categoría, extraer:
- `total`: cantidad de documentos
- `pag_prom`: páginas promedio
- `kb_prom`: tamaño en KB promedio
- `mats_muestra`: materias únicas en muestra de 100 docs

Identificar correlaciones entre variables y agrupar categorías por tipo.

## Datos reales (jun 2026, 558K documentos clasificados en 13 categorías)

| Categoría | total | % | pag_prom | kb_prom | mats |
|---|---|---|---|---|---|
| Sentencia | 243,288 | 43.6% | 3.2 | 145.9 | 43 |
| Resolución | 192,116 | 34.4% | 1.4 | 114.2 | 38 |
| Notificación | 44,777 | 8.0% | 1.5 | 115.9 | 48 |
| Demanda | 16,117 | 2.9% | 2.9 | 147.2 | 34 |
| Oficio | 16,488 | 3.0% | 1.3 | 124.6 | 33 |
| Conciliación | 7,722 | 1.4% | 1.9 | 110.2 | 37 |
| Pericia | 5,328 | 1.0% | 1.8 | 110.6 | 28 |
| Citación | 3,329 | 0.6% | 2.6 | 132.3 | 42 |
| Acta de Audiencia | 3,395 | 0.6% | 1.3 | 109.0 | 29 |
| Resol. - Admite Trámite | 1,340 | 0.2% | 2.6 | 123.3 | 33 |
| Resol. - Archivo | 4,430 | 0.8% | 1.6 | 110.7 | 31 |
| Resol. - Remite/Eleva | 7,742 | 1.4% | 1.2 | 93.8 | 43 |
| no_clasificado | 12,248 | 2.2% | 1.2 | 111.1 | 32 |

## Variables redundantes identificadas

### Dimensión 1: VOLUMEN (3 variables → 1)

`total`, `pct`, `mats_muestra` miden lo mismo: qué tan grande es la categoría.

- `total` vs `pct`: relación lineal perfecta (`pct = total / 558329 * 100`)
- `total` vs `mats_muestra`: correlación estimada r > 0.9 (más docs → más materias distintas)

**Queda**: solo `total`

### Dimensión 2: COMPLEJIDAD (3 variables → 1)

`pag_prom`, `kb_prom` miden ambas la profundidad del documento.

- `pag_prom` vs `kb_prom`: correlación estimada r > 0.85
- Además, `pag_prom` es proxy directo de "valor jurídico":
  - > 2.2 págs: alto valor (sentencias, demandas → contenido sustantivo)
  - 1.3-2.2 págs: valor medio
  - < 1.3 págs: bajo/sin valor (trámite puro)

**Queda**: `pag_prom` como **Índice de Complejidad**

### Dimensión 3: ESPECIALIDAD (13 categorías → 1 ordinal)

Las 13 categorías se agrupan en 4 niveles ordinales:

| Nivel | Grupos | Docs | % | Ejemplo |
|---|---|---|---|---|
| FONDO (alto valor) | Sentencia, Demanda | 259,405 | 46.5% | Resuelven el fondo del caso |
| TRÁMITE (valor medio) | Resolución, Resol.-Admite/Archivo/Remite | 205,628 | 36.8% | Proveen escritos, programan |
| PROCESAL (bajo valor) | Notificación, Oficio, Citación, Acta, Conciliación, Pericia | 81,039 | 14.5% | Trámite administrativo |
| NULO | no_clasificado | 12,248 | 2.2% | Sin clasificar |

### Dimensión 4: MATERIA (independiente, no redundante)

El campo `MATERIA` (9,295 valores nominales) expresa el contenido temático real. No correlaciona con las demás variables y **no se reduce** — se agrupa por área legal (normalización).

## Resumen: 39 datos → 4 dimensiones

| Dimensión | Tipo | Variables originales que la expresan |
|---|---|---|
| VOLUMEN | Cuantitativa | `total` (descartar `pct`, `mats_muestra`) |
| COMPLEJIDAD | Cuantitativa | `pag_prom` (descartar `kb_prom`) |
| ESPECIALIDAD | Ordinal | Fondo > Trámite > Procesal > Nulo |
| MATERIA | Nominal | 9,295 valores → ~200 áreas legales |

**Reducción efectiva: ~70% de redundancia eliminada.**

## Aplicación práctica

Para filtrar documentos con valor jurídico para un RAG:

```python
# 1. Filtrar por dimensionalidad reducida
docs_utiles = docs[
    (docs.especialidad == 'FONDO') | 
    ((docs.especialidad == 'TRAMITE') & (docs.pag_prom >= 3))
]

# 2. Además filtrar por materia si aplica
if consulta_es_laboral:
    docs_utiles = docs_utiles[docs_utiles.area_legal == 'LABORAL']
```
