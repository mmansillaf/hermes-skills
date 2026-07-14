# Embeddings Comparison — MiniLM 384d vs E5 1024d

Date: 30 April 2026
Conclusion: MiniLM is 4.7x better. Do NOT migrate.

## Test Setup
6 queries in Spanish legal domain: SBS disolucion, INDECOPI designacion, prorroga tributaria, viaje Chile, beneficios regularizacion, viaje superintendente.

## Results
| Model | Dims | Range | Speed | Discrimination |
|-------|------|-------|-------|----------------|
| MiniLM 384d | 384 | 1.590 | 96 q/s | Excellent |
| E5-large 1024d | 1024 | 0.341 | 11 q/s | Poor |

MiniLM spreads 0.13-0.75. E5 gives 0.80-0.90 for everything. MiniLM is 4.7x more discriminative and 8.9x faster.

## Verdict
Keep MiniLM 384d. Embeddings upgrade would degrade Qdrant search.
