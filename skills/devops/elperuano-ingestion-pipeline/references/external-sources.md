# Fuentes externas para normas faltantes

Cuando un test de batería revela que normas específicas NO están en la base de datos, estas fuentes pueden proporcionar los textos completos para ingestión:

## Fuentes por tipo de norma

| Norma | Fuente principal | Fuente alterna | Formato |
|-------|-----------------|----------------|---------|
| Resoluciones SUSALUD | `iuslatin.pe` (PDF) | `lapatria.pe/elperuano/` (HTML) | PDF + HTML |
| Resoluciones Supremas | `gob.pe` (PDF oficial) | `lapatria.pe/elperuano/` (HTML) | PDF |
| Ordenanzas Regionales | `lapatria.pe/elperuano/` (HTML) | Portal web del GORE (PDF) | HTML |
| Decretos Supremos | `busquedas.elperuano.pe` | `lapatria.pe/elperuano/` | HTML |
| Acuerdos de Concejo | `busquedas.elperuano.pe` | — | HTML |

## Urls específicas (caso SUSALUD + BNP + San Martín)

```
RS 040-2024-SUSALUD/S:
  PDF: https://iuslatin.pe/wp-content/uploads/2024/02/Resolucion-N°-040-2024-SUSALUD_S.pdf
  HTML: https://lapatria.pe/elperuano/481-14/resolucion-n-040-2024-susalud-s

RS 042-2024-SUSALUD/S:
  HTML: https://lapatria.pe/elperuano/481-15/resolucion-n-042-2024-susalud-s

RS 009-2024-MC (BNP):
  PDF: https://cdn.www.gob.pe/uploads/document/file/6813250/5898540-rs-009-2024-mc.pdf

ORD 001-2024-GRSM/CR (San Martín):
  HTML: https://lapatria.pe/elperuano/481-19/ordenanza-n-001-2024-grsm-cr
```

## Pipeline de ingesta para normas individuales

```python
# 1. Descargar
import requests
pdf_url = "https://iuslatin.pe/.../RS_040-2024-SUSALUD_S.pdf"
resp = requests.get(pdf_url, timeout=30)
with open("norma.pdf", "wb") as f:
    f.write(resp.content)

# 2. Extraer texto
import fitz  # PyMuPDF
doc = fitz.open("norma.pdf")
texto = ""
for page in doc:
    texto += page.get_text()
doc.close()

# 3. Insertar en SQLite
import sqlite3
con = sqlite3.connect("data/normas_total.db")
con.execute("""
    INSERT INTO normas (id, tipo_norma, numero, fecha_publicacion, emisor, 
                        sumilla, titulo, texto_completo, source_format, ...)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ...)
""", (norm_id, tipo, numero, fecha, emisor, sumilla, titulo, texto, "pdf", ...))
con.commit()

# 4. Actualizar FTS (Full-Text Search)
con.execute("""
    INSERT INTO normas_fts (tipo_norma, numero, emisor, sumilla, materia, texto_completo)
    VALUES (?, ?, ?, ?, ?, ?)
""", (tipo, numero, emisor, sumilla, materia, texto))
con.commit()

# 5. Verificar
con.execute("SELECT COUNT(*) FROM normas WHERE numero LIKE '%040-2024%'")
print(f"Insertada: {con.fetchone()[0]} registros")
```

## Pitfalls

1. **lapatria.pe tiene anuncios/spam**: Los extractores HTML deben filtrar líneas con `[олимп казино]`, `[покер дом]`, `[1 win]`.
2. **PDFs de iuslatin.pe pueden expirar**: URLs de sitios de terceros no son permanentes. Descargar y guardar localmente.
3. **Formato de ID**: El ID en normas_total.db es `YYYY-MM-DD/norma_N` o `YYYY-MM-DD/XXXXXXX-X`. Para normas nuevas, usar `YYYY-MM-DD/norma_{N+1}`.
4. **FTS requiere insert manual**: El índice FTS5 no se actualiza automáticamente. Hay que insertar en `normas_fts` después de insertar en `normas`.
5. **Qdrant no se actualiza automáticamente**: Si se necesita la norma en búsqueda semántica, re-vectorizar. Para pocas normas (≤10), el impacto es mínimo.
