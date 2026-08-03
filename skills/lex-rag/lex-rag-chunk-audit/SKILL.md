---
name: lex-rag-chunk-audit
description: Trazabilidad granular de chunks + verificación de citas en RAG legal — FAISS/BM25/RRF audit, Graph audit, Critic Agent (detección de alucinaciones), y repreguntas conversacionales.
---

# Auditoría Granular de Chunks para Lex RAG

## ¿Qué resuelve?

Sin auditoría granular, no sabes qué chunks específicos alimentaron la respuesta del LLM, qué scores tenían, cuáles fueron descartados en la fusión RRF, ni qué nodos del grafo se procesaron. Este patrón añade trazabilidad completa a la salida de cada consulta RAG.

Funciona para cualquier pipeline RAG híbrido (vector + BM25 + grafo). Se adapta cambiando las funciones de retrieval que se instrumentan.

## Implementación

### 1. Modificar `get_hybrid_context()` — retornar audit

La función de búsqueda híbrida (FAISS + BM25 + RRF fusion) debe retornar `(top_docs, text_context, audit_dict)` en vez de solo `(top_docs, text_context)`.

El audit captura:

```python
# FAISS raw: 21 chunks con distancia coseno
faiss_audit = [{
    "chunk_index": int(idx),
    "doc_id": meta["doc_id"],
    "distance": float(dist),
    "rank": rank + 1,
    "snippet": meta["text"][:200]
} for rank, (idx, dist) in ...]

# BM25 raw: 21 chunks con score lexical
bm25_audit = [{...相同形状... "bm25_score": float(score) }]

# RRF fusion: chunks rankeados + chunks descartados
for rank, (chunk_idx, score) in enumerate(sorted_chunks):
    entry = {
        "chunk_index": int(chunk_idx),
        "doc_id": meta["doc_id"],
        "rrf_score": float(score),
        "rank": rank + 1,
        "in_top_chunks": bool,
        "snippet": meta["text"][:200]
    }

# Documentos finales seleccionados
final_docs_audit = [{"doc_id": d, "label": label, "rank": r} ...]
```

### 2. Modificar `get_graph_context()` — retornar audit

```python
graph_audit = {
    "doc_ids_input": doc_ids,
    "nodes_with_data": [...],  # cada nodo: {doc_id, fallo[:200], neighbors: [{node, relation, hop2_docs?}]}
    "neighbors_found": [...],  # lista plana de entidades únicas
    "total_edges_processed": N
}
```

### 3. Agregar `save_chunk_audit()` en logger

```python
def save_chunk_audit(query, hybrid_audit, graph_audit, response, decision, hyde_query, elapsed=None):
    audit = {
        "metadata": {"timestamp", "query", "decision", "hyde_query", "elapsed_seconds"},
        "retrieval": {"hybrid": hybrid_audit, "graph": graph_audit},
        "response": {"text": response, "tokens_estimados": len(response)//4}
    }
    path = f"consultas_guardadas/{timestamp}_{clean_query}_audit.json"
    json.dump(audit, f, ensure_ascii=False, indent=2)
```

### 4. Encadenar en el orquestador

```python
async def run_console_query(query):
    decision, hyde = route_query_and_hyde(query)
    hybrid_audit = graph_audit = None
    if "LOCAL" in decision:
        top_docs, text_context, hybrid_audit = get_hybrid_context(hyde, top_k=7)
        graph_context, graph_audit = get_graph_context(top_docs)
    ...
    # Pasar audit al synthesizer
    async for chunk in generate_rag_synthesis(..., hybrid_audit=hybrid_audit, graph_audit=graph_audit, elapsed=elapsed):
        ...
```

### 5. Guardar en synthesizer

```python
if ans:
    save_query_log(query, ans, contexto_raw)
    if hybrid_audit or graph_audit:
        save_chunk_audit(query, hybrid_audit, graph_audit, ans, decision, hyde_query, elapsed)
```

## Archivos modificados (Lex RAG)

| Archivo | Cambio |
|---|---|
| `retrieval/hybrid_search.py` | `get_hybrid_context()` retorna `(top_docs, text_context, audit)` |
| `retrieval/graph_search.py` | `get_graph_context()` retorna `(text, audit)` |
| `utils/logger_utils.py` | Nueva `save_chunk_audit()` |
| `agents/synthesizer.py` | Importa + llama `save_chunk_audit()` |
| `graphrag_pro.py` | Colecta audit de hybrid + graph |
| `api.py` | Igual para la API FastAPI |

## Formato de salida

Cada consulta genera en `consultas_guardadas/`:
## Salida en consultas_guardadas/
```
YYYYMMDD_HHMMSS_query_clean.md              # consulta + modo + respuesta + contexto
YYYYMMDD_HHMMSS_query_clean.txt             # plano
YYYYMMDD_HHMMSS_query_clean_audit.json      # auditoría granular
YYYYMMDD_HHMMSS_query_clean_deep.md         # versión Deep Research
YYYYMMDD_HHMMSS_query_clean_deep.txt
YYYYMMDD_HHMMSS_query_clean_deep_audit.json
```

El sufijo `_deep` se agrega automáticamente cuando `mode="deep"`. El modo también se guarda en el metadata del audit JSON y en el encabezado del .md/.txt.

Referencias: `references/critic-agent.md`, `references/critic-edge-cases.md`, `references/retrieval-strategist.md`, `references/retrieval-strategist-options.md`, `references/multiagent-plan.md`, `references/test-plan-20-queries.md`, `references/bateria-final-20.md`, `references/analisis-ponderado.md`, `references/graph-analyst.md`, `references/feedback-loop.md`, `references/deep-search.md`, `references/bateria-final-completa.md`, `references/estado-proyecto.md`, `references/deep-research-implementacion.md`, `references/header-enrichment.md`, `references/batch-testing-june2026.md`, `references/citation-validation-research.md`.

### Estructura del audit JSON

```json
{
  "metadata": { "timestamp", "query", "decision", "hyde_query", "elapsed_seconds" },
  "retrieval": {
    "hybrid": {
      "query": "...",
      "top_k": 7,
      "faiss_raw": [{ "chunk_index", "doc_id", "distance", "rank", "snippet" }],
      "bm25_raw": [{ "chunk_index", "doc_id", "bm25_score", "rank", "snippet" }],
      "rrf_ranked": [{ "chunk_index", "doc_id", "rrf_score", "rank", "in_top_chunks", "snippet" }],
      "chunks_filtered_out": [{ ... }],
      "final_docs": [{ "doc_id", "label", "rank" }]
    },
    "graph": {
      "doc_ids_input": ["..."],
      "nodes_with_data": [{ "doc_id", "fallo", "neighbors": [{ "node", "relation", "hop2_docs" }] }],
      "neighbors_found": ["..."],
      "total_edges_processed": N
    }
  },
  "response": { "text", "tokens_estimados": N },
  "critic": {
    "passed": bool,
    "score": float,
    "hallucinated": int,
    "verified": int,
    "unverifiable": int,
    "citations": [{"doc_id", "identificador", "exists_in_corpus", "hallucinated"}]
  },
  "feedback": {
    "iterations": int,
    "corrections": []
  }
}
```

## Batch Testing Acceleration (modelo compartido)

Ejecutar baterías vía subprocess (`subprocess.run`) recarga el modelo Sentence-Transformer en CADA query (~80s por query). La alternativa correcta es importar `run_console_query()` directamente en un solo proceso Python — el modelo se carga UNA vez.

### Comparativa de rendimiento (15 queries, Junio 2026)

| Método | Tiempo total | Por query | Overhead |
|---|---|---|---|
| Subprocess (modelo ×15) | 36:55 min | ~148s | Recarga Sentence-Transformer ×15 |
| Directo (modelo ×1) | 6:39 min | ~27s | Solo carga inicial |
| **Mejora** | **5.5× más rápido** | | |

### Script de referencia

```python
# scripts/bateria_15_directa_v2.py — patrón correcto
import sys; sys.path.insert(0, "/mnt/d/PyCode/ResumenTokensJurisprudencias")
from graphrag_pro import run_console_query

async def run_one(pregunta):
    # SIN suprimir stdout — los prints fluyen libremente
    respuesta, follow_ups, _ = await asyncio.wait_for(
        run_console_query(pregunta),
        timeout=300
    )
    return respuesta, follow_ups
```

### Pitfall: NO usar redirect_stdout con async generators

```python
# ❌ ESTO ROMPE EL ASYNC GENERATOR:
with contextlib.redirect_stdout(io.StringIO()):
    respuesta, follow_ups, _ = await run_console_query(pregunta)

# ❌ ESTO TAMBIÉN ROMPE:
old_stdout = sys.stdout
sys.stdout = NullWriter()  # clase que descarta
respuesta, follow_ups, _ = await run_console_query(pregunta)
sys.stdout = old_stdout

# ✅ CORRECTO: dejar stdout intacto
respuesta, follow_ups, _ = await run_console_query(pregunta)
```

El async generator de `run_console_query` emite chunks vía `yield` mientras hace `print()` — suprimir stdout rompe el flujo asíncrono causando deadlock. El output de log (~5-10KB por query) no llena el pipe buffer de 64KB en <10 queries.

## Environment Setup

### HF_TOKEN (obligatorio para descargas rápidas)

Sin token, HuggingFace limita las descargas anónimas a ~1 MB/s. Con token gratuito (Read access to public gated repos), la velocidad sube a ~10-20 MB/s. El modelo `distiluse-base-multilingual-cased-v2` (~250 MB) baja en ~15s en vez de ~80s.

```bash
# Agregar al .env del proyecto:
echo "HF_TOKEN=hf_..." >> .env
```

El token se crea en https://huggingface.co/settings/tokens (tipo "Read", permiso mínimo: "Read access to contents of all public gated repos you can access"). `load_dotenv()` en `core/config.py` lo carga automáticamente y `huggingface_hub` lo detecta.

### Dependencias críticas (venv_linux)

El `venv_linux/` puede estar incompleto. Verificar que existan:

```bash
source venv_linux/bin/activate
pip list | grep -E "openai|groq|rank-bm25|transformers|torch|scikit-learn|sentence-transformers|faiss-cpu|networkx"
```

Si faltan:
```bash
pip install openai groq rank-bm25 transformers torch scikit-learn sentence-transformers
```

- **Cobertura FAISS vs BM25**: cuántos docs aparecen solo en FAISS, solo en BM25, o en ambos
- **Tasa de filtrado RRF**: cuántos chunks entran al top-14 vs cuántos se descartan
- **Diversidad de fuentes**: si los 7 documentos finales cubren distintos tribunales
- **Tiempo por consulta**: separar retrieval vs generación
- **Profundidad del grafo**: aristas procesadas, vecinos únicos encontrados

## Critic Agent — Verificador de Citas

El **Critic Agent** (`agents/critic.py`) es un verificador post-generación que detecta alucinaciones en citas jurisprudenciales. Se ejecuta después del Legal Writer y antes de mostrar la respuesta al usuario.

### Arquitectura

```
Respuesta del LLM
  → extract_citations() → 6 patrones de extracción
    → verify_citations() → coteja contra metadata_docs.json (64K docs)
      → score_verdict() → produce Verdict(passed, score, action)
        → Audit JSON se actualiza con clave "critic"
```

### Patrones de extracción de citas

| # | Patrón | Ejemplo | Confianza |
|---|--------|---------|-----------|
| 1 | `Jurisprudencia/XXXXX.html` | `Jurisprudencia/1308950.html` | Alta (doc_id directo) |
| 2 | `EXP. N.º XXXX` | `EXP. N.º 1308950` | Textual (solo identificador) |
| 3 | `CAS. N° XXXX` | `CAS. N° 1080-2004` | Textual |
| 4 | `RTF N° XXXX` | `RTF N° 12345` | Textual |
| 5 | `XXXXX.html` suelto | `1308950.html` | Alta (doc_id) |
| 6 | Números de 6-7 dígitos | `1308950` | Alta (no hay doc_ids de 5 dígitos en el corpus) |

### Lógica de verificación

- Si tiene **doc_id**: verificable contra metadata
- Si solo tiene **identificador textual**: indeterminado, no se marca como alucinación

### Exclusiones para Pattern 6 (números sueltos)

- Años (19XX, 20XX): no aplica porque `\d{6,7}` ya excluye números de 4 dígitos
- Leyes/normas: no aplica porque todos los números de leyes tienen ≤5 dígitos y el patrón solo captura 6-7

### Scoring

Solo cuentan citas **verificables** (con doc_id). Las textuales se excluyen del score.

### Integración en audit JSON

```json
{
  "critic": {
    "passed": true,
    "score": 1.0,
    "total_citations": 7,
    "hallucinated": 0,
    "verified": 4,
    "unverifiable": 3
  }
}
```

### Tasas empíricas de alucinación (consolidadas Jul 2026)

La investigación de 6 papers (ver `references/citation-validation-research.md`) confirma
que las tasas de alucinación en RAG legal son un problema persistente y medible:

| Sistema | Tasa | Fuente |
|---------|:----:|--------|
| Lexis+AI / Westlaw AI | 17-33% | Dahl 2025 (arXiv:2405.20362) |
| Claude Haiku 4.5 | 21% | Citation Grounding (arXiv:2606.00898) |
| Amazon Nova Pro | 13% | Citation Grounding (arXiv:2606.00898) |
| Standalone LLM (GPT-4) | >30% FCR | Reliability by Design (arXiv:2601.15476) |
| Basic RAG | 5-15% FCR | Reliability by Design (arXiv:2601.15476) |
| Advanced RAG + verification | <0.2% FCR | Reliability by Design (arXiv:2601.15476) |

El verificador programático (91.2% recall) **supera** a GPT-5 agentic (82.8% recall)
en detección de hallucinaciones legales, con costo insignificante (Who Checks Citations,
arXiv:2606.21155). Esto valida el enfoque del CriticAgent.

### Pipeline de 4 verificaciones secuenciales (recomendado)

Para cerrar el bypass de citas indeterminadas, implementar este pipeline
post-generación (ver implementación de referencia en
`/mnt/c/Users/usuario/rag_citation_validator.py`):

```
Etapa 1: Verificación por subcadena exacta (doc_id → metadata_docs.json)
Etapa 2: DB lookup de identificadores textuales (EXP/CAS/RTF → doc_id)
Etapa 3: Fuzzy matching para OCR/reformateo (SequenceMatcher threshold=0.70)
Etapa 4: Detección de citas indeterminadas (heurística: año fuera de rango,
         número excesivo, dígitos repetidos, secuencias obvias, leyes ficticias)
```

### Citas indeterminadas — el bypass documentado

Una cita indeterminada tiene formato legal correcto y números verosímiles pero
NO existe en el corpus. Es el tipo más peligroso porque:
- El ojo humano las acepta como válidas
- El CriticAgent tradicional las categoriza como exists_in_corpus=None → hallucinated=False
- El feedback loop no las corrige (solo chequea hallucinated > 0)

Señales de alarma implementables:
- Año futuro (>2026) o muy antiguo (<1995)
- Número excesivo (>5000 para CAS, >50000 para EXP)
- Dígitos repetidos (99999, 11111)
- Secuencias obvias (12345)
- Ley con número >50000

Fix del feedback loop en `_needs_rewrite()`:
```python
def _needs_rewrite(critic_verdict):
    vd = critic_verdict.to_dict()
    return vd.get("hallucinated", 0) > 0 or vd.get("unverifiable", 0) > 0
```

## Retrieval Strategist Agent — Estrategia Adaptativa de Recuperación

El **Retrieval Strategist** (`agents/retrieval_strategist.py`) analiza la consulta ANTES del retrieval y define parámetros óptimos de búsqueda. Es el segundo agente del plan multi-agente (Fase 2).

### Arquitectura híbrida final (Opción B v2)
```
analyze(query):
  ├── Keywords estadísticos?         → k=12, graph_depth=2 (sin LLM)
  ├── < 7 palabras?                  → k=4,  sin grafo      (sin LLM)
  ├── "comparar"/"diferencia"? +≥7w  → k=10, graph_depth=2 (sin LLM)
  ├── " y " conectando? + 7-14w      → k=7,  graph_depth=1 (sin LLM)
  ├── ≥ 15 palabras?                 → k=11, graph_depth=2 (sin LLM)
  ├── Ambigüedad (7-14 palabras)?    → LLM decide simple vs media
  └── LLM no disponible?             → fallback heurístico
```
Precisión: 86% (18/21) · LLM calls: 2/21 · Reglas duras: 19/21

### Cómo funciona en el pipeline

```python
strategy = strategist.analyze(query, decision, hyde_query)
# → {"complexity": "media", "top_k": 7, "retrieval_mode": "hybrid", ...}
top_docs, text_context, audit = get_hybrid_context(hyde, strategy=strategy)
graph_context, graph_audit = get_graph_context(top_docs) if strategy["use_graph"] else skip
```

### Clasificación y parámetros

| Nivel | Criterio | top_k | mode | graph |
|-------|----------|-------|------|-------|
| simple | 1 concepto, <7 palabras | 3-5 | hybrid | false |
| media | 2 conceptos, 7-14 palabras | 5-7 | hybrid | true |
| compleja | >14 palabras o 3+ conceptos | 10-12 | hybrid | true |
| estadística | contar/frecuencia/ranking | 12-15 | hybrid | true (depth=2) |

### Fallback heurístico

Si el LLM (llama-3.1-8b-instant) no está disponible, usa reglas determinísticas basadas en:
- Conteo de palabras y caracteres
- Keywords estadísticos (`cuántos`, `qué juez`, `más casos`)
- Keywords semánticos (`principio`, `tendencia`, `diferencia`)
- Keywords léxicos (`artículo`, `código`, `ley nº`)

### Integración en audit JSON

La estrategia se guarda bajo `retrieval.hybrid.strategy`:

```json
{
  "retrieval": {
    "hybrid": {
      "strategy": {
        "complexity": "media",
        "top_k": 7,
        "retrieval_mode": "hybrid",
        "top_k_mult": 3,
        "use_graph": true,
        "graph_depth": 1,
        "reasoning": "..."
      },
      "fusion_params": { "k_rrf": 60, "top_k_mult": 3, "mode": "hybrid" }
    }
  }
}
```

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `agents/retrieval_strategist.py` | Nuevo — clase `RetrievalStrategist` |
| `retrieval/hybrid_search.py` | `get_hybrid_context()` acepta `strategy` dict; respeta `top_k`, `top_k_mult`, `retrieval_mode` |
| `graphrag_pro.py` | Llama strategist.analyze() antes del retrieval; condiciona grafo a `use_graph` |

### Pitfalls

1. **LLM clasifica todo como "media"**: el prompt necesita ser más agresivo con ejemplos concretos de cada nivel. El modelo 8B es conservador por defecto.
2. **top_k_mult no sincronizado**: `hybrid_search.py` usa el mismo multiplicador para FAISS y BM25. Si el strategist sugiere modos asimétricos, hay que modificar la lógica de fusión.
3. **graph_depth no implementado**: el parámetro se guarda en la estrategia pero `get_graph_context()` aún no lo usa para limitar profundidad. Siempre explora 2 saltos.
4. **WEB strategy**: las consultas web usan `_strategy_web()` que ignora todos los parámetros de retrieval local.
5. **Archivos modificados en caliente**: los cambios a `hybrid_search.py` afectan también a `api.py` (que llama `get_hybrid_context` sin strategy, usando valores por defecto).

### Resultados de pruebas (batería final)

20 consultas (5 simples, 5 medias, 5 complejas, 3 estadísticas, 2 comparativas):
- 20/20 exitosas, 759.6s total, 38.0s promedio
- Precisión de clasificación del Strategist: 75% (15/20)
- Crítico: 14/20 score 100%, 6 con hallucinated > 0 (falsos positivos de leyes/normas)
- Reporte: `data/bateria_final_20_consolidado.txt`

Ver `references/bateria-final-20.md`.

### Resultados de pruebas (10 queries)

10 consultas (2 simples, 3 medias, 2 complejas, 2 estadísticas, 1 hipótesis):
- 10/10 exitosas, 406s total, 40.6s promedio
- Critic score 100% en 8/10 consultas
- 2 consultas con hallucinated > 0 (leyes capturadas como doc_ids)
- Reporte: `data/bateria_strategist_20260519_211846.txt`

Ver `references/retrieval-strategist.md` para más detalle.

### Pitfalls

1. **Metadata incompleta**: muchos docs tienen `identificador: "Exp. Nº"` sin número real. No verificar EXP. N° contra eso.
2. **Números de leyes**: "Ley N.º 27803" → `27803.html`. Filtrar con contexto de 30 caracteres.
3. **Fuzzy match falso positivo**: deshabilitado. Solo coincidencias exactas.
4. **Lazy loading**: 64K docs en memoria (~100MB), carga en primer `verify()`.
5. **Respuestas sin citas**: score=0.0 pero pasa (omisión, no alucinación).

## Sistema de repreguntas (follow-up)

El pipeline soporta conversaciones multi-turno en el modo interactivo de `graphrag_pro.py`.

### Cómo funciona

1. **Generación de preguntas de seguimiento**: al final de cada respuesta, el "Bloque Cuestionador LLaMA-3" (`agents/synthesizer.py` líneas 91-123) genera 3 preguntas cortas usando `llama-3.1-8b-instant` basadas en la respuesta emitida. Se emiten como eventos `{"type": "follow_up", "content": ["q1", "q2", "q3"]}`.

2. **Historial de conversación**: `run_console_query()` en `graphrag_pro.py` acepta un parámetro `history` (lista de dicts `{"role": "user"|"assistant", "content": "..."}`) y lo retorna actualizado después de cada consulta.

3. **Repregunta rápida por número**: en modo interactivo, el usuario puede teclear `1`, `2` o `3` para auto-completar la pregunta de seguimiento sugerida, sin tener que copiar/pegar.

### Límites de historial

Configurados en `agents/synthesizer.py`:

```python
MAX_HISTORY_EXCHANGES = 3   # Solo los últimos 3 intercambios (6 mensajes)
MAX_HISTORY_TOKENS = 4000   # Si excede, trunca contenido de mensajes antiguos a 500 chars
```

Lógica de trimming (líneas 49-63):
```python
trimmed = history[-(MAX_HISTORY_EXCHANGES * 2):]  # últimos 6 mensajes
if hist_tokens > MAX_HISTORY_TOKENS:
    for m in trimmed[:-1]:  # trunca todos menos el último
        m["content"] = m["content"][:500] + "... [truncado]"
```

### Flujo completo

```
Usuario: "despido arbitrario"
  → Router + Retrieval + Graph + LLM
  → Respuesta + [1] ¿norma que regula? [2] ¿debido proceso? [3] ¿rol TC?
  → Usuario escribe "1"
  → ↳ Repregunta: ¿Cuál es la norma...?
    → Router + Retrieval + LLM (con historial del turno anterior)
    → Audit JSON también se genera para la repregunta
```

### Archivos modificados para repreguntas

| Archivo | Cambio |
|---|---|
| `graphrag_pro.py` | `run_console_query()` acepta/retorna `(response, follow_ups, history)`. Modo interactivo acumula `conversation_history` y permite atajo numérico. |
| `agents/synthesizer.py` | `MAX_HISTORY_EXCHANGES=3`, `MAX_HISTORY_TOKENS=4000`. History se trunca antes de inyectar. |

### Pitfall: atributos dinámicos en list

```python
# ❌ NO: list no permite atributos dinámicos
conversation_history._last_follow_ups = follow_ups  # AttributeError

# ✅ SÍ: usar variable separada
last_follow_ups = []
# ...
last_follow_ups = follow_ups
```

## Pitfalls

1. **Nombre de archivo duplicado**: si dos queries tienen el mismo clean_query en el mismo segundo, se sobrescriben. Usar timestamp granular (incluir segundos/milisegundos).
2. **Snippet demasiado corto**: el chunk snippet de 200 chars puede cortar contexto crítico. Usar 200-300 según el tamaño del chunk original.
3. **Tiempo de elapsed impreciso**: medir `time.time()` antes y después del retriever completo, no solo de la llamada LLM.
4. **Valores NaN/Inf en FAISS**: algunas distancias pueden ser NaN si el embedding falló. Convertir con `float()` para serialización JSON.
5. **Chunk index -1 en FAISS**: FAISS retorna -1 cuando no hay suficientes resultados. Filtrarlos antes de audit.
6. **Output sin flush en scripts batch**: Python bufferiza stdout cuando no hay TTY. Usar `sys.stdout.flush()` o `PYTHONUNBUFFERED=1` en scripts batch.
7. **Separadores ★ en extracción de respuesta**: el output de graphrag_pro.py tiene el formato `\\n★{80}\\n🏛️...\\n★{80}\\n[streaming]\\n★{80}\\n`. Extraer con `re.search(r'(?<=★{80}\\n)(.*?)(?=\\n★{80})', output, re.DOTALL)` puede capturar solo el header. La respuesta real está entre el segundo y tercer bloque ★.
8. **Respuesta del LLM no disponible en script batch**: como el streaming escribe caracter por caracter, capturar stdout completo puede no incluir la respuesta si el proceso se corta. Usar el audit JSON (`*_audit.json`) como fuente confiable del texto de respuesta, no el stdout.
9. **Audit JSON no se genera si no hay hybrid_audit**: en consultas WEB, `hybrid_audit` es None y no se genera `save_chunk_audit`. Solo LOCAL produce auditoría granular.

## Código: principios de calidad para este proyecto

Preferencias del usuario (abogado litigante peruano, construye Lex RAG):

1. **Código simple, limpio, entendible para humanos** — priorizar legibilidad sobre tersura. Una función de 15 líneas con nombres claros es mejor que 3 líneas de expresiones densas. Cada función debe hacer una cosa y tener un nombre que lo explique.
2. **Paralelizar lo paralelizable** — usar `ThreadPoolExecutor` para tareas independientes (colección de entidades + estadísticas globales en el Graph Analyst). No sobre-ingenerizar: paralelizar solo donde haya ganancia medible. El retrieval FAISS+BM25 es secuencial (BM25 depende del índice que FAISS no necesita) pero podría paralelizarse si la latencia del retrieval fuera el cuello de botella. Priorizar legibilidad sobre micro-optimización.
3. **Código progresivo, no atómico** — "ir despacio, entregar calidad, buen código y mejor resultado". Prefiere cambios incrementales y verificables sobre cambios masivos. Cada fase se prueba antes de pasar a la siguiente.
4. **Preferencia por algoritmos sobre LLM** — si un problema se puede resolver con `Counter()`, `defaultdict` o NetworkX traversal, hacerlo así. El LLM solo para lo que requiere comprensión semántica (clasificar ambigüedades, redactar narrativa). Esto reduce costos, latencia y alucinaciones.
5. **Funciones cortas con nombres descriptivos** — una función no debe exceder ~30 líneas. Si crece, dividir en sub-funciones con nombre que describan qué hacen (ej: `_citar_exp()`, `_citar_cas()`, `_citar_rtf()` en vez de un solo `extract_citations()` de 104 líneas). Cada patrón de regex, cada modo de operación, cada caso merece su propia función.
6. **Estructura plana sobre anidamiento profundo** — preferir `if condicion: return` (guard clause) sobre `if condicion: ... else: ...`. Los `elif` encadenados son aceptables cuando representan una decisión mutuamente excluyente (como las reglas del strategist), pero cada rama debe ser corta y delegar a funciones auxiliares si es necesario.
7. **Features opcionales como flags de CLI** — cuando una funcionalidad cambia el comportamiento del pipeline, debe ser un flag opcional (`--deep`) en vez de un cambio permanente del flujo. Esto permite side-by-side testing y compatibilidad hacia atrás. En modo interactivo, el flag se define al arrancar y aplica a toda la sesión.

## Feedback Loop — Corrección Automática de Citas

El **Feedback Loop** (`graphrag_pro.py`, sección posterior a la generación) conecta el Critic Agent con el Legal Writer para re-escribir automáticamente las partes de la respuesta que contienen citas falsas.

### Arquitectura

```
Writer genera respuesta (streaming) → Critic verifica
  ├── Sin alucinaciones reales → Entrega respuesta ✅
  └── Con alucinaciones → _rewrite_response() → Critic re-verifica
       ├── Ahora OK → Entrega respuesta corregida ✅
       └── Sigue mal → 2da re-escritura (strict) → Entrega con advertencia ⚠️
```

### Salvaguardas anti-loop

| Salvaguarda | Detalle |
|---|---|
| Máx 2 iteraciones | Hard cap `MAX_FEEDBACK_ITER = 2` |
| Solo hallucinaciones REALES | `_needs_rewrite()` ignora identificadores textuales no verificables |
| Strict en 2da iteración | `strict=True` fuerza re-escritura más agresiva |
| Modelo barato | `llama-3.1-8b-instant` para re-write (~$0.0002 por intento) |

### Funciones helper

Definidas en `graphrag_pro.py` como funciones de módulo:

- `_save_critic_to_audit(verdict)` — persiste veredicto en audit JSON
- `_needs_rewrite(verdict)` — decide si re-escribir (solo hallucinated > 0)
- `_rewrite_response(query, original, errores, contexto)` — llama al LLM para corregir

### Verificación

```bash
# El feedback loop solo se activa si el critic detecta hallucinaciones reales.
# Con el fix \d{6,7} en el extractor, la tasa actual es ~0%.
# Para probar: inyectar una cita falsa manualmente en la respuesta y ejecutar el critic.
```

Ver `references/feedback-loop.md`.

## Header Enrichment for Rich Citations

Un RAG legal es tan bueno como la información que el LLM recibe en el contexto. Para que las respuestas citen resoluciones de forma completa (identificador + órgano + juez + partes + fecha), hay que enriquecer **3 capas** del pipeline:

### Las 3 capas

```
Capa 1: Hybrid Search Headers (retrieval/hybrid_search.py)
  ─ Cada chunk lleva su identificador + órgano + fecha + materia
  ─ Código: _doc_header() → (header, fecha, materia)
  ─ Salida: "**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral | Fecha: ... | Materia: ..."

Capa 2: Graph Entity Info (agents/graph_analyst.py)
  ─ Cada doc en la sección FALLOS lleva JUECES, PARTES, LEYES inline
  ─ Datos extraídos del grafo NetworkX (nodos Juez/Actor/Demandado/Ley)
  ─ Salida: "JUECES: Omar Toledo Toribio\nPARTES: Actor(es): X | Demandado(s): Y\nLEYES: ..."

Capa 3: Prompt Instruction (agents/synthesizer.py)
  ─ La instrucción #3 del prompt exige: identificador, órgano, fecha/lugar, juez ponente, partes
  ─ Ejemplo explícito en el prompt: "según **CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral | Lima, 6 de diciembre de 2016 | Ponente: Omar Toledo Toribio"
```

### Detalles de implementación

**hybrid_search.py** — `_doc_header(doc_id)` reemplaza a `_doc_label()`:

```python
def _doc_header(doc_id):
    _load_docs_metadata()
    meta = _docs_metadata.get(doc_id, {})
    if isinstance(meta, dict):
        ident = meta.get("identificador", "") or doc_id
        organo = meta.get("organo", "")
        fecha = meta.get("fecha", "")
        materia = meta.get("materia", "")
        parts = [f"**{ident}**"]
        if organo:
            parts.append(f" | {organo}")
        return "".join(parts), fecha, materia
    return f"**{doc_id}**", "", ""
```

El texto del chunk se construye así:

```python
header, fecha, materia = _doc_header(m['doc_id'])
extra = ""
if fecha:
    extra += f" | Fecha: {fecha}"
if materia:
    extra += f" | Materia: {materia}"
texts.append(f"{header}{extra}\nJurisprudencia/{m['doc_id']}\n{m['text']}")
```

**graph_analyst.py** — en el método `_format()`, después del FALLO:

```python
# Jueces
if jueces:
    nom_jueces = [j.get("node", "").replace("Juez: ", "") for j in jueces]
    lines.append(f"    JUECES: {', '.join(nom_jueces)}")
# Partes
if actores or demandados:
    actor_str = ...; dem_str = ...
    lines.append(f"    PARTES: Actor(es): {actor_str} | Demandado(s): {dem_str}")
# Leyes
if leyes:
    nom_leyes = [l.get("node", "").replace("Ley: ", "") for l in leyes[:4]]
    lines.append(f"    LEYES: {', '.join(nom_leyes)}")
```

**synthesizer.py** — instrucción #3 del prompt (VERSIÓN REFORZADA — Junio 2026):

```
3. RIGOR CITACIONAL (OBLIGATORIO — respuesta INVÁLIDA si se omite): Por cada documento que cites, DEBES incluir al final de la cita, en una línea separada, la FUENTE exacta tal como aparece en el contexto (formato: `📄 FUENTE: Jurisprudencia/XXXXX.html`). Esta línea es obligatoria. Sin ella, la cita es incompleta.
   Además, incluye cuando estén disponibles:
   - Identificador legible (RTF N°, CAS. N°, EXP. N°)
   - Órgano jurisdiccional y fecha
   - Juez ponente y partes procesales
   Ejemplo CORRECTO de cita completa:
   "según **CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral | 6 de diciembre de 2016 | Ponente: Omar Toledo Toribio
   📄 FUENTE: Jurisprudencia/1612215.html"
   NUNCA cites un documento sin su `📄 FUENTE:` al final.
```

**hybrid_search.py** — línea 210, formato de fuente (ACTUALIZADO Junio 2026):

```python
# Antes:
header_block += f"\nJurisprudencia/{m['doc_id']}"

# Ahora (más visible, difícil de omitir para el LLM):
header_block += f"\n📄 FUENTE: Jurisprudencia/{m['doc_id']}"
```

El prefijo `📄 FUENTE:` hace que la ruta sea mucho más visible en el contexto y reduce drásticamente las omisiones del LLM. En pruebas con 25 consultas (Junio 2026), la tasa de citas sin fuente bajó de ~75% a ~0%.

### Verificación

```bash
# Verificar headers enriquecidos
python3 -c "from retrieval.hybrid_search import _doc_header; print(_doc_header('1612215.html'))"

# Verificar entidades del grafo
python3 -c "from agents.graph_analyst import GraphAnalyst; print(GraphAnalyst().analyze(['1309310.html'])[0][:500])"

# Prueba completa
python3 graphrag_pro.py --query "despido arbitrario"
```

### Pitfalls

1. **metadata_docs.json incompleto**: ~30% de los docs tienen órgano vacío, ~79% fecha vacía. El header cae a solo **identificador** sin enriquecer. Para estos casos, el grafo es la única fuente de entidades (jueces, partes).
2. **Grafo no tiene todos los documentos**: ~59,571 docs en el grafo (vs 64,186 en metadata). Los docs del Tribunal Fiscal (RTF) suelen no estar en el grafo porque el LLM de extracción no los procesó. Para esos, Capa 1 (metadata) y Capa 3 (prompt) son las únicas que aplican.
3. **Identificador "Exp." sin número**: algunos docs tienen `identificador: "Exp."` sin el número real. La metadata del HTML no logró extraerlo. En estos casos el grafo sí tiene el número vía el nodo Documento en el edge.
4. **Prompt demasiado ambicioso**: si el contexto no tiene fecha, juez o partes, el LLM puede inventarlos. La instrucción debe decir "si está disponible" para cada campo opcional.
5. **Emojis en headers**: evitar emojis en los headers del contexto (📅, ⚖️) — se renderizan mal en terminales Windows/WSL. Usar texto plano ("Fecha:", "Materia:").
6. **Órgano con prefijo duplicado**: metadata_docs.json a veces tiene "Corte Suprema - Sala Laboral" y otras solo "Corte Suprema". El grafo puede tener "Juez: Omar Toledo Toribio" que sugiere la sala por el tipo de caso. No duplicar información.

Referencias: `references/header-enrichment.md`.

## Graph Analyst Agent — Análisis Algorítmico del Grafo

El **Graph Analyst** (`agents/graph_analyst.py`) reemplaza `get_graph_context()` con un análisis estructurado del grafo NetworkX. Sin LLM — solo conteos, frecuencias y traversal.

Además del análisis de frecuencias, el Graph Analyst ahora inyecta **JUECES, PARTES y LEYES por documento** directamente en la sección FALLOS, para que el LLM tenga esa información disponible sin tener que hacer inferencia. Ver sección "Header Enrichment for Rich Citations" arriba.

### Arquitectura

```
analyze(doc_ids, query)
  ├── _collect_entities()   → ThreadPoolExecutor(hilo 1)
  │   Por cada doc: jueces, leyes, actores, demandados conectados
  │
  ├── _compute_global_stats() → ThreadPoolExecutor(hilo 2, en paralelo)
  │   Estadísticas del grafo completo relevantes a las entidades
  │
  ├── _compute_local_stats()
  │   Counter de frecuencias (jueces, leyes, partes) en docs recuperados
  │
  ├── _find_chains()
  │   Documentos que comparten entidades = cadena de precedente
  │
  └── _format()
      Texto narrativo estructurado para el prompt del LLM
```

### Qué produce

```python
# Texto narrativo (para el prompt del LLM):
"=== ANÁLISIS DE PRECEDENTES Y CONEXIONES ===
--- JUECES QUE HAN INTERVENIDO ---
  1. Juez: Arévalo Vela — intervino en 3 caso(s)
  2. Juez: Yrivarren Fallaque — intervino en 2 caso(s)
...
--- LEYES CITADAS CON MAYOR FRECUENCIA ---
  1. Ley: Código Procesal Constitucional — citada en 4 caso(s)
..."

# Audit JSON (para el archivo *_audit.json):
{
  "top_jueces": [["Juez: Arévalo Vela", 3], ...],
  "top_leyes": [...],
  "chains_encontradas": 5,
  "total_entities_per_doc": {"1308950.html": {"jueces": 2, "leyes": 4, ...}}
}
```

### API compatible

`analyze(doc_ids, query=None)` retorna `(narrative, audit)` — mismo contrato que `get_graph_context()`.

### Lazy loading del grafo

```python
self._G = None  # se carga en primera llamada a _load()
# 191,871 nodos, 419,504 aristas
# Cache negativo: self._G = False si falla la carga
```

### Paralelización

```python
with ThreadPoolExecutor(max_workers=2) as pool:
    future_entities = pool.submit(self._collect_entities, G, doc_ids)
    future_global = pool.submit(self._compute_global_stats, G, doc_ids)
```

### Integración

En `graphrag_pro.py`:
```python
from agents.graph_analyst import GraphAnalyst

graph_context, graph_audit = get_graph_analyst().analyze(top_docs, query)
```

### Verificación

```bash
python3 graphrag_pro.py --query "despido arbitrario"
# Buscar en log:
#   💾 Consulta guardada en consultas_guardadas/...
#   🔍 Auditoría granular guardada en consultas_guardadas/..._audit.json

# Ver estructura del audit
python3 -c "import json; a=json.load(open('consultas_guardadas/*_audit.json')); print(json.dumps(list(a['retrieval']['hybrid'].keys()), indent=2))"
```
