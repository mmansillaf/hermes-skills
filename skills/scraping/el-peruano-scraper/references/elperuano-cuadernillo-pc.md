# Cuadernillo PC El Peruano — detalle de sesión (Jul 2026)

Proyecto de referencia: D:\PyCode\ProcesosConstitucionalesDEEPSEEK

## Resultados reales

- Rango 2021-07-31 → 2026-07-31: 842 PDFs (1.2 GB), 463 fechas ausentes
  (feriados/fines de semana), 0 errores de descarga.
- 14,564 casos únicos en JSON (casos/YYYY/YYYYMMDD_<exp>_<tipo>.json),
  0 ids duplicados, consistencia metadata↔archivos 100% (verificado con
  sets: 0 sin archivo / 0 sin metadata).
- Calidad: 100% expediente · 99.6% distrito (64 vacíos = límites del PDF:
  casos PI/TC nacionales sin distrito, demandantes directos tras el EXP,
  palabra partida "LI\nMA") · 96.6% fecha ISO (491 sin fecha: avisos/quejas).
- Distribución por tipo: AMPARO 7,722 · HABEAS_CORPUS 5,415 ·
  CUMPLIMIENTO 800 · HABEAS_DATA 498 · ACCION_POPULAR 67 ·
  INCONSTITUCIONALIDAD 32 · COMPETENCIA 9 · OTRO 21.
- Distribución por año: 2021: 1,248 · 2022: 1,092 · 2023: 2,536 ·
  2024: 2,702 · 2025: 4,142 · 2026: 2,844.
- Tiempos: descarga 41 min (delay 1.2 s, 1,905 fechas/h) + reintento 11 min;
  extracción 841-842 PDFs en ~18 min (~50 PDFs/min, 1,000+ casos/50 PDFs).
- Tokens de conversación estimados (in+out, deepseek-v4-flash): ~240K.

## Scripts reutilizables (proyecto)

- `scripts/html_extractor.py` — urlPDF/paginas/fecha del HTML (stream RR7)
- `scripts/descargar_cuadernillos.py` — orquestador: checkpoint.json,
  auto-regulación de delay, `--reintentar-pendientes`, skip sáb/dom,
  verificación pymupdf por PDF
- `scripts/extraer_casos.py` — parser multi-formato (TC/CS/PJ), fechas,
  distritos, filtro anti-citas
- `scripts/procesar_casos.py` — CLI extracción masiva a JSON + índice
  (glob case-insensitive `*.[pP][dD][fF]`)
- `scripts/reparar_distritos.py` — re-procesa PDFs de casos afectados tras
  un fix del parser; actualiza JSONs + casos_metadata.json

## Cronología de fixes (QA iterativo, Fase 3)

1. 25→60→61 casos: el regex inicial perdía cabeceras sin prefijo
   ("AMPARO N°" vs "PROCESO DE AMPARO N°"); el criterio correcto de
   cabecera real = línea anterior en MAYÚSCULAS (bloque de órgano).
2. "del año" en fecha en letras: regex `del\s+año\s+`; la ñ se normaliza
   a "n" en el texto → usar `a[nñ]o`.
3. Año glotón capturando "i" de "I. VISTA" → tokens de ≥2 chars + 
   backtracking de tokens en `_anio_letras` (crash TypeError resuelto).
4. rf-string `{0,4}` → placeholder de formato (bug silencioso) → `{{0,4}}`.
5. Distrito "EXPEDIENTE" capturado como distrito (formato CS) → regex
   "CORTE SUPERIOR DE JUSTICIA(?: DE | )" + blacklist de campos.
6. "CORTE SUPERIOR DE JUSTICIA VENTANILLA" sin "DE" → DE opcional.
7. Nombres de demandantes como distrito ("ALEXANDER MARTÍN KOURI") →
   validación contra lista oficial de 35 distritos judiciales (ñ→n).
8. Distrito inline tras el EXP (`...PHC/TC LIMA`) y en el VISTA
   ("– Huaura, en audiencia" → HUAURA).
9. Digitalización 2021 con espacios inyectados: "J UNÍN"→JUNIN,
   "P IURA"→PIURA, "LI MA"→LIMA (match sin espacios, prefijo, ≥5 chars);
   "LIBERTAD"→LA LIBERTAD; "AMAZONA"→AMAZONAS; alias DEL SANTA→SANTA,
   CHANCHAMAYO→SELVA CENTRAL.
10. Extensión `.PDF` mayúscula: glob case-sensitive no la ve → normalizar
    nombre a .pdf al descargar + glob `*.[pP][dD][fF]`.
11. 92 "OTRO" reclasificados: sufijos TC PHC/TC, PI/TC, CC/TC, PCC/TC no
    mapeados → mapear (PHC=habeas corpus, PI=inconstitucionalidad,
    CC/PCC=competencia).

## Método usado (reproducible)

SDD (spec/SPEC.md) → TDD (21 tests, 10 fixtures reales 2021-2026:
2 HTML + 8 PDFs) → descarga background con notify_on_complete → extracción
background → QA por muestreo por año/tipo → reparación dirigida → reporte
final .md/.txt (REPORTE_FINAL.txt) con cobertura, calidad y tokens.

Pendientes del proyecto: ingesta a LexRAG (FAISS); rango 2016-2021 con los
mismos scripts (riesgo: formatos más antiguos, más OCR).
