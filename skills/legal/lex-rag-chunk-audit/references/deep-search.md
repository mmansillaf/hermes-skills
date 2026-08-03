# Deep Research para Lex RAG — Análisis y Diseño

## ¿Qué es Deep Research?

No es un modelo nuevo. Es un patrón de orquestación que combina:
1. **Planificación** → descomponer pregunta en sub-preguntas
2. **Búsqueda paralela** → múltiples queries al retrieval simultáneamente
3. **Extracción estructurada** → hechos, no documentos enteros
4. **Detección de lagunas** → ¿falta algo? busca más
5. **Síntesis multi-fuente** → responde integrando todo

## Estado actual del pipeline

```
query → [HyDE] → [FAISS+BM25] → [Graph] → [Synthesis] → [Critic + Feedback]
```

Soporta solo UNA ronda de retrieval con UNA query de búsqueda.

## Opciones de implementación

### 🥇 Opción A: Multi-Query + Fusión (recomendada, 3-5 días)

**Componentes:**
1. Planificador: dado `query`, genera 3-5 sub-queries con distintos enfoques (LLM 8B)
2. Búsqueda paralela: `ThreadPoolExecutor` con `get_hybrid_context()` para cada sub-query
3. Fusión extendida: RRF con todos los chunks de todas las queries
4. Detector de lagunas: critic extendido que verifica cobertura conceptual
5. Iteración: segunda ronda de retrieval solo para las lagunas

**Costo adicional:**
- LLM calls: +1-3 (planificador + lagunas)
- Retrieval calls: +2-4 (en paralelo, apenas +1-2s latencia)
- Input tokens: ~2× (~8,000 vs ~4,500)
- Latencia total: +20-50% (~45-55s vs ~37s)
- Costo/query DeepSeek: ~$0.007 vs ~$0.004

### 🥈 Opción B: Solo Multi-Query (rápida, 1-2 días)

Sin planificador ni detector de lagunas. Generar 3 queries desde la original con reglas, buscar en paralelo, fusionar. 60% del beneficio con 30% del esfuerzo.

**Generación de queries adicionales por reglas:**
```python
def expand_queries(query):
    queries = [query]
    # Versión más específica (añadir términos clave del dominio)
    if len(query.split()) < 8:
        queries.append(query + " jurisprudencia peruana")
    # Versión con sinónimos
    if "indemnización" in query:
        queries.append(query.replace("indemnización", "reparación"))
    # Versión enfocada en fallo
    queries.append(query + " fallo corte suprema")
    return queries[:5]
```

## Cambios al código

### Impacto mínimo con flag opcional `--deep`

| Archivo | Cambio |
|---|---|
| `graphrag_pro.py` | +5 líneas: flag `--deep` al argparse |
| `graphrag_pro.py` | +8 líneas: if deep: en run_console_query() |
| `agents/deep_searcher.py` | ~120 líneas nuevas: DeepSearcher class |
| `retrieval/hybrid_search.py` | 0 cambios |
| `agents/synthesizer.py` | 0 cambios |
| `agents/critic.py` | 0 cambios |

### Uso

```bash
# Sin deep research (comportamiento actual)
python3 graphrag_pro.py --query "despido arbitrario"

# Con deep research
python3 graphrag_pro.py --query "despido arbitrario" --deep

# En modo interactivo
python3 graphrag_pro.py --deep
```

### Lo que NO cambia

- Graph Analyst (estadísticas del grafo)
- Synthesis (generación de respuesta)
- Critic (verificación de citas)
- Feedback loop (re-escritura automática)
- Repreguntas (historial)
- Auditoría granular (JSON)
- Batería de pruebas existentes

## Comparativa: hoy vs con Deep Research

| Aspecto | Hoy | Con Deep Research |
|---|---|---|
| Queries de búsqueda | 1 (HyDE) | 3-5 (planificador LLM) |
| Chunks recuperados | 21 | 63-105 (paralelo) |
| Documentos únicos | 7 | 15-25 |
| Cobertura de conceptos | 1 ángulo | 3-5 ángulos |
| Detección de lagunas | No | Sí (critic extendido) |
| Feedback loop | Solo citas | Citas + cobertura conceptual |

## Costo mensual estimado (3,000 consultas)

| Escenario | Hoy | Opción A (Multi-Query) | Incremento |
|---|---|---|---|
| LLM calls | ~9,000 | ~15,000 | +67% |
| Con Groq | **$0** | **$0** | **$0** |
| Con DeepSeek V4 flash | ~$12 | ~$21 | +$9/mes |
| Con DeepSeek V4 pro | ~$45 | ~$75 | +$30/mes |
