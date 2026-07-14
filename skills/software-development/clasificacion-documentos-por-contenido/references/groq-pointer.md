# Pointers to related references

This skill references Groq Batch API for batch document extraction.
See the `elperuano-ingestion-pipeline` skill's reference:
`references/groq-batch-extraction.md` — model comparison data, 
max_tokens optimization, JSON repair strategies, chunking patterns.

Key findings from this session (Jun 2026):
- Llama 3.1 8B with max_tokens=1024 achieves 100% JSON validity
- 30K char content limit covers 89% of documents fully
- 99.8% batch success rate for 2,000 docs at $0.18
