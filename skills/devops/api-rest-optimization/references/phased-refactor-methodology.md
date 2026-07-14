# Metodología de Refactorización por Fases (Zero-Downtime)

Metodología probada en El Peruano RAG: api_rest.py 2209→1443 líneas (-35%) sin romper nada, 24/24 tests PASS.

## Principios

1. **Una fase a la vez** — nunca mezclar extracciones de dominios distintos en un solo paso
2. **Backup antes de cada fase** — copia local + SHA256, no depender de git
3. **Verificación inmediata** — sintaxis (`ast.parse`) + health check API tras cada extracción
4. **Test battery multinivel** — queries BÁSICO/INTERMEDIO/AVANZADO_ANALISIS/AVANZADO_CREACION
5. **Subagentes para trabajo pesado** — delegar extracciones a `delegate_task` preserva el contexto del agente principal y permite tracking de tokens por fase
6. **Rollback instantáneo** — `cp backups/api_rest_vX.Y_pre_faseN.py api_rest.py`

## Plantilla de fases

### Fase 1 — Quirúrgico, bajo riesgo (1-2h)
- Extraer el módulo más autocontenido (ej: confidence scoring)
- Eliminar dead code trivial (funciones con 0 usos)
- Corregir bugs de inicialización
- **Resultado esperado:** -250 líneas, 1 módulo nuevo

### Fase 2 — Módulos independientes (3-5h)
- Extraer funciones sin dependencias complejas (web, cache, metadata)
- Consolidar constantes duplicadas (stop words)
- **Resultado esperado:** -300 líneas, 4-5 módulos nuevos

### Fase 3 — Deduplicación (4-6h)
- Identificar bloques duplicados entre funciones (ej: prompt, contexto, enriquecimiento)
- Extraer helpers compartidos, unificar divergencias
- **Resultado esperado:** -30 líneas netas, ~170 líneas duplicadas eliminadas

### Fase 4 — Estructural (6-10h)
- Extraer bloques inline grandes (router, graph traversal)
- Convertir reglas hardcodeadas a data-driven
- **Resultado esperado:** -160 líneas, 2 módulos nuevos

## Checklist por fase

```
[ ] Backup: cp api_rest.py backups/api_rest_vX.Y_pre_faseN_YYYYMMDD.py
[ ] SHA256: sha256sum api_rest.py > backups/api_rest_vX.Y_YYYYMMDD.sha256
[ ] Delegar extracción a subagente con toolsets=["terminal","file","search"]
[ ] Verificar sintaxis: python3 -c "import ast; ast.parse(open('api_rest.py').read())"
[ ] Verificar nuevo módulo: python3 -c "import ast; ast.parse(open('nuevo.py').read())"
[ ] Arrancar API: python3 api_rest.py & (background)
[ ] Health check: curl localhost:8000/health
[ ] Test battery: 8-12 queries multinivel
[ ] Guardar reporte: reports/test_faseN_YYYYMMDD.txt
[ ] Actualizar skill api-rest-optimization con nuevas métricas
```

## Señales de peligro

- No delegar extracción masiva (5+ módulos en un solo subagente) — alto riesgo de fallos de parsing
- No extraer funciones que dependen de `sys.path.insert()` — arreglar imports primero
- Si un test falla, NO seguir — hacer rollback, diagnosticar, reintentar
- El `ast.parse()` detecta errores de sintaxis pero NO errores de import — por eso el health check
