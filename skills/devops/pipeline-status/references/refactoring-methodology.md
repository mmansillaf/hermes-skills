# Metodología de Refactorización por Fases

## Enfoque usado en api_rest.py (El Peruano RAG, 05-may-2026)

### Principios
1. **Cambios quirúrgicos** — extraer un módulo, testear, commit. No refactor masivo.
2. **Subagentes por fase** — delegar cada fase a un subagente aislado para tracking de tokens.
3. **Backup antes de cada fase** — git tag + copia local con checksum SHA256.
4. **Verificación por paso** — AST parse después de cada cambio, nunca asumir que funciona.

### Pipeline por fase
```
1. Backup (git tag + cp + sha256sum)
2. Delegar extracción a subagente (contexto: solo la fase actual)
3. Verificar sintaxis: python3 -c "import ast; ast.parse(open('file.py').read())"
4. Health check: curl http://localhost:8000/health
5. Actualizar skill pipeline-status con nuevo estado
```

### Resultados cuantificados (5 fases + D1 completadas)

| Fase | Archivo | Antes | Después | Delta | Módulos creados |
|------|---------|-------|---------|-------|----------------|
| F1 | api_rest.py | 2209 | 1942 | -267 | confidence.py (288) |
| F2 | api_rest.py | 1942 | 1638 | -304 | fallback.py (163), scoring.py (38), cache.py (37), metadata_extractor.py (103) |
| F3 | api_rest.py | 1638 | 1605 | -33 | _enrich_entities(), _build_context(), SYSTEM_PROMPT (helpers inline) |
| F4 | api_rest.py | 1605 | 1443 | -162 | router.py (151), graph_traversal.py (67) |
| D1 | — | — | — | deprecación | orchestrators v3/v4 → scripts_legacy, CLI migrado a API REST |
| **Total** | | **2209** | **1443** | **-766 (-35%)** | **8 módulos + 3 helpers** |

### Tokens consumidos en refactor (DeepSeek V4-Pro)
- F1 subagente: 255,851 tokens
- F2 subagente: 894,548 tokens
- F3 subagente: 634,014 tokens
- F4 subagente: 488,265 tokens
- D1 subagente: 184,770 tokens
- Informe análisis: 814,761 tokens
- Token tracker build: 890,447 tokens
- **Total refactor: ~4.2M tokens ($3.70 USD)**

### Lecciones aprendidas
- Extraer funciones autocontenidas primero (confidence scoring era el módulo más aislado)
- Las fases con más módulos pequeños son más eficientes que una fase grande
- El hack `'_var' in dir()` es señal de scope demasiado grande — la variable debería inicializarse explícitamente
- Los imports `import re as _re_X` son síntoma de archivo monolítico: cada función intenta aislar su namespace
- No modificar código en el informe de análisis — solo describir. Implementar en fases separadas.
- **Token tracking dual**: crear tracker para la app RAG (token_tracker.py, Groq) Y otro para Hermes (hermes_token_tracker.py, DeepSeek). La app no mide el consumo del agente.
- **Simulación antes de deprecar**: comparar respuestas reales del sistema actual vs legacy antes de eliminar código. Los números (confianza, fuentes, derrotismo) son más persuasivos que argumentos.
- **Decisiones D1-D4**: preguntar al usuario en vez de asumir. Presentar opciones con ejemplos concretos de impacto.
