# TC SearchRAG — Demo Session (Jun 2026)

End-to-end demo with all 4 query modes, verified working.

## Prereqs

- Python 3.12+ with deps installed (requirements.txt)
- GROQ_API_KEY in .env (valid, not expired)
- 11,483 docs indexed (data/faiss_index.bin, bm25_index.pkl, etc.)

## 1. Búsqueda simple (sin IA)

```bash
cd /mnt/d/PyCode/TC_SearchRAG
python3 src/search_tc.py "pension" --top-k 3
# → ~1.8s retrieval, 3 resultados con EXP, materia, snippet
```

## 2. Filtros (sin texto)

```bash
python3 src/search_tc.py "" --materia Pensiones --cosa-juzgada --top-k 3
# → 5-12ms, 526 resultados de Pensiones con cosa juzgada
```

## 3. Consulta legal formal (Groq)

```bash
python3 src/ask_tc.py "requisitos para pension por enfermedad profesional" --top-k 5
# → Groq llama-3.3-70b, 2.4s (!), respuesta estructurada
```

Output: (a) respuesta directa, (b) fundamentos con EXP N° y archivo, (c) conclusión, preguntas seguimiento.

## 4. Consulta conversacional (Groq)

```bash
python3 src/narrar_tc.py "por que me niegan mi pension si tengo silicosis"
# → Groq llama-3.3-70b, ~74s, respuesta explicativa profesional
```

## 5. API REST

```bash
# Terminal 1: servidor
cd /mnt/d/PyCode/TC_SearchRAG/src && python3 app.py
# Esperar ~50s a que cargue índices

# Terminal 2: consultas
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/search?q=pension&materia=Pensiones&top_k=2"
curl -s http://localhost:8000/stats
```

## Timings observed

| Query mode | Time | Notes |
|-----------|:----:|-------|
| search_tc.py "pension" | 1.8s | ~11s first-run (loading indices) |
| search_tc.py filters only | 17ms | 526 docs returned |
| ask_tc.py (Groq 70b) | **2.4s** | Surprisingly fast — Groq 70b is not always 25-32s |
| narrar_tc.py (Groq 70b) | 74s | Slower due to more context tokens |
| app.py /health | instant | After indices loaded |
| app.py /stats | instant | After indices loaded |

Key insight: Groq 70b response time varies WILDLY (2.4s → 74s) depending on context length and Groq's internal queue. Not a code issue.
