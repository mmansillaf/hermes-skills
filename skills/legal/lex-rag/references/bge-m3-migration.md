# BGE-M3 + BM25 + RRF — Stack Híbrido para RAG Legal

## Resumen

Migración de LexRAG desde `distiluse-base-multilingual-cased-v2` (512-d, 512 tokens)
a `BAAI/bge-m3` (1024-d, 8192 tokens, 100+ idiomas, dense+sparse en 1 forward pass).

Código de referencia: `/mnt/c/Users/usuario/bge-m3-lexrag/`
- `core_bge_m3.py` — Singleton BGE-M3, encode dense+sparse, lexical scoring
- `hybrid_search_bge.py` — Pipeline: FAISS + BM25 + sparse BGE-M3 + RRF (k=80, pesos jerarquía) + cross-encoder reranker
- `migracion/migracion_lexrag_bgem3.py` — Script de migración en 5 fases

## BGE-M3 Especificaciones

| Parámetro | Valor |
|-----------|-------|
| Dimensión embedding | 1024 |
| Máx tokens de entrada | 8192 |
| Idiomas | 100+ (incluye español) |
| Funcionalidades | Dense, sparse (token weights), multi-vector (ColBERT) |
| RAM | ~1.1 GB FP32 / ~0.6 GB FP16 |
| Parámetros | ~567M (xlm-roberta-large) |
| Licencia | MIT |
| Instalación | `pip install -U FlagEmbedding` |

## Ventajas Clave vs distiluse Actual

| Aspecto | distiluse (actual) | BGE-M3 | Impacto |
|---------|:------------------:|:------:|---------|
| Dimensión | 512 | 1024 | +100% capacidad semántica |
| Contexto máx | 512 tokens | 8192 tokens | **documentos completos sin chunkear** |
| Sparse retrieval | ❌ BM25 separado | ✅ nativo (token weights) | 3 fuentes en 1 forward pass |
| Recall@100 (MLDR) | ~78% (BM25) | ~89% (dense+sparse) | +11-17% |
| Recall@10 (MIRACL es) | ~52% (dense) | ~69.5% | +17% |

**Tokens de contexto**: La mejora más impactante. Hoy LexRAG chunktea a 512 tokens.
Con BGE-M3, cada documento completo entra en 8192 tokens. Documentos >8192 tokens
pueden chunkearse a 4096+4096 sin perder contexto de oración.

## Pipeline Híbrido de 3 Fuentes

```
Query → BGE-M3 encode (dense + sparse)
  ↓
FAISS dense (top_k×3)        → 21 docs
BGE-M3 sparse (top_k×3)      → 21 docs  (sin costo extra)
BM25 (top_k×3)               → 21 docs
  ↓
RRF fusion (k=80, pesos ×1.5 TC, ×1.3 CS)
  → top 14
  ↓
bge-reranker-v2-m3 cross-encoder
  → top 7
```

**RRF k óptimo por número de fuentes:**
- 2 fuentes (FAISS + BM25): k=60
- 3 fuentes (FAISS + BM25 + BGE-sparse): k=80
- k más alto suaviza diferencias cuando hay más fuentes

**Pesos por jerarquía normativa** (aplicados al score RRF final):
```python
PESOS_JERARQUIA = {
    "constitucional": 1.5,   # TC — prioridad máxima
    "casacion": 1.3,          # Corte Suprema
    "tributario": 1.2,        # Tribunal Fiscal
    "default": 1.0,
}
```

## Preprocesamiento para Español Legal

Tokenización para BM25 con:

1. **Normalización**: minúsculas, sin acentos, ñ→n
2. **Stopwords legales**: 90+ términos procesales (ante, bajo, cabe, conforme, mediante, según)
3. **Stemming ligero**: solo sufijos legales predecibles (-ciones→-ción, -mientos→-miento, -dades→-dad)
4. **Sin stemmers agresivos**: preservar términos clave (casación, amparo, habeas corpus)

Referencia: `tokenizar_legal()` en `hybrid_search_bge.py`

## Cross-encoder Reranker

`bge-reranker-v2-m3` — mismo backbone que BGE-M3, multilingüe, ~567M params.

**Colocación**: DESPUÉS de RRF, no antes.
- RRF filtra 63→14 candidatos (~$0)
- Cross-encoder rerankea solo 14 pares query-documento
- Ahorra ~70% de latencia vs rerankear todos los candidatos

## Plan de Migración (5 Fases)

### Fase 0: Instalación
```bash
pip install -U FlagEmbedding   # BGE-M3 + reranker
# Ya instalado: rank-bm25, faiss-cpu, sentence-transformers
```

### Fase 1: Escaneo
```bash
python migracion/migracion_lexrag_bgem3.py \
  --lexrag-dir /mnt/d/PyCode/LexRAG-Optimizado --scan-only
```
Reporta: número de chunks, dimensión actual, tamaño de textos.

### Fase 2: Re-embedding
```bash
python migracion/migracion_lexrag_bgem3.py \
  --lexrag-dir /mnt/d/PyCode/LexRAG-Optimizado \
  --output-dir /mnt/d/PyCode/LexRAG-Optimizado/data/indices_bge3
```
Lee chunks FAISS, reagrupa por doc_id, genera dense+sparse con BGE-M3.
Tiempo estimado: 30-60 min para 50K docs (CPU). RAM: ~3-4 GB.

### Fase 3: A/B Testing
```bash
python migracion/migracion_lexrag_bgem3.py --ab-test \
  --lexrag-dir /mnt/d/PyCode/LexRAG-Optimizado \
  --output-dir /mnt/d/PyCode/LexRAG-Optimizado/data/indices_bge3 \
  --queries-file consultas_prueba.txt
```
Métrica: Jaccard similarity entre top-5 distiluse vs top-5 BGE-M3.

### Fase 4: Integración

**core/index_manager.py** — cambiar paths:
```python
FAISS_INDEX_PATH = "data/indices_bge3/faiss_index_bge3.bin"
FAISS_META_PATH = "data/indices_bge3/faiss_meta_bge3.pkl"
BM25_PATH = "data/indices_bge3/bm25_index_bge3.pkl"
```

**core/embedding.py** — cambiar modelo:
```python
# Opción A: SentenceTransformer (solo dense)
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer('BAAI/bge-m3')

# Opción B: FlagEmbedding (dense + sparse)
from FlagEmbedding import BGEM3FlagModel
embedding_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
```

**retrieval/hybrid_search.py** — actualizar:
- Agregar `get_scores_bge_sparse()` después de FAISS
- Reemplazar `_tokenize()` por `tokenizar_legal()` de `hybrid_search_bge.py`
- Agregar rrf_fusion de 3 fuentes con k=80

### Fase 5: Verificación
```bash
python -c "from core.index_manager import IndexManager; im = IndexManager(); im.initialize(); idx,_=im.get_faiss(); print(f'{idx.ntotal} vectores, dim={idx.d}')"
python graphrag_pro.py --query "despido arbitrario"
```

## Índices Independientes

Los índices nuevos NO reemplazan a los antiguos — coexisten:

```
data/indices/           ← distiluse 512-d (control)
data/indices_bge3/      ← BGE-M3 1024-d (tratamiento)
```

Para revertir: cambiar paths en `index_manager.py` de vuelta a `data/indices/`.

## RAM Estimada (50K docs)

| Componente | RAM |
|-----------|:----:|
| Modelo BGE-M3 (FP32) | ~1.1 GB |
| FAISS 1024-d (50K vectores) | ~200 MB |
| BM25 | ~250 MB |
| Sparse weights | ~100 MB |
| Metadata + textos | ~50 MB |
| **Total** | **~1.7 GB** |

Cabe en 16 GB RAM con margen.

## Notas Técnicas

- BGE-M3 **NO requiere query instruction** (a diferencia de BGE-v1.5 que necesita "Represent this sentence for searching relevant passages:")
- Sparse weights de BGE-M3 son contextuales (peso depende del contexto, no solo frecuencia) — diferente de BM25
- BM25 se mantiene como 3ª fuente porque captura matching léxico puro que BGE-M3 podría perder en ciertos edge cases
- El modelo se descarga (~2.2 GB) desde HuggingFace en primera ejecución. Usar HF_TOKEN para acelerar.
