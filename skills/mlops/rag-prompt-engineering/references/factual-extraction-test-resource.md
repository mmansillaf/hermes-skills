# Factual Extraction Test Resource: Criminal Case Corpus

## Source Files

The directory `Jurisprudencia/` contains a contiguous block of criminal case
files from the Corte Suprema (Sala Penal) in the range **1014875–1014898**,
plus a few scattered labor/tax files. Each file is a complete appellate
ruling with `HECHOS`, `PROBLEMA`, and `FALLO` sections.

| File | Case | Topic |
|------|------|-------|
| `1014875.html` | Edilberto Dionisio Moya | Corrupción de funcionarios |
| `1014876.html` | Raymunda Alverca Guerrero / Wilder Aguirre Caldas | Tráfico ilícito de drogas |
| `1014877.html` | Ignacio Chalco Choque / Sabino ... | Nulidad parcial |
| `1014878.html` | Modesto Edilberto Rivera Otero | Robo agravado |
| `1014879.html` | Luis Américo Ayala Gonzáles | Coautoría → complicidad secundaria |
| `1014880.html` | Rusbelt Tránsito Meza | Secuestro |
| `1014881.html` | José Clider Muñoz Fernández et al. | Ronda campesina, coacción, error de prohibición |
| `1014883.html` | Adelmar Arquimides Contreras Marcelo | Defraudación tributaria |
| `1014885.html` | Esteban Flores Alvarado | Tráfico ilícito de drogas |
| `1014886.html` | (hallazgo en ómnibus Guadalupe) | Tráfico ilícito de drogas |
| `1014887.html` | Liberato Eugenio Gomero | Tráfico ilícito de drogas |
| `1014888.html` | Julia Paredes Campaña / Alvaro Vera Avalos | Robo agravado |
| `1014889.html` | Chirst Chunga Carranza | Robo agravado |
| `1014890.html` | Hilario Quispe Rojas et al. | Corrupción de funcionarios (exalcaldes) |
| `1014891.html` | (apreciación de hechos) | Procesal penal |
| `1014892.html` | (violación a menor) | Violación de la libertad sexual |
| `1014893.html` | José Antonio Ocampo Cueva | Omisión |
| `1014894.html` | Justiniano Luján Carrasco | Traslado de alimentos |
| `1014895.html` | Raúl Ramiro Lizárraga Aguilar | Absolución recurrida |
| `1014896.html` | Claudio Hugo Santiago Sacsa | Servicio solicitado |
| `1014897.html` | Iqnacia Herlinda Cañares Leyva | Depositaria judicial |
| `1014898.html` | Milton Noe Ríos Paucar | Violación de la libertad sexual |

## Why This Matters for Testing

Most RAG evaluation focuses on **conceptual/semantic** queries (e.g., "what
is the principle of proportionality?"). These criminal case files allow
testing **factual extraction** — queries that require the system to retrieve
and reproduce specific facts accurately:

```python
# Factual extraction queries (hard mode for chunk-based RAG)
"¿Cuántos años de pena se impusieron a Wilder Aguirre Caldas?"
"¿Qué artículo del Código Penal se citó en el caso Muñoz Fernández?"
"¿Cómo se llamaba la testigo en el caso Zavaleta Rodríguez?"
```

## Success Rates

| Query type | Expected hit rate | Why |
|------------|------------------|-----|
| **Case name lookup** | MODERATE | HECHOS section usually contains names, easy for FAISS |
| **Numeric facts** (pena years, montos) | LOW | Numbers are embedded in prose chunks; FAISS may not surface the exact chunk |
| **Article references** | MODERATE | Legal article citations (`Art. 15° CP`) are distinctive tokens for BM25 |
| **Witness / party names** | MODERATE | Names in HECHOS, but small variations break exact matching |

## How to Run

```bash
cd /mnt/d/PyCode/ResumenTokensJurisprudencias
export CUDA_VISIBLE_DEVICES=""

# Single query
python3 -c "
import asyncio
from graphrag_pro import run_console_query
asyncio.run(run_console_query('Cuantos anos de pena se impusieron a Wilder Aguirre Caldas'))
"

# Batch of queries (create a script list and run sequentially)
python3 scripts/run_bateria_adaptada.py
```

## Chunking Limitation Notice

The FAISS index chunks each document at 512 words with 50-word overlap.
For factual extraction queries, a fact may span a chunk boundary or be
in a chunk whose embedding doesn't match the query well enough. This is
inherent to the architecture — factual extraction is harder than semantic
retrieval in a chunk-based system.
