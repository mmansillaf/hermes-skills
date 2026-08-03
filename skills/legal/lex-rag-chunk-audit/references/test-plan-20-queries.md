# Plan de Pruebas — 20 Consultas con Auditoría Granular

## Objetivo

Validar que el sistema de auditoría granular de chunks capture métricas correctas
para consultas de diferente nivel de complejidad: simple, mediana, compleja, y
estadística/topológica.

## Niveles

| Nivel | # | Longitud | Descripción |
|-------|---|----------|-------------|
| 1 - Simple | P01-P05 | 3-6 palabras | Un concepto, una materia |
| 2 - Mediana | P06-P10 | 6-12 palabras | Dos conceptos combinados |
| 3 - Compleja | P11-P15 | 15+ palabras | Multi-arista, lenguaje técnico |
| 4 - Estadística | P16-P20 | Variable | Cuantitativa sobre el grafo |

## Distribución por materia

- Laboral: P01, P06, P07, P11, P14 (5)
- Civil-Procesal: P02, P09, P13 (3)
- Familia: P03 (1)
- Tributario: P04, P08, P15 (3)
- Constitucional: P05, P08, P12 (3)
- Penal: P10 (1)
- Estadístico: P16, P17, P18 (3)
- Comparativo: P19 (1)
- Hipótesis: P20 (1)

## Ejecución

```bash
# Desde el proyecto Lex RAG
python3 scripts/bateria_20_audit.py
```

O usando el script portable del skill:
```bash
# Copiar y ejecutar
cp ~/.hermes/skills/lex-rag-chunk-audit/scripts/bateria_audit_rag.py scripts/
python3 scripts/bateria_audit_rag.py
```

## Métricas que se verifican por consulta

1. **FAISS raw**: deben aparecer 21 chunks (top_k*3) con distance decreciente
2. **BM25 raw**: deben aparecer 21 chunks con bm25_score
3. **RRF fusion**: deben aparecer 14 chunks (top_k*2) rankeados por rrf_score
4. **Chunks filtered out**: chunks que no entraron al top-14
5. **Final docs**: exactamente 7 documentos (top_k) con label legible
6. **Graph nodes**: al menos 5 de 7 docs deben tener datos en el grafo
7. **Router**: debe retornar LOCAL para consultas jurídicas
8. **Elapsed**: tiempo total en segundos

## Reporte generado

El script produce un TXT en `data/bateria_audit_<timestamp>.txt` con:

```
================================================================================
BATERÍA DE 20 PREGUNTAS - AUDITORÍA GRANULAR DE CHUNKS
================================================================================

Total consultas: 20 | Exitosas: 20 | Tiempo total: 788.8s

ID    T(s)    Nivel  Materia                      FAISS   BM25    RRF   Desc
--------------------------------------------------------------------------------
P01   62.2    1      Laboral                       21      21      14    Despido arbitrario
...

DETALLE POR CONSULTA
################################################################################
## P01 | Nivel 1 | Laboral
**Query:** despido arbitrario
**Tiempo:** 62.2s | **Router:** LOCAL
--- RETRIEVAL HÍBRIDO ---
FAISS raw: 21 | BM25 raw: 21
Solo FAISS: 21 | Solo BM25: 21 | Ambos: 0
RRF top: 14 | Filtrados: 28 | Docs finales: 7
Top-3 chunks RRF:
  #1 | doc=850792.html | rrf=0.01639 | snippet...
--- CONTEXTO DEL GRAFO ---
Nodos: 7 | Vecinos únicos: 31 | Aristas: 39
--- RESPUESTA ---
...
```

## Resultados de referencia (2026-05-19)

- 20/20 exitosas
- 788.8s total (~39s promedio)
- 100% router LOCAL
- FAISS vs BM25: ~21 docs exclusivos cada uno, ~0-1 en común
- RRF top: siempre 14 chunks de 42 candidatos (tasa de filtrado 67%)
- Grafo: 30-55 aristas, 31-40 vecinos únicos
