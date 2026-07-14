# Análisis LightRAG/GraphRAG vs Arquitectura Actual

**Fecha:** 30-abr-2026
**Documentos analizados:** Doc_Tecnico_Desarrollo (36 KB), Reporte_Validacion (28 KB), Informe_RAG (97 KB, 13 páginas)

## Stack Actual

| Componente | Tecnología | Peso en blend |
|------------|-----------|---------------|
| Sparse retrieval | SQLite FTS5 (BM25) | 50% |
| Dense retrieval | Qdrant 384d (MiniLM) | 30% (relevance=0.0) |
| Graph enrichment | Neo4j (entity lookup) | 20% (signal≈0) |
| LLM | Groq llama-3.3-70b | — |

## Lo que proponen los documentos

Arquitectura donde el **grafo es el componente PRIMARIO**:
- Neo4j con modelo FRBRoo: Norma→Título→Capítulo→Artículo→Inciso + TemporalVersion
- LightRAG: recuperación local (vectorial) + global (grafo de comunidades)
- Router multi-agente: clasifica por nivel Básico/Intermedio/Avanzado
- Embeddings BGE-multilingual-large (768d)
- Cobertura proyectada: 75% (no implementado)

## Lo que ya tenemos mejor

| Métrica | Documentos | Nosotros |
|---------|-----------|----------|
| Implementación | Teórica | Funcional |
| Cobertura real | 75% (proyectado) | 92.5% (verificado) |
| Motor principal | Grafo Neo4j | SQLite FTS5 |
| Nivel Avanzado | 0% (modo asistido) | 100% (10/10) |
| Costo query | Variable | $0.006/query |
| Confianza | No reportada | 0.628 |

## Recomendación: 4 fases progresivas

| Fase | Qué | Impacto | Esfuerzo |
|------|-----|---------|----------|
| 1 | Embeddings BGE 768d | Qdrant útil de nuevo | 3h CPU |
| 2 | Grafo jerárquico (Mejora 2) | +5 queries leyes | 2 días |
| 3 | Router B/I/A | -40% costo API | 1 día |
| 4 | LightRAG (fork) | ¿? | 3 días |

**NO reemplazar la arquitectura actual.** Nuestro 92.5% supera el 75% proyectado. Adoptar componentes específicos, no reescribir.

## Ver documento completo

`reports/analisis_lightrag_vs_actual.md` (10,509 chars)
