# El Peruano — Cuadernillo PC (Procesos Constitucionales) — detalle validado

Sesión 2026-07-31. Validación LOCAL con los PDFs que el usuario ya había
descargado: `PC20260729.pdf` y `PC20260720.pdf`.

## Fuente

| Atributo | Detalle |
|----------|---------|
| **URL patrón** | `https://busquedas.elperuano.pe/cuadernillo/PC/YYYYMMDD` (una URL por fecha) |
| **Contenido** | Cuadernillo "PC" = Procesos Constitucionales. Sentencias del Poder Judicial: Corte Suprema, Sala de Derecho Constitucional y Social Permanente (procesos de amparo, hábeas corpus, cumplimiento, etc.) |
| **Cobertura** | Últimos 5 años ≈ 1.200–1.300 fechas con publicación (días hábiles − feriados). Fechas sin cuadernillo (feriados/fines de semana) → 404/ausencia |
| **Anti-bot/WAF** | NO VERIFICADO — validar en vivo (3–4 URLs: reciente + 2021 + feriado) antes de descarga masiva |

## Estructura PDF validada

- **Texto vectorial**: pymupdf extrae texto limpio (148 págs → ~1.2M
  chars; 8 págs → ~68K chars). **NO requiere OCR** para ediciones
  recientes. Años viejos (2021–22) sin verificar → fallback tesseract
  (spa) si texto < umbral.
- **PITFALL — page count**: `file PC20260729.pdf` reporta "10 page(s)"
  pero el contenido real es 148. El `/Count` del trailer del PDF está
  mal (productor del PDF). **SIEMPRE usar `fitz.open(...).page_count`
  (pymupdf), nunca la salida de `file`** para estos PDFs.
- **Tamaño**: ~110 KB/página promedio (8 págs/867 KB; 148 págs/1.78 MB).
  Proyección 5 años: 3–8 GB.
- **Header de edición** por PDF: `PROCESOS CONSTITUCIONALES / El Peruano
  / DIARIO OFICIAL DEL BICENTENARIO / <Día> <fecha> de <año> / Año XXII
  / Nº <N>`.

## Segmentación de casos (regex, sin IA)

Un PDF contiene MUCHOS casos concatenados. Cada caso arranca con cabecera:

```
PROCESO DE AMPARO N° 25738-2024
CORTE SUPREMA DE JUSTICIA DE LA REPÚBLICA
SALA DE DERECHO CONSTITUCIONAL Y SOCIAL PERMANENTE
LIMA                       ← distrito judicial
Lima, siete de abril de dos mil veintiséis   ← fecha de sentencia EN LETRAS
I. VISTA: ... → MATERIA DEL RECURSO → ANTECEDENTES → ...
```

**Ancla regex**: `(PROCESO|ACCIÓN) DE (AMPARO|HÁBEAS CORPUS|CUMPLIMIENTO|
HÁBEAS DATA|ACCIÓN POPULAR|...) N° \d+-\d{4}` + variantes vistas en QA
(QUEJA, DENUNCIA, etc.).

**Campos a extraer por caso**: tipo_proceso, numero_expediente,
sala/corte, distrito_judicial, fecha_sentencia (parsear de "Lima,
<fecha en letras>"), partes (demandante/demandado/procuraduría),
texto íntegro.

## Plan de descarga (5 años)

- Rango: 2021-07-31 → 2026-07-31.
- Ritmo conservador: User-Agent realista, delay ~1.5 s, reintentos con
  backoff (×5), 404 → skip silencioso (feriados), `checkpoint.json`
  reanudable, verificar que el PDF abra y tenga páginas post-descarga.
- Progreso al usuario cada 10 min (fecha actual, %, GB).

## Formato de entrega (preferencia del usuario)

- **Propuestas/reportes en archivo**: `.txt` (texto plano) + `.md`,
  dentro de la carpeta del proyecto, con sección "Decisiones a
  confirmar" (D1–D4). El usuario revisa el archivo, no texto en chat.
- **Salida**: `casos/YYYY/YYYYMMDD_<EXP>.txt` (un txt por caso) +
  `casos_metadata.csv` maestra.
- **Metodología**: SDD primero (`spec/`), TDD con tests RED→GREEN usando
  los PDFs ya descargados como fixtures, antes de correr nada masivo.
- Fases: 0) validación en vivo (~15 min) → 1) descarga masiva (2–4 h
  background) → 2) extracción casos → 3) QA por muestreo por tipo y año
  + reporte .md/.txt.

## Estado del proyecto (2026-07-31)

- `D:\PyCode\ProcesosConstitucionales\requerimientos.txt` — requisito
  original del usuario.
- `D:\PyCode\ProcesosConstitucionales\PROPUESTA.txt` + `PROPUESTA.md` —
  propuesta de 4 fases entregada; el usuario la está revisando.
- Decisiones pendientes del usuario: D1 rango fechas, D2 ritmo de
  descarga, D3 formato salida (+JSON?), D4 ingesta a LexRAG.
- Próximo paso acordado: tras aprobación → Fase 0 (validación en vivo)
  + spec SDD.
