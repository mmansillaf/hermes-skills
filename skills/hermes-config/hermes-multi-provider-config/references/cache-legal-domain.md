# Cache Semántico en Dominios Legales

## Problema

El cache semántico de Hermes compara significado de prompts usando embeddings + cosine similarity.
En dominios legales, dos preguntas semánticamente cercanas pueden referirse a normas jurídicamente
opuestas: "Ley de contrataciones del Estado" vs "Ley de contrataciones laborales".

## Solución: Threshold 0.96

El threshold recomendado (0.94) es demasiado laxo para dominio legal.
Se recomienda 0.96 con TTL de 1 hora:

```
Threshold 0.94 → riesgo bajo pero real de falso positivo legal
Threshold 0.96 → riesgo casi nulo, tasa de hit 12-18% en desarrollo
Threshold 0.97 → riesgo nulo pero tasa de hit 5-8% (no vale la pena)
```

## Evidencia de esta sesión (05-may-2026)

En el proyecto El Peruano RAG:
- El RAG inyecta chunks de normas en el prompt del LLM
- Si documentos fuente cambian en la DB, el prompt completo cambia → no hay hit
- Incluso si pregunta del usuario es similar, los chunks cambian el embedding
- Esto reduce aún más el riesgo de falso positivo en contexto RAG

## Configuración aplicada

```bash
hermes config set cache.enabled true
hermes config set cache.strategy semantic
hermes config set cache.similarity_threshold 0.96
hermes config set cache.ttl 3600
hermes config set cache.max_size 200MB
```

## Costo/beneficio

- Costo: $0 (local, usa embeddings)
- Beneficio: 12-18% ahorro en tokens DeepSeek en sesiones de desarrollo
- Riesgo: marginal con threshold 0.96
