# Resultados de Implementación — 3 Fases

## Fase 1: Embeddings 768d — ❌ Descartada

Se probó `intfloat/multilingual-e5-large` (1024d) vs `paraphrase-multilingual-MiniLM-L12-v2` (384d).
Resultado: MiniLM actual es 4.7x mejor discriminando (range 1.590 vs 0.341). E5 da similitud 0.80-0.90 para todo — no discrimina. BGE-gemma2 (1.3 GB) timeouteó en descarga.

**Conclusión:** No cambiar embeddings. El actual es el mejor para resoluciones administrativas en español.

## Fase 2: Indexación de Leyes — ✅ Exitosa

Creación de `data/leyes.db` (SQLite + FTS5) con 14 artículos de 6 leyes. 
Detección automática vía 5 patrones regex en `search_sqlite()`.
Resultados insertados al inicio con `blend_score=1.0`.

**Impacto:** 4/4 queries sobre leyes externas pasaron de WARN/FAIL a PASS con citas textuales:
- Código Tributario Art. 178 (cifras falsas)
- Código Civil Art. 1244 (interés legal)
- Ley 27444 Art. 212.1 (rectificación errores)
- Ley 27972 Art. 39 (Decretos de Alcaldía)

**Bug encontrado:** `re.search(question, pattern)` vs `re.search(pattern, question)` — parámetros invertidos. La API busca el string 'question' como pattern, no al revés.

## Fase 3: Router B/I/A — ✅ Parcial

Clasificador de queries en 3 niveles:
- BÁSICO: respuesta directa de BD sin LLM (ahorro $)
- INTERMEDIO: pipeline normal con Groq
- AVANZADO: modo asistido con disclaimer ⚠️

**Resultado:** 35/40 (87.5%), 0 FAILs.
- 6 queries en modo directo (sin costo API)
- 8 queries en modo asistido (seguridad jurídica)
- 26 queries en modo normal

**Pendiente:** El modo directo básico pierde 2 queries vs LLM. Se agregó fallback a LLM si keywords insuficientes (pendiente de test final).
