# Lote 2 - Resultados de Clasificación

Procesado el 2026-06-05 en ThinkPad P53 (i7-9850H, 46GB RAM, HDD USB).

## Archivos nuevos por fuente

| Fuente | PDFs | DOC/DOCX |
|---|---|---|
| DescargaTotalSALACOMPIE-COPIADO | 90,072 | 91,402 |
| Descargas/SAL/Files | 45,390 | 8,435 |
| DESCARGA-PESQUERA | 1,260 | 4,118 |
| DescargaPJ_PENDIENTE | 519 | 391 |
| **Total** | **137,241** | **104,346** |

## Distribución Lote 2

| Categoría | Cantidad | % |
|---|---|---|
| no_clasificado | 87,429 | 36.2% |
| resolucion_generica | 68,218 | 28.2% |
| sentencia | 44,314 | 18.3% |
| demanda | 11,601 | 4.8% |
| notificacion | 10,867 | 4.5% |
| acta_audiencia | 5,975 | 2.5% |
| oficio | 5,279 | 2.2% |
| pericia | 2,243 | 0.9% |
| resolucion_remite | 2,117 | 0.9% |
| resolucion_archivo | 1,350 | 0.6% |
| resolucion_admite | 743 | 0.3% |
| conciliacion | 530 | 0.2% |
| citacion | 437 | 0.2% |
| error | 342 | 0.1% |
| sin_texto | 142 | 0.1% |

## Total Consolidado (Lote 1 + Lote 2)

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
| **TOTAL** | **799,993** | 100% |

**Documentos con valor jurídico (Sentencia + Resolución): 547,572 (68.4%)**
**Cero duplicados entre lotes** (deduplicación por nombre de archivo).

## Performance

- 241,587 archivos en 1,150s (19 min 11s)
- Velocidad promedio: 210 docs/s
- PDFs solos: ~250 docs/s
- DOC/DOCX solos: ~198 docs/s
- Workers: 12 (ProcessPoolExecutor para PDFs, ThreadPoolExecutor para DOCS)
- Cuello de botella: HDD USB (no CPU ni RAM)
