# Model Comparison via Groq Batch API

Methodology for head-to-head comparison of LLM models on extraction tasks.

## When to Use

- Choosing a model for bulk document extraction
- Validating that a cheaper/faster model doesn't degrade quality
- Checking if a preview model is ready for production use

## Method

1. Prepare **identical** JSONL files for each model (same N documents, same prompts)
2. Send all batches **simultaneously** to Groq (they process in parallel)
3. Download results and compare on 4 quality dimensions

## Quality Dimensions

### 1. JSON Validity Rate
Two metrics:
- **JSON directo** — % that parse without repair
- **JSON final** — % after applying repair strategies

### 2. Content Quality
- **Fallo concreto** — % where `resumen_fallo` is specific (>20 chars, not "No se proporciona")
- **Con leyes** — % with non-empty `leyes_y_articulos_citados`
- **Hechos** — check if the facts are actually case-specific vs generic

### 3. Economics
- **Tokens in/out actual** — compare to estimates
- **Cost per 100 docs** — at normal and Batch (-50%) pricing
- **Projected cost** for the full corpus

### 4. Latency
- **Batch completion time** — how long Groq took to process (varies by load)

## Example Comparison (100 docs each, max_tokens=1024)

```
Model               JSON dir   JSON final   Fallo   Leyes   $/100  $/562K
------------------  ---------  -----------  ------  ------  -----  ------
Llama 3.1 8B        99%        99%          99%     87%     $0.01  $51
Llama 4 Scout 17B   97%        97%          87%     86%     $0.02  $117
Llama 3.3 70B       93%        93%          94%     85%     $0.11  $592
Qwen3 32B           0%         0%           N/A     N/A     $0.03  $158
```

## Script Template

```python
import json, time, requests

MODELOS = [
    ("llama-3.1-8b-instant", 0.05, 0.08),
    ("meta-llama/llama-4-scout-17b-16e-instruct", 0.11, 0.34),
    ("llama-3.3-70b-versatile", 0.59, 0.79),
]

for model_id, price_in, price_out in MODELOS:
    # 1. Build JSONL with N identical docs
    # 2. Upload to Groq Files API
    # 3. Create batch
    # 4. Poll until complete
    # 5. Download and parse each line
    #    - Count ok_raw, ok_repaired, fail
    #    - Count tiene_leyes, tiene_fallo_concreto
    # 6. Print metrics
```

## Pitfalls

1. **Always use the same documents** across all models — token counts will differ slightly due to different tokenizers
2. **Run all batches at the same time** — Groq's load varies; running sequentially introduces timing bias
3. **Check for deprecation** — Preview models may be removed mid-test. Check `console.groq.com/docs/deprecations` first
4. **Qwen3 32B Batch format issue** — This model returns responses in a format incompatible with the standard Batch output parsing. Test sync first before trusting Batch results
5. **Small sample sizes (< 50 docs)** can give misleading quality percentages. Use 100+ for stable metrics
