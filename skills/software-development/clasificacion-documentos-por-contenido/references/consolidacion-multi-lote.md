# Consolidación Multi-Lote

Resultados reales de procesar dos lotes de documentos judiciales peruanos en una sola sesión.

## Fuentes de datos

| Lote | Fuente | Formato | Archivos | Tiempo |
|---|---|---|---|---|
| 1 | `/media/usuario/Nuevo vol/ResolucionesSAL/PDFs/` (72 GB) | PDF (558,329 total, 479,817 clasificados + reclasificados) | ~62 min |
| 2 | Varias carpetas: DescargaTotalSALACOMPIE-COPIADO, Descargas/SAL/Files, DESCARGA-PESQUERA, DescargaPJ_PENDIENTE | PDF (137,241) + DOC/DOCX (104,346) | 241,587 nuevos | 19 min |

## Documentos únicos totales: 799,993

| Categoría | Cantidad | % |
|---|---|---|
| Sentencia | 287,434 | 35.9% |
| Resolución | 260,138 | 32.5% |
| No clasificado | 100,298 | 12.5% |
| Notificación | 55,601 | 7.0% |
| Demanda | 27,649 | 3.5% |
| Oficio | 21,758 | 2.7% |
| Resolución - Remite/Eleva | 9,854 | 1.2% |
| Acta de Audiencia | 9,329 | 1.2% |
| Conciliación | 8,251 | 1.0% |
| Pericia | 7,571 | 0.9% |
| Resolución - Archivo | 5,769 | 0.7% |
| Citación | 3,766 | 0.5% |
| Resolución - Admite Trámite | 2,079 | 0.3% |
| Error / Sin Texto | 496 | 0.1% |

**Documentos con valor jurídico (Sentencias + Resoluciones): 547,572 (68.4%)**

## Distribución por área legal (500,895 docs con materia detectada)

| Área | Docs | % |
|---|---|---|
| CIVIL | 146,795 | 29.3% |
| LABORAL | 111,679 | 22.3% |
| OTROS (no normalizadas) | 79,307 | 15.8% |
| COMERCIAL | 77,876 | 15.5% |
| CONTENCIOSO ADMINISTRATIVO | 66,889 | 13.4% |
| CONSTITUCIONAL | 8,201 | 1.6% |
| PENAL | 5,242 | 1.0% |
| FAMILIA | 2,910 | 0.6% |
| SIN CLASIFICAR | 1,002 | 0.2% |

## Rendimiento

| Métrica | Lote 1 | Lote 2 | Total |
|---|---|---|---|
| Velocidad | ~129 docs/s (pymupdf) | ~210 docs/s (pdftotext+python-docx, 12 workers) | — |
| Cobertura MATERIA | 92.8% | 78% (DOCS tienen peor calidad MATERIA) | 89.5% |
| Errores | 0.001% | 0.14% (DOC corruptos) | — |
| Duplicados | — | 0% (ningún nombre repetido entre lotes) | — |

## Nota sobre deduplicación

La deduplicación se hizo por nombre de archivo (case-insensitive). No hubo ningún solapamiento entre lotes — los archivos del Lote 2 provenían de carpetas distintas a la del Lote 1 y los nombres no se repitieron. Para futuros lotes, siempre construir el set de conocidos antes de procesar.
