# Retrieval: Extracción Automática de Nombres de Documentos desde la Query

## Problema

Cuando el usuario escribe "compara X con Y" o "encuentra contradicciones entre A y B", el retrieval híbrido (vector + FTS5) busca por similitud semántica de toda la frase. Esto hace que:

1. Documentos NO solicitados aparezcan en los resultados (porque "compara" es semánticamente similar a muchos textos)
2. Los documentos específicos que el usuario mencionó no estén en el top-k del hybrid search
3. La respuesta del LLM use chunks de documentos irrelevantes y diga "no encontré los documentos que mencionas"

## Solución (3 partes)

### Parte 1: `search_documents_fuzzy()` en VectorStore

```python
def search_documents_fuzzy(self, name_fragment: str) -> List[Dict]:
```

Busca documentos por nombre con múltiples variantes:
- El nombre exacto (`%nombre%`)
- Con extensiones (`.txt`, `.pdf`, `.docx`)
- Palabra por palabra (tokens de >3 caracteres)
- Deduplica por doc_id
- Ordena por relevancia: primero los que matchean el nombre completo

Ubicación: `src/core/vector_store.py`

### Parte 2: `_extract_doc_names_from_query()` en Orchestrator

```python
def _extract_doc_names_from_query(self, query: str) -> Optional[List[str]]:
```

Ubicación: `src/agents/pipeline.py`

Algoritmo:
1. Busca fragmentos entre comillas (ej: `"contrato_servicios.txt"`)
2. Si no hay comillas, parte la query por `y`, `vs`, `,`, `con`
3. Limpia stop words (`compara`, `entre`, `documento`, `vs`, etc.)
4. Para cada fragmento candidato (mínimo 5 caracteres), llama a `search_documents_fuzzy()`
5. Retorna lista de `doc_name` encontrados, o `None` si no encontró nada

### Parte 3: Fallback en `retrieval_agent()`

Cuando hay `doc_filter` activo:
1. Aumenta `top_k` de 20 a 60 para no perder chunks de los documentos filtrados
2. Filtra resultados por `doc_name`
3. Si quedan 0 candidatos tras filtrar, hace un segundo intento:
   - Usa los nombres de documento como query de búsqueda (en vez de la query original)
   - Busca con esos nombres en hybrid search
   - Vuelve a filtrar por doc_name
4. El reranker reordena los resultados finales

### Flujo completo

```
Query: "compara contrato_servicios.txt con contrato_locacion.txt"
  ↓
classify_intent() → Intent.COMPARE
  ↓
_extract_doc_names_from_query()
  → busca fragmentos, limpia stop words
  → search_documents_fuzzy("contrato_servicios.txt")
    → LIKE "%contrato_servicios%", LIKE "%contrato_servicios.txt%"
    → encuentra: contrato_servicios_profesionales.txt ✓
  → search_documents_fuzzy("contrato_locacion.txt")
    → encuentra: contrato_locacion_servicios_v2.txt ✓
  ↓
retrieval_agent(doc_filter=["contrato_servicios...", "contrato_locacion..."])
  → hybrid_search(top_k=60)  ← 3x el default
  → filtra por doc_name
  → reranker
  ↓
compare_agent() → compara solo esos 2 documentos
```

## Casos de prueba

| Query | Resultado esperado |
|---|---|
| `"compara X con Y"` (nombres exactos) | Encuentra ambos |
| `"compara el contrato de servicios con el de locacion"` | Encuentra por palabras clave |
| `"encuentra contradicciones entre resolucion e informe"` | Encuentra resolucion* e informe* |
| `"compara este documento con este otro"` | None (no hay nombres concretos) |

## Pitfalls

- **stop words en español:** La lista debe incluir variantes con/sin tilde (`contradiccion`/`contradicción`, `seccion`/`sección`)
- **Palabras cortas:** Se ignoran tokens de ≤4 caracteres para evitar ruido
- **Múltiples matches:** Un fragmento como "contrato" puede matchear 10+ docs. El retrieval filter + reranker maneja esto.
- **Comillas:** Si el usuario usa comillas, se priorizan sobre el split por comas/conjunciones
- **Sin coincidencias:** Si `_extract_doc_names_from_query()` retorna None, el pipeline cae al comportamiento original (hybrid search sin filtro)
