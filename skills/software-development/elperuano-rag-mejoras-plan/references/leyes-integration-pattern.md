# Patrón de Integración: Base de Datos Secundaria con FTS5

## Caso de uso
Agregar una base de conocimiento complementaria (leyes, jurisprudencia, doctrina) que se busca ANTES de la base principal de normas diarias.

## Estructura

```sql
-- BD secundaria: data/leyes.db
CREATE TABLE leyes (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,        -- "Ley N° 27972"
    tipo TEXT NOT NULL,          -- "Ley", "Constitución", "Código"
    numero TEXT,                 -- "27972"
    articulo_num TEXT NOT NULL,  -- "39"
    articulo_texto TEXT NOT NULL -- Texto completo del artículo
);

CREATE VIRTUAL TABLE leyes_fts USING fts5(
    nombre, articulo_num, articulo_texto,
    content='leyes', content_rowid='rowid'
);
```

## Detección en la query

Usar patrones regex para detectar menciones a la base secundaria:

```python
_ley_patterns = [
    r'(?:C[oó]digo\s*(?:Civil|Penal|Tributario|Procesal))',
    r'(?:Constituci[oó]n\s*(?:Pol[ií]tica)?)',
    r'(?:Ley\s*(?:N[°º]\s*)?(\d{4,6}))',
]

_ley_match = None
for _lp in _ley_patterns:
    _m = re.search(_lp, question, re.IGNORECASE)  # ← pattern PRIMERO, string después
    if _m:
        _ley_match = _m.group(0)
        break
```

## Integración en search_sqlite()

```python
if _ley_match:
    _leyes_db = sqlite3.connect(str(DB_PATH).replace('normas_2024.db', 'leyes.db'))
    # Buscar con FTS5
    _ley_rows = _leyes_db.execute(
        "SELECT ... FROM leyes_fts f JOIN leyes l ON f.rowid = l.rowid WHERE MATCH ?",
        (_ley_match_fts,)
    ).fetchall()
    # Formatear resultados como dicts compatibles con el pipeline
    for _lr in _ley_rows:
        _leyes_results.append({
            "id": f"ley_{...}", "tipo": "Ley", "source": "leyes",
            "texto_completo": _lr[2], "relevance": 1.0, "_key_boosted": True
        })
```

## Inserción en resultados finales

```python
# Antes del return en search_sqlite():
if _leyes_results:
    for _lr in _leyes_results:
        _lr["blend_score"] = 1.0  # Máximo para que aparezcan primeros
    unique_results = _leyes_results + unique_results
```

## Pitfalls

- ⚠️ `re.search(question, pattern)` NO funciona. El orden correcto es `re.search(pattern, string)`.
- ⚠️ FTS5 con `content=` requiere `INSERT INTO leyes_fts(leyes_fts) VALUES('rebuild')` después de inserts.
- ⚠️ Siempre loguear resultados: `logger.info(f"[LEYES] Found {len(results)} for '{match}'")`.
