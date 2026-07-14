# FTS5 con TEXT IDs — Pitfall y Solución

## El problema

Cuando la tabla `normas` usa `id TEXT` (ej: `"2024-06-20/2299514-4"`) en vez de `INTEGER PRIMARY KEY`, el FTS5 con `content='normas', content_rowid='id'` **no funciona**. El índice se crea pero queda vacío (0 entradas) aunque la tabla tenga datos.

Esto ocurre porque `content_rowid` espera una columna INTEGER que haga referencia al `rowid` interno de SQLite. Si la columna es TEXT, la referencia se rompe silenciosamente.

## La solución

Usar `content=''` (tabla externa sin sincronización automática) e insertar manualmente con el `rowid`:

```sql
-- Crear FTS5 como tabla independiente (content='')
CREATE VIRTUAL TABLE normas_fts USING fts5(
    tipo_norma, numero, emisor, sumilla, materia, texto_completo,
    content=''
);

-- Insertar datos manualmente con rowid
INSERT INTO normas_fts(rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo)
SELECT rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo FROM normas;
```

## Query (api_rest.py)

La query de búsqueda usa `rowid` para el JOIN, lo cual funciona con ambos esquemas:

```sql
SELECT n.id, n.tipo_norma, n.numero, n.fecha_publicacion,
       n.emisor, n.sumilla, n.texto_completo, fts.rank
FROM normas_fts fts
JOIN normas n ON n.rowid = fts.rowid
WHERE normas_fts MATCH ?
ORDER BY fts.rank
LIMIT 15
```

## Verificar que FTS5 tiene datos

```bash
sqlite3 data/normas_total.db "SELECT COUNT(*) FROM normas_fts"
# Debe devolver el mismo número que:
sqlite3 data/normas_total.db "SELECT COUNT(*) FROM normas"
```

## Cuándo aplicar este fix

- Después de cualquier `INSERT` masivo en la tabla `normas`
- Después de merge de DBs (el DROP+CREATE+INSERT es necesario)
- Cuando `sqlite_count=0` en todas las queries (señal de FTS5 vacío)

## NO usar

```sql
-- ❌ Esto NO funciona con TEXT ids:
CREATE VIRTUAL TABLE normas_fts USING fts5(
    tipo_norma, numero, ...,
    content='normas', content_rowid='id'  -- 'id' es TEXT → FTS5 vacío
);

-- ❌ Esto tampoco:
INSERT INTO normas_fts(normas_fts) VALUES('rebuild');  -- no hace nada con content=''
```
