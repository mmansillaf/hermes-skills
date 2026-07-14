#!/usr/bin/env python3
"""Merge 5 yearly SQLite DBs into one normas_total.db"""
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent.parent if '__file__' in dir() else Path.cwd()
TOTAL_DB = BASE / "data" / "normas_total.db"
YEAR_DBS = {
    "2021": BASE / "data" / "normas_2021.db",
    "2022": BASE / "data" / "normas_2022.db",
    "2023": BASE / "data" / "normas_2023.db",
    "2024": BASE / "data" / "normas_2024.db",
    "2025": BASE / "data" / "normas_2025.db",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS normas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    custom_id TEXT UNIQUE,
    tipo_norma TEXT, numero TEXT, fecha_publicacion TEXT, emisor TEXT,
    sumilla TEXT, materia TEXT, texto_completo TEXT,
    source_path TEXT, source_year INTEGER,
    normas_citadas TEXT, base_legal TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS norma_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_id INTEGER, entity_type TEXT, entity_value TEXT,
    FOREIGN KEY (norma_id) REFERENCES normas(id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS normas_fts USING fts5(
    tipo_norma, numero, emisor, sumilla, materia, texto_completo,
    content='normas', content_rowid='id'
);
"""

# Create fresh DB
if TOTAL_DB.exists(): TOTAL_DB.unlink()
total = sqlite3.connect(str(TOTAL_DB))
total.executescript(SCHEMA)

total_normas = 0
id_offset = 0

for year, db_path in YEAR_DBS.items():
    if not db_path.exists(): continue
    src = sqlite3.connect(str(db_path))
    src.row_factory = sqlite3.Row
    count = src.execute("SELECT COUNT(*) FROM normas").fetchone()[0]
    print(f"  {year}: {count} normas")
    
    # Copy normas
    for row in src.execute("""SELECT custom_id, tipo_norma, numero, fecha_publicacion,
        emisor, sumilla, materia, texto_completo, source_path, source_year,
        normas_citadas, base_legal FROM normas"""):
        total.execute("""INSERT INTO normas (custom_id, tipo_norma, numero,
            fecha_publicacion, emisor, sumilla, materia, texto_completo,
            source_path, source_year, normas_citadas, base_legal)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", tuple(row))
    
    # Copy entities (map old_id→new_id via position)
    ents = list(src.execute("SELECT norma_id, entity_type, entity_value FROM norma_entities"))
    if ents:
        # Get new IDs for this year's normas (just inserted)
        new_ids = total.execute(
            f"SELECT id FROM normas WHERE id > {id_offset} ORDER BY id"
        ).fetchall()
        old_to_new = {i+1: row[0] for i, row in enumerate(new_ids)}
        for old_nid, etype, evalue in ents:
            new_nid = old_to_new.get(old_nid)
            if new_nid:
                total.execute("INSERT INTO norma_entities (norma_id, entity_type, entity_value) VALUES (?,?,?)",
                            (new_nid, etype, evalue))
    
    id_offset += count
    total_normas += count
    src.close()

# Rebuild FTS5
total.execute("INSERT INTO normas_fts(normas_fts) VALUES('rebuild')")
total.commit()
total.close()
print(f"  DONE: {total_normas} normas merged")
