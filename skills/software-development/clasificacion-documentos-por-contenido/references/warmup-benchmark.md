# Warmup Tests — Qwen 2.5 7B Q4_K_M (Quadro T1000 4GB)

## Test: 3 consultas idénticas (server recién iniciado)

```python
texto_prueba = '...'  # ~2000 chars de texto juridico
for i in range(3):
    resp = requests.post(f'{SERVER}/v1/chat/completions', json={
        'model': 'qwen',
        'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': texto_prueba}],
        'temperature': 0.1,
        'max_tokens': 200
    }, timeout=120)
```

Resultados:

| Consulta | Tiempo | Prompt→Completion | Tok/s | Nota |
|----------|--------|-------------------|-------|------|
| #1 | **18.2s** | 928→63 | **3.5** | Warmup: carga KV cache en GPU |
| #2 | **4.9s** | 928→63 | **12.7** | Cache caliente |
| #3 | **4.9s** | 928→63 | **12.8** | Estable |

## Implicaciones para batch

- Primera consulta: ~18s (warmup)
- Consultas siguientes: ~5s (régimen)
- En batch de 10,000 docs: 1 warmup × 18s + 9,999 × 5s = ~50,013s (~13.9h)
- El warmup representa solo el 0.04% del tiempo total en batch de 10,000
- **NUNCA reiniciar el server entre documentos de un batch**

## Implicaciones para testeo

- Si pruebas con pocos docs (1-5), la primera consulta infla el promedio
- Estrategia: descartar el primer resultado o hacer una consulta dummy primero
- El test de 4 muestras de esta sesión: primera muestra tomó 36.2s (warmup incluido), las siguientes ~25s
