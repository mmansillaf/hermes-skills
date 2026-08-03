# Feedback Loop: Critic → Writer Re-write

## Qué resuelve

El crítico detecta alucinaciones pero no las corrige. El feedback loop conecta la salida del crítico con el writer para re-escribir automáticamente las partes con citas falsas.

## Arquitectura

```
Writer genera respuesta → Critic verifica
  ├── Sin alucinaciones → Entrega ✅
  └── Con alucinaciones → _rewrite_response() → Critic re-verifica
       ├── OK → Entrega ✅
       └── Sigue mal → 2da re-escritura (strict) → Entrega con warning ⚠️
```

## Implementación en graphrag_pro.py

### Variables de control
```python
MAX_FEEDBACK_ITER = 2    # Máximo de iteraciones
feedback_iter = 0         # Contador
critic_verdict = None     # Último veredicto
```

### Loop principal
```python
while feedback_iter < MAX_FEEDBACK_ITER:
    feedback_iter += 1
    critic_verdict = critic.verify(respuesta, context_doc_ids, strict=(feedback_iter > 1))
    _save_critic_to_audit(critic_verdict)
    
    if not _needs_rewrite(critic_verdict):
        break  # Sin alucinaciones reales → salir
    
    if feedback_iter >= MAX_FEEDBACK_ITER:
        print("Límite alcanzado")
        break
    
    correccion = _rewrite_response(query, respuesta, errores, contexto)
    if correccion:
        respuesta = correccion  # Reemplazar para próxima iteración
```

## Salvaguardas anti-loop

| Salvaguarda | Detalle |
|---|---|
| Máx 2 iteraciones | Hard cap. Rara vez hay más de 1-2 citas falsas. |
| Solo hallucinaciones reales | `_needs_rewrite()` ignora identificadores no verificables (EXP. N°, CAS. N° textuales). |
| Strict en 2da iteración | `strict=True` fuerza re-escritura más agresiva. |
| Modelo barato para re-write | `llama-3.1-8b-instant` en vez del modelo principal (~$0.0002 por re-escritura). |

## Función _needs_rewrite

```python
def _needs_rewrite(critic_verdict):
    """Solo re-escribe si hay hallucinaciones REALES (doc_id no existe en corpus).
    No re-escribe por identificadores no verificables (EXP. N°, CAS. N° textuales)."""
    if not critic_verdict:
        return False
    vd = critic_verdict.to_dict()
    return vd.get("hallucinated", 0) > 0
```

## Función _rewrite_response

```python
def _rewrite_response(query, respuesta_original, errores, contexto):
    """Pide al LLM que re-escriba eliminando citas falsas.
    Usa llama-3.1-8b-instant para la corrección."""
    prompt = f"""...lista de CITAS FALSAS A ELIMINAR...
...RESPUESTA ORIGINAL...
1. Elimina referencias a citas falsas
2. NO inventes nuevas citas
3. Mantén formato y estructura
4. Responde SOLO texto corregido"""
    return groq_client.chat.completions.create(model="llama-3.1-8b-instant", ...)
```

## Integración en audit JSON

El audit JSON se actualiza con:
```json
{
  "critic": {...},
  "feedback": {
    "iterations": 1,
    "corrections": ["9999999.html eliminado"]
  }
}
```

## Cuándo NO se activa

- Respuesta sin citas → score=100% → break
- Solo identificadores textuales no verificables → hallucinated=0 → break
- Critic lanza excepción → break (catch general)
- Re-write devuelve None o texto muy corto → break
