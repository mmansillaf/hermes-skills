# Monitoreo de Artefactos en Baterías de Prueba

## Qué mide

Durante la ejecución de una batería de preguntas, cada artefacto del sistema puede activarse o no. Monitorear cuáles se activan revela:
- Cobertura real de la DB (SQLite FTS5)
- Dependencia de búsqueda externa (Serper, Web Fallback)
- Efectividad de búsqueda semántica (Qdrant)
- Utilidad del grafo de relaciones (Neo4j)
- Calidad del router (modo BÁSICO directo vs fallback LLM)

## Métricas a capturar por query

```python
artifact_stats = {
    "serper_web": 0,      # ¿Se activó Serper (Google)?
    "qdrant_used": 0,     # ¿Qdrant contribuyó resultados?
    "neo4j_used": 0,      # ¿Neo4j contribuyó resultados?
    "web_fallback": 0,    # ¿Se usó web fallback (3 capas)?
    "cache_hits": 0,      # ¿Respuesta desde cache?
    "llm_fallback": 0,    # ¿Modo BÁSICO rechazado → LLM?
    "directo": 0,         # ¿Modo BÁSICO directo aceptado?
    "borrador": 0,        # ¿AVANZADO_CREACION generó borrador?
    "leyes": 0,           # ¿Se consultaron leyes externas?
    "sql_count": 0,       # Total resultados SQLite
}
```

## Interpretación

| Artefacto | % Alto (>50%) | % Bajo (<20%) | Significado |
|-----------|---------------|---------------|-------------|
| qdrant_used | Buena cobertura vectorial | Vectores no indexados o collection incorrecta |
| neo4j_used | Grafo de entidades útil | entity_terms vacíos o Neo4j caído |
| serper_web | DB no cubre estas queries | DB cubre bien, no necesita internet |
| llm_fallback | Modo BÁSICO está rechazando correctamente | Modo BÁSICO aceptando respuestas potencialmente malas |
| directo | **Preocupante si >10%** — riesgo de falsos positivos | **Ideal <5%** — solo respuestas confirmadas |

## Ejemplo real (50q PJ/Callao, 2026-05-02)

```
sql_count: 2185       (44 resultados/query promedio)
qdrant_used: 37/50    (74% — buena cobertura vectorial)
neo4j_used: 20/50     (40% — grafo útil)
web_fallback: 19/50   (38% — muchas queries necesitan internet)
serper_web: 17/50     (34% — Google como fallback)
llm_fallback: 9/50    (18% — modo BÁSICO rechazando bien)
directo: 1/50         (2% — solo 1 query pasó validación, EXCELENTE)
```

## Conclusión de esta batería

- Cobertura DB: MEDIA (38% necesita web fallback)
- Qdrant: BUENO (74% de queries lo usan)
- Modo BÁSICO: EXCELENTE (solo 2% aceptado, 0 falsos positivos)
- Problema detectado: sumillas vacías en PJ/municipales → alto web fallback
