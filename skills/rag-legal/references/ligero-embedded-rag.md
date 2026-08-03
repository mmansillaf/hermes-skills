# RAG Ligero Embedded — Arquitectura para Abogados

**Contexto:** Sistema para que abogados procesen 2k-3k documentos locales (contratos, resoluciones, informes) con capacidad de agregar/eliminar documentos, resumir, y detectar errores/contradicciones. Difiere de GRegElPeruano en que es **single-user, embedded, sin servidores externos, con CRUD**.

---

## Diferencia Fundamental con GRegElPeruano

| Dimensión | GRegElPeruano (producción) | KRagLocal (ligero) |
|-----------|---------------------------|-------------------|
| Documentos | 21,584 normas públicas | 2k-3k documentos privados |
| CRUD | No (corpus fijo) | **Sí** (agregar/eliminar) |
| Despliegue | VM servidor (Docker) | Laptop del abogado |
| LLM | Groq API (cloud) | Local (o hybrid opt-in) |
| BBDD externas | Qdrant server + Neo4j | Ninguna — todo embedded |
| Usuario | Técnico | Abogado no-técnico |

Son proyectos complementarios pero arquitectónicamente distintos.

---

## Stack Recomendado: ChromaDB + e5-small + SQLite FTS5 + Ollama + Streamlit

### Vector Store → ChromaDB

**Por qué:** Embedded, no servidor. `pip install chromadb`. Persiste a disco automáticamente. CRUD nativo:

```python
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("documentos")

# Crear
collection.add(ids=["doc1"], embeddings=[vec], metadatas=[{"filename":"contrato.pdf"}])

# Leer
results = collection.query(query_embeddings=[query_vec], n_results=5)

# Eliminar
collection.delete(ids=["doc1"])

# Actualizar metadata
collection.update(ids=["doc1"], metadatas=[{"filename":"contrato_v2.pdf"}])
```

**Alternativa:** SQLite + `sqlite-vec` (aún más lightweight, menos maduro).

### Embedding Model → `multilingual-e5-small`

| Modelo | Dims | Tamaño | Español | Veredicto |
|--------|------|--------|---------|-----------|
| `intfloat/multilingual-e5-small` | 384 | ~120MB | Bueno | **Recomendado** (usar `intfloat/` namespace, no requiere auth) |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~470MB | Bueno | Alternativa probada |
| `bge-m3` | 1024 | ~1.2GB | Excelente | Overkill para 3k docs |
| `all-MiniLM-L6-v2` | 384 | ~80MB | Pobre | No para español legal |

Costo: ~30ms/chunk en CPU moderna. 3k docs × 20 chunks = 60k chunks ≈ 30 min ingesta.

Uso con e5 (formato query/passage):
```python
from sentence_transformers import SentenceTransformer

# USAR intfloat/ namespace. El namespace sentence-transformers/ requiere
# autenticacion HF (401 error si no hay HF_TOKEN configurado).
model = SentenceTransformer("intfloat/multilingual-e5-small")

# Formato obligatorio para e5
query_vec = model.encode(f"query: {question}")
passage_vecs = model.encode([f"passage: {chunk}" for chunk in chunks])
```

### Keyword Search → SQLite FTS5

Complementa al vector search. El abogado busca "indemnización" y debe encontrar exactamente esa palabra.

```python
import sqlite3
conn = sqlite3.connect("metadata.db")
conn.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(titulo, contenido, tokenize='unicode61 remove_diacritics 2')")
results = conn.execute(
    "SELECT * FROM docs_fts WHERE contenido MATCH ? ORDER BY rank",
    ("indemnización",)
).fetchall()
```

**Hybrid Search Blend:**
```
score = vector_relevance × 0.7 + fts5_relevance × 0.3
```

### Chunking → Por Cláusula/Considerando (No Fixed-Size)

| Tipo de doc | Estrategia |
|-------------|-----------|
| Contrato | Por cláusula ("Cláusula Primera:", "Segunda:") |
| Resolución | Por considerando ("CONSIDERANDO:") |
| Informe | Por sección ("I.", "II.", o títulos) |
| Genérico | 512 tokens, overlap 2-3 oraciones |

```python
import re

def chunk_contract(text: str) -> list[dict]:
    """Divide contrato por cláusulas."""
    clauses = re.split(r'(Cláusula\s+\w+)', text, flags=re.IGNORECASE)
    chunks = []
    for i in range(1, len(clauses), 2):
        chunks.append({
            "title": clauses[i].strip(),
            "text": (clauses[i] + clauses[i+1]).strip()
        })
    return chunks

def chunk_resolution(text: str) -> list[dict]:
    """Divide resolución por considerandos."""
    parts = re.split(r'(CONSIDERANDO:\s*)', text)
    chunks = []
    for i in range(1, len(parts), 2):
        chunks.append({
            "title": "CONSIDERANDO",
            "text": (parts[i] + parts[i+1]).strip()
        })
    return chunks
```

### LLM — Modo Dual (Local/Cloud)

| Modo | LLM | RAM | Precisión | Seguridad |
|------|-----|-----|-----------|-----------|
| Local (default) | Llama 3.2 3B Q4 (Ollama) | ~2GB | Suficiente para resúmenes | Datos nunca salen |
| Cloud (opt-in) | Groq/OpenAI/Claude | 0 | Alta para contradicciones | Requiere consentimiento |

**Regla:** Local por defecto (air-gapped). Cloud solo cuando el abogado **elige** activarlo, con pop-up de confirmación y log de auditoría.

```python
# Ollama local
import requests
resp = requests.post("http://localhost:11434/api/generate", json={
    "model": "llama3.2:3b",
    "prompt": f"Contexto: {context}\n\nPregunta: {question}",
    "stream": False
})
answer = resp.json()["response"]
```

---

## Estimación de Recursos (Laptop 2020+)

| Componente | RAM | Disco | CPU |
|-----------|-----|-------|-----|
| ChromaDB + vectores | ~100MB | ~300MB | Mínimo |
| Embedding model | ~250MB | ~120MB | Moderado |
| LLM 3B Q4 (Ollama) | ~2GB | ~2GB | Alto |
| Documentos (3k) en bruto | — | ~500MB | — |
| **TOTAL con 3B LLM** | **~3GB** | **~3GB** | **Moderado** |
| **TOTAL sin LLM** | **~500MB** | **~1GB** | **Muy bajo** |

Corre en cualquier laptop con 8GB RAM y SSD.

---

## Seguridad

1. **Default air-gapped.** Sin telemetría, sin analytics, sin llamadas externas.
2. **Modo cloud: opt-in explícito.** Cada sesión, pop-up de confirmación.
3. **Log de auditoría.** Qué documentos se enviaron, a qué proveedor, cuándo.
4. **Hash SHA256.** Cada documento se hashea al ingestar. Detecta duplicados y verifica integridad.
5. **Cero puertos expuestos.** Solo `localhost:puerto`.
6. **(Opcional) Cifrado en reposo.** sqlcipher para metadatos, o cifrado a nivel de filesystem.

---

## Comparativa de Stacks

| Stack | Pro | Contra | Peso RAM |
|-------|-----|--------|----------|
| **A: ChromaDB + e5-small + Ollama 3B + Streamlit** | Balance óptimo | LLM local limitado | ~3GB |
| **B: SQLite-vec + MiniLM-L6 + solo retrieval** | Liviano extremo (<500MB) | Sin generación | ~500MB |
| **C: Qdrant embedded + bge-m3 + Ollama 7B** | Máxima precisión | Pesado para laptop | ~6GB |
| **D: Qdrant + e5-small + Groq API** | Ya conoces las piezas | Dependencia cloud | ~1GB |

---

## Pipeline de Query (5 Etapas)

1. **RECIBIR** pregunta del abogado
2. **EXPANDIR** con sinónimos legales (reutilizar lógica de GRegElPeruano)
3. **HYBRID SEARCH**: vector (ChromaDB) + keyword (FTS5)
4. **RERANK** (opcional): cross-encoder ligero (`cross-encoder/ms-marco-MiniLM-L6-v2`, ~150MB, mejora precisión 10-15%)
5. **GENERAR**: LLM con chunks como contexto

Para **detección de contradicciones**:
- Query especial: busca 2+ chunks que traten el MISMO tema con lenguaje incongruente
- Prompt estructurado: "Compara las siguientes cláusulas. Identifica contradicciones textuales entre ellas."
- Output estructurado: documento A cláusula X vs documento B cláusula Y

---

## Riesgos Conocidos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Retrieval recupera chunks incorrectos | Hybrid search + cross-encoder reranker |
| LLM local alucina cláusulas | Prompt restrictivo + post-cleaner regex |
| Ingesta de 3k docs toma horas | Progreso en background + lotes + caché por hash SHA256 |
| Abogado no sabe instalar/ejecutar | Script único install.sh + launcher + modo appliance |
| Documentos confidenciales enviados a cloud | Default local + pop-up + log de auditoría |

---

## Cuándo Usar Este Patrón vs GRegElPeruano

**Usar este patrón (ChromaDB embedded) cuando:**
- El usuario es un abogado individual o una firma pequeña
- Los documentos son privados y confidenciales
- Se necesita CRUD (agregar/eliminar documentos frecuentemente)
- No hay presupuesto para servidores o APIs cloud
- El corpus es de 1k-10k documentos

**Usar GRegElPeruano (Qdrant + Neo4j + Groq) cuando:**
- El corpus es de 10k+ documentos
- Se necesita búsqueda por grafos de entidades
- Hay un servidor dedicado
- El presupuesto cubre APIs cloud
- El corpus es público o semi-público
