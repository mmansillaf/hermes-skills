---
name: elperuano-rag-mejoras-plan
title: "Plan de Mejoras Fase 1-3 - El Peruano RAG"
description: "Plan detallado de 3 mejoras arquitectonicas - embeddings 768d, grafo jerarquico de leyes, y router por nivel de complejidad. Cada fase es independiente y reversible."
---

# Plan de Mejoras - El Peruano RAG v2.5 a v3.0

## Estado Base
- Tag: v2.5-stable-92.5
- Rendimiento: 37/40 (92.5%), confianza 0.628
- Backup: ~/el_peruano_rag/backups/

## Referencias

- `references/model-architecture.md` — Arquitectura de modelos: cuál modelo para qué función (respuesta, ingesta, embeddings)
- `references/resultados-implementacion.md` — Resultados reales de las 3 fases
- `references/confidence-calibration-3factor.md` — Modelo 3-factores para boost de confianza post-LLM (entidades + calidad + negación)
- `references/refactoring-systematic-methodology.md` — Metodología de refactorización sistemática Fase 1-3 (api_rest.py 2209→1605 líneas, -27%)

### Resultado del test (30-abr-2026)

El modelo actual `paraphrase-multilingual-MiniLM-L12-v2` (384d) fue comparado contra `intfloat/multilingual-e5-large` (1024d). Resultados:

- MiniLM 384d: range=1.590 — Excelente discriminación (0.13 vs 0.75)
- E5-large 1024d: range=0.341 — Pobre discriminación (todo entre 0.80-0.90)
- MiniLM es **4.7x mejor** discriminando documentos legales en español

**Conclusión:** No cambiar el modelo de embeddings. El actual es superior para este corpus.
No implementar mejoras que los tests demuestren que empeoran el sistema.

## Fase 2: Grafo Jerarquico Leyes (2 dias) — ✅ IMPLEMENTADA

### Resultado (30-abr-2026)

Creada base `data/leyes.db` con SQLite+FTS5. 14 artículos de 6 leyes cargados.
Detección automática con 5 patrones regex. Resultados:

- Código Tributario (cifras falsas): ❌→✅ cita Art. 178
- Código Civil (interés legal): ❌→✅ cita Art. 1244
- Ley 27444 (rectificación errores): ⚠️→✅ cita Art. 212.1
- Ley 27972 (Decretos Alcaldía): ⚠️→✅ cita Art. 39

**Bug corregido durante implementación:** `re.search(question, pattern)` vs `re.search(pattern, question)` — parámetros invertidos, fallo silencioso.

### Pendiente: expandir de 14 a ~500 artículos (~50 leyes)

## Fase 3: Router por Nivel (1 dia) — ✅ IMPLEMENTADA

### Resultado (30-abr-2026)

Router B/I/A implementado en `query_endpoint()` (api_rest.py línea 1429+).

Clasificación de queries:
- BÁSICO: detectado por palabras clave factuales + len < 200. Responde directo de BD sin LLM.
- AVANZADO: detectado por palabras de análisis jurídico (dictamen, analice, constitucionalidad).
  Modo ASISTIDO: lista normas relevantes + disclaimer ⚠️. NO genera dictamen automático.
- INTERMEDIO: pipeline normal con Groq LLM (sin cambios).

Test inicial 5/5 queries correctamente clasificadas:
- BASICO: 2956ms, sin LLM, respuesta "RESOLUCIÓN Nº 000147-2024-GEG/INDECOPI"
- AVANZADO: 1218-5540ms, disclaimer presente, lista de normas

### Código (api_rest.py línea 1429)
```python
_nivel = "INTERMEDIO"  # default
if any(p in _ql for p in ['dictamen', 'analice', 'constitucionalidad', ...]):
    _nivel = "AVANZADO"
elif any(p in _ql for p in ['número de', 'quién es', ...]) and len(question) < 200:
    _nivel = "BASICO"
```

### Resultado final (30-abr-2026) — 37/40 (92.5%) — NO 40/40

Batería cuarto set: 37/40 PASS, 2 WARN, 0 FAIL. El reporte inicial de 40/40 (100%) fue un error de medición causado por la confianza invertida.

Router v1 dio 35/40 — modo BASICO directo sin LLM no contenía keywords. Fix: fallback a LLM si respuesta directa no matchea >=60% de keywords de la pregunta. Con fix: 37/40.

### Fixes de Confianza (01-may-2026) — 6 parches

Tras diagnóstico quirúrgico de `confidence_score()`, se aplicaron 6 fixes (ver `rag-retrieval-diagnostics` > `references/confidence-fixes-20260501.md`):
1. `db = get_sqlite()` — Capa 4 estaba muerta (db_ratio = 0.0 siempre)
2. Floor condicional `ratio >= 0.65 OR db_ratio >= 0.90`
3. Post-hoc `<= 0.75` + starts-negation check
4. Capa 4 thresholds 0.30/0.50
5. `debug_conf` poblado
- Prompt con sección FUENTES

### Qdrant source tracking (01-may-2026)

**Problema:** `semantic_quality=0.0` siempre. Merge por `numero` mantenía `source="sqlite"`.
**Fix:** Flag `_qdrant_contributed=True` + confidence_score usa `_qdrant_score`.
**Impacto:** semantic_quality pasa de 0.0 a 0.25-0.40.

### Neo4j entity filter (01-may-2026)

**Problema:** `len(t) > 4` excluía acrónimos (MTC, ONPE, UIT, CAP). El fix 27-abr seguía en pie.
**Fix:** `len(t) >= 3`, top 5→8 tokens. Log de entity_terms.

### Router AVANZADO split (01-may-2026)

**Problema:** Bloqueaba TODAS las queries avanzadas con disclaimer.
**Fix:** CREACION (dictamen, proponga, formule) → bloqueado. ANALISIS (analice, compare, integre) → LLM + disclaimer.
**Impacto:** A38: 0.24→0.61, A44: 0.47→0.50.

### Resultado 100q (01-may-2026) — 99/100 (99%)

Batería combinada SET1 (50 originales) + SET2 (50 profundizadas): 40 PASS, 59 WARN, 1 FAIL.
- SET1: 50/50 OK, avg_conf=0.55
- SET2: 49/50 OK, avg_conf=0.34
- SET2 confianza más baja por queries que requieren detalle fino no presente en sumillas

### Pendiente
- Medir ahorro real en llamadas Groq API
