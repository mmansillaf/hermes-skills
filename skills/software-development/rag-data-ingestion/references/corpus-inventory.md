# Corpus Inventory — Peruvian Legal Documents

Methodology for inventorying a classified legal document corpus by type and materia, based on the 558K-document ClasificacionJurisPDF corpus.

## Document Type Distribution

From a corpus of 558,320 PDF/DOC files classified by content type:

| Type | Count | % | Value for RAG |
|------|:-----:|:-:|:-------------:|
| **Sentencia** | 243,288 | 43.6% | Highest — contains fallo, hechos, ratio decidendi |
| **Resolución** | 192,116 | 34.4% | High — procedural rulings with legal reasoning |
| Notificación | 44,777 | 8.0% | Low — procedural notices, little legal value |
| Oficio | 16,488 | 3.0% | Low — inter-court correspondence |
| Demanda | 16,117 | 2.9% | Medium — complaint filings, petitioner arguments |
| Conciliación | 7,722 | 1.4% | Low — settlement records |
| Pericia | 5,328 | 1.0% | Medium — expert reports |
| Otros (Acta, Citación, etc.) | ~32,498 | 5.8% | Variable |
| **Total** | **558,320** | 100% | |

**Key insight:** Sentencia + Resolución = **435,404 docs (78%)** — these are the ones with real legal reasoning worth extracting and indexing.

## Materia Detection by Filename Pattern

Peruvian judicial document filenames contain a court/office code that reveals the materia (subject matter). Common patterns:

| Materia | Pattern | Found in 435K Sent+Res | Example filename |
|---------|:-------:|:----------------------:|------------------|
| **LABORAL** | `-LA-` | 76,773 | `00001-2018-0-1706-JP-LA-01.pdf` |
| **CIVIL** | `-CI-` | 12,545 | `00002-2019-0-1801-JP-CI-02.pdf` |
| **COMERCIAL** | `-CO-` | 2,162 | `00003-2020-0-1801-JP-CO-03.pdf` |
| **FAMILIA** | `-FT-` | 49 | `00004-2020-0-1801-JP-FT-04.pdf` |
| **Sin materia visible** | (none) | **343,875** | No pattern match |

**IMPORTANT: These patterns are on the FILENAME, not the content.** The 343,875 docs without a recognizable pattern may still have materia — but you'd need to extract the carátula (case header from page 1) to classify them. The pattern-based approach only identifies ~21% of Sentencia+Resolucion documents by materia.

### Detection Script

```python
import os
from collections import Counter

base = '/path/to/Clasificados'
patrones = {
    'LABORAL': ('-LA-', 76773),
    'CIVIL': ('-CI-', 12545),
    'COMERCIAL': ('-CO-', 2162),
    'FAMILIA': ('-FT-', 49),
}

counts = Counter()
for cat in ['Sentencia', 'Resolución']:
    cat_dir = os.path.join(base, cat)
    for f in os.listdir(cat_dir):
        for materia, (patron, _) in patrones.items():
            if patron in f:
                counts[materia] += 1
                break
```

## Processing Priority

| Priority | Materia | Docs | Rationale |
|:--------:|---------|:----:|-----------|
| **P0** | LABORAL | 76,773 | Most common in queries (despido, beneficios sociales, utilidades) |
| **P1** | COMERCIAL | 2,162 | Contract disputes, corporate law |
| **P2** | FAMILIA | 49 | Small set, quick to process |
| **P3** | CIVIL | 12,545 | Obligations, property, contracts |
| **P4** | Sin materia | 343,875 | Needs carátula extraction first |

## Indexing Progress Tracking

Track what's been processed using `custom_id` prefixes in Groq batch outputs:

```python
from collections import Counter

procesados = Counter()
for fname in ['batch_results/batch_lote1_output.jsonl', ...]:
    for line in open(fname):
        d = json.loads(line)
        cid = d.get('custom_id', '')
        if cid and '_' in cid:
            procesados[cid.rsplit('_', 1)[0]] += 1
```

## Cost Projection by Materia

Using Llama 3.1 8B Instant via Groq Batch API ($0.000088/doc):

| Batch | Docs | Cost | Time (Batch API) |
|-------|:----:|:----:|:----------------:|
| LABORAL | 76,773 | $6.76 | ~3-4h (3 batches) |
| COMERCIAL | 2,162 | $0.19 | ~15 min (1 batch) |
| FAMILIA | 49 | $0.004 | ~1 min (inline) |
| CIVIL | 12,545 | $1.10 | ~1h (1 batch) |
| Sin materia | 343,875 | $30.26 | ~4 batches |
| **TOTAL Sent+Res** | **435,404** | **$38.32** | **~9 batches** |
| **Corpus completo** | **558,320** | **$49.13** | **~12 batches** |

## Observed Batch Timing (Groq Batch API)

| Batch Size | Completion Time | Throughput | Notes |
|:----------:|:---------------:|:----------:|-------|
| 25,000 docs | ~3 hours | ~139 docs/min | Lote 1 (LAB) |
| 7,935 docs | ~4 hours | ~33 docs/min | Lote 2 (LAB+COM) — slower |
| 12,500 docs | ~2 hours | ~104 docs/min | Lote 1a (estimated) |

Timing is unpredictable — Groq's 24h window means batches can complete anywhere from 2 min to 12h. The smaller batch taking longer (Lote 2 vs Lote 1) is typical of batch scheduling.

## File Size Limits

Groq accepts max **200 MB** per uploaded JSONL file. At ~7 KB/line (30K chars input + request overhead):

- ~28,000 lines max per file
- Split with: `split -l 12500 -d --additional-suffix=.jsonl input.jsonl output_prefix_`

Real sizes observed:
- 25,000 docs: ~157 MB (under limit)
- 12,500 docs: ~75-80 MB (safe)
- 7,935 docs: ~42 MB (very safe)
