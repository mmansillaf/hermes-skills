# Worked example: buscador offline de jurisprudencia TC (Perú)

Delivered 2026-08-01 en `D:\PyCode\ProcesosConstitucionales\html_casos_v2\` — el
patrón completo del skill aplicado a 8,794 sentencias del Tribunal Constitucional
peruano publicadas en El Peruano (2016-2021).

## Corpus fuente
- `D:\PyCode\ProcesosConstitucionales\data\casos_2016_2021\<YYYY-MM-DD>\NNN_Tipo_Numero.json`
- 855 fechas, 8,794 JSON, ~156.8 MB de texto total, ~17,830 chars promedio por caso
  (máx 316,345), campo `texto` con saltos de línea dentro del JSON.
- Campos del JSON: fecha_publicacion, edicion, tipo (Amparo/Cumplimiento/Habeas
  Corpus/Habeas Data/Accion Popular), numero, sentencia, distrito, corte,
  fecha_resolucion, demandante (TRUNCADO: "don Frank"), texto.

## Extracción semántica (regex, en el generador Python)
- **demandante completo**: `interpuesto por (don|doña|d\.)\s+(Nombre...)` (1-7
  palabras capitalizadas) o `demandante (don|doña)...`; fallback al campo JSON.
- **fallo**: buscar cerca de "declar..." → IMPROCEDENTE > INFUNDADA > FUNDADA
  (primera coincidencia; con votos divididos puede diferir del voto singular).
  Conteos reales: FUNDADA 2,085 · IMPROCEDENTE 5,038 · INFUNDADA 1,619.
- **derecho vulnerado** (12 categorías por diccionario de regex sobre texto
  normalizado): Pensión, Salud, Acceso a información, Debido proceso, Educación,
  Propiedad, Trabajo, Libertad de expresión, Igualdad, Vida e integridad,
  Libertad personal, Debido procedimiento admin. Máx 3 por caso.
- **ponentes**: `PONENTE\s+([A-Z...]+)` o `VOTO DE LOS MAGISTRADOS ...`.
- **citas STC**: `STC\s*(\d{4,5}-\d{4}(?:-[A-Z]{2,4})?(?:/TC)?)` +
  `Expediente\s+(\d{4,5}-\d{4}.../TC)`; máx 12 por caso; se indexan los tokens
  de la cita para "¿qué fallos citan a X?".
- **resumen**: primeras frases tras la sección ASUNTO, ~420 chars; también se usa
  como snippet de 1,000 chars en datos.js (campo 12).

## Calidad de datos (lección clave del skill, pitfall 10)
El scraper capturó mal el campo `distrito` en ~1,360 casos: valores "DEMANDANTE"
(959), "JUEZ" (299), "DEMANDADO" (98), "PROCEDENCIA" (3); 3,521 vacíos.
Recuperación:
1. `CORTE SUPERIOR DE JUSTICIA DE\s+(X)` → X (p. ej. AYACUCHO)
2. fallback: `([A-Z...]{2,30}),\s*\d{1,2}\s+de\s+[a-z]+` (ciudad en línea de fecha
   "Ayacucho, 13 de abril del 2016")
3. `.upper()` para unificar variantes de capitalización (AYACUCHO 1,357 + 561
   "Ayacucho" minúscula → 1,918).
Residual aceptado: 2 casos con "AYACUCHO EN REITERADAS SENTENCI..." (el regex de
ciudad capturó texto de más). Reportar estos residuos al usuario con transparencia.

## Índice (números reales)
- 99,903 términos · 7,951,873 postings
- Claves: token crudo + `5:`+primeros-5 + `s:`+stem (plural/sufijos); metadatos x3
- Límite de indexación: 12,000 chars de texto por caso
- `indice.js` delta-encoded: 15.3 MB (vs 25.7 MB plano) · `datos.js`: 5.4 MB
- Carga con `<script src>` (file:// no permite fetch) — decodificación perezosa
  por token con cache en Map.

## Bug que costó más (pitfall 3 — sinónimos como AND)
`SINONIMOS = {'pension': ['jubilacion','onp','afp','sctr'], ...}` se aplicaba como
conjuntos AND extra → `pension NOT onp` = pension AND onp AND NOT onp = vacío.
Fix: los sinónimos se unen al MISMO set OR del término dentro de `expandirTermino()`.

## UI final (todos verificados en navegador)
- Búsqueda: frase `"..."`, NOT, OR, campos numero:/tipo:/distrito:/año:/sentencia:/
  fallo:/derecho:/ponente:, sin tildes, stems, sinónimos, autocompletado con
  conteos, rango fechas, 4 órdenes, paginación 50.
- Tabs: Nube de términos (click=buscar), Distritos, Gráfico por año (click=filtrar),
  Favoritos (localStorage).
- Export CSV/JSON (Blob + a.download).
- Caso individual: breadcrumb, TOC lateral de secciones, badges fallo/ponente/
  derecho, fallos citados con link `../index.html?q=<cita>`, resaltado `?q=`,
  subrayar-y-anotar selección (localStorage `tc-notas`), dark mode (`tc-tema`),
  print CSS.
- El índice lee `?q=` inicial: `new URLSearchParams(location.search).get('q')` para
  que el flujo cita→búsqueda funcione end-to-end.

## Archivos
- `generar_v2.py` (generador completo: lee JSON → casos HTML + datos.js + indice.js)
- `index.html` / `index_v2.html` (UI; copiar index_v2.html a index.html tras editar)
- v1 (solo metadatos, sin full-text) quedó en `html_casos\` — útil para comparar.

## Métricas de sesión
- Regeneración completa: ~3.5-5 min en background (lectura NTFS es el cuello)
- cp -r a /mnt/d: 42 s para 8,794 archivos (vs escritura directa Python ~9 min)
