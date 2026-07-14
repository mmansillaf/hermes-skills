# Async Groq Timeout Pattern (06-may-2026)

## Problema
`generate_answer()` era sincronica y bloqueaba el event loop de FastAPI/uvicorn.
Si Groq tardaba >45s, TODAS las queries subsecuentes quedaban en cola. La API se colgaba completamente.

## Solucion
Convertir `generate_answer` a async usando `asyncio.to_thread()` + `asyncio.wait_for()`:

```python
async def generate_answer(question, profile, results, sources) -> str:
    try:
        context = _build_context(results, sources)
        prompt = SYSTEM_PROMPT.format(...)
        model = _model_for_level(sources.get("router", {}).get("nivel", "INTERMEDIO"))
        max_tok = 3000 if router_nivel in ("AVANZADO_CREACION", "AVANZADO_ANALISIS", "INTERMEDIO") else 1500

        def _do_groq():
            t0 = time.time()
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tok, "temperature": 0.3},
                timeout=45
            )
            r.raise_for_status()
            d = r.json()
            ms = round((time.time() - t0) * 1000)
            _track_groq_call(model, d.get("usage", {}), "generate_answer", question, profile, ms)
            return d["choices"][0]["message"]["content"].strip()

        answer = await asyncio.wait_for(
            asyncio.to_thread(_do_groq),
            timeout=50
        )
        return answer
    except asyncio.TimeoutError:
        return "[La respuesta esta siendo generada, por favor intenta de nuevo o reformula tu pregunta.]"
```

## Call site changes
`route_response` en `router.py` tambien se hizo async:
```python
async def route_response(...):
    llm_answer = await generate_answer(question, profile, unique_results, sources)
```

Y en `api_rest.py`:
```python
llm_answer, sources = await route_response(question, profile, unique_results, sources, confidence, generate_answer, logger)
```

## Pitfalls
1. `_track_groq_call` debe ejecutarse DENTRO de `_do_groq()` porque tiene acceso a `t0`
2. `requests` se importa dentro de la funcion async porque no es async-safe a nivel modulo
3. No olvidar `import asyncio` en los imports del modulo
4. `asyncio.TimeoutError` se captura explicitamente, no como `Exception` generico
5. Tiempos: HTTP timeout=45s (requests), global timeout=50s (asyncio.wait_for) — 5s de margen

## Resultado
Bateria de 100 queries: 0 timeouts, 4.8 min total. Antes: se colgaba en la query #2.
