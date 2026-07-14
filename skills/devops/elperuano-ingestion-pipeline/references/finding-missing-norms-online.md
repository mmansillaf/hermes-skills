# Finding & Ingesting Missing Norms Online

## When to use

A battery of test questions references norms by number (e.g., "RS 040-2024-SUSALUD") but the database returns "NO INDEXADA" for those queries. The norms exist in the real world (published in El Peruano) but were not part of the initial ingestion pipeline.

## Search sources (ordered by reliability)

| Source | URL Pattern | Notes |
|--------|-------------|-------|
| **SPIJ** (Minjus) | `spij.minjus.gob.pe` | Official legal database. May block automated extraction. |
| **El Peruano** (official) | `busquedas.elperuano.pe/dispositivo/NL/<ID>` | Official; IDs can be found via Google. Often blocks extraction. |
| **El Peruano** (mirror) | `lapatria.pe/elperuano/<edicion>/<slug>` | Unofficial republication with full HTML text, extractable via web_extract. Most reliable source for automatic extraction. |
| **Gob.pe** | `cdn.www.gob.pe/uploads/document/file/<ID>/<filename>` | Official government PDF repository. Direct PDF downloads work. |
| **iuslatin.pe** | `iuslatin.pe/wp-content/uploads/...` | Legal blog with PDFs. Good for SUSALUD resolutions. |
| **Regional gov sites** | `regionsanmartin.gob.pe`, etc. | Each regional government publishes their own ordinances. |

## Search methodology

### Step 1 — Identify exact norm titles

Before searching, determine the EXACT title from the question battery:
- "RS 040-2024-SUSALUD" → "Resolución de Superintendencia N° 040-2024-SUSALUD/S"
- "DS 141-2024-EF" → "Decreto Supremo N° 141-2024-EF"

Use web_search with site operators:
```python
queries = [
    'site:diariooficial.elperuano.pe "Resolución de Superintendencia" 040-2024 SUSALUD',
    'site:lapatria.pe "Resolución" 042-2024 SUSALUD',
    'site:gob.pe "Resolución Suprema" 009-2024-MC',
    'site:regionsanmartin.gob.pe "Ordenanza Regional" 001-2024',
]
```

### Step 2 — Download text content

For PDFs (most reliable):
```python
import fitz  # PyMuPDF
doc = fitz.open("norma.pdf")
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

For HTML (lapatria.pe):
Use `web_extract` tool — it typically returns the full legal text. The site has spam links at the bottom which can be ignored.

### Step 3 — Save as text file

Save each norm as a `.txt` file in `data/normas_faltantes/`:
```
data/normas_faltantes/
├── RS_040-2024-SUSALUD.txt
├── RS_042-2024-SUSALUD.txt
├── RS_009-2024-MC.txt
└── ORD_001-2024-GRSM-CR.txt
```

### Step 4 — Ingest into SQLite

```python
import sqlite3
from datetime import datetime

con = sqlite3.connect('data/normas_total.db')
cur = con.cursor()

norms = [
    {
        'tipo': 'RESOLUCIÓN DE SUPERINTENDENCIA',
        'num': '040-2024-SUSALUD/S',
        'fecha': '2024-02-19',
        'emisor': 'Superintendencia Nacional de Salud (SUSALUD)',
        'materia': 'Salud - IAFAS - Regulación Financiera',
        'sumilla': 'Aprueban el Reglamento de Solvencia Patrimonial...',
        'titulo': 'Aprueban el Reglamento de Solvencia Patrimonial...',
        'archivo': 'RS_040-2024-SUSALUD.txt',
    },
    # ... more norms
]

# Get max ID number for new IDs
cur.execute("SELECT COUNT(*) FROM normas WHERE id LIKE '2024-%'")
base_id = cur.fetchone()[0]

for i, n in enumerate(norms):
    norm_id = f"{n['fecha']}/norma_{base_id + i}"
    
    with open(f"data/normas_faltantes/{n['archivo']}") as f:
        texto = f.read()
    
    # Check if already exists
    cur.execute("SELECT id FROM normas WHERE tipo_norma = ? AND numero = ?",
                (n['tipo'], n['num']))
    if cur.fetchone():
        print(f"  Ya existe: {n['num']}")
        continue
    
    cur.execute("""
        INSERT INTO normas 
        (id, tipo_norma, numero, fecha_publicacion, emisor, materia, 
         estado, sumilla, titulo, texto_completo, ...)
        VALUES (?,?,?,?,?,?,?,?,?,?, ...)
    """, (norm_id, n['tipo'], n['num'], n['fecha'], n['emisor'],
          n['materia'], 'VIGENTE', n['sumilla'], n['titulo'],
          texto, ...))

con.commit()
```

### Step 5 — Update FTS index

The `normas_fts` table is NOT auto-synced with content='' mode. Insert manually:

```python
cur.execute("""
    INSERT INTO normas_fts (tipo_norma, numero, emisor, sumilla, materia, texto_completo)
    VALUES (?, ?, ?, ?, ?, ?)
""", (n['tipo'], n['num'], n['emisor'], n['sumilla'], n['materia'], texto))
```

### Step 6 — Update Qdrant (optional)

For immediate full-text coverage, the FTS update is sufficient. For semantic search, re-run vectorization on the new norms.

## Pitfalls

### FTS index requires manual insert
When `normas_fts` uses `content=''` (not content-sync), new records in `normas` are NOT automatically indexed. You MUST insert into `normas_fts` separately. Verify with:
```sql
SELECT COUNT(*) FROM normas_fts WHERE normas_fts MATCH '040-2024'
```

### ID format must be unique
IDs in `normas_total.db` follow the pattern `YYYY-MM-DD/XXXXXXX-X` or `YYYY-MM-DD/norma_NNNNN`. Count existing records for the target year to pick a unique sequential ID.

### Some norms already exist under different IDs
The `normas_total.db` already contains some of these documents ingested through the main pipeline. Always check `SELECT id FROM normas WHERE tipo_norma = ? AND numero = ?` before inserting.

### Busqueda precisa: tipo_norma + numero evita falsos positivos
Buscar por texto completo (`LIKE '%141-2024-EF%'`) da falsos positivos: numeros similares aparecen en contextos no relacionados. Ejemplo real: `"072-2025"` da 213 resultados por texto completo, pero solo 1 es el Acuerdo de Concejo de Megantoni buscado. Usar SIEMPRE filtro por `tipo_norma` primero:
```sql
SELECT id, titulo FROM normas 
WHERE tipo_norma = 'DECRETO SUPREMO' AND numero LIKE '%141%' 
  AND fecha_publicacion LIKE '%2024%';
```

### web_extract from lapatria.pe includes spam
The extracted HTML contains casino/ad links at the bottom. Strip the lead section with spam links if needed. The legal text starts after the RESOLUCIÓN/ORDENANZA heading.

### PyMuPDF vs pdfplumber
For structured regulatory text (articles, sections), PyMuPDF (`fitz`) is sufficient. For financial tables with cell boundaries, use `pdfplumber` for table extraction.
