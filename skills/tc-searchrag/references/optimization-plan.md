# TC SearchRAG — Optimization Plan & Results (Jun 2026)

Based on real benchmarks of the 11,483-doc corpus. BM25 loading dominates (9.3s), FAISS is negligible (1.77ms), LLM API varies wildly (2-74s).

**Status:** P0-P3 implemented and verified. P4 attempted but not faster than pickle.

## P0 — Servidor persistente (ALTO impacto, mínimo esfuerzo) ✅

**Problema:** cada `python3 src/search_tc.py` arranca proceso nuevo → carga ~11s de índices.
**Solución:** mantener `app.py` corriendo en background y consultar via HTTP/curl.

```bash
cd /mnt/d/PyCode/TC_SearchRAG/src && python3 app.py
curl "http://localhost:8000/search?q=pension&top_k=3"
```

**Ahorro:** ~11s por consulta (índices ya en RAM).
**Implementado:** `tc.bat` wrapper que arranca el servidor automáticamente si no está corriendo.

## P1 — Caché exacto (ALTO impacto, bajo esfuerzo) ✅

**Problema:** misma pregunta 2 veces → mismo pipeline completo.
**Solución:** `QueryCache` class en `search_tc.py` con hash MD5 de query + filtros serializados.

```python
cache = QueryCache(max_entries=500)
key = hashlib.md5((query + str(filters)).encode()).hexdigest()
if key in cache: return cache[key]
resultado = pipeline(query, filters)
cache[key] = resultado
```

**Limitación:** el caché vive en RAM del proceso. NO persiste entre procesos. Funciona dentro del mismo proceso (modo interactivo, servidor app.py).
**Ahorro:** ~1.5-13s por consulta repetida dentro del mismo proceso.

## P2 — Skip BM25 si query vacía (ALTO impacto, bajo esfuerzo) ✅

**Problema:** `search_tc.py "" --materia Pensiones` carga BM25 (9.3s) innecesariamente.
**Solución:** `IndexManager.load(solo_filtros=True)` que salta BM25, documentos y embeddings.

**Resultado medido:** `0.5s` vs `11s` (20x más rápido). Muestra `(solo filtros)` en el log.

## P3 — Wrapper CLI (UX, no rendimiento) ✅

**Solución:** `tc.bat` para PowerShell. Detecta si el servidor corre en puerto 8000.

Comandos disponibles:
- `tc "pension"` — consulta normal
- `tc --server-start` — arranca servidor
- `tc --server-stop` — detiene servidor
- `tc --server-status` — verifica estado

## P4 — BM25 SQLite (descartado) ❌

**Intento:** Convertir BM25 pickle (265 MB) a SQLite para carga más rápida.
**Resultado:**
- Conversión: 87s (7.8M pares término-documento)
- Tamaño: 298 MB (vs 265 MB pickle)
- Carga: más lento que pickle por overhead de SQL queries + construcción de dicts en RAM

**Conclusión:** El cuello de botella no es el formato de almacenamiento sino la cantidad de datos (7.8M pares term-doc). La solución real es P0 (servidor persistente) que carga BM25 UNA SOLA VEZ.
**Código preservado como referencia:** `src/bm25_sqlite.py`

## P5 — Modelo embeddings más rápido (no implementado)

**Riesgo:** requiere re-indexar todo (`--force`) = ~2.5h.
**No implementado porque:** P0 (servidor) mantiene el modelo cargado, y P2 lo salta en consultas de solo filtros.

## Resultados finales

| Escenario | Antes | Después | Beneficio |
|-----------|:-----:|:-------:|:---------:|
| Solo filtros (CLI) | ~13s | **~1.2s** | 10x |
| Consulta repetida (servidor) | ~1.5s | **~0.1s** | 15x |
| 2da consulta (servidor) | ~13s | **~1.5s** | 8.6x |
| Consulta IA (ya cargado) | ~15s | **~4-15s** | similar |
