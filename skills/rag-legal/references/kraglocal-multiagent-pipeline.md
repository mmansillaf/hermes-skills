# KRagLocal — Pipeline Multi-Agente para Análisis Legal

**Contexto:** Sistema RAG ligero construido desde cero para abogados peruanos.
Stack: ChromaDB embedded + `intfloat/multilingual-e5-small` (384d) + SQLite FTS5 +
Groq API (con fallback a Ollama local). FastAPI + HTML plano (NO Streamlit).

---

## Arquitectura Multi-Agente (5 Agentes)

```
Usuario Query
    │
    ▼
┌─────────────────┐
│ ORCHESTRATOR    │  Clasifica intención (qa, resumen, comparar,
│ Agent 0         │  contradicciones, analizar, listar)
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│RETRIEVAL│ │COMPARE │ │CONTRA- │ │GENERATE│ │VALIDATE│
│Agent 1  │ │Agent 2 │ │DICTIONS│ │Agent 4 │ │Agent 5 │
│         │ │        │ │Agent 3 │ │        │ │        │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘

  1. RETRIEVAL: hybrid search (ChromaDB vector + FTS5 keyword) + reranker
  2. COMPARE: compara chunks de 2+ documentos lado a lado
  3. CONTRADICTIONS: detecta incongruencias entre documentos
  4. GENERATE: produce respuesta con citas [Documento, Seccion, Lineas]
  5. VALIDATE: verifica que toda cita existe en los chunks recuperados
```

---

## Agent 0: Intent Classifier

Clasifica la consulta en una de 6 intenciones:

| Intento | Palabras clave típicas | Ruta |
|---------|----------------------|------|
| `qa` | preguntas factuales | Retrieval → Generate |
| `resumen` | resume, sintesis, abstract | Retrieval → Generate (summary prompt) |
| `comparar` | compara, vs, diferencia, ambos | Retrieval → Compare Agent |
| `contradicciones` | contradic, inconsistente, conflicto | Retrieval → Contradictions Agent |
| `analizar` | error, riesgo, cumplimiento, problema | Retrieval → Generate (analysis prompt) |
| `listar` | lista, documentos, tengo, cargados | Directo a DB (sin LLM) |

**Prompt:**
```
Eres un clasificador de intenciones para un sistema legal RAG.
Clasifica la consulta en UNA de estas categorias: qa, resumen,
comparar, contradicciones, analizar, listar.
Responde SOLO con el nombre de la categoria.
```

**Fallback por keywords** cuando el LLM no responde:
```python
if any(w in kw for w in ["compara", "comparar", "vs", "diferencia"]):
    return Intent.COMPARE
if any(w in kw for w in ["contradic", "inconsistente", "conflicto"]):
    return Intent.CONTRADICTIONS
```

---

## Agent 1: Retrieval

Pipeline de búsqueda:

1. **Embedding de query** con prefix `query:` (obligatorio para e5)
2. **Hybrid search**: ChromaDB (vector) + SQLite FTS5 (keyword)
3. **Blend scoring**: `score = vector_score * 0.7 + keyword_score * 0.3`
4. **Reranking** opcional con cross-encoder

```python
def retrieval_agent(query, store, embedder, reranker, top_k=5):
    query_emb = embedder.embed_query(query)
    candidates = store.hybrid_search(query_emb, query, top_k=20)
    ranked = reranker.rerank(query, candidates, top_k=top_k)
    return ranked
```

**Hybrid search implementation:**
```python
def hybrid_search(self, vector_emb, keyword_query, top_k=20, vector_weight=0.7):
    vector_hits = self.search_vector(vector_emb, top_k=top_k*2)
    keyword_hits = self.search_keyword(keyword_query, top_k=top_k*2)
    combined = {}
    for h in vector_hits:
        combined[h["chunk_id"]] = {**h, "score": h["score"] * vector_weight}
    for h in keyword_hits:
        cid = h["chunk_id"]
        if cid in combined:
            combined[cid]["score"] += h["score"] * (1.0 - vector_weight)
        else:
            combined[cid] = {**h, "score": h["score"] * (1.0 - vector_weight)}
    return sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:top_k]
```

---

## Agent 2: Compare

Compara chunks de dos o más documentos lado a lado.

**Prompt:**
```
Eres un asistente legal experto en analisis de documentos.
Se te proporcionan chunks de DOS documentos diferentes.

Tu tarea: comparar los documentos y producir un analisis estructurado.
Para cada punto de comparacion, indica:
- El tema o clausula
- Que dice el Documento A
- Que dice el Documento B
- CITAS: [Documento: X, Seccion: Y, Lineas: Z1-Z2]

Formato de salida:
**Comparacion: [TEMA]**
- Documento A: ... [cita]
- Documento B: ... [cita]
- Diferencia: ...
```

**Output esperado:**
```
**Comparacion: Plazo del Contrato**
- Documento A: 12 meses con renovacion automatica [Doc: contrato1, Seccion: PLAZO, L12-14]
- Documento B: 6 meses sin renovacion [Doc: contrato2, Seccion: PLAZO, L12-14]
- Diferencia: El contrato A es por 12 meses con auto-renovacion; el B es por 6 meses fijo.
```

---

## Agent 3: Contradictions

Detecta incongruencias textuales o lógicas entre documentos. Busca:
1. Cláusulas sobre el mismo tema pero con contenido opuesto
2. Definiciones inconsistentes del mismo término
3. Obligaciones contradictorias
4. Fechas, montos o condiciones que no coincidan

**Prompt:**
```
Eres un asistente legal experto en deteccion de contradicciones.
Se te proporcionan chunks de MULTIPLES documentos.

Tu tarea: identificar contradicciones textuales o logicas entre ellos.
Busca:
1. Clausulas que traten el mismo tema pero digan cosas opuestas
2. Definiciones inconsistentes del mismo termino
3. Obligaciones que se contradicen entre documentos
4. Fechas, montos o condiciones que no coincidan

Para cada contradiccion:
- Documento A: [nombre], Seccion: [seccion], dice: [texto exacto]
- Documento B: [nombre], Seccion: [seccion], dice: [texto exacto]
- Contradiccion: [explicacion]
```

**Requisito:** Se necesitan al menos 2 documentos en los chunks recuperados.

---

## Agent 4: Generation

Produce la respuesta final. Dos modos:

**QA mode:**
```
Eres un asistente legal que responde preguntas sobre documentos.
Usa SOLO la informacion del contexto proporcionado.
Si la respuesta no esta en el contexto, di "No encontre esta informacion."
SIEMPRE cita la fuente exacta: [Documento: "nombre", Seccion: "seccion", Lineas: X-Y]
```

**Summarize mode:**
```
Proporciona un resumen estructurado que incluya:
1. Tipo de documento y partes involucradas
2. Objeto y proposito principal
3. Puntos clave (max 5-7)
4. Fechas, montos o hitos importantes
5. Riesgos u obligaciones relevantes
Para cada punto, cita la fuente.
```

**Construcción del contexto:**
```python
context = ""
for i, c in enumerate(chunks):
    meta = c["metadata"]
    context += f"[Fuente {i+1}]\n"
    context += f"Documento: {meta['doc_name']}\n"
    context += f"Seccion: {meta['section']}\n"
    context += f"Pagina: {meta.get('page', 0)}\n"
    context += f"Lineas: {meta['line_start']}-{meta['line_end']}\n"
    context += f"Tipo: {meta.get('tipo', 'texto')}\n"
    context += f"Contenido: {c['content']}\n\n"
```

---

## Agent 5: Citation Validator

Verifica que cada cita en la respuesta corresponda a contenido REAL en los chunks recuperados.

**IMPORTANTE:** El LLM genera citas en múltiples formatos. El validador debe capturar todos:

| # | Formato | Ejemplo | Regex |
|---|---------|---------|-------|
| 1 | Bracket con comillas | `[Documento: "nombre.txt", Seccion: "seccion", Lineas: 10-15]` | `r'\[Documento:\s*"([^"]+)"[,\s]+Seccion:\s*"([^"]+)"...` |
| 2 | Bracket sin comillas | `[Documento: nombre.txt, Seccion: seccion, Lineas: 10-15]` | `r'\[Documento:\s*([^,\]]+?)[,\s]+Seccion:\s*([^,\]]+?)...` |
| 3 | Bullet (compare/contradictions agents) | `* Documento A: nombre.txt, Sección: seccion, dice: ...` | `r'\* Documento [A-Z]+:\s*([^,]+),\s*Secci[oó]n:\s*([^,]+),'` |
| 4 | Bracket shorthand | `[nombre.txt, Seccion, L10-15]` | `r'\[([^,\]]+\.txt)[,\s]+([^,\]]+)[,\s]+(?:L[íi]neas?\|L\|line)\s*\d+'` |

**Algoritmo completo:**

```python
def validation_agent(response, chunks, llm) -> (bool, str):
    # Build lookup set (normalized to lowercase)
    known_docs = set()
    for c in chunks:
        meta = c["metadata"]
        known_docs.add((meta["doc_name"].strip().lower(),
                        meta["section"].strip().lower()))

    # Extract all citation-like patterns (4 formats)
    all_citations = []

    # Pattern 1: [Documento: "name", Seccion: "name", Lineas: X-Y]
    for m in re.finditer(REGEX_PATTERN_1, response):
        all_citations.append((m.group(1), m.group(2)))

    # Pattern 2: [Documento: name, Seccion: name, Lineas: X-Y] (unquoted)
    for m in re.finditer(REGEX_PATTERN_2, response):
        all_citations.append((m.group(1), m.group(2)))

    # Pattern 3: * Documento A/B: name, Sección: name, (from compare/contradictions)
    for m in re.finditer(REGEX_PATTERN_3, response):
        all_citations.append((m.group(1), m.group(2)))

    # Pattern 4: [name.txt, Seccion, N]
    for m in re.finditer(REGEX_PATTERN_4, response):
        all_citations.append((m.group(1), m.group(2)))

    # If no citations found but response mentions document names, accept it
    if not all_citations:
        if any(ref in response.lower() for ref in ["contrato_", "informe_", "resolucion"]):
            return (True, "VALIDO")
        return (False, "No citations found")

    # Validate each citation with fuzzy matching
    errors = []
    for doc_name, section in all_citations:
        doc_name = doc_name.strip().strip('"').strip("'").lower()
        section = section.strip().strip('"').strip("'").lower()[:50]

        # Direct match
        match_found = (doc_name, section) in known_docs

        if not match_found:
            # Fuzzy: doc name contains known or vice versa (handles .txt suffix mismatch)
            for kd_name, kd_section in known_docs:
                name_match = (doc_name in kd_name or kd_name in doc_name or
                              doc_name.replace('.txt','') in kd_name or
                              kd_name.replace('.txt','') in doc_name)
                section_match = (section in kd_section or kd_section in section)
                if name_match and section_match:
                    match_found = True
                    break

        if not match_found and len(errors) < 3:
            errors.append(f"Cita dudosa: Doc='{doc_name}', Sec='{section}'")
    return (len(errors) == 0, " | ".join(errors) if errors else "VALIDO")
```

**Salida de validación:**
```python
{
    "response": "...respuesta con citas...",
    "citations_valid": True/False,
    "validation_msg": "VALIDO" o lista de errores
}
```

---

## Orchestrator: Flujo Completo

```python
class Orchestrator:
    def process_query(self, query, doc_filter=None, prefer_cloud=False):
        # 1. Clasificar intención
        intent = classify_intent(query, self.llm)

        # 2. Si es "listar", responder desde DB (sin LLM)
        if intent == Intent.LIST:
            return {"response": listar_documentos(store), "intent": "listar"}

        # 3. Retrieval
        chunks = retrieval_agent(query, store, embedder, reranker)

        # 4. Análisis especializado según intención
        if intent == Intent.COMPARE:
            response = compare_agent(query, chunks, llm)
        elif intent == Intent.CONTRADICTIONS:
            response = contradictions_agent(query, chunks, llm)
        else:
            response = generate_response(query, intent, chunks, llm)

        # 5. Validar citas
        valid, msg = validation_agent(response, chunks)

        return {
            "intent": intent.value,
            "response": response,
            "citations_valid": valid,
            "validation_msg": msg,
            "chunks_used": [...]  # metadatos de los chunks recuperados
        }
```

---

## Cuándo Usar Este Patrón

Este pipeline multi-agente es apropiado cuando:
- El sistema maneja **documentos legales heterogéneos** (contratos + resoluciones + informes)
- Se necesita **detección automática de contradicciones** entre documentos
- Las **citas exactas a fuentes** son un requisito no-negociable (abogados)
- El corpus es **gestionable activamente** (CRUD: entra/sale documentación)

No es apropiado para:
- Corpus fijos de normas públicas (usar GRegElPeruano con Qdrant + Neo4j)
- Sistemas sin necesidad de análisis comparativo
- Donde la precisión del retrieval es secundaria

---

## Pruebas Realizadas

Con 22 documentos reales (19 PDF + 4 TXT = 354 chunks) en `Contratos/` y 7 queries:

| Prueba | Resultado |
|--------|-----------|
| QA factual | ✅ Cita exacta [contrato, OBJETO, L6] |
| Resumen estructurado | ✅ 7 puntos con fuentes |
| Comparación 2 contratos | ✅ 10+ diferencias identificadas |
| Contradicciones | ✅ Plazo, monto, mora, confidencialidad, PI, seguro, resolución, arbitraje |
| Análisis de riesgos | ✅ 4 riesgos con citas |
| Resolución de Alcaldía | ✅ 6 artículos resumidos |
| Browser UI (22 docs) | ✅ Sidebar, dropdown, citas clickables, fuentes visibles |

## Pitfalls de Producción

### 1. PDFs escaneados = 0 chunks
PyMuPDF solo extrae texto seleccionable. PDFs escaneados (imágenes) producen 0 chunks silenciosamente. No hay error visible en el log — solo aparecen con `num_chunks=0` en el listado. Solución: agregar OCR con `pytesseract` o detectar 0 chunks y alertar al usuario.

### 2. Carpeta Contratos/ es la canónica
El usuario espera que todos los documentos estén en `Contratos/`. La carpeta `test_docs/` es solo para desarrollo. Siempre ingestar desde `Contratos/` usando `krag ingest ./Contratos`.

### 3. Config.py: STATIC_DIR debe existir
Si `STATIC_DIR` se elimina de `config.py` pero el bucle `for d in [DATA_DIR, STATIC_DIR]` lo referencia, el servidor falla con `NameError`. Siempre mantener ambas definiciones sincronizadas.

### 4. Tiempo de ingesta
22 documentos (19 PDF) tomaron ~2 minutos en CPU. A 5,000 documentos, estimar ~30-60 minutos. Ingesta incremental por hash SHA256 evita reprocesar duplicados.

