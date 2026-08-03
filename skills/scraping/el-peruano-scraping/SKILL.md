---
name: el-peruano-scraping
description: Scrape El Peruano (busquedas.elperuano.pe) PDFs by date.
category: scraping
triggers:
  - "el peruano cuadernillo pc descargar"
  - "busquedas.elperuano.pe pdf masivo"
  - "procesos constitucionales el peruano extraer casos"
  - "diario oficial peru sentencias corte suprema"
  - "elperuano normas legales scraping"
---

# El Peruano — Diario Oficial del Perú (busquedas.elperuano.pe)

## Cuándo usar

- Descargar masivamente PDFs de El Peruano por fecha (cuadernillos PC,
  normas legales, edictos, resoluciones).
- Extraer casos individuales (amparo, hábeas corpus, cumplimiento,
  etc.) de PDFs que concatenan muchas sentencias.
- Proyecto ejecutado: `D:\PyCode\ProcesosConstitucionalesDEEPSEEK`
  (descarga 2021-07-31→2026-07-31 COMPLETADA: 842 PDFs OK, 463 ausentes,
  0 errores; extracción con parser multi-formato). Scripts en
  `scripts/`: html_extractor.py, descargar_cuadernillos.py,
  extraer_casos.py, procesar_casos.py. Spec: `spec/SPEC.md`.
  21 tests TDD con 10 fixtures reales (2021-2026).

## Fuente (VALIDADO en vivo 2026-07-31)

| Atributo | Detalle |
|----------|---------|
| **URL patrón** | `https://busquedas.elperuano.pe/cuadernillo/PC/YYYYMMDD` (una URL por fecha) |
| **Contenido PC** | Procesos Constitucionales. El corpus MEZCLA 3 formatos: TC (Tribunal Constitucional), PJ Cortes Superiores, PJ Corte Suprema — el formato NO es uniforme por año |
| **1 PDF por fecha** | Sí. La URL real sale del HTML (ver SPA abajo). **404 = feriado/fin de semana** → registrar ausente y seguir |
| **WAF** | Imperva/Incapsula (IP 38.187.10.142). Corta el TLS (`SSL_ERROR_SYSCALL`) a clientes SIN headers de navegador — incluso `requests`, `curl.exe` de Windows y browser_navigate fallan. openssl s_client sí completa el handshake |
| **Anti-bot solución** | Headers de Chrome COMPLETOS (Accept, Accept-Language, Accept-Encoding, Sec-Fetch-Dest/Mode/Site, Upgrade-Insecure-Requests) + HTTP/2 → `requests` y `curl` funcionan, SIN librerías de impersonación |
| **Rate limit** | ~2-3 requests seguidas OK, luego bloqueo temporal (recuperación ~25 s). Delay auto-regulado obligatorio |
| **Ritmo validado** | delay 1.2 s: 842 PDFs en ~41 min sin bloqueos. Regla: ≥3 bloqueos en 20 req → delay ×1.5 (máx 15 s); 0 bloqueos → reducir hacia 1.2 s |
| **Costo** | $0 — requests + pymupdf (+ tesseract spa si hay escaneos) |

## SPA React Router v7 — dónde está la URL del PDF

`/cuadernillo/PC/YYYYMMDD` es una SPA. El HTML server-rendered inyecta el
loader en:

```
window.__reactRouterContext.streamController.enqueue("<JSON escapado>")
```

El JSON es un **array plano de pares key/value** (formato single-fetch,
con referencias `{"_N": idx}` para valores duplicados). Campos útiles como
pares: `"urlPDF"` → `/api/archivo/file/<TOKEN>/*/<nombre>.pdf`,
`"paginas"`, `"fechaPublicacion"`, `"tipoPublicacion"`.

- Decodificación: `json.loads('"' + raw + '"')` (desescapar) → `json.loads`
  (array) → buscar el valor inmediatamente posterior a la key `"urlPDF"`.
- **Token estable server-side** (el HTML es igual para todos los visitantes)
  — no requiere sesión ni cookies.
- PDF directo: `GET https://busquedas.elperuano.pe + urlPDF` con los mismos
  headers → `application/pdf`.
- Nombres de archivo: 2026 → `PC20260729_4381.pdf` (con nº de edición);
  2021 → `PC20210730.pdf` (sin). El nombre viene en `urlPDF`, no hay que
  construirlo.
- Si el HTML no tiene stream (`urlPDF` ausente) → fecha sin cuadernillo.

## Descarga masiva (parámetros validados)

- **Saltar sábados/domingos** (El Peruano no publica PC en finde): reduce
  requests de ~1.826 a ~1.305.
- `checkpoint.json` reanudable: `{fechas: {YYYYMMDD: {estado:
  ok|ausente|error|sin_pdf, archivo, paginas, bytes}}, delay_actual}`.
- Verificar post-descarga con pymupdf (abre y `page_count > 0`); si falla,
  borrar y marcar error. Estado `error` → pasada `--reintentar-pendientes`
  al final (los 403/5xx puntuales se resuelven solos).
- Retry con backoff `[5, 15, 45, 90]` s ante HTTP 000/429/5xx.
- Mismo pipeline aplica a otras series del buscador (normas legales,
  edictos) cambiando el segmento `/PC/` de la URL.

## Parser multi-formato (3 formatos en el corpus)

Un parser de casos debe cubrir los 3 formatos a la vez (2024-2026 siguen
publicando TC y CS junto a la Corte Suprema). Detalle completo en
`references/el-peruano-multiformato-parsing.md`.

**A) TC — Tribunal Constitucional** (todo el rango):
```
PROCESO DE AMPARO | PROCESO DE CUMPLIMIENTO | PROCESO DE HÁBEAS CORPUS | PROCESO DE INCONSTITUCIONALIDAD
Pleno. Sentencia 676/2020 | Sala Segunda. Sentencia 372/2022
EXP. N.° 01739-2018-PA/TC | EXP. Nº 01130-2022-PC/TC | Expediente 0019-2015-PI/TC (sin N°)
```
Ancla: `^\s*EXP(?:EDIENTE)?\.?\s*N?[°º]?\.?[°º]?\s*(\d{4,5}-\d{4}-[A-Z]{1,3}/TC)`

**B) PJ Cortes Superiores** (2022+):
```
PROCESO DE HÁBEAS CORPUS
CORTE SUPERIOR DE JUSTICIA DE ICA
EXPEDIENTE : 01676-2021-0-1401-JR-PE-03
DEMANDADO : ... / MATERIA : / DEMANDANTE : / BENEFICIARIO :
```
Ancla: `^\s*EXPEDIENTE\s*:\s*(\d{4,5}-\d{4}-\d{1,2}-\d{1,5}-JR-[A-Z]+-\d{1,3})`
Distrito de `CORTE SUPERIOR DE JUSTICIA DE <X>` — OJO variante SIN "DE":
`CORTE SUPERIOR DE JUSTICIA VENTANILLA` (249 casos mal parseados por esto)
→ regex `CORTE SUPERIOR DE JUSTICIA(?:\s+DE\s+|\s+)([A-ZÁÉÍÓÚÑÜ ]+)`.
Variante 2026: `Expediente :` en Title Case → IGNORECASE obligatorio.
Fallback de distrito: primera línea en mayúsculas tras el ancla, EXCLUYENDO
campos del formato CS (blacklist: EXPEDIENTE, JUEZ, ESPECIALISTA, MATERIA,
DEMANDADO, DEMANDANTE, BENEFICIARIO, AGRAVIADO, IMPUTADO, PROCESADO,
DENUNCIADO, SECRETARIO, SALA PENAL, JUZGADO DE ORIGEN, ...).

**C) PJ Corte Suprema** (2024-2026):
```
PROCESO DE AMPARO N° 25738-2024   |   AMPARO N° 32405-2024 (sin prefijo)
RECURSO DE CASACIÓN N° 11546-2022-TACNA DE FECHA...
```
Prefijo `PROCESO DE|RECURSO DE|QUEJA DE|...` opcional.

### Regla de oro: caso REAL vs cita interna

El PDF menciona MUCHOS expedientes dentro del texto de otros casos.
Discriminador fiable:

- **Caso real**: la línea ANTERIOR a la cabecera está en MAYÚSCULAS
  COMPLETAS (PERMANENTE / SALA... / CORTE... / PODER JUDICIAL /
  TRIBUNAL CONSTITUCIONAL / PLENO JURISDICCIONAL), o es
  `Pleno/Sala X. Sentencia N/AAAA`, o `PROCESO DE <TIPO>`. Longitud ≥ 8
  caracteres y sin empezar por `(`.
- **Cita interna**: línea anterior en minúsculas, número de página suelto
  (`8\nCasación Laboral N° 10277-2016`), o `(STC` →
  `(STC\nexpediente\n3179-2004-AA/TC,\nfundamento j...` → RECHAZAR.
- No usar "¿hay SALA/CORTE en las 10 líneas previas?" como criterio: las
  citas dicen "emitida por la Tercera Sala... de la Corte Suprema" y
  generan falsos positivos.

### Fechas (3 variantes reales)

- Letras: `Lima, siete de abril de dos mil veintiséis` → 2026-04-07
- "del año": `Ica, siete de octubre del año dos mil veintiuno` → 2021-10-07
  (el regex debe tolerar `de |del año ` antes del año)
- Numéricas: `Lima, 30 de noviembre de 2022` y
  `a los 19 días del mes de octubre de 2022` → 2022-11-30 / 2022-10-19

### Campos por caso

`id` (fecha_expediente_tipo), `fuente_pdf`, `fecha_publicacion`,
`tipo_proceso` (AMPARO / HABEAS_CORPUS / CUMPLIMIENTO / HABEAS_DATA /
INCONSTITUCIONALIDAD / ACCION_POPULAR / CASACION / QUEJA_CASACION /
COMPETENCIA / OTRO), `expediente`, `sala`, `corte`, `distrito_judicial`,
`fecha_sentencia` (ISO), `partes_texto`, `texto` (íntegro).

## Pitfalls de implementación (todos vividos en producción)

1. **f-string regex**: `rf"...{0,4}..."` — las llaves se interpretan como
   placeholder de formato (`f"{0,4}"` es válido y SILENCIOSO, no da error).
   En rf-strings SIEMPRE escapar cuantificadores: `{{0,4}}`.
2. **Año en letras greedy**: `dos mil veinticuatro lima` captura tokens
   extra del texto siguiente → `_anio_letras` con backtracking de tokens
   (probar de N a 1) y manejar `None` (evita `TypeError: int + None`).
3. **Nombre de archivo**: `"PC20210804.pdf"` → `stem[:8]` = `"PC2021080"`
   (lleva prefijo PC). Extraer fecha con `re.search(r"(\d{8})", stem)`.
4. **`file` reporta páginas mal** (trailer /Count erróneo): usar siempre
   `fitz.open(...).page_count`.
5. **"EXP. N.° "** = N + punto + grado: el orden `N.°` rompe regex tipo
   `N[°º]?\s*` → usar `N[°º]?\.?[°º]?\s*`.
6. **Línea siguiente a la cabecera**: tras el match la línea puede ser
   vacía (`\nLIMA\n...`) → tomar la primera línea NO vacía para el
   distrito.
7. **Sospecha de escaneo**: chars/página < 500 → OCR fallback (tesseract
   spa). En el corpus 2021-2026 no apareció ningún PDF escaneado.

## QA y reparación post-corrida (corregir el parser DESPUÉS de extraer)

Cuando un fix del parser llega tarde (corpus ya extraído), NO re-correr
todo: reparación quirúrgica (patrón `reparar_distritos.py`, validado):

1. Identificar casos afectados por el VALOR del campo (p.ej.
   `distrito_judicial in ("EXPEDIENTE","SALA","CORTE",...)` o vacío).
2. Agrupar por `fuente_pdf` (~150 PDFs) y re-extraer solo esos.
3. Reemplazar cada JSON individual y actualizar `casos_metadata.json`.
   El `id` puede CAMBIAR al reclasificar el tipo (sufijo) → localizar el
   caso nuevo por `expediente` (fallback si el id no coincide), borrar el
   archivo viejo, escribir el nuevo.
4. Verificación final por conjuntos: `ids_metadata - ids_archivos == ∅` y
   viceversa (basename sin extensión). Ojo: `glob` puede contar menos que
   el set por basenames repetidos entre años — los sets son la verdad.

Dato real: 249 casos con distrito "EXPEDIENTE" + 29 vacíos → reparados en
153 PDFs (2.680 JSON reescritos) en ~5 min, sin tocar el resto del corpus.

### Reclasificación por sufijo de expediente TC (casos "OTRO"→real)

Sufijos que aparecen y su tipo (además de PA/PC/HC/PHD/PI/AA):
`PHC/TC` = hábeas corpus, `CC/TC` y `PCC/TC` = conflicto de competencia
(COMPETENCIA). Un caso queda "OTRO" legítimo solo si el expediente no
declara tipo (p.ej. expedientes de juzgados `-JR-CI-01` sin sección).

## Workflow (4 fases, validado)

1. **Fase 0 — Validación en vivo (~15 min)**: GET 3-4 URLs (reciente +
   año viejo + feriado) con curl y headers completos; guardar HTML y PDFs
   reales como fixtures de test.
2. **Fase 1 — Descarga** en background con `notify_on_complete`; reportar
   progreso cada 10 min (fecha actual, %, GB).
3. **Fase 2 — Extracción**: parser con TDD sobre fixtures reales
   (10+ PDFs de 2021-2026 cubriendo los 3 formatos).
4. **Fase 3 — QA**: muestreo por tipo y por año; verificar que ningún
   caso quede partido/pegado; corregir regex; reporte .md+.txt.

## Reglas de entrega (preferencias del usuario)

- **Propuestas en archivo**: `.txt` (plano) + `.md` en la carpeta del
  proyecto, con sección "Decisiones a confirmar" (D1–D4). El usuario
  revisa el archivo, no texto en chat.
- **Plan + estimaciones ANTES de ejecutar**; aprobación previa a
  escanear el sitio.
- **SDD + TDD obligatorios**: spec/ primero, tests RED→GREEN con los
  PDFs ya descargados como fixtures antes de correr nada masivo.
- Reportes en .md + .txt (texto plano sin markdown).
- Modo "autónomo": el usuario puede autorizar "procede con todo,
  auto-evalúa y corrige" — entonces ejecutar el ciclo completo
  (Fase 0 → QA) sin pedir aprobación intermedia.

## Render del corpus a HTML legible + índice con buscador

Patrón validado (2026-08-01) para convertir los JSON de casos (campos:
`fecha_publicacion, edicion, tipo, numero, sentencia, distrito, corte,
fecha_resolucion, demandante, texto`) en HTML para consumo humano.

Corpus 2016-2021: **8.794 casos / 830 fechas** en
`D:\PyCode\ProcesosConstitucionales\data\casos_2016_2021\` (una subcarpeta
por fecha). Salida en `D:\PyCode\ProcesosConstitucionales\html_casos\`
(`index.html` + `casos/<fecha>/<stem>.html`). Receta completa y
generador en `references/casos-json-a-html.md`.

**Upgrade a buscador FULL-TEXT** (2026-08-01): el índice básico (solo
`data-t`/`data-n`) "no funcionaba" — distrito y demandante daban 0
resultados porque no estaban indexados y el campo `demandante` del JSON
viene truncado ("don Frank"). Solución: índice invertido JS (`datos.js` +
`indice.js`, ~36 MB para 8.794 docs) que busca en el TEXTO COMPLETO con
ranking, snippet y highlight. Detalle completo en
`references/buscador-fulltext-archivos-locales.md`.

Pitfalls clave del full-text (vividos en producción):

1. **file:// NO permite fetch()** (CORS) — los datos se cargan con
   `<script src="datos.js">` + `<script src="indice.js">` exponiendo
   `window.CASOS` / `window.INDICE`.
2. **Stopwords y normalización (NFD sin tildes) DEBEN ser idénticas en
   Python (build) y JS (query)** — si difieren, "abuso del derecho" da 0
   porque `del` no existe en el índice y la intersección AND muere.
3. **Demandante truncado → extraer del texto** con regex
   (`interpuesto por don/doña X…`); usar el campo solo si tiene ≥25 chars.
4. **Probar el buscador COMO PERSONA** (directiva explícita del usuario):
   buscar distrito ("LIMA"), nombre completo ("Vela Albornoz"), concepto
   con stopword ("abuso del derecho"), sin tilde ("habeas corpus"),
   filtro combinado ("pensión"+Amparo), término inexistente (debe dar
   aviso, no vacío mudo), y clic en resultado → abre el HTML correcto.
   Set de pruebas completo en la referencia.

Pitfalls clave (vividos en producción):

1. **Detección de secciones por keywords exactas + prefijos conocidos**
   (ASUNTO, ANTECEDENTES, FUNDAMENTOS, HA RESUELTO, VOTO, RAZÓN DE
   RELATORÍA, PROCESO DE…, EXP.…, SENTENCIA DEL TRIBUNAL…), NUNCA por
   heurística de "línea en mayúsculas": marca falsos positivos (nombres de
   magistrados, "SS.", códigos tipo "W-1972663-34"). Detectar a nivel de
   LÍNEA, ANTES de unir párrafos — si se detecta después de unir, los
   títulos quedan pegados al párrafo siguiente.
2. **WSL/NTFS: escribir miles de archivos pequeños directo a /mnt/d es
   lento** (~17-64 archivos/s). Generar todo en `/tmp` (ext4 local: 8.794
   archivos en segundos) y copiar en lote con `cp -r` (~42 s para 8.794).
   Nunca `write_text()` uno a uno contra el destino NTFS final.
3. Metadatos del JSON en grid de tarjetas (Expediente, Sentencia, Tipo,
   Distrito, Publicación, Edición, Corte, Demandante); el campo `texto`
   (con `\n`) se convierte en párrafos justificados + secciones `<h3>`.

## Reference files

- `references/el-peruano-multiformato-parsing.md` — detalle de los 3
  formatos con ejemplos reales, reglas anti-citas, parser de fechas y
  bugs de implementación.
- `references/casos-json-a-html.md` — receta JSON→HTML: estructura del
  índice con buscador en vivo + pills por tipo, listas de keywords de
  sección, CSS (azul judicial, base 13px) y patrón de staging /tmp→cp -r.
- `references/buscador-fulltext-archivos-locales.md` — buscador full-text
  en file://: índice invertido JS (window.CASOS/window.INDICE vía
  `<script src>`), sync Python/JS de stopwords+NFD, extracción de
  demandante completo, ranking+snippet, y set de pruebas "como persona".

## Skills relacionadas

- `web-data-extraction` — técnica WAF generalizada (headers de navegador
  completos para Imperva, sección 2).
- `peruvian-judicial-scraping` — umbrella de portales judiciales
  peruanos (CEJ/PJ, SEDETC/TC, Indecopi); el patrón El Peruano encaja
  como patrón adicional.
- `tc-ingesta-lexrag` — ingesta de PDFs de jurisprudencia a LexRAG
  (FAISS+BM25+Graph); aplicable al corpus PC si se indexa.
