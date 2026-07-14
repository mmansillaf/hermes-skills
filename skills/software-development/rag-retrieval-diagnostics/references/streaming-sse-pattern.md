# Streaming SSE Pattern (Groq + FastAPI)

## When to use
Adding real-time token streaming to an existing FastAPI endpoint that calls Groq/OpenAI LLM.

## Prerequisites
- `groq>=1.1.2` library installed
- `pip install groq httpx`

## Pattern

1. Add `stream: bool = False` to Pydantic model
2. Change endpoint `def` to `async def`
3. Create `async def generate_stream()` generator with SSE yields
4. Branch in endpoint: `if req.stream: return StreamingResponse(...)`

## SSE event format
```
data: {"event": "start", "results_count": 5}\n\n
data: {"event": "token", "text": "La"}\n\n
data: {"event": "token", "text": " Ley"}\n\n
data: {"event": "done"}\n\n
```

## Key headers for StreamingResponse
```python
headers={
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no"  # critical: disable nginx proxy buffering
}
```

## Backward compatibility
Non-streaming endpoint path unchanged. Streaming activates only with `"stream": true` in request body. Results: TTFT 0.34s vs 3-5s full response, ~336 tokens live. Same Groq cost either way.
