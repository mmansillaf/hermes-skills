# Groq Batch API — Extracción de Metadatos y Enriquecimiento RAG

## Problema: Sumillas Incorrectas por Schema Inadecuado

### Síntoma
19,892 normas legales peruanas indexadas con sumillas que no corresponden al contenido real. Ej: DS 102-2024-PCM (Estado de Emergencia Islay) tenía sumilla "Nombran Ministra de Comercio Exterior".

### Causa raíz
El pipeline antiguo (`fase2_generar_jsonl_batch.py`) usaba un schema diseñado para sanciones municipales:
```json
{
  "Nro_Resolucion": "...",
  "Cronograma_Procesal": {...},
  "Datos_Votacion": {"Miembros_Concejo": ..., "Votos_A_Favor": ...},
  "Materia": "Vacancia, Nepotismo..."
}
```
Este schema asume que toda norma es una sanción de concejo municipal. Al aplicarlo a normas del Peruano (resoluciones ministeriales, decretos supremos, designaciones), Groq no encontraba los campos esperados y alucinaba valores.

### Solución: Pipeline Moderno con Schema Universal

El script `02_groq_batch_pipeline.py` usa un schema universal:
```json
{
  "tipo_norma": "DS",
  "numero": "102-2024-PCM",
  "fecha": "2024-09-30",
  "emisor": "Presidencia del Consejo de Ministros",
  "sumilla": "Prorroga Estado de Emergencia...",
  "materia": "Estado de Emergencia",
  "funcionarios": ["Dina Boluarte Zegarra"],
  "entidades": ["INDECI", "Gobierno Regional Arequipa"],
  "base_legal": ["Constitución Art. 137"],
  "montos": [],
  "normas_citadas": ["DS 001-2024-PCM"]
}
```

### Flujo Completo

```bash
# 1. Backup
cp data/normas_2024.db data/normas_2024.db.pre_reingest

# 2. Generar JSONL desde Markdown (schema universal)
python scripts/data_prep/02_groq_batch_pipeline.py generate

# 3. Subir a Groq Batch API (procesamiento asíncrono)
python scripts/data_prep/02_groq_batch_pipeline.py upload

# 4. Monitorear (1-4 horas)
python scripts/data_prep/02_groq_batch_pipeline.py status

# 5. Descargar resultados
python scripts/data_prep/02_groq_batch_pipeline.py download

# 6. Reconstruir SQLite
python scripts/data_prep/03_build_sqlite.py --reset

# 7. Re-vectorizar Qdrant
python scripts/data_prep/04_vectorize_qdrant.py
```

### Costos Reales (Groq Batch API, 50% descuento)

| Modelo | Input $/1M | Output $/1M | Costo 19,892 normas |
|--------|-----------|-------------|-------------------|
| llama-3.1-8b-instant | $0.05 | $0.08 | **$0.83** |
| llama-3.3-70b-versatile | $0.59 | $0.79 | $9.58 |

**8B es suficiente para extracción de metadatos.** La tarea es estructurada (extraer tipo, número, fecha, nombres de un texto), no requiere razonamiento complejo.

### Qdrant — Point ID debe ser uint o UUID

Error: `value 2024-06-20/2299514-4 is not a valid point ID`

Fix: convertir string ID a hash numérico:
```python
import hashlib
point_id = int(hashlib.md5(row["id"].encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
```

---

## Enriquecimiento del Contexto LLM (Opción 1 + 1.5 + 2 + B + C)

### Opción 1: Campos Estructurados desde norma_entities

La tabla `norma_entities` contiene datos extraídos por Groq que el RAG no consultaba:
- `funcionario`: DINA ERCILIA BOLUARTE ZEGARRA, JUAN JOSÉ SANTIVÁÑEZ
- `entidad`: INDECI, Ministerio del Interior, PNP

**Fix en `generate_answer()`:**
```python
# Enriquecer resultados con entidades
db = get_sqlite()
for r in results:
    nid = r.get("id", "")
    if nid:
        rows = db.execute(
            "SELECT entity_type, entity_value FROM norma_entities WHERE norma_id = ?",
            (nid,)
        ).fetchall()
        r["_funcionarios"] = [row[1] for row in rows if row[0] == "funcionario"][:5]
        r["_entidades"] = [row[1] for row in rows if row[0] == "entidad"][:5]

# Incluir en el prompt del LLM
for r in results:
    if r.get('_funcionarios'):
        parts.append(f"    Funcionarios: {', '.join(r['_funcionarios'])}")
    if r.get('_entidades'):
        parts.append(f"    Entidades: {', '.join(r['_entidades'])}")
```

### Opción 1.5: Inferencia de Rol desde Sumilla

Los funcionarios en `norma_entities` no tienen rol asociado. Una lista plana de nombres no le dice al LLM quién es el ministro, quién el designado, quién el viajero. La inferencia por palabras clave en la sumilla resuelve esto:

```python
sumilla = (r.get("sumilla") or "").lower()
roles = []
for f in funcionarios_raw[:6]:
    role = None
    if any(w in sumilla for w in ['designa','nombra','aceptan renuncia']):
        role = "designado" if f != funcionarios_raw[0] else None
    if any(w in sumilla for w in ['autorizan viaje','comisión de servicio']):
        role = "viajero/comisionado" if f != funcionarios_raw[0] else None
    if any(w in sumilla for w in ['disolución','liquidación','administrador']):
        role = "administrador/liquidador" if f != funcionarios_raw[0] else None
    if any(w in sumilla for w in ['prorroga','prórroga','estado de emergencia']):
        role = "firmante del decreto" if f == funcionarios_raw[0] else None
    if any(w in sumilla for w in ['aprueban','aprueba','modifican']):
        role = "firmante/aprobador" if f == funcionarios_raw[0] else None
    # El primer funcionario suele ser firmante por defecto
    if role is None and f == funcionarios_raw[0] and len(funcionarios_raw) > 1:
        role = "firmante"
    roles.append((f, role))
```

**Regla clave:** El primer funcionario de la lista suele ser el firmante/aprobador, no el sujeto de la norma. Los funcionarios subsiguientes son los sujetos (designados, viajeros, administradores).

**Impacto:** Resuelve preguntas como "¿quién es el ministro?", "¿quiénes son los administradores?", "¿quién firma?". Pasó de 0 a 5+ respuestas correctas en batería de 40 preguntas.

### Opción 2: Texto Completo en FTS5 (8000 chars)

Cargar el texto completo de los archivos `.md` en SQLite y reconstruir FTS5:

```sql
ALTER TABLE normas ADD COLUMN texto_completo TEXT;
UPDATE normas SET texto_completo = ? WHERE id = ?;
DROP TABLE IF EXISTS normas_fts;
CREATE VIRTUAL TABLE normas_fts USING fts5(
    tipo_norma, numero, emisor, sumilla, materia, texto_completo,
    content='normas', content_rowid='rowid'
);
INSERT INTO normas_fts(rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo)
SELECT rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo FROM normas;
```

Incluir en el prompt del LLM (truncar a 2000 chars):
```python
if r.get('texto_completo'):
    parts.append(f"    Texto: {r['texto_completo'][:2000]}")
```

### Resultados Combinados (O1+O1.5+O2+B+C)

| Nivel | Sin enriquecimiento | Con todos los fixes |
|-------|-------------------|---------------------|
| Básico (Q1-15) | 3/15 (20%) | ~12/15 (80%) |
| Intermedio (Q16-30) | 5/15 (33%) | ~13/15 (87%) |
| Avanzado (Q31-40) | 8/10 (80%) | ~10/10 (100%) |
| **Total** | **16/40 (40%)** | **~35/40 (87%)** |

### Validator — Falso Positivo de Montos

El `ResponseValidator` extrae montos numéricos de la respuesta y verifica que existan en las fuentes. Pero confundía números de ley ("Ley 32108") con montos ($32,108). Fix:

```python
# Excluir si el número aparece como número de ley/resolución
norm_pattern = r'(?:Ley|DL|DS|RM|RS|RD|RE|N[°º])\s*' + re.escape(match)
if re.search(norm_pattern, texto, re.IGNORECASE):
    continue  # No es un monto, es un número de norma
```

---

## Lecciones Aprendidas

1. **El schema de extracción define la calidad.** Un schema incorrecto causa corrupción en cascada.
2. **Groq Batch API: $0.83 para 19,892 documentos** con llama-3.1-8b-instant.
3. **8B es suficiente para extracción estructurada.** No se necesita 70B.
4. **Los datos estructurados extraídos deben exponerse al LLM con ROL.** Una lista plana de nombres no sirve.
5. **Texto completo a 8000 chars en FTS5** permite responder preguntas de detalle que las sumillas de 100 chars no cubren.
6. **Prioridad local sobre web.** Poner resultados web al final (no al frente) permite que el enriquecimiento de entidades funcione.
7. **Los falsos positivos del validador degradan el scoring.** Excluir números de ley del detector de montos.
8. **Categorizar fallos por tipo de dato faltante** (PERSONA, MONTO, FECHA, CANTIDAD) permite identificar qué fix aplicar.
