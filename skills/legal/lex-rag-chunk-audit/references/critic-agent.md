# Critic Agent — Verificador de Citas Jurisprudenciales

## Rol
Post-procesa la respuesta del Legal Writer y verifica que cada cita
corresponda a un documento real en el corpus.

## Archivo
`agents/critic.py` — clase `CriticAgent`

## Salida
`Verdict(passed, score, action, errors, warnings, citations)` con método `to_dict()`.

## Integración
En `graphrag_pro.py`, después del bucle de streaming:

```python
critic = CriticAgent()
verdict = critic.verify(respuesta_completa, context_doc_ids=top_docs, strict=False)
if not verdict.passed:
    print("🔍 CRÍTICO DE CITAS:")
    for err in verdict.errors:
        print(f"   ⚠️ {err}")
```

El veredicto se añade al audit JSON existente bajo clave `"critic"`.

## Fases
- **Fase 1 (actual)**: warn-only. Muestra advertencias, no bloquea.
- **Fase 2**: re-rewrite cuando `strict=True`. El Orchestrador decide si re-escribir.

## Test results (10 queries)
```
Critic score 100%: 8/10 queries
Hallucinations detected: 2 queries (M2=2, C1=1) — leyes capturadas como doc_ids
Unverifiable (identificadores textuales): ~30% de citas
```
