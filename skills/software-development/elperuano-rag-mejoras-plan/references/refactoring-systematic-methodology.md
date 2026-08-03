# Metodología de Refactorización Sistemática — api_rest.py

**Sesión:** 2026-05-05 | **Resultado:** 2209 → 1605 líneas (-604, -27%)

## Principios

1. **Cambios quirúrgicos por fase** — no refactorización masiva. Extraer un módulo, testear, commit.
2. **Subagentes paralelos** — analysis + implementation en paralelo vía `delegate_task`. El análisis no modifica código, la implementación sí.
3. **Test battery después de cada fase** — 8-12 queries multinivel (BÁSICO, INTERMEDIO, AVANZADO_ANALISIS, AVANZADO_CREACION).
4. **Backup antes de empezar** — git tag + checksum + copia de src/.

## Fases ejecutadas

### Fase 1 — Extracción de confidence scoring (quirúrgico, ~1h)
- Extraídas 7 funciones de confidence scoring → `src/core/confidence.py` (288 líneas)
- Eliminado dead code: `_make_result()`, `get_qdrant()`
- Corregidos bugs: type annotation (float→Tuple[float,dict]), dir() hack en `_materia_params`, vars sin inicializar
- **Resultado:** 2209 → 1917 líneas (-292)

### Fase 2 — Extracción de módulos autocontenidos (~1.5h)
- `src/web/fallback.py` (163 líneas): search_local_htmls, search_web_fallback, search_tavily
- `src/core/scoring.py` (38 líneas): _dedup_and_blend
- `src/core/cache.py` (37 líneas): _get_cached, _set_cache
- `src/core/metadata_extractor.py` (103 líneas): extract_structured_metadata
- Stop words consolidados automáticamente por extracciones previas
- **Resultado:** 1917 → 1638 líneas (-279)

### Fase 3 — Unificación de generate_answer / generate_answer_stream (~1.5h)
- Creados 3 helpers compartidos: `_enrich_entities()`, `_build_context()`, `SYSTEM_PROMPT`
- `generate_answer()`: 160 → 27 líneas (-133)
- `generate_answer_stream()`: 85 → 40 líneas (-45)
- Bug corregido: streaming hardcodeaba modelo, ahora usa `_model_for_level()`
- **Resultado:** 1638 → 1605 líneas (-33 netas, -174 duplicadas)

## Patrón de delegación para refactoring

```python
delegate_task(
    goal="Extraer X funciones a src/nuevo/modulo.py",
    context="Archivo: api_rest.py (NNNN líneas). Funciones en líneas A-B...",
    toolsets=["terminal", "file", "search"]
)
```

El subagente:
1. Lee las funciones a extraer
2. Crea el nuevo módulo con imports
3. Elimina las funciones de api_rest.py + agrega import
4. Verifica sintaxis con `ast.parse()`

## Test battery mínima (8 queries)

Niveles: BASICO (2), INTERMEDIO (2), AVANZADO_ANALISIS (2), AVANZADO_CREACION (2)
Criterio PASS: respuesta > 50 chars, confianza razonable, sin errores HTTP

## Estructura final post-Fase 3

```
api_rest.py (1605 líneas)
src/
├── core/
│   ├── confidence.py          (288)  Fase 1
│   ├── scoring.py             (38)   Fase 2
│   ├── cache.py               (37)   Fase 2
│   ├── metadata_extractor.py  (103)  Fase 2
│   └── query_classifier.py    (667)  existente
├── web/
│   └── fallback.py            (163)  Fase 2
└── utils/
    └── token_tracker.py       (183)  tracker
```

## Pendiente (Fases 4-5)

- Fase 4: Extraer routing y graph traversal
- Fase 5: Decisiones (unificar orchestrators, archivar legacy, consolidar CLIs)
