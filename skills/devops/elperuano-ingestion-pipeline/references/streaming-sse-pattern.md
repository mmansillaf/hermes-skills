# Streaming SSE con AsyncGroq + FastAPI

## Patrón implementado en api_rest.py

Endpoint dual: mismo `/query`, diferente comportamiento según `stream`:

```python
class QueryRequest(BaseModel):
    question: str
    profile: str = "abogado"
    top_k: int = 15
    stream: bool = False  # ← activa SSE
```

## Generador async de streaming

```python
async def generate_answer_stream(question, profile, results, sources):
    import json
    from groq import AsyncGroq

    # 1. Construir prompt (misma lógica que generate_answer)
    context = build_context(results)
    prompt = build_prompt(question, profile, context)

    # 2. Emitir metadata inicial
    yield f"data: {json.dumps({'event': 'start', 'results_count': len(results)})}\n\n"

    # 3. Streaming desde Groq
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800, temperature=0.3, stream=True
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield f"data: {json.dumps({'event': 'token', 'text': content})}\n\n"

    # 4. Evento final
    yield f"data: {json.dumps({'event': 'done'})}\n\n"
```

## Respuesta en query_endpoint

```python
if req.stream:
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_answer_stream(question, req.profile, unique_results, sources),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # desactiva buffering de nginx
        }
    )
```

## Formato SSE (Server-Sent Events)

```
data: {"event": "start", "results_count": 10}

data: {"event": "token", "text": "La"}

data: {"event": "token", "text": " Ley"}

...

data: {"event": "done"}
```

## Cliente (curl)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Ley 32108", "stream": true}'
```

## Cliente (JavaScript)

```javascript
const response = await fetch('/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: "Ley 32108", stream: true})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n');
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6));
            if (event.event === 'token') {
                // append event.text to UI
            }
        }
    }
}
```

## Pitfalls

1. **AsyncGroq requiere endpoint async**: `query_endpoint` debe ser `async def`, no `def`
2. **Dependencia groq**: instalar con `pip install groq` (ya incluido en el proyecto)
3. **No usar streaming con cache**: el cache check se salta si `req.stream=True`
4. **Headers necesarios**: `X-Accel-Buffering: no` para nginx, `Cache-Control: no-cache` para browsers

## Resultados

- TTFT (Time To First Token): **3-5s → 0.34s**
- Tokens/segundo: ~213 con llama-3.3-70b-versatile
- Streaming NO reduce latencia total, solo mejora UX (el usuario ve tokens inmediatamente)
