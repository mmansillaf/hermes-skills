# Data Quality Audit & Groq Batch Re-indexing

## When to use
After building a RAG system with LLM-extracted metadata (sumillas), when the system returns "no se encontró" for queries about norms you KNOW are in the database, despite high confidence scores. The retrieval works (correct norm ID), but the content indexed is wrong.

## Detection: Sumilla Corruption Pattern

### Symptoms
- High confidence (≥0.75) but LLM says "no se encontró" consistently
- Multiple queries about the same norm all return empty/negative answers
- Norm retrieval works (correct tipo + numero in results) but content is irrelevant
- Sumilla length is suspiciously short (< 200 chars) for the norm type

### Quick Check
```bash
python3 -c "
import sqlite3
db = sqlite3.connect('data/normas_2024.db')
row = db.execute(\"SELECT numero, sumilla, length(sumilla) FROM normas WHERE numero LIKE '%102-2024-PCM%' LIMIT 1\").fetchone()
print(f'Sumilla ({row[2]} chars): {row[1]}')
"
# If sumilla doesn't match the norm's known topic, data is corrupted
```

### Real Case: El Peruano RAG (2026-04-29)

| Norma ID (correct) | Sumilla registrada (wrong) | Contenido real |
|-----|---------------------------|----------------|
| DS 102-2024-PCM | "Nombran Ministra de Comercio Exterior y Turismo" | Estado de Emergencia por contaminación hídrica en Islay y General Sánchez Cerro |
| RM 1206-2024-IN | "Aceptan renuncia de fiscal adjunta provincial" | Listado de Inversiones Estratégicas PESEM Sector Interior 2030 |

### Root Cause
The ingestion pipeline used a **municipal sanctions-specific schema** for all 19,892 norms:
```json
{
  "Nro_Resolucion": "...",
  "Cronograma_Procesal": {...},
  "Datos_Votacion": {"Miembros_Concejo": ..., "Votos_A_Favor": ...},
  "Materia": "Vacancia, Nepotismo, Propaganda..."
}
```
This schema assumes every norm is a municipal council sanction. When applied to national norms, the LLM hallucinated or cross-assigned values from other norms in the same batch.

---

## Solution: Re-index via Groq Batch API

### Universal Schema (correct)
```json
{
  "tipo_norma": "DS",
  "numero": "102-2024-PCM",
  "fecha": "2024-04-01",
  "emisor": "Presidencia del Consejo de Ministros",
  "sumilla": "Prorroga Estado de Emergencia por contaminación hídrica...",
  "materia": "Estado de Emergencia",
  "funcionarios": ["Dina Boluarte Zegarra"],
  "entidades": ["INDECI", "Gobierno Regional Arequipa"],
  "base_legal": ["Constitución Política Art. 137"],
  "montos": [],
  "normas_citadas": ["DS 001-2024-PCM"]
}
```

### Why Batch API over Sync
- **50% discount** on token prices
- Async processing (submit and poll)
- No rate limit headaches (RPM/RPD limits don't apply to batch)
- Perfect for 10K+ documents

### Cost Analysis (19,892 normas)

| Model | Input $/1M | Output $/1M | Total Cost |
|-------|-----------|-------------|------------|
| llama-3.1-8b-instant | $0.05 | $0.08 | **$0.83** |
| llama-3.3-70b-versatile | $0.59 | $0.79 | $9.58 |

**Recommendation: 8B is sufficient** for metadata extraction. 70B is 12x more expensive with no quality gain.

### Token Estimation
- Input per document: ~1,500 tokens (cleaned markdown text)
- Output per document: ~100 tokens (JSON metadata)
- 19,892 docs × 1,500 = 29.8M input tokens
- 19,892 docs × 100 = 2.0M output tokens

### Pipeline Script
```bash
# 1. Backup
cp data/normas_2024.db data/normas_2024.db.pre_reingest

# 2. Generate JSONL batches
python scripts/data_prep/02_groq_batch_pipeline.py generate

# 3. Upload to Groq Batch API (async)
python scripts/data_prep/02_groq_batch_pipeline.py upload

# 4. Check status (poll until completed)
python scripts/data_prep/02_groq_batch_pipeline.py status

# 5. Download results
python scripts/data_prep/02_groq_batch_pipeline.py download

# 6. Rebuild SQLite from extracted JSON
python scripts/data_prep/03_build_sqlite.py

# 7. Re-vectorize Qdrant
python scripts/data_prep/04_vectorize_qdrant.py
```

### Validation After Re-indexing
```bash
# Check 5 known norms have correct sumillas
python3 -c "
import sqlite3
db = sqlite3.connect('data/normas_2024.db')
for num in ['102-2024-PCM', '1206-2024-IN', '1203-2024-IN', '1202-2024-IN', '569-2024-MTC']:
    row = db.execute(\"SELECT numero, sumilla FROM normas WHERE numero LIKE ?\", (f'%{num}%',)).fetchone()
    print(f'{row[0]}: {row[1][:100]}')
"

# Run 3-type functional test
# Exact ID → expect conf ≥ 0.75, no web fallback
# Adversarial → expect conf ≤ 0.15, web fallback active
# Thematic → expect conf ≥ 0.75, answer has content
```

### Prevention Checklist
- [ ] Schema fields are universal (tipo_norma, numero, fecha, emisor, sumilla, materia)
- [ ] No domain-specific fields unless 100% of documents are that domain
- [ ] Post-ingestion sampling: check 50 random sumillas against known document topics
- [ ] Checksum per batch: hash original HTML content to detect cross-assignment
- [ ] Separate schemas for separate document sources (El Peruano ≠ municipal)
- [ ] Backup before every re-ingestion
