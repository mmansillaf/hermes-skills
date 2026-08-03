# El Peruano cuadernillos PC — parsing multi-formato (detalle)

Validado contra PDFs reales 2021-2026 (proyecto
D:\PyCode\ProcesosConstitucionalesDEEPSEEK, julio 2026).
Los 3 formatos coexisten en el corpus: un PDF cualquiera puede contener
solo TC, solo CS, solo PJ-Sup, o mezclas.

## Formato A — TC (Tribunal Constitucional)

Estructura de un caso:

```
PROCESOS CONSTITUCIONALES
TRIBUNAL CONSTITUCIONAL
PROCESO DE AMPARO                 ← sección (tipo)
Pleno. Sentencia 676/2020         ← o "Sala Segunda. Sentencia 372/2022"
EXP. N.° 01739-2018-PA/TC         ← ancla
LIMA                              ← distrito
ÓSCAR UGARTECHE GALARZA           ← demandante (mayúsculas)
RAZÓN DE RELATORÍA
...
SENTENCIA DEL TRIBUNAL CONSTITUCIONAL
En Lima, a los 19 días del mes de octubre de 2022, ...
```

Variantes del ancla observadas:
- `EXP. N.° 01739-2018-PA/TC` (punto + grado)
- `EXP. Nº 01130-2022-PC/TC` (grado directo)
- `Expediente 0019-2015-PI/TC` (sin N°, proceso de inconstitucionalidad)

Sufijos de expediente TC y su tipo: PA/TC = amparo, PC/TC = cumplimiento,
HC/TC = hábeas corpus, PHD/TC = hábeas data, PI/TC = inconstitucionalidad,
AA/TC = acción de amparo (sentencias viejas citadas), PHC/TC = hábeas
corpus (variante 3 letras — 92 casos quedaron "OTRO" hasta mapearlo),
CC/TC y PCC/TC = conflicto de competencia (COMPETENCIA).

Regex de ancla probado:
`^\s*EXP(?:EDIENTE)?\.?\s*N?[°º]?\.?[°º]?\s*(\d{4,5}-\d{4}-[A-Z]{1,3}/TC)`

## Formato B — PJ Cortes Superiores (hábeas corpus de CSJ)

```
PROCESO DE HÁBEAS CORPUS          ← sección
CORTE SUPERIOR DE JUSTICIA DE ICA ← órgano (distrito = ICA)
PRIMERA SALA PENAL DE APELACIONES Y FLAGRANCIA DE ICA
EXPEDIENTE : 01676-2021-0-1401-JR-PE-03   ← ancla (a veces "Expediente :" en Title Case)
DEMANDADO : JENNER MOISÉS VÁSQUEZ MARTÍNEZ
MATERIA : HABEAS CORPUS
DEMANDANTE : MIGUEL ANTONIO DÍAZ MERINO.
BENEFICIARIO : OSCAR EDUARDO MORE MATÍAS.
SENTENCIA DE VISTA
RESOLUCIÓN Nº 10.-
Ica, siete de octubre del año dos mil veintiuno.-
```

- El `:` puede estar en la línea SIGUIENTE a "EXPEDIENTE" (`EXPEDIENTE\n:
  01676...`) — usar `\s*` (incluye \n) entre clave y valor.
- Los campos DEMANDADO/DEMANDANTE/BENEFICIARIO son el "partes_texto".
- Regex de ancla: `^\s*EXPEDIENTE\s*:\s*(\d{4,5}-\d{4}-\d{1,2}-\d{1,5}-JR-[A-Z]+-\d{1,3})`
  (el segmento `JR` es fijo — patrón NNNN-YYYY-NN-NNNN-JR-XX-NN).
- Distrito: `CORTE SUPERIOR DE JUSTICIA DE ICA`, pero EXISTE la variante
  SIN "DE": `CORTE SUPERIOR DE JUSTICIA VENTANILLA` (2021). Regex que
  cubre ambas: `CORTE SUPERIOR DE JUSTICIA(?:\s+DE\s+|\s+)([A-ZÁÉÍÓÚÑÜ ]+)`.
- Fallback de distrito (si el órgano no matchea): primera línea en
  mayúsculas tras el ancla con BLACKLIST de campos del formato
  (EXPEDIENTE, JUEZ, ESPECIALISTA, MATERIA, DEMANDADO, DEMANDANTE,
  BENEFICIARIO, AGRAVIADO, IMPUTADO, PROCESADO, DENUNCIADO, SECRETARIO,
  SALA PENAL, JUZGADO DE ORIGEN, SISTEMA DE NOTIFICACIONES, SALA, CORTE...).
  Sin la blacklist, 249 casos quedaron con distrito = "EXPEDIENTE".

## Formato C — PJ Corte Suprema

```
PROCESO DE AMPARO                 ← sección (puede faltar)
CORTE SUPREMA DE JUSTICIA DE LA REPÚBLICA
SALA DE DERECHO CONSTITUCIONAL Y SOCIAL
PERMANENTE
PROCESO DE AMPARO N° 25738-2024   ← ancla (o "AMPARO N° 32405-2024" sin prefijo)
LIMA                              ← distrito
Lima, siete de abril de dos mil veintiséis   ← fecha en letras
I. VISTA: ... MATERIA DEL RECURSO ... ANTECEDENTES ...
```

- Casaciones: `RECURSO DE CASACIÓN N° 11546-2022-TACNA DE FECHA 17 DE...`
  — el distrito va INCRUSTADO en el expediente (`-TACNA`).
- La línea de sección "PROCESO DE AMPARO" sola (sin N°) NO es ancla.
- Regex de ancla: cabecera con prefijo opcional
  `(?:(PROCESO|RECURSO|QUEJA|CONFLICTO|DENUNCIA|INVESTIGACIÓN)\s+DE\s+)?`
  + tipo + `N[°º]?\s*\d{1,6}\s*[-–—]\s*\d{4}`.

## Regla de discriminación caso real vs cita (CRÍTICA)

Criterios que FALLARON (no usar):
- "¿hay SALA/CORTE en las 10 líneas previas?" → las citas internas
  mencionan "emitida por la Tercera Sala de Derecho Constitucional y
  Social Transitoria de la Corte Suprema de Justicia" y pasan el filtro.
- "¿el match está precedido por un watermark W-NNNNNNN-NNN?" → hay más
  watermarks (79) que casos (61); marcan páginas digitalizadas, no casos.
- "¿empieza en página nueva?" → los casos se suceden en la misma página.

Criterio que FUNCIONÓ: la línea inmediatamente anterior (no vacía) a la
cabecera debe estar en MAYÚSCULAS COMPLETAS, con ≥ 8 caracteres, sin
empezar por "(" y sin puntuación final; o ser `Pleno/Sala X. Sentencia
N/AAAA`; o `PROCESO DE <TIPO>`. Citas típicas rechazadas:
- `(STC\nexpediente\n3179-2004-AA/TC,\nfundamento j...` (línea previa "(STC")
- `8\nCasación Laboral N° 10277-2016` (número de página como línea previa)
- `III. ANTECEDENTES\n1. Demanda\nNolberto Díaz Cueva, mediante escrito de...`
  (línea previa en minúsculas)

Resultado en fixture de 148 págs: 75 matches de cabecera → 61 casos reales
(60 amparo + 1 casación) — el resto eran citas.

## Parser de fechas

Tres variantes (función separada para letras y para números):

```
fecha_letras_a_iso:  "siete de abril de dos mil veintiséis"     → 2026-04-07
                     "siete de octubre del año dos mil veintiuno" → 2021-10-07
fecha_numerica_a_iso:"Lima, 30 de noviembre de 2022"            → 2022-11-30
                     "a los 19 días del mes de octubre de 2022" → 2022-10-19
                     "3 de noviembre de 2020"                   → 2020-11-03
```

Puntos finos:
- Días en letras: incluir "treinta y uno" (con espacios) y variantes con
  tilde (veintiséis/veintiseis, dieciséis/dieciseis) — normalizar sin
  tildes antes de comparar.
- Años: "dos mil veintiséis" (2000+n), "mil novecientos ochenta y cinco"
  (1900+n), "mil..." (1000+n). Años válidos del corpus: 2000-2026.
- El año en letras NO debe capturar tokens del texto siguiente: usar
  backtracking (probar fullmatch con N tokens, N-1, ...) y devolver None
  si nada cuadra (nunca crashear con int + None).

## Bugs de Python vividos (con síntomas)

| Bug | Síntoma | Fix |
|-----|---------|-----|
| `rf"...{0,4}..."` en regex | función devuelve None silenciosamente (el cuantificador se convirtió en placeholder de formato) | `{{0,4}}` |
| `_anio_letras` sin manejo de None | `TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'` a mitad de la corrida (PDF 201) | devolver None y propagar; backtracking de tokens |
| `stem[:8]` sobre "PC20210804.pdf" | "Procesando 0 PDFs" (filtro de fechas descarta todo) | `re.search(r"(\d{8})", stem)` |
| `EXPEDIENTE\s*:` sin IGNORECASE | 0 casos del formato CS (variante "Expediente :") | `re.I` |
| Regex `-JR-` duplicado en patrón de expediente CS | nunca matchea | segmento JR único: `-JR-[A-Z]+-\d{1,3}` |
| buscar distrito en primera línea tras cabecera | línea vacía `\n` → distrito "" | tomar primera línea NO vacía |

## Métricas reales de la corrida (para estimar futuras)

- Descarga completa 2021-07-31→2026-07-31: 842 PDFs OK + 463 ausentes
  (fin de semana/feriado), 0 errores finales, ~41 min con delay 1.2 s.
- 842 PDFs ≈ 1,2 GB en `pdf/YYYY/` (~1,5 MB/PDF promedio).
- Extracción: ~50 PDFs/min en serie; ~20 casos por PDF en ediciones de
  Corte Suprema (60-148 págs).
- RESULTADO FINAL: 14.581 casos JSON (no 15-18K proyectados) — 0 ids
  duplicados, 100% con expediente, 99,8% con distrito, 96,6% con fecha
  de sentencia; 14 casos "OTRO" (juzgados sin tipo declarable).
- Distribución final por tipo: AMPARO 7.729, HABEAS_CORPUS 5.430,
  CUMPLIMIENTO 800, HABEAS_DATA 498, ACCION_POPULAR 67,
  INCONSTITUCIONALIDAD 33, COMPETENCIA 10, OTRO 14.
- Distribución por año (PDFs): 2021: 127, 2022: 114, 2023: 178,
  2024: 180, 2025: 166, 2026: 115 — los 3 formatos presentes en
  casi todos los años.
