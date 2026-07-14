---
name: clasificacion-documentos-por-contenido
title: Clasificación Masiva de Documentos por Contenido
description: >-
  Clasificar cientos de miles de documentos legales/PDF por su contenido usando
  pymupdf + regex, con organización por symlinks y reporte CSV. Cubre calibración
  de reglas sobre muestra, extracción batch, y fase de embedding para no-clasificados.
tags: [clasificacion, pdf, regex, batch, symlinks, reporte, sentencias, documentos-legales]
---

# Clasificación Masiva de Documentos por Contenido

## Cuándo usar esto

- El usuario tiene 10K-1M+ archivos (PDFs principalmente) en una carpeta plana.
- Quiere organizarlos en subcarpetas por tipo de contenido (sentencia, resolución, notificación, citación, etc.).
- Quiere un reporte de lo clasificado.

## Estrategia general

No uses un LLM para clasificar documento por documento — **no escala**. A ~1-2 segundos por LLM call, 500K documentos tomarían semanas. Usa un pipeline de dos fases:

1. **Reglas regex** (~185 docs/s con pymupdf) — clasifica 70-85% de los documentos.
2. **Embeddings + clustering** (sentence-transformers + K-Means) — para el remanente no clasificado.

## Paso a paso

### Fase 1: Exploración de muestra (SIEMPRE primero)

Nunca programes el clasificador final sin antes inspeccionar una muestra real de documentos.

```python
import random, glob, fitz, re
from collections import Counter

sample = random.sample(all_pdfs, 500)
for p in sample:
    txt = fitz.open(p)[0].get_text()[:500]  # primera página
    upper = txt.upper()
    # Detecta qué palabras clave aparecen
```

Esto te dice:
- ¿Qué variantes ortográficas tiene el texto? (RESOLUCIÓN NÚMERO vs Resolución Nro. vs RESOLUCIÓN N°)
- ¿Hay texto repetido por stamps/watermarks? (típico en PDFs judiciales)
- ¿Qué proporción real tiene cada categoría?
- ¿Hay categorías que no previste?

**Pitfall crítico**: En PDFs judiciales peruanos, los headers se repiten 4-5 veces por página (solapamiento de texto). Usar `re.search` con `upper()` para evitar falsos negativos por minúsculas, y priorizar patrones específicos sobre genéricos.

**Pitfall: Orden de prioridad importa**. Si "sentencia" tiene patrón "FALLO" y "notificación" no tiene su patrón propio, una notificación también podría caer en sentencia si el texto incluye "SE RESUELVE". Priorizar los más específicos (acta, citación, oficio) antes de los genéricos (resolución y sentencia).

### Fase 1.5: Auditoría y calibración de reglas sobre "no clasificados" (CRÍTICO)

Después de la primera pasada, NO asumas que los "no clasificados" son documentos raros. En la práctica son **resoluciones reales con variaciones de formato** que el regex base no cubre. El método:

1. Toma una muestra aleatoria de 80-200 de la carpeta `no_clasificado/`
2. Clasifícalos manualmente en patrones: ¿tienen "Resolución Nro X"? ¿"No." en vez de "N°"? ¿"Resolución X" sin prefijo? ¿Actas? ¿Oficios con formato distinto?
3. Con los patrones identificados, amplía los regex y reclasifica
4. Repite hasta que el remanente sea < 2% de no clasificados

**Proporción esperada** de no clasificados en archivos judiciales peruanos (~17K/480K ≈ 3.5% tras primera pasada):

| Subtipo | % estimado | Ejemplo de texto |
|---|---|---|
| Actas de audiencia | ~37% | "ACTA DE VISTA DE LA CAUSA", "ACTA DE REGISTRO DE AUDIENCIA ÚNICA" |
| Resolución con formato atípico | ~32% | "Resolución Nro Ocho", "RESOLUCIÓN No. QUINCE", "Resolución 2" |
|   ├─ Nro/No + número en letras | (3%) | "Resolución Nro Ocho", "RESOLUCIÓN No. QUINCE" |
|   ├─ solo dígito (sin prefijo) | (1%) | "Resolución 2", "RESOLUCIÓN 19" |
|   └─ otras variantes | (~28%) | RESOLUCIÓN en línea aparte, minúsculas |
| Oficio con "No." | ~2% | "OFICIO No.- 2217-2020" |
| Carátulas/metadata SINOE | ~29% | 1 página con datos del caso + firma digital |

De las resoluciones atípicas identificables (~5,500): **~4,500 son interlocutorias** (1-2 págs, mero trámite, bajo valor) y **~1,000 son completas** (3+ págs, con CONSIDERANDOS, citas legales — ALTO valor para RAG).

Todos los patrones concretos y ejemplos de texto real están en `references/categorias-judiciales.md`.
El script `scripts/reclasificar.py` aplica la reclasificación moviendo symlinks y generando reportes.

### Fase 2: Clasificador por reglas

Estructura las categorías en **orden de prioridad descendente** (más específico primero):

```\norden_sugerido = [\n    "sentencia",        # SENTENCIA, FALLO, SE RESUELVE\n    "notificacion",     # CÉDULA DE NOTIFICACIÓN, NOTIFÍQUESE\n    "citacion",         # CITO, CÍTESE\n    "oficio",           # OFICIO N° / No. / NÚMERO\n    "acta_audiencia",   # ACTA DE VISTA, AUDIENCIA ÚNICA, VISTA DE LA CAUSA\n    "pericia",          # INFORME PERICIAL, DICTAMEN PERICIAL\n    "conciliacion",     # ACTA DE CONCILIACIÓN\n    "demanda",          # INTERPONE DEMANDA\n    "resolucion_admite",    # ADMITIR TRÁMITE\n    "resolucion_archivo",   # ARCHÍVESE\n    "resolucion_remite",    # REMÍTASE / ELEVAR LOS AUTOS\n    "resolucion_generica",  # RESOLUCIÓN (con todas las variantes)\n]\n```

**Puntos clave**:
- Extraer solo las primeras 3-5 páginas (el encabezado y resolución están al inicio).
- Usar `text.upper()` para no depender de mayúsculas/minúsculas.
- Aceptar variantes ortográficas: `C[EÉ]DULA`, `N[UÚ]MERO`, `RESOLUCI[OÓ]N`.
- El regex `RESOLUCI[OÓ]N\\s+N[°º]` captura "Resolución N° 17" que no matchea con "RESOLUCIÓN NÚMERO".
- **"VISTA LA CAUSA" pertenece a Acta de Audiencia, NO a Sentencia.** Si está en sentencia, roba falsos positivos de actas. Moverlo a acta_audiencia.
- **Las resoluciones pueden tener el número en letras** ("Resolución Nro Ocho", "RESOLUCIÓN No. QUINCE"), con solo dígito sin prefijo ("Resolución 2"), o con el número en la línea siguiente ("RESOLUCIÓN \\n 09"). Cubrir con patrones específicos (ver references/categorias-judiciales.md).

### Fase 3: Organización con symlinks (NO mover originales)

**Siempre usar symlinks, no mover los archivos originales.** Razones:
- Si una regla clasifica mal, borras el symlink y re-clasificas. Los originales intactos.
- Cero duplicación de espacio en disco.
- El backup se hace después, con tranquilidad.

```python
def crear_symlink(origen, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.islink(destino) or os.path.exists(destino):
        os.remove(destino)
    os.symlink(origen, destino)
```

Estructura de salida:
```
Clasificados/
├── Sentencia/
├── Notificación/
├── Citación/
├── Resolución/
├── Resolución_-_Admite_Trámite/
├── ...
├── Sin_Texto_Extraible/
├── Errores_de_Lectura/
└── no_clasificado/
```

### Fase 4: Reporte

Generar siempre:
1. **CSV** completo: filename, categoria, nombre_categoria, confianza, expediente, juzgado, paginas, size_kb, ruta_original, error
2. **JSON** resumen: distribución, tiempo, docs/s

### Fase 5: Clasificación por Materia (tema del caso)

Después de clasificar por **tipo de documento** (sentencia vs resolución vs notificación), se puede clasificar por **tema** (materia jurídica) para filtrar qué documentos son relevantes para un RAG.

**Técnica**: los PDFs judiciales peruanos tienen un campo `MATERIA` en la carátula. Extraerlo con regex:

```python
pat_materia = re.compile(r'MATERIA\s*:?\s*(.+?)(?:\n|$)', re.IGNORECASE)
```

Materias frecuentes (de ~375K sentencias+resoluciones):
- Alta: OBLIGACION DE DAR SUMA DE DINERO, EJECUCION DE GARANTIAS, PAGO DE BENEFICIOS SOCIALES, INDEMNIZACION, REPOSICION, CESE DE ACTOS DE HOSTILIDAD, NULIDAD DE RESOLUCION
- Media: ALIMENTOS, DESPIDO, DIVORCIO, TENENCIA, RESOLUCION DE CONTRATO, COBRO DE DOLARES, ACCION DE AMPARO
- Baja: OBLIGACION DE HACER, HABEAS CORPUS, DESALOJO, RETRACTO, MEJOR DERECHO

**Valor para RAG**: filtrar por MATERIA permite responder consultas temáticas precisas. Distribución completa en `references/materias-judiciales.md`.

**Performance**: solo extraer MATERIA (~400 docs/s) es más rápido que clasificación completa (~185 docs/s).

**Pitfall: nombres de directorio con caracteres especiales.** Al iterar sobre categorías como "Resolución" (con ó), no uses string.replace() para normalizar — el nombre real del directorio en disco puede diferir de lo que esperas. Siempre leer el directorio con `os.listdir(base)` o usar la ruta exacta del CATEGORY_NAMES. Ejemplo de error: `.replace('ó','o')` produce "Resolucion" pero el directorio real se llama "Resolución". Esto lanza `FileNotFoundError` después de horas de procesamiento.

**Pitfall: estimaciones de muestra ≠ resultados reales.** Una muestra de 200 no_clasificados sugería ~32% resoluciones atípicas; la reclasificación real de 17,058 mostró solo 8.3%. La muestra pequeña sobrerrepresenta los casos más visibles. Siempre reclasificar el lote completo antes de reportar métricas.

**Pitfall**: algunas carátulas tienen `MATERIA:` con texto en la misma línea, otras en la siguiente. Usar `re.search` sin anclaje captura ambos. Si no hay MATERIA, inferir del juzgado (ej: laboral → materia laboral).

### Fase 6: Normalización de Materias (clasificación por tema jurídico)

Después de clasificar por tipo de documento, **normalizar las materias** (campo MATERIA de la carátula) para agrupar variantes del mismo tema. Es común encontrar 9,000+ valores únicos que en realidad representan ~200-300 temas reales.

**Técnica: reglas regex + lookup table.** Sin LLM, todo determinístico.

Paso a paso:

1. **Extraer todas las materias** con `pdftotext` + 8 workers (150K+ docs en ~5 min)
2. **Aplicar reglas de limpieza**: quitar acentos (`Ó→O`, `Í→I`), normalizar `N°→NUMERO`, `NRO→NUMERO`, `No.→NUMERO`
3. **Agrupar por patrón regex** de mayor a menor especificidad: las 10 variantes de "OBLIGACION DE DAR SUMA DE DINERO" → una sola materia
4. **Asignar área legal** a cada materia normalizada mediante un diccionario estático
5. **Generar lookup JSON**: `materia_original → {materia_normalizada, area}` para usar en el RAG

**Reglas de agrupación comunes:**

```python
MATERIA_GROUPS = [
    # Civil - Cobranzas
    (r'^OBLIGACION\s+(DE\s+)?DAR\s+SUMA', 'OBLIGACION DE DAR SUMA DE DINERO'),
    (r'^OBLIGACIONES?\s+DE\s+DAR\s+HASTA', 'OBLIGACION DE DAR SUMA DE DINERO (HASTA 50 URP)'),
    # Civil - Garantías
    (r'^EJECUCION\s+(DE\s+)?GARANTIAS?', 'EJECUCION DE GARANTIAS'),
    # Laboral
    (r'^PAGO\s+DE\s+BENEFICIOS\s+(SOCIALES|ECONOMICOS)', 'PAGO DE BENEFICIOS SOCIALES'),
    (r'^REPOSICION', 'REPOSICION'),
    # Contencioso Administrativo
    (r'^NULIDAD\s+(DE\s+)?RESOLUCION?\s+(O\s+ACTO\s+)?ADMINISTRATIVO?', 'NULIDAD DE RESOLUCION O ACTO ADMINISTRATIVO'),
    # Constitucional
    (r'^ACCION\s+(DE\s+)?AMPARO', 'ACCION DE AMPARO'),
    # etc.
]
```

**Resultados reales** (sobre 404,011 docs con materia detectada):
- 9,295 materias originales → 3,980 normalizadas (57% de reducción)
- El 12.2% cae en "OTROS" (variantes muy específicas no cubiertas por reglas)
- Ver `references/normalizacion-materias.md` para el mapeo completo y distribución por área legal

**Pitfall**: algunas carátulas tienen `MATERIA:` en una línea y el texto en la siguiente. Usar dos patrones:
```python
pat1 = re.compile(r'MATERIA\s*:?\s*(.+?)$', re.I | re.M)  # misma línea
pat2 = re.compile(r'MATERIA\s*\n+\s*(.+?)$', re.I | re.M)  # línea siguiente
```

**Pitfall: Una muestra de 200 no_clasificados NO es representativa.** En la práctica, los archivos se leen en orden alfabético por symlink, lo que sesga la muestra. Siempre procesar el lote completo para métricas reales.

### Fase 7: Análisis de Redundancia (reducción de dimensionalidad)

Al tener múltiples categorías (13+) con atributos cuantitativos compartidos (total, páginas promedio, KB promedio), es útil comprobar cuántas **dimensiones reales** existen:

**Técnica**: correlación entre atributos por categoría.

**Proceso**:
1. Por cada categoría, extraer: `total`, `pag_prom`, `kb_prom`, `mats_muestra`
2. Identificar correlaciones: `total` vs `mats_muestra` (r>0.9), `pag_prom` vs `kb_prom` (r>0.85)
3. Mapear 13 variables nominales a 1 dimensión ordinal (Fondo > Trámite > Procesal > Nulo)

**Resultado real** sobre 13 categorías de clasificación:
| Variable original | Dimensión real | Por qué |
|---|---|---|
| total | VOLUMEN | Se queda |
| pct | REDUNDANTE | Es total*100/558329 |
| mats_muestra | REDUNDANTE | Correlacionada con total (r>0.9) |
| pag_prom | COMPLEJIDAD | Se queda |
| kb_prom | REDUNDANTE | Correlacionada con pag_prom |
| 13 categorías | ESPECIALIDAD (ordinal) | Fondo > Trámite > Procesal > Nulo |

Reducción: ~70% de redundancia. Ver `references/analisis-redundancia.md`.

### Fase 8: Reclasificación de no_clasificados

Después de la primera pasada, el remanente (~3-5% del total) se puede reclasificar con un script específico que:

1. Lee SOLO la carpeta `no_clasificado/`
2. Aplica los patrones ampliados (con variantes ortográficas, números en letras, etc.)
3. Mueve los symlinks a la categoría correcta
4. Reporta lo que sigue sin clasificar

**Script disponible**: `scripts/reclasificar.py` — ejecutar después de actualizar los patrones en el clasificador principal.

**Tiempo**: para ~17K no_clasificados, ~90-100 segundos con pymupdf (1 hilo) o más rápido con pdftotext+workers.

**Valor esperado**: de ~17K no_clasificados, recuperar ~1,400 resoluciones y ~3,400 actas de audiencia. Las ~12,200 restantes son notificaciones SINOE, carátulas, y documentos de 1 página sin texto — bajo o nulo valor jurídico.

**Pitfall: no_calsificado puede contener millones de documentos con nulo valor.** Las actas de audiencia (que pueden ser ~20% del remanente) no son resoluciones. Si el usuario solo quiere sentencias y resoluciones para el RAG, las actas deben ir a su propia categoría, no mezclarse con resoluciones. Filtro final: `paginas >= 3 AND (CONSIDERANDO OR SE RESUELVE)` para identificar contenido jurídico sustantivo.

El ~15-30% que no matchea regex se puede agrupar con:

```python
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(textos_no_clasificados)
clusters = KMeans(n_clusters=10).fit_predict(embeddings)
```

Luego inspeccionas los clusters, les pones nombre, y etiquetas el lote.

## Performance esperada

| Herramienta | Velocidad | 10K docs | 100K docs | 240K docs (mix) |
|-------------|-----------|----------|-----------|----------------|
| pymupdf (1 hilo) | ~185 docs/s | ~1 min | ~9 min | ~22 min |
| pdftotext (1 hilo, 1 pág) | ~225 docs/s | ~45 s | ~7 min | ~18 min |
| pdftotext (8 workers, 1 pág) | ~400-480 docs/s | ~25 s | ~3.5 min | ~10 min |
| **pdftotext (12 workers) + python-docx** | **~210 docs/s (mix)** | **~48 s** | **~8 min** | **~19 min** |

**Hardware observado (ThinkPad P53, i7-9850H):**
- 6 núcleos físicos / 12 hilos @ 2.6-4.6 GHz
- 46 GB RAM
- NVIDIA Quadro T1000 (4 GB) — no se usa en clasificación (solo CPU)
- El cuello de botella real es el **disco de origen**:
  - HDD USB 7200 RPM (~100 MB/s): 8 workers óptimo para PDFs
  - NVMe interno (~3500 MB/s): 12 workers funciona sin saturar I/O
- RAM nunca fue problema: el script procesa un archivo a la vez por worker, no carga todo en memoria

**Recomendación**: Para extracción MASIVA de texto (solo primera página, sin -layout complejo), usar `pdftotext` + `ProcessPoolExecutor` con 8+ workers. Es 2-3x más rápido que pymupdf porque evita cargar toda la estructura del PDF en memoria y distribuye la I/O del disco.

```python
import subprocess, re, json
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter

def extraer_campo(path, patron):
    try:
        res = subprocess.run(
            ['pdftotext', '-f', '1', '-l', '1', path, '-'],
            capture_output=True, text=True, timeout=5)
        m = re.search(patron, res.stdout, re.IGNORECASE)
        return m.group(1).strip().upper() if m else None
    except:
        return None

# Uso: extraer MATERIA de 435K PDFs en ~15-18 min con 8 workers
with ProcessPoolExecutor(max_workers=8) as pool:
    futuros = {pool.submit(extraer_campo, p, r'MATERIA\s*:?\s*(.+?)$'): p for p in paths}
    for f in as_completed(futuros):
        # procesar resultado
        pass
```

**Pitfall**: `pdftotext -layout` (con formato tabular) es ~30% más lento que sin él. Usar `-layout` solo si necesitas preservar posición de columnas (tablas). Para extraer el campo MATERIA de la carátula, **no uses `-layout`** — el texto corrido es más rápido y suficiente.

**Pitfall: pdftotext es ~2-3x más rápido que pymupdf para extracción masiva de primera página.**

### Fase 11: Local LLM para Extracción Estructurada (Qwen / Gemma 4 + llama.cpp)

Para reemplazar APIs externas (Groq/OpenAI) en la extracción de campos estructurados (hechos, problema, fallo, entidades) de documentos legales, se puede usar un modelo local via llama.cpp.

**Hardware requerido:** GPU con 4+ GB VRAM (ej: Quadro T1000) y 32+ GB RAM.

**⚠ ADVERTENCIA: Gemma 4 E2B NO cabe en Quadro T1000 4GB — y es más lento que Qwen 7B**\nA pesar de ser un modelo MoE de solo 2.9 GB Q4_K_M, Gemma 4 E2B NO puede cargar todos los layers en GPU en una Quadro T1000 4GB. Datos REALES (6 Jun 2026, 4 muestras multi-formato, mismas condiciones):
- -ngl 30 (intentar GPU completo): OOM — "unable to allocate CUDA0 buffer of size 1295956608"
- -ngl 20: OOM — "unable to allocate CUDA0 buffer of size 1028540800"
- -ngl 12 con VRAM libre: **funciona** pero genera ~2.0 GB en GPU, resto en CPU
- Velocidad REAL: **9.9 tok/s** (vs 10.7 tok/s de Qwen 7B)
- Tiempo REAL por doc: **48.1s** (vs 32s de Qwen 7B) — **51% más lento**
- JSONs válidos: 4/4 (igual que Qwen)

**Conclusión: Gemma 4 E2B NO es recomendable para Quadro T1000 4GB.** El offloading parcial de layers elimina cualquier ventaja de velocidad que su arquitectura MoE podría ofrecer. Para 500K docs: **278 días** (vs 184 con Qwen 7B). Solo sería superior con GPU de 6 GB+ VRAM (RTX 3060/4060).

**⚠ Pitfall: truncado duro a 7000 chars PIERDE el RESUELVE (fallo).**
El método de `texto[:7000]` corta el texto por posición fija, sin respetar párrafos. En resoluciones judiciales peruanas, esto pierde sistemáticamente:
- El **RESUELVE** completo (la decisión del tribunal, parte resolutiva)
- Los nombres de los **jueces firmantes** (S.S., firmas)
- **Notas al pie** con citas jurisprudenciales (ej: CAS N° 3353-2000-Ica)

Ejemplo real: una resolución de 8,659 chars truncada a 7,000 perdió los últimos 1,659 chars que contenían el RESUELVE completo, los nombres de los jueces, y la nota al pie. Qwen no puede extraer información que no recibe.

Solución: usar chunking semántico por párrafos o priorizar el final del documento (ver sección "Chunking semántico"). Nunca truncar por posición fija.

**⚠ Pitfall: Prompt JSON + Python .format() colisiona.**
El JSON del prompt contiene llaves `{ }` que Python .format() interpreta como placeholders. Error: `KeyError: '"resumen_hechos"'`. Solución: usar f-strings con la variable texto como único placeholder, o concatenar el JSON como string plano usando concatenación (`+`) o f-string con la variable separada. Nunca usar `.format(texto=texto)` en un string que contiene JSON con llaves.

**⚠ Pitfall: JSON truncado por Qwen (max_tokens insuficiente o respuesta cortada).**
Qwen a veces genera JSONs incompletos cuando se excede el límite de max_tokens o cuando la respuesta se corta. El error típico es `Unterminated string starting at: line X column Y`. Solución: implementar un reparador multi-intento que:
1. Identifica la línea del error (del mensaje de excepción)
2. Elimina la línea problemática y lo que sigue
3. Busca el último `}` válido
4. Intenta parsear con `json.loads()` en hasta 5 iteraciones, recortando progresivamente
5. Si falla, registrar como error y continuar — no reintentar la request a Qwen

**Configuración probada en (ThinkPad P53 + Quadro T1000 4 GB):**

| Modelo | Tamaño GGUF Q4 | n_gpu_layers | Velocidad REAL | Tiempo/doc REAL | 500K docs |
|--------|---------------|-------------|----------------|------------|-----------|
| **Qwen 2.5 7B Q4_K_M** | ~4.5 GB | **20** (NO 24 — OOM) | **~10.7 tok/s** | **~32s** | **~184 días** |
| **Qwen 2.5 3B Q4_K_M** | ~2.0 GB | 30 (GPU completa) | ~30-35 tok/s (est.) | ~10-12s (est.) | ~64 días |
| **Gemma 4 E2B Q4_K_M** | ~3.0 GB | 12 (parcial, OOM con 20+) | **9.9 tok/s** (real) | **48.1s** (real) | **~278 días** |
| **Gemma 4 12B Q4_K_M** | ~7.5 GB | 12 (parcial) | ~6-8 tok/s | ~45-50s | ~272 días |

**Recomendación por caso (basada en tests reales en Quadro T1000 4GB):**
- Extracción selectiva (cientos de docs): **Qwen 7B** — probado, calidad garantizada
- Batch masivo (miles+): **Qwen 3B Q4_K_M** — cabe 100% en GPU, mismo stack, ~64 días para 500K
- NO recomendar Gemma 4 E2B para este hardware — es más lento que Qwen 7B (48s vs 32s por doc) por offloading parcial. Solo sería superior con GPU de 6 GB+ VRAM (RTX 3060/4060).

#### Warmup behavior (CRÍTICO para batch)

La primera consulta a un server recién iniciado toma ~18s (carga KV cache en GPU). Las consultas siguientes bajan a ~5s (~12-13 tok/s). En batch secuencial solo hay un warmup para todo el lote — no reiniciar el server entre documentos.

Datos reales (Qwen 7B, Quadro T1000, 6 Jun 2026, texto LABORAL real de ~2000 chars):\n```\nTest de warmup: 3 consultas iguales\n #1: 18.2s | 3.5 tok/s  (warmup: carga KV cache)\n #2: 4.9s  | 12.7 tok/s (cache caliente, 72% mas rapido)\n #3: 4.9s  | 12.8 tok/s (estable)\n```\n\nSin warmup el promedio sería ~32s/doc; con warmup, el primer doc toma ~85s y los siguientes ~30s. Para batch de 10,000 docs: el warmup inicial es despreciable (~0.01% del tiempo total).

#### Chunking semántico por párrafos (NO truncado duro)

Problema: El truncado por posición fija (ej: 7,000 chars) corta documentos a mitad de un párrafo. En resoluciones judiciales, esto pierde el RESUELVE (fallo), los nombres de los jueces firmantes, y notas al pie con citas jurisprudenciales.

Solución: Chunking semántico que respeta límites de párrafo con overlap.

Tres estrategias implementadas en scripts/chunking_demo.py:

1. **Chunking multi-pasada con overlap — RECOMENDADA para indexación completa**
   - Divide el documento en chunks que respetan párrafos (nunca corta una idea)
   - Overlap de ~500 chars entre chunks consecutivos para mantener contexto
   - Documento de 17K chars produce ~6 chunks de 4K chars cada uno
   - El último chunk siempre contiene el RESUELVE
   - Cada chunk se envía a Qwen por separado → N veces más lento pero sin pérdida

2. **Priorizar fallo (una pasada Qwen, rápida, pierde fundamentos medios)**
   - Toma últimos párrafos (RESUELVE) + primeros párrafos (contexto inicial)
   - Pierde ~50% del contenido (fundamentos del medio)
   - Util cuando solo se necesita el fallo para indexación rápida

3. **Sub-chunking (para párrafos individualmente muy largos)**
   - Divide un párrafo de 3500+ chars por saltos de línea internos
   - Caso borde: párrafos de notas al pie muy extensas

Las estimaciones sin chunking vs con chunking:
| Lote | Sin chunking (~32s/doc) | Con chunking 2 chunks (~64s/doc) |
|---|---|---|
| 1,000 docs | 8.8 hr | 17.6 hr |
| 10,000 docs | 3.7 días | 7.4 días |
| 50,000 docs | 18.4 días | 36.8 días |
| 500,000 docs | 184 días | 368 días |

Para la mayoría de casos de indexación RAG, **sin chunking es suficiente** porque el fallo siempre está al final, los hechos al inicio, y las entidades (jueces, leyes) aparecen repetidas en todo el texto. Los fundamentos medios son contexto, no parte resolutiva.

Pitfall de implementación: El prompt JSON no puede usar Python .format() directamente porque las llaves { } del JSON colisionan. Usar f-strings o concatenación de strings, nunca .format().

**Velocidad real probada (4 muestras multi-formato + 7 LABORAL reales, Jun 2026):**
- PDF (7K chars, test): ~39s promedio, 11.1 tok/s
- DOCX (7K chars): ~23s, 11.0 tok/s
- DOC legacy (1.2K chars): ~26s, 9.2 tok/s (via catdoc)
- **PDF LABORAL real (7K chars, 7 docs): ~86s promedio** (textos más largos y complejos que samples de prueba)
- Tasa éxito JSON: 87.5% (7/8)
- Tasa éxito JSON con reparador: 100% (8/8, 1 reparado)

**NOTA IMPORTANTE: La velocidad REAL en documentos LABORAL reales es ~86s/doc, no ~32s como estimaban los samples de prueba.** La diferencia se debe a que los samples de prueba (4 documentos) tenían textos más cortos y menos complejos que las resoluciones laborales reales del Poder Judicial peruano. Los documentos reales tienen más texto (~7K chars) y generan respuestas más largas (~400 tokens completion vs ~315 tokens de los samples). Factor de corrección: multiplicar estimaciones de samples × 2.7 para proyecciones reales.

**Estimaciones con chunking:**
| Lote | Sin chunking (~32s/doc) | Con chunking 2 chunks (~20s/doc) |
|---|---|---|
| 1,000 docs | 8.8 hr | 5.6 hr |
| 10,000 docs | 3.7 días | 2.3 días |
| 50,000 docs | 18.4 días | 11.6 días |
| 500,000 docs | 184 días | 116 días |

**Conclusión:** El LLM local es viable para extracción selectiva (cientos de documentos) pero sigue siendo lento para lotes masivos. Mantener Groq API para batch processing masivo y usar LLM local para documentos sensibles o sin internet.

### Fase 11B: Alternativa Cloud — Groq API para Batch Masivo

Para lotes de 100K+ documentos, **Groq API es ~70x más rápido y más barato que LLM local.** La integración es OpenAI-compatible — mismo prompt, misma estructura de respuesta, solo cambia el endpoint.

#### Modelo recomendado: Llama 3.1 8B Instant

Probado en producción (Jun 2026, 100 docs LABORAL reales):
- **100 docs en 1.9 min** (vs 2.4 horas con Qwen 7B local)
- **1.2s por documento** (vs 86s local)
- **98% tasa éxito JSON** (vs 87% local)
- **Costo: ~$0.01** para 100 docs

Detalle de 5 docs LABORAL reales via Groq:
```
[1/5] OK 2.1s | 979→337 tok
[2/5] OK 1.1s | 977→337 tok
[3/5] OK 1.4s | 2090→353 tok
[4/5] OK 1.7s | 1904→470 tok
[5/5] OK 1.4s | 1897→412 tok
```

#### Costos para corpus completo

| Escenario | Docs | Costo normal | Batch -50% | Tiempo (paralelo 50x) |
|-----------|:----:|:------------:|:----------:|:--------------------:|
| LABORAL | 111,679 | $13 | **$7** | ~3 min |
| LAB+COM+FAM | 221,024 | $25 | **$13** | ~5 min |
| Solo Sentencias | 243,288 | $28 | **$14** | ~6 min |
| Todo con valor | 562,297 | $64 | **$32** | ~14 min |

#### Cómo integrar (código mínimo)

```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def query_groq(texto):
    prompt = PROMPT_TPL.format(json_schema=json_schema, texto=texto[:6500])
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 512
        },
        timeout=60
    )
    # Parsear igual que con llama.cpp local
```

**⚠ Pitfall: Mismo prompt, mismo formato, mismo reparador.** La compatibilidad es total — los archivos `rag_listo_batch_qwen_*.json` generados por Groq se indexan con `indexer.py` sin cambios. No hay que modificar el pipeline downstream.

**⚠ Pitfall:** `response_format: {"type": "json_object"}` SÍ funciona en Groq (a diferencia de llama.cpp). Pero no es necesario ni recomendado para mantener compatibilidad entre proveedores.

**⚠ Pitfall:** Rate limits de Groq Developer Plan: 250K TPM, 1K RPM. Para lotes de 10K+ docs, usar Batch API (50% descuento, 24-48h procesamiento) o paralelizar con ~50 requests concurrentes.

#### Cuándo elegir cada uno

| Situación | Recomendación |
|-----------|--------------|
| 100-1,000 docs | Groq (~$0.01-$0.11, minutos) |
| 10,000-100,000 docs | Groq Batch API (~$1-$11, 24-48h) |
| 500,000+ docs | Groq Batch API (~$32, 24-48h) |
| Sin internet / datos sensibles | Qwen 3B local (~30s/doc) |
| Costo cero obligatorio | Qwen 3B local (~200 días para 500K) |

**Conclusión: Para extracción batch, Groq es la opción óptima por velocidad y costo.** $32 para 562K docs es menos que la electricidad de dejar la PC 6 meses.

**Estimaciones por área legal** (de 500,895 docs con materia, datos reales de KGraphResolucionesV3):
**Estimaciones REALES con 86s/doc (Qwen 7B) y 30s/doc (Qwen 3B est.) probado en LABORAL real:**
| Área | Cantidad | Qwen 7B (86s/doc real) | Qwen 3B (30s/doc est.) |
|------|----------|----------------------|----------------------|
| LABORAL | 111,679 | 111.2 días | 38.8 días |
| COMERCIAL | 77,876 | 77.5 días | 27.0 días |
| FAMILIA | 2,910 | 2.9 días | 1.0 días |
| **Total 3 áreas** | **192,465** | **191.6 días** | **66.8 días** |
| **Full corpus** | **500,895** | **~498 días** | **~174 días** |

**Alternativa Groq:** Estos tiempos se reducen de meses a horas por ~$11-$33 (ver references/groq-cost-analysis.md).

**Preferencia del usuario:** filtrar solo LABORAL, COMERCIAL y FAMILIA para extracción con LLM local. Son 192,465 documentos con materia. Con Qwen 7B: ~71 días (24/7). Con Qwen 3B: ~24.5 días.

**Integración con KGraphResolucionesV3 (indexer.py)**

El `indexer.py` del repo espera archivos `rag_listo_batch_*.json` con esta estructura exacta:

```python
doc = {
    "id_documento": "hash_md5_16chars",
    "ruta_local": "/path/al/pdf",
    "contenido_a_vectorizar": {
        "hechos": "Sintesis de los hechos del caso",
        "problema": "Cuestion juridica central",
        "fallo": "Decision final del tribunal"
    },
    "metadatos_graphrag": {
        "jueces_magistrados": ["Nombre del juez"],
        "demandantes_accionantes": ["Nombre del demandante"],
        "demandados_accionados": ["Nombre del demandado"],
        "leyes_y_articulos_citados": ["Ley X, Art. Y"]
    }
}
```

Flujo completo:
1. `extractor_qwen.py` genera `data_raw/rag_listo_batch_qwen_*.json` (checkpoints cada 100 docs)
2. `python3 pipeline/indexer.py --force` reconstruye FAISS + BM25 + NetworkX
3. Las consultas con `graphrag_pro.py` / `graphrag_console.py` funcionan sin cambios

Config de indexer.py relevante (en pipeline/indexer.py):
- Busca archivos `rag_listo_batch_*.json` en `data_raw/`
- Construye FAISS con sentence-transformers
- Construye BM25 con rank_bm25
- Construye grafo NetworkX con nodos Documento/Juez/Ley/Actor/Demandado
- Guarda checkpoints cada 1000 docs

Ver `references/kgraph-integration.md` para el extractor de ejemplo completo.

**Pitfalls comprobadas (ordenadas por frecuencia):**
1. OOM con -ngl 24 en Quadro T1000 4GB. Forzar -ngl 20 para Qwen 7B.
2. response_format type json_object NO funciona con llama.cpp, solo OpenAI/Groq.
3. catdoc/antiword no instalados por defecto en Ubuntu 24.04. Instalar: sudo apt-get install -y catdoc antiword
4. Server no persiste tras reboot, hay que iniciarlo manualmente cada vez.
5. Gemma 4 thinking mode: deshabilitar con `--reasoning off` (llama.cpp moderno) o `--chat-template-kwargs '{"enable_thinking":false}'` (legacy). `--chat-template-kwargs` está deprecado en builds recientes.
6. python-docx NO abre formato .doc binario antiguo. Usar catdoc o antiword.
7. **Prompt con JSON + .format() colisiona.** El JSON contiene llaves `{ }` que Python .format() interpreta como placeholders. Error: `KeyError: '"resumen_hechos"'`. Solución: usar f-strings con la variable texto como único placeholder, o concatenar el JSON como string plano separado de la variable usando concatenación o f-string, nunca .format().
8. Warmup crítico en batch: primera consulta ~18s (carga KV cache), siguientes ~5s. NO reiniciar server entre documentos.

**Flujo recomendado:**
1. Iniciar server (llama-server con el modelo elegido)
2. Verificar health: curl -s http://127.0.0.1:8080/health
3. Extraer texto según formato: PDF con pdftotext, DOCX con python-docx, DOC con catdoc/antiword
4. Aplicar chunking semántico si el texto excede el límite práctico de tokens
5. Enviar a Qwen/Gemma con prompt JSON estructurado (sin response_format)
6. Parsear respuesta JSON

Ver `references/thinkpad-p53-llamacpp-setup.md`, `scripts/extractor.py` (en /home/usuario/Escritorio/PyCode/QwenLegalExtractor/), `scripts/chunking_demo.py` (misma ruta), `scripts/test_gemma4.py` (misma ruta), `reports/comparativa_final_qwen_vs_gemma4.md`, `reports/comparativa_qwen_vs_gemma4.md`, `references/gemma4-e2b-test-results.md`, `references/warmup-benchmark.md`, `references/kgraph-integration.md`.

**Lo que NO se recomienda:**
- Modelos 8B+ que no quepan ni parcialmente en GPU
- Modelos 1.5B (pierden calidad en entidades legales complejas)
- Usar LLM local para clasificación inicial (regex es ~185 docs/s, LLM es ~0.017 docs/s)

### Fase 12: Consolidación de Reportes Multi-Lote y Análisis de Corpus

**Datos reales del corpus completo (Jun 2026, 7 fuentes):**

| Fuente | Archivos |
|--------|:--------:|
| ResolucionesSAL/PDFs | 558,329 |
| Saleman/DescargaTotalSALACOMPIE-COPIADO | 374,570 |
| Descargas/SAL/Files | 73,968 |
| Saleman/FundadaSolesDolares | 48,344 |
| Saleman/varios | 21,514 |
| Saleman/DescargaPJpc-lnvhome3PENDIENTE-EXTRACT | 17,604 |
| Saleman/DESCARGA-PESQUERA | 13,554 |
| **Total bruto** | **1,107,883** |
| **Duplicados (por nombre exacto)** | **-301,283** |
| **Total únicos** | **806,600** |
| PDF: 695,052 / DOC: 111,530 / Otros: 18 |

**Proporción con valor jurídico:** De los 558,334 documentos en ResolucionesSAL/PDFs (fuente primaria mejor analizada), 451,521 tienen valor jurídico (80.9%): 243,288 sentencias + 192,116 resoluciones + 16,117 demandas.

**Estimación para todo el corpus:** ~652,539 documentos con valor jurídico (562,297 PDFs + 90,242 DOC).

**Pitfall: pdftotext es ~2-3x más rápido que pymupdf para extracción masiva de primera página.** La diferencia es dramática en lotes de 100K+ documentos. Para 435K PDFs:
- pymupdf (1 hilo, 2 págs): ~170 docs/s → ~43 min
- pdftotext (1 hilo, 1 pág): ~225 docs/s → ~32 min
- pdftotext (8 workers, 1 pág): ~400-480 docs/s → ~15-18 min

Usar `ProcessPoolExecutor` con `pdftotext` es la opción recomendada para extracción masiva de texto de carátulas (solo página 1, sin -layout).

**Pitfall**: `ProcessPoolExecutor` con 8 workers en un disco USB externo puede saturar el bus I/O. Si ves que la velocidad no escala linealmente al aumentar workers, reduce a 4. Para discos NVMe internos, 8-12 workers funciona bien.

## Valor jurídico para el pipeline RAG (post-clasificación)

**Preferencia del usuario:** solo importan las **sentencias y resoluciones con valor jurídico sustantivo**. Los demás tipos documentales (notificaciones, oficios, citaciones, actas de audiencia, conciliaciones) no deben priorizarse en el pipeline RAG. Categorías enteras como "Acta de Audiencia" (~3,393 recuperadas) son irrelevantes si no son resoluciones/sentencias.

Para filtrar por valor dentro de las sentencias+resoluciones:

No todas las resoluciones clasificadas tienen el mismo valor para un sistema RAG. Las **resoluciones interlocutorias** (1-2 páginas, "mero trámite": tener por apersonado, proveer escrito, correr traslado) tienen bajo valor jurídico. Las **resoluciones completas** (3+ páginas, con CONSIDERANDOS, citas legales, análisis jurídico sustantivo) tienen **alto valor para RAG**.

Al reclasificar no_clasificados, las ~1,000 resoluciones completas rescatadas (identificadas por tener 3+ páginas) son las de mayor valor — contienen fundamentación legal: citas de códigos, jurisprudencia, análisis de admisibilidad (amparo, contencioso administrativo), etc.

Para filtrar por valor en el pipeline RAG:
- **Alto valor**: sentencias + resoluciones de 3+ páginas que contienen "PRIMERO:", "SEGUNDO:", "CONSIDERANDO", "FUNDAMENTOS"
- **Valor medio**: resoluciones de 1-2 páginas con algún fundamento ("ATENDIENDO:", "Que, ...")
- **Bajo valor**: resoluciones de 1 página con solo "Téngase presente/presente por" — trámite puro

En el archivo de salida CSV, el campo `paginas` es un buen proxy inicial: filtrar `paginas >= 3` para contenido jurídico sustantivo.

### Fase 9: Procesamiento de DOC/DOCX (formato Word)

No todos los archivos judiciales vienen en PDF. Los archivos `.doc` y `.docx` requieren herramientas distintas:

| Formato | Herramienta | Velocidad típica |
|---|---|---|
| `.docx` | `python-docx` (`Document(path).paragraphs`) | ~200 docs/s |
| `.doc` (binario) | `python-docx` (falla a veces) o `olefile` | ~150 docs/s |
| `.doc` corrupto | Ambos fallan → clasificar como "error" | — |

```python
# Para .docx (moderno)
from docx import Document
doc = Document(path)
txt = ' '.join(p.text for p in doc.paragraphs[:50])

# Para .doc (binario antiguo)
try:
    from docx import Document
    doc = Document(path)  # A veces funciona aunque sea .doc
except:
    import olefile
    ole = olefile.OleFileIO(path)
    txt = ole.openstream('WordDocument').read().decode('utf-8', errors='ignore')[:3000]
```

**Performance con mix PDF+DOC:**
- PDFs: `ProcessPoolExecutor(workers=12)` con `pdftotext` (sin `-layout`)
- DOCX: `ThreadPoolExecutor(workers=12)` con `python-docx` (I/O bound, no CPU)
- NO mezclar pools — procesar PDFs primero, DOCS después en secuencia
- Los DOC son ~2x más lentos que los PDFs (~200 vs ~400 docs/s)

**Pitfall: CSV de resultados se rompe si el campo materia contiene comas.** Si el CSV se genera con concatenación manual (`f.write(...)`) en vez de `csv.writer`, y el campo materia contiene comas, el archivo se corrompe. Al leerlo aparecen nombres de personas como categorías porque el split por comas se desalinea (ej: `read_csv` interpreta nombres propios como categorías). Usar SIEMPRE `csv.writer` o `csv.DictWriter` para cualquier CSV que pueda contener texto legal con comas, puntos y coma, o saltos de línea.

**Pitfall: algunos .doc tienen extensión .doc pero son formato binario antiguo.** `python-docx` solo abre Office Open XML (.docx). Para `.doc` legacy probar primero con `python-docx`, y si lanza `PackageNotFoundError`, caer en `olefile`. Si ambos fallan, clasificar como "error".

**Referencia:** este método procesó 104,346 DOC/DOCX + 137,241 PDFs en 19 min (210 docs/s) en un lote real.

### Fase 10: Procesamiento de Nuevos Lotes (evitando duplicados)

Cuando aparecen nuevas fuentes de datos, NO reprocesar todo desde cero. Usar deduplicación por nombre de archivo:

```python
# 1. Construir set de ya clasificados (por nombre de archivo)
known = set()
for cat_dir in os.listdir(CLASIFICADOS_DIR):
    for f in os.listdir(os.path.join(CLASIFICADOS_DIR, cat_dir)):
        known.add(f.lower())

# 2. Identificar solo archivos nuevos en las fuentes
pdfs, docs = [], []
for source_dir in [dir1, dir2, dir3]:
    for f in os.listdir(source_dir):
        if f.lower() in known:
            continue  # ya clasificado
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(source_dir, f))
        elif f.lower().endswith(('.doc', '.docx')):
            docs.append(os.path.join(source_dir, f))
```

**Técnica para DOC/DOCX** (formato Word, no PDF):
- `.docx` → `python-docx` (Document(archivo).paragraphs)
- `.doc` (formato binario antiguo) → `olefile` para abrir y extraer stream WordDocument
- Ambos fallan con archivos corruptos — capturar excepción y clasificar como "error"

**Performance mix (PDFs + DOCS simultáneos):**
- PDFs: `ProcessPoolExecutor(workers=12)` con `pdftotext` (sin -layout)
- DOCX: `ThreadPoolExecutor(workers=12)` con `python-docx` (I/O bound, no CPU bound)
- Los DOC son ~2x más lentos que los PDFs (~200 vs ~400 docs/s)
- Procesar PDFs primero, DOCS después, en secuencia (no mezclar pools)

**Script disponible:** `scripts/clasificador_lote2.py` — procesa lotes adicionales contra un set de conocidos, genera CSV y JSON separados. Diseñado para hardware i7-9850H (12 hilos) con disco HDD USB como bottleneck. Ajustar `MAX_WORKERS_PDF` según el disco: 8 para HDD USB, 12 para NVMe.

**Hardware observado (ThinkPad P53, i7-9850H):**
- 6 núcleos físicos / 12 hilos @ 2.6-4.6 GHz
- 46 GB RAM
- El cuello de botella real es el **disco de origen** (HDD USB ~100 MB/s), no la CPU
- 12 workers saturan el bus I/O del USB; 8 workers es el punto óptimo para HDD
- Para NVMe interno, 12 workers funciona bien

### Fase 11: Consolidación de Reportes Multi-Lote

Después de procesar múltiples lotes (ej: Lote 1 = clasificación inicial, Lote 2 = archivos nuevos de otras fuentes), generar un reporte consolidado que:

1. **Identifica solapamiento por nombre de archivo** — nunca contar dos veces
2. **Suma distribuciones** por categoría acumulada
3. **Lista fuentes** procesadas con tamaños y tiempos
4. **Indica pendientes** si los hay

```python
# Construir set completo de archivos conocidos (por nombre, case-insensitive)
known = set()
for cat_dir in os.listdir(CLASIFICADOS_DIR):
    for f in os.listdir(os.path.join(CLASIFICADOS_DIR, cat_dir)):
        known.add(f.lower())

# Nuevos lote: solo los que NO están en known
nuevos = 0
for name in lote2_nombres:
    if name not in known:
        nuevos += 1

# Total único = len(known) + nuevos
```

**Estructura del reporte consolidado (formato txt):**
- Totales por cada lote (archivos, tiempo, velocidad)
- Distribución combinada (sin duplicados)
- Documentos con valor jurídico (Sentencia + Resolución) acumulados
- Lista de fuentes de datos procesadas
- Archivos generados

**Resultados reales de esta sesión (dos lotes):**
- Lote 1 (ResolucionesSAL/PDFs): 479,817 clasificados en ~62 min
- Lote 2 (carpetas nuevas, mix PDF+DOC): 241,587 clasificados en 19 min
- Total único: **806,600 documentos** (301,283 eliminados como duplicados entre 7 fuentes)
- Sentencias + Resoluciones acumuladas: 547,572 (68.4%)

Nota sobre formato de reporte preferido: guardar reportes como .txt (para leer en terminal) y .json (para lookup tables programaticas). Colocar todo en reports/. Ver resultados completos del Lote 2 en references/lote2-resultados.md.
- Total único: **806,600 documentos** (0% duplicados por nombre exacto, 301,283 duplicados entre fuentes)
- Sentencias + Resoluciones acumuladas: **547,572 (68.4%)**
- Tiempo total de clasificación: ~81 min (todo en un día)

**Formato preferido del usuario:** guardar reportes como `.txt` y `.json`. El `.txt` para leer en terminal, el `.json` para lookup tables programáticas (materia→área legal). Colocar en `reports/`.

Después de procesar múltiples lotes, generar un reporte consolidado que:
1. Suma todos los lotes procesados
2. Muestra distribución acumulada
3. Lista las fuentes procesadas y sus tamaños
4. Indica cuántos archivos siguen pendientes (si los hay)

**Formato preferido del usuario:** guardar como `.txt` (legible en terminal) y `.md` (estructurado para lectura en navegador). Guardar en `reports/`.

## Pitfalls comunes

1. **"Resolución Nro." no matchea "RESOLUCIÓN NÚMERO"** — Usar regex con alternativas: `N[UÚ]MERO|N[°º]|NRO\\.`
2. **PDFs escaneados/imagen** — Si no tiene texto extraíble (< 50 chars), va a `sin_texto`. No hay OCR automático; requiere tesseract.
3. **Archivos corruptos** — pymupdf lanza excepción. Capturarla y mandar a carpeta de errores.
4. **Backup comprimido** — Los PDFs ya están comprimidos internamente. `tar -czf` de 72GB → ~40-50GB. Decide si vale la pena.
5. **Truncado duro a 7000 chars PIERDE el RESUELVE (fallo).** El corte por posición fija pierde sistemáticamente el RESUELVE, los nombres de los jueces, y notas al pie. Usar chunking semántico o priorizar el final del documento.
6. **Prompt JSON + .format() colisiona.** El JSON del prompt contiene llaves `{ }` que Python .format() interpreta como placeholders. Error: `KeyError: '"resumen_hechos"'`. Usar f-strings con la variable texto como único placeholder, o concatenación de strings. Nunca `.format(texto=texto)` en un string que contiene JSON con llaves.
7. **JSON truncado por Qwen (max_tokens insuficiente).** Qwen a veces genera JSONs incompletos (`Unterminated string`). Implementar reparador multi-intento que recorte progresivamente hasta encontrar el último `}` válido.
8. **Nombres de archivo con espacios** — Al crear symlinks, usar ruta absoluta como target.
9. **Nombres de directorio con caracteres especiales (ó, é, í)** — Al iterar sobre categorías como "Resolución" (con ó), NO uses `string.replace('ó','o')` para normalizar el nombre del directorio. El nombre real en disco se llama "Resolución", no "Resolucion". Usar la ruta exacta del CATEGORY_NAMES o leer con `os.listdir()`.
10. **pdftotext no siempre extrae texto con codificación UTF-8 correcta** — En PDFs generados por sistemas legacy del Poder Judicial peruano, caracteres como "Ó" pueden aparecer como "?" o "O". Siempre buscar patrones con alternativas: `RESOLUCI[OÓ]N`, `N[UÚ]MERO`.
11. **Preferencia del usuario: solo importan sentencias y resoluciones con valor juridico sustantivo para el RAG.** Documentos de trámite (notificaciones, oficios, citaciones, actas de audiencia, conciliaciones) no deben priorizarse en el pipeline RAG aunque aparezcan clasificados. Filtrar por paginas >= 3 y presencia de CONSIDERANDO o SE RESUELVE para identificar contenido jurídico sustantivo. Las ~1,000 resoluciones completas rescatadas de no_clasificados (3+ páginas) son las de mayor valor.
12. **Encabezados repetidos** — Los PDFs judiciales peruanos suelen tener texto solapado (4-5 veces). No afecta el matcheo pero infla el texto extraído.
13. **OOM con -ngl 24 en Quadro T1000 4GB.** Forzar -ngl 20 para Qwen 7B. Gemma 4 E2B solo funciona con -ngl 12 y contexto 4096 — y aún así es 51% más lento que Qwen 7B.
**⚠ Pitfall: Procesos Python en background de Hermes NO flushean output y mueren por tcsetattr.**\nCuando Hermes ejecuta un comando largo en background (terminal background=true), el shell bash recibe una señal `SIGTTOU` (tcsetattr: Función ioctl no apropiada para el dispositivo) y el proceso hijo muere con exit code 143 o 255. Síntomas: proceso muere tras primer print(), log vacío, mensaje \"tcsetattr\" en stderr.\n\nSoluciones por orden de preferencia:\n1. **execute_code()** — Usar execute_code de Hermes. Ejecuta Python directamente sin bash intermediario, evitando el PTY problemático. Es la opción más confiable para scripts de hasta 600s.\n2. **Redirigir a archivo** — Usar: `PYTHONUNBUFFERED=1 python3 -u script.py > log.txt 2>&1`. El stdout va directo a archivo sin pasar por el pipe de Hermes. Luego monitorear con `tail -f log.txt` en otro terminal().\n3. **batch_runner.py** — Script que usa subprocess.Popen desde Python puro para lanzar llama-server como proceso hijo. No pasa por bash, no tiene problemas de PTY. Probado y funcionando (ver `batch_runner.py` en KGraphResolucionesV3/).\n4. **Lanzar.sh + tee** — Script bash que usa `| tee archivo.log` en vez de redirección de shell de Hermes. Ejecutar directamente desde terminal del usuario, no desde Hermes background.\n\nNO usar nohup/&/setsid desde terminal foreground de Hermes — el bloqueo de señal llega igual. NO confiar en el output preview de process(action='poll') para procesos que generan mucho output — el buffer se pierde al matar el proceso.

**Pitfall: response_format type json_object NO funciona con llama.cpp.** Solo OpenAI/Groq soportan este parámetro. En llama.cpp, forzar JSON en el prompt de texto sin formato.
15. **catdoc/antiword no instalados por defecto en Ubuntu 24.04.** Para procesar .DOC legacy: `sudo apt-get install -y catdoc antiword`.
16. **Server no persiste tras reboot.** Hay que iniciar llama-server manualmente cada vez.
17. **Gemma 4 thinking mode:** Deshabilitar con `--reasoning off` (llama.cpp moderno). `--chat-template-kwargs` está deprecado en builds recientes.
18. **python-docx NO abre formato .doc binario antiguo.** Usar catdoc o antiword como fallback.
19. **Warmup crítico en batch:** Primera consulta ~18s (carga KV cache), siguientes ~5s. NO reiniciar server entre documentos.
20. **Proceso Python no flushea output en background de Hermes.** Usar `> archivo.log 2>&1` y monitorear con `tail -f`. O usar `PYTHONUNBUFFERED=1 python3 -u`.

**Flujo de integración con KGraphResolucionesV3:**

El `indexer.py` del repo espera archivos `rag_listo_batch_*.json` con esta estructura:
```python
doc = {"id_documento": "...", "contenido_a_vectorizar": {"hechos":"...", "problema":"...", "fallo":"..."},
       "metadatos_graphrag": {"jueces_magistrados":[], "demandantes_accionantes":[], "demandados_accionados":[],
                              "leyes_y_articulos_citados":[], "conceptos_legales_clave":[]}}
```
Flujo: `extractor.py` genera `rag_listo_batch_qwen_*.json` → `indexer.py --force` reconstruye FAISS+BM25+NetworkX → las consultas con `graphrag_pro.py`/`graphrag_console.py` funcionan sin cambios.

**Precauciones:**
- Hacer backup de pipeline/indexer.py, core/config.py, core/embedding.py, retrieval/hybrid_search.py antes de modificar
- El doc_id debe ser único por documento (usar hash del texto + nombre)
- Los JSONs se guardan en `data_raw/` con checkpoints cada 100 documentos
- Ejecutar `python3 pipeline/indexer.py --force` después del batch para reindexar

Ver `references/kgraph-integration.md` para el formato exacto y extractor de ejemplo.

## Referencia

Ver `references/groq-cost-analysis.md` con análisis de costos Groq vs local para batch processing masivo (192K-575K documentos).
Ver `references/groq-batch-results.md` con resultados reales de la prueba de 100 docs vía Groq (1.2s/doc, 98% éxito).
Ver `references/groq-batch-workflow.md` con el workflow completo de Groq Batch API, comparativa de modelos, y el hallazgo crítico de max_tokens=640 para 99% JSON valido.
Ver `references/background-process-death.md` con diagnóstico y soluciones para procesos Python que mueren en background de Hermes.
Ver `references/categorias-judiciales.md` con patrones regex exactos y ejemplos de texto real de esta sesión.
Ver `references/materias-judiciales.md` con la distribución real de materias (9,295 valores, top 20 con frecuencias).
Ver `references/normalizacion-materias.md` con el mapeo completo materia → área legal.
Ver `references/analisis-redundancia.md` con el análisis de reducción de 13 categorías a 4 dimensiones reales.
Ver `references/lote2-resultados.md` con los resultados del procesamiento del segundo lote (241K archivos, mix PDF+DOC).
Ver `references/consolidacion-multi-lote.md` con los resultados consolidados de 799,993 documentos únicos clasificados en dos lotes.
Ver `references/reporte-consolidado.md` con el reporte final que integba todos los procesos (clasificación, materias, normalización, análisis de redundancia).
Ver `references/qwen-extraccion-resultados.md` con los resultados de prueba de extracción estructurada con Qwen 2.5 7B local (JSON, tiempos, pitfalls).