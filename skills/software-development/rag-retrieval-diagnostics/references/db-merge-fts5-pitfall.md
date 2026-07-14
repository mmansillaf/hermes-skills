# PATRÓN: DB Merge + FTS5 Rebuild con TEXT Primary Keys

## Cuándo usar

Cuando se necesita unificar múltiples bases SQLite (por año, por fuente) en una sola, preservando el índice FTS5.

## El pitfall: FTS5 vacío después del merge

**Síntoma:** `sqlite=0` en todas las queries. FTS5 `SELECT COUNT(*)` retorna 0. Los datos existen en la tabla `normas` pero la búsqueda textual no funciona.

**Causa:** Las tablas usan `id TEXT PRIMARY KEY` (no `INTEGER`). FTS5 con `content='normas'` espera `rowid` para el mapeo. Al hacer `INSERT INTO ... SELECT ...`, los nuevos `rowid` son autoincrementales (1, 2, 3...). Pero el `INSERT INTO normas_fts(normas_fts) VALUES('rebuild')` falla silenciosamente porque los rowids no matchean las filas existentes.

**Fix:**

```sql
-- NO usar rebuild automático (falla con TEXT PKs):
-- INSERT INTO normas_fts(normas_fts) VALUES('rebuild')

-- USAR inserción explícita con rowid:
DROP TABLE IF EXISTS normas_fts;
CREATE VIRTUAL TABLE normas_fts USING fts5(
    tipo_norma, numero, emisor, sumilla, materia, texto_completo, 
    content=''
);
INSERT INTO normas_fts(rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo) 
SELECT rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo FROM normas;
```

**Verificación:** `SELECT COUNT(*) FROM normas_fts` debe igualar `SELECT COUNT(*) FROM normas`.

## Proceso de merge validado (97K normas, 5 años)

```python
# 1. Copiar schema de la primera DB
for row in src.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
    total.execute(row[0])

# 2. Insertar todas las filas preservando columnas
cols = [row[1] for row in src.execute("PRAGMA table_info(normas)")]
cols_str = ", ".join(cols)
placeholders = ", ".join(["?"] * len(cols))

for year_db in year_dbs:
    rows = src.execute(f"SELECT {cols_str} FROM normas").fetchall()
    total.executemany(f"INSERT INTO normas ({cols_str}) VALUES ({placeholders})", rows)

# 3. Reconstruir FTS5 explícitamente (NO usar 'rebuild')
total.execute("DROP TABLE IF EXISTS normas_fts")
total.execute("CREATE VIRTUAL TABLE normas_fts USING fts5(...)")
total.execute("INSERT INTO normas_fts(rowid, ...) SELECT rowid, ... FROM normas")
```

## Resultado

| Año | Normas | DB Size |
|-----|--------|---------|
| 2021 | 28,351 | — |
| 2022 | 17,397 | — |
| 2023 | 16,729 | — |
| 2024 | 18,694 | — |
| 2025 | 16,638 | — |
| **Total** | **97,809** | **194 MB** |

## Verificación post-merge

```bash
# FTS5 debe tener el mismo count que normas
sqlite3 data/normas_total.db "SELECT COUNT(*) FROM normas_fts"
# Debe retornar 97809

# API debe retornar sqlite count > 0
curl -X POST http://localhost:8000/query -d '{"question":"Ley 32108"}'
# "sources": {"sqlite": {"count": 9, ...}}
```
