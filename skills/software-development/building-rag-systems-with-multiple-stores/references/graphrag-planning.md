# GraphRAG Planning & Cost Estimation for El Peruano

## Trigger
User wants to assess whether to implement full GraphRAG (community detection + graph traversal + LLM summarization) vs staying with a multi-store RAG (SQLite + Qdrant + Neo4j as entity lookup).

## 1. Hardware Assessment

Essential commands to audit current hardware:

```bash
# Memory
free -h

# Disk (ARCHVOS012 = project storage)
df -h /media/usuario/ARCHVOS012/

# GPU
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

# Docker containers + resource usage
docker ps --format '{{.Names}} {{.Ports}}'
docker stats --no-stream --format '{{.Name}}: {{.MemUsage}}'

# Qdrant disk usage
docker exec qdrant_peruano du -sh /qdrant/storage

# Project data size
du -sh ~/el_peruano_rag/PeruanoSearchEngine02/data/

# SQLite size and stats
ls -lh ~/el_peruano_rag/PeruanoSearchEngine02/data/normas_2024.db
```

## 2. Data Audit

```python
import sqlite3
db = sqlite3.connect('data/normas_2024.db', timeout=30)

# Total, date range, column count
total = db.execute('SELECT COUNT(*) FROM normas').fetchone()[0]
f_min, f_max = db.execute('SELECT MIN(fecha_publicacion), MAX(fecha_publicacion) FROM normas').fetchone()

# Type breakdown
tipos = db.execute('SELECT tipo_norma, COUNT(*) as cnt FROM normas GROUP BY tipo_norma ORDER BY cnt DESC LIMIT 15').fetchall()

# Emitter stats
emisores = db.execute('SELECT emisor, COUNT(*) as cnt FROM normas GROUP BY emisor ORDER BY cnt DESC LIMIT 10').fetchall()
total_emisores = db.execute('SELECT COUNT(DISTINCT emisor) FROM normas').fetchone()[0]
```

```cypher
// Neo4j counts
MATCH (n) RETURN count(n) AS nodos
MATCH ()-[r]->() RETURN count(r) AS relaciones
MATCH (n:Norma) RETURN count(n) AS normas
MATCH (n:Persona) RETURN count(n) AS personas
MATCH (n:Organismo) RETURN count(n) AS organismos
MATCH (n:Monto) RETURN count(n) AS montos
```

```python
# Qdrant collections via HTTP API
import requests
resp = requests.get('http://localhost:6333/collections', timeout=10)
for col in resp.json().get('result',{}).get('collections',[]):
    name = col['name']
    det = requests.get(f'http://localhost:6333/collections/{name}', timeout=10).json()
    r = det.get('result',{})
    pts = r.get('points_count', '?')
    size = r.get('config',{}).get('params',{}).get('size', '?')
    print(f'{name}: pts={pts}, dims={size}')
```

## 3. What GraphRAG Actually Needs (vs Current State)

| Component | Current Status | Required for GraphRAG |
|-----------|---------------|----------------------|
| Graph DB with entities | Neo4j (58K nodes, 165K relations) | Already have it |
| Community detection (Leiden/Louvain) | Not installed | GDS plugin OR networkx in Python |
| Graph traversal in query pipeline | Not implemented | Cypher queries of 2-3 hops |
| LLM summaries per community | Not implemented | Groq Batch API calls per cluster |
| Vector index of community summaries | Not implemented | Qdrant collection of summary vectors |
| Community-based reranking | Not implemented | Python logic post-retrieval |
| Interactive graph dashboard | Not implemented | cytoscape.js or neovis.js |

## 4. Community Detection Options

### Option A: GDS Plugin in Neo4j (Native, recommended for production)
```dockerfile
FROM neo4j:5.18.1-community
ENV NEO4J_PLUGINS='["graph-data-science"]'
ENV NEO4J_dbms_memory_heap_max__size=12G
ENV NEO4J_dbms_memory_pagecache_size=2G
```
- Requires Docker rebuild (~30 min)
- CPU only (GDS does not use GPU)
- Community limit: ~10M nodes (we have ~200K — fine)
- RAM needed: ~12 GB peak for 200K nodes + 1.4M relations

### Option B: NetworkX in Python (Simpler, no Docker changes)
```python
import networkx as nx
import community as community_louvain  # pip install python-louvain

G = nx.Graph()
# Add edges from Neo4j export
partition = community_louvain.best_partition(G)
```
- RAM needed: ~2 GB for 200K nodes + 1.4M edges
- Time: ~15-30 min for Leiden
- Works with 29 GB free RAM — **cómodo**

### Option C: cuGraph on GPU
- Quadro T1000 has 4GB VRAM
- 200K nodes + 1.4M edges in COO format ~2.5-3 GB
- Too tight, not recommended

**Recommendation**: Start with NetworkX (B). If graph grows beyond 500K nodes, migrate to GDS.

## 5. Groq Batch API Cost Estimation

### Pricing (llama-3.3-70b-versatile)
| Aspect | Sync | Batch | Savings |
|--------|------|-------|---------|
| Input/1M tokens | $0.59 | ~$0.30 | 50% |
| Output/1M tokens | $0.79 | ~$0.40 | 50% |

### Community Summarization (108K norms, ~80-150 communities)
| Parameter | Estimate |
|-----------|----------|
| Communities expected | 80-150 (medium resolution) |
| Tokens per summary | ~500 input + ~300 output |
| Total input | ~75,000 tokens |
| Total output | ~45,000 tokens |
| **Batch cost** | **~$0.04** |

### Full-pipeline norm summarization (if needed — NOT needed here since norms already have sumilla/titulo/articulos_clave)
- 108K norms × ~1K tokens = 108M tokens
- Sync cost: ~$68
- Batch cost: ~$34
- Batch rate: ~300 req/min → ~6 hours for 108K

**Key insight**: For El Peruano, we DON'T need norm-level summarization because SQLite already has `sumilla`, `titulo`, `articulos_clave`, `palabras_clave`. Only community-level summarization is needed.

## 6. Phased Strategy

### Phase 0: Preparation (2-3 hours)
- [ ] Renew Groq API key
- [ ] Verify Serper API works
- [ ] Measure baseline latency: SQLite + Qdrant + Neo4j + Groq
- [ ] Snapshot current data (backup)

### Phase 1: Graph Traversal in Query (4-6 hours) — HIGHEST IMPACT
No GDS or communities needed. Pure Cypher.

```python
def graph_expand(slugs: list[str], depth: int = 2, max_results: int = 10):
    """Navigate graph from found norms, return expanded context."""
    expanded = []
    for slug in slugs:
        with driver.session() as session:
            result = session.run("""
                MATCH (n:Norma {slug: $slug})-[:MENCIONA]->(e)<-[:MENCIONA]-(related:Norma)
                WHERE related <> n
                RETURN related, count(e) AS conexiones
                ORDER BY conexiones DESC LIMIT $max
            """, slug=slug, max=max_results)
            expanded.extend([r.data() for r in result])
    return expanded
```

**Impact**: ~15% recall@10 improvement on queries seeking indirect connections.

### Phase 2: Community Detection with NetworkX (1 day)
1. Export Neo4j graph → CSV edges
2. Build networkx graph (~2 GB RAM, ~2 min)
3. Run Louvain/Leiden (~15-30 min)
4. Store communities in SQLite
5. Evaluate quality (modularity > 0.3)

### Phase 3: LLM Summarization via Groq Batch (2-4 hours, ~$0.04)
Prompt pattern:
```
Analiza esta comunidad de normas legales peruanas:
ID: {id}
Normas ({count}): {summaries}
Entidades: {entities}
Emisores: {emitters}

Genera:
1. Tema principal (max 5 palabras)
2. Resumen (2-3 oraciones)
3. Entidades clave (max 5)
4. Palabras clave (max 8)
5. Organismo principal
```

Store in SQLite table `community_summaries`, vectorize summaries and index in Qdrant collection `comunidades_peruano`.

### Phase 4: Full GraphRAG Query Pipeline (1 day)
```
Query → Retrieve(SQLite+Qdrant) → GraphExpand(Neo4j 2-hops) 
      → CommunityRerank → Enrich(context + summary) → Generate(Groq)
```

### Phase 5: Interactive Graph Dashboard (1-2 days)
- cytoscape.js or vis-network in Streamlit
- Nodes colored by community
- Click to expand node
- Tooltips with metadata

## 7. Full Resource Budget

### One-time costs
| Item | Cost |
|------|------|
| GDS plugin (optional) | $0 |
| NetworkX + python-louvain | $0 (pip install) |
| Groq Batch (150 communities) | ~$0.04 |
| Development time | ~3-4 days |
| **Total** | **~$0.04** |

### Monthly recurring
| Item | Cost |
|------|------|
| Groq API (sync queries) | $0 (free tier: 30 req/min) |
| Groq Batch (quarterly re-index) | ~$0.04 every 3 months |
| Serper API | $0 (free: 2,500 req/mes) |
| Electricity (ThinkPad P53 130W) | ~$5-8 |
| **Total** | **~$5-8/mes** |

### Hardware capacity check (5-year projection)
| Component | RAM needed | Available | OK? |
|-----------|-----------|-----------|-----|
| Neo4j (Docker) | ~2-3 GB | 1.3 GB current | Increase limit |
| Qdrant (Docker) | ~2-3 GB | 72 MB current | Increase limit |
| NetworkX + Leiden | ~2 GB peak | 29 GB free | Sobrado |
| GDS projection (if used) | ~8-12 GB peak | 29 GB free | Sobrado |
| Embeddings model | ~400 MB | - | OK |
| **Total peak (with GDS)** | **~15 GB** | **29 GB free** | **SI** |

### Storage projection (5 years)
| Component | Now | 5 years | Growth |
|-----------|-----|---------|--------|
| SQLite | 63 MB | ~325 MB | 5x |
| Qdrant (3 collections) | 591 MB | ~3 GB | 5x |
| Neo4j (Docker volume) | ~1 GB | ~2-3 GB | ~3x |
| Qdrant communities | 0 | ~50 MB | New |
| SQLite summaries | 0 | ~5 MB | New |
| Models | ~400 MB | ~400 MB | 1x |
| **Total** | **~5 GB** | **~6-7 GB** | **~1.3x** |

## 8. When to NOT Implement Full GraphRAG

With only 1 year of data (21K norms), the graph is too small for meaningful communities. Graph Traversal alone (Phase 1) provides 80% of the value. Full community detection + summarization only pays off with 3-5 years (~65K-108K norms).

**Decision tree**:
```
¿Tienes 3+ años de datos? → NO → Solo Graph Traversal (Phase 1)
  → SI → ¿Resultados locales insuficientes? → NO → Mejorar FTS5 + re-ranker
      → SI → Implementar GraphRAG completo (Phases 1-5)
```

## 9. Dual-Path .env Management

During development, two project paths may exist:
- Canonical: `~/el_peruano_rag/PeruanoSearchEngine02/`
- Backup: `/media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/`

The terminal working directory may be in either path. Always sync `.env` changes:

```bash
# After editing canonical .env
cp ~/el_peruano_rag/PeruanoSearchEngine02/.env /media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/.env

# Verify both have the same keys
diff ~/el_peruano_rag/PeruanoSearchEngine02/.env /media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/.env
```

**Pitfall discovered**: `read_file` shows `SERPER_API_KEY=a9267d...bff5` with `...` even when the actual file has the full key. This is display-only truncation — always verify with `grep` in terminal before assuming a key is truncated.

## 11. Competitive Landscape & Academic Validation (added 2026-04-27)

### Key Academic Paper: SAT-GraphRAG (arXiv 2505.00039)

"An Ontology-Driven Graph RAG for Legal Norms: A Hierarchical and Temporal Approach" — directly validates the architecture direction. Proposes:
- Hierarchical ontology (Constitution → Laws → Decrees → Resolutions)
- Temporal dimension (enactment dates, amendments, repeals)
- Structure-Aware Temporal Graph RAG framework

This is the blueprint for Horizonte 3. The paper demonstrates that a graph with hierarchical + temporal structure significantly outperforms both simple RAG and flat GraphRAG for legal norms retrieval.

### Key Academic Paper: Domain-Partitioned Hybrid RAG (arXiv 2602.23371)

Hybrid architecture achieves **70% pass rate vs 37.5% RAG-only baseline**. Directly validates the multi-store approach (SQLite+Qdrant+Neo4j) over single-store RAG.

### Closest Open-Source Project: justicio (⭐141)

https://github.com/bukosabino/justicio — RAG for BOE (Spanish official gazette). Same domain, same language. Architecture: simple vector search + LLM (no graph, no multi-store, no adversarial defense). El Peruano is architecturally more advanced.

### Most Advanced Open-Source: Azure GraphRAG Legal (⭐115)

https://github.com/Azure-Samples/graphrag-legalcases-postgres — Vector search + Semantic Ranking + GraphRAG on PostgreSQL with 500K US case law. The only project architecturally comparable to El Peruano's vision.

### Competitive Gap: No Latin American Legal RAG

No open-source project exists for legal RAG in Latin America. El Peruano could be the first. Full competitive analysis in `reports/investigacion_mercado_rag_legal_2026-04-27.md`.

### Architecture evaluation report

Full architecture evaluation with Horizon 1-3 roadmap in `reports/evaluacion_arquitectura_2026-04-27.md`.

## Verification

After implementing any phase:
- [ ] Latency: <2.5s for full GraphRAG pipeline
- [ ] Recall@10: documented improvement over baseline
- [ ] No 5.x Neo4j syntax errors (COUNT{} vs size())
- [ ] No Qdrant API breaking changes (query_points vs search)
- [ ] Groq key responds with valid response
- [ ] Serper returns organic results for site:elperuano.pe
- [ ] Community modularity > 0.3
- [ ] Dual .env files are synced