# EA-based RAG Pipeline Optimization

> Evolutionary Algorithms (DEAP) for hyperparameter tuning of retrieval-augmented generation systems.
> Validated for LegalTech RAG with hybrid search (FAISS + BM25 + RRF + reranker).
> 16 papers reviewed (2023-2026), 3 GitHub projects identified.

## When to Use

- **Existing RAG system** needs systematic hyperparameter tuning (not build-from-scratch)
- **Hybrid search pipeline** (vector + sparse): optimize FAISS weight, BM25 k1/b, RRF_K, alpha fusion coefficient
- **Legal/domain-specific RAG**: where grid search is too expensive and hand-tuning is unreliable
- **Before/after retrieval changes**: quantify improvement over baseline

## Parameters Optimizable

| Parameter | Type | Range | Component | 
|-----------|------|-------|-----------|
| chunk_size | int | 128-1024 | Chunking |
| overlap | int | 0-200 | Chunking |
| top_k | int | 3-25 | Retrieval |
| k1 (BM25) | float | 0.5-2.5 | Sparse search |
| b (BM25) | float | 0.1-0.9 | Sparse search |
| alpha (fusion weight) | float | 0.0-1.0 | Hybrid fusion |
| rrf_k | int | 10-100 | RRF fusion (if used) |
| reranker_threshold | float | 0.1-0.8 | Cross-encoder filter |
| reranker_top_k | int | 2-10 | Cross-encoder output |

## Fitness Function (Retrieval-Only — Recommended for First Pass)

```python
fitness = 0.5 * NDCG@10 + 0.3 * MRR + 0.2 * Recall@10
```
Cost: ~$0.09-0.10 for a full optimization with DeepSeek Flash (pop=20, gens=15, 50 validation queries).

## Workflow: Retrieval-Only First, Then Full Pipeline

**Always start with retrieval-only fitness** — no LLM calls needed per evaluation, keeps cost at ~$0.09-0.10 for a full run.

```
Fase 1 — Retrieval-Only EA (costo ~$0.09)
  Fitness: NDCG@10 + MRR + Recall@10
  Sin LLM, puro FAISS+BM25 → benchmark queries
  → Mejor conjunto de hiperparámetros de retrieval

Fase 2 — Full Pipeline EA (costo ~$9.60)
  Fitness: LLM-as-judge (precisión factual, tono, citaciones)
  Usar mejores parámetros de Fase 1 como baseline
  Solo optimizar LLM-dependentes (prompt, threshold reranker)
```

## DEAP Setup Pattern

### Single-Objective (Retrieval Fitness)

```python
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutPolynomialBounded, 
                 low=[128, 0, 3, 0.5, 0.1, 0.0, 0.1, 2],
                 up=[1024, 200, 25, 2.5, 0.9, 1.0, 0.8, 10], 
                 eta=20.0, indpb=0.15)
toolbox.register("select", tools.selTournament, tournsize=3)
```

### Multi-Objective (NSGA-II) — Recomendado para LegalTech

Cuando necesitas trade-offs explícitos entre precisión de retrieval y calidad de respuesta:

```python
# Dos objetivos: NDCG@10 (maximizar) y grounding_score (maximizar)
creator.create("FitnessMin", base.Fitness, weights=(-1.0, 0.5))
toolbox.register("select", tools.selNSGA2)
hof = tools.HallOfFame(10)
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("pareto_front", lambda pop: len(tools.sortNondominated(pop, len(pop))[0]))

algorithms.eaMuPlusLambda(pop, toolbox, mu=20, lambda_=40,
                          cxpb=0.7, mutpb=0.2, ngen=15,
                          stats=stats, halloffame=hof, verbose=True)
```

**Ventaja en LegalTech:** NSGA-II produce un frente de Pareto de configuraciones. El usuario puede elegir entre alta precisión de retrieval, alto grounding score, o balanceado.

### Fitness Function para LegalTech (Multi-Objetivo)

```python
def fitness_legal(config, benchmark_queries, docs_metadata):
    configure_pipeline(config)
    ndcg_scores, grounding_scores = [], []
    for query, ground_truth_docs in benchmark_queries:
        retrieved = hybrid_search(query, top_k=config['top_k'],
                                  alpha=config['alpha'], rrf_k=config['rrf_k'])
        ndcg = ndcg_at_k(retrieved, ground_truth_docs, k=10)
        ndcg_scores.append(ndcg)
        relevant = [d for d in retrieved if d['doc_id'] in ground_truth_docs]
        grounding_scores.append(len(relevant) / max(len(ground_truth_docs), 1))
    return (-np.mean(ndcg_scores), np.mean(grounding_scores))
```

## Paralelización de Evaluaciones

```python
import multiprocessing as mp
with mp.Pool(processes=8) as pool:
    fitness_values = pool.starmap(fitness_legal, 
                                  [(ind, bench_queries, meta) for ind in population])
```

Para evaluaciones con LLM-as-judge (evitar rate limits):
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
def evaluate_individual_with_llm(config, queries):
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(llm_judge, q, config): q for q in queries}
        scores = [f.result() for f in as_completed(futures)]
    return np.mean(scores)
```

Costo fase 2: 300 evaluaciones × 50 queries = 15K consultas DeepSeek Flash ≈ ~$9-10.

## Misevolución en RAG Context

| Riesgo | Síntoma | Mitigación |
|--------|---------|------------|
| **overfitting al benchmark** | Optimiza NDCG pero falla en queries reales | Holdout set (20%), queries rotativas |
| **reward hacking** | LLM-as-judge encuentra atajos | Evaluación humana periódica |
| **colapso de diversidad** | Una configuración domina | NSGA-II + archive (top-10 configs) |
| **deriva temporal** | Parámetros fallan meses después | Re-evaluar cada 3-6 meses |

## Surrogate-Assisted Evolution (Reducir Costo ~80%)

Cuando el fitness usa LLM-as-judge, entrenar un surrogate model:

```python
from sklearn.ensemble import RandomForestRegressor
X_train = [ind for ind in initial_population]
y_train = [real_llm_fitness(ind) for ind in initial_population]
surrogate = RandomForestRegressor(n_estimators=100)
surrogate.fit(X_train, y_train)

# Usar surrogate para ~80% de evaluaciones, LLM real solo para top 20%
for ind in population:
    if random.random() < 0.2 or generation % 5 == 0:
        ind.fitness.values = real_llm_fitness(ind)
    else:
        ind.fitness.values = (surrogate.predict([ind])[0],)
```

**Ahorro:** $9.60 → ~$2.00 para fase 2.

## Key Papers

| Paper | Venue | Why Matters |
|-------|-------|-------------|
| **HyPA-RAG** (Kalra et al.) | CustomNLP4U@EMNLP 2024 | First documented adaptive RAG for legal/policy. Directly applicable. |
| **AutoRAG-HP** | EMNLP 2024 Findings | Formulates RAG tuning as MAB. Recall@5=0.8 with 20% of grid search cost. |
| **Fusion Functions for Hybrid Retrieval** | ACM TOIS 2023 | Convex combination beats RRF. Sample-efficient (10-100 examples for α). |
| **GARAG: Genetic Attack on RAG** | EMNLP 2024 Findings | Proof-of-concept that GAs work on RAG space. Open source (⭐9). |
| **Searching for Best Practices in RAG** | EMNLP 2024 | Massive config benchmark. Practical guidance for chunk sizes, top-K. |

## Cost Estimates (DeepSeek Flash)

| Scenario | Pop | Gens | Evals | Retrieval-only | With LLM-as-judge |
|----------|-----|------|-------|---------------|-------------------|
| Small | 10 | 10 | 100 | ~$0.03 | ~$1.60 |
| Medium | 20 | 15 | 300 | ~$0.09 | ~$4.80 |
| Large | 30 | 20 | 600 | ~$0.18 | ~$9.60 |

82% cache hit rate on DeepSeek Flash reduces costs further for repeated evaluations.

## GitHub Projects

- **AutoRAG** (⭐4,936) — https://github.com/Marker-Inc-Korea/AutoRAG
- **AutoRAG-Research** (⭐145) — https://github.com/NomaDamas/AutoRAG-Research
- **DEAP** — https://github.com/DEAP/deap

## Benchmark Datasets for Legal RAG

- **LEXTREME** (EMNLP 2023) — 11 legal datasets, 24 languages (includes Spanish)
- **MrTyDi** — Multilingual retrieval benchmark (11 languages, Spanish included)
- **MultiEURLEX** — 65K EU laws, multilingual (Spanish included)

Best practice: build 50-100 query benchmark from your own corpus with manual ground truth.

## Pitfalls

1. **chunk_size requires reindexing** — cannot vary per-evaluation. Pre-build 3-5 variants and optimize separately.
2. **BM25 parameters (k1, b) require BM25 rebuild** — lightweight (<1s for 348K docs), can vary per eval.
3. **Overfitting to benchmark** — use holdout set (20% of queries) not seen during evolution.
4. **Convergence premature** — increase population when landscape is noisy. Use Hofstede archive (top-5 configs, not just best).
5. **Crossover producing invalid individuals** — always validate after mate/mutate (`overlap < chunk_size`, `nprobe < nlist`).
