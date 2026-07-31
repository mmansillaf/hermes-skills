# Diagnóstico de performance LexRAG

## Perfil de tiempo por query (subprocess)

| Paso | Tiempo | Acumulado |
|---|---|---|
| DeepSeek init | ~1s | 1s |
| FAISS load (116 MB) | ~1s | 2s |
| Sentence-Transformer download + load | **~80s** | 82s |
| Hybrid search (BM25+FAISS+RRF+grafo) | ~10s | 92s |
| LLM synthesis (DeepSeek streaming) | ~30-45s | 130s |
| Critic verification | ~5s | 135s |
| Follow-up generation (Groq) | ~3s | 138s |

## Cuello de botella

El 58% del tiempo (~80s) se pierde descargando/cargando el modelo
`distiluse-base-multilingual-cased-v2` en cada subprocess nuevo.

En una batería de 15 queries:
- Tiempo real útil: ~15 × 55s = 13.75 min
- Tiempo perdido en recarga: ~15 × 80s = 20 min
- **Total: ~36 min → se podría reducir a ~14 min**

## Soluciones (orden de prioridad)

### A) HF_TOKEN (inmediato, 5 min)
Agregar `HF_TOKEN=hf_xxx` al `.env`. Reduce el rate limiting de HuggingFace.
La descarga pasa de ~80s a ~30s. No elimina el problema pero mitiga.

### B) Modelo compartido (definitivo, ~30 min de código)
Ejecutar todas las queries en un solo proceso Python que carga el modelo UNA vez.
El fix al intento fallido de `bateria_15_directa.py`:
```python
# En vez de contextlib.redirect_stdout (rompe async generators):
old_stdout = sys.stdout
sys.stdout = open(os.devnull, 'w')
try:
    respuesta, follow_ups, history = await run_console_query(pregunta)
finally:
    sys.stdout = old_stdout
```

### C) Usar CPU en vez de GPU para embeddings
Ya se hace (`device='cpu'` en `core/embedding.py`). Correcto para WSL sin GPU.

### D) Modelo más pequeño
`distiluse-base-multilingual-cased-v2` (134 MB, 512 dims) ya es el más pequeño
de la familia Sentence-Transformers multilingüe. Alternativas más rápidas:
- `paraphrase-multilingual-MiniLM-L12-v2` (118 MB) — similar calidad, ~15% más rápido
- `all-MiniLM-L6-v2` (80 MB) — solo inglés, no sirve para corpus legal peruano
