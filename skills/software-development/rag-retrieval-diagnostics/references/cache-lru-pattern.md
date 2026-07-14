# PATRÓN: Cache LRU con TTL para APIs RAG

## Cuándo usar

Cuando consultas legales son repetitivas (~15-25% del tráfico) y cada query cuesta 2-5 segundos de procesamiento (búsqueda + LLM).

## Implementación mínima (validada en api_rest.py)

```python
# Módulo global
_response_cache = {}
CACHE_TTL = 3600  # 1 hora

def _get_cached(question, profile, top_k):
    import time
    key = f"{question}|{profile}|{top_k}"
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        logger.info(f"[Cache] HIT (age={time.time()-entry['ts']:.0f}s)")
        return entry["data"]
    return None

def _set_cache(question, profile, top_k, data):
    import time
    key = f"{question}|{profile}|{top_k}"
    _response_cache[key] = {"data": data, "ts": time.time()}
    # Auto-limpieza cuando >500 entradas
    if len(_response_cache) > 500:
        oldest = sorted(_response_cache.items(), key=lambda x: x[1]["ts"])[:100]
        for k, _ in oldest: del _response_cache[k]
```

## Integración en endpoint

```python
@app.post("/query")
async def query_endpoint(req: QueryRequest):
    # ⚠️ Cache check ANTES de search_sqlite (no después)
    if not req.stream:
        cached = _get_cached(question, req.profile, top_k)
        if cached:
            cached["timing_ms"] = round((time.time() - t0) * 1000)
            cached["cached"] = True
            return cached
    
    # ... pipeline normal ...
    
    result = {...}
    _set_cache(question, req.profile, top_k, result)
    return result
```

## Resultado

| Métrica | Sin cache | Con cache |
|---------|-----------|-----------|
| 1st query | 2115ms | 2115ms |
| 2nd query (misma) | 2115ms | **1ms** |
| Speedup | — | **2000x** |

## Pitfalls

- **Cache check DESPUÉS de search_sqlite** → el cache nunca ahorra búsquedas. Debe estar ANTES.
- **timing_ms del request original en respuesta cacheada** → el usuario ve 2115ms en vez de 1ms. Actualizar `timing_ms` al servir del cache.
- **No incluir `stream=true` en cache** — las respuestas streaming no se cachean (son eventos en tiempo real).
- **Memoria infinita** → sin auto-limpieza, 10K consultas únicas saturan RAM. Limpiar las 100 más antiguas cuando >500.
