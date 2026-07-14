# Pipeline Schema Enhancement — source_path y metadata

**Sistema:** El Peruano RAG v3.0 | **Fecha:** 2026-05-01

## Campos agregados al esquema SQLite

```sql
ALTER TABLE normas ADD COLUMN source_path TEXT;
ALTER TABLE normas ADD COLUMN source_year INTEGER;
ALTER TABLE normas ADD COLUMN normas_citadas TEXT;  -- JSON array
ALTER TABLE normas ADD COLUMN base_legal TEXT;      -- JSON array
```

## Por que

Los campos `source_path` y `source_year` permiten:
- Generar links directos al archivo fuente en Cloudflare R2
- Filtrar consultas por ano sin parsear el id
- Mostrar la ubicacion del documento original en la respuesta

Los campos `normas_citadas` y `base_legal` permiten:
- Enriquecer las respuestas con referencias cruzadas
- Navegacion entre normas relacionadas

## Como se pueblan

Desde el `custom_id` del batch de Groq (formato: `YYYY-MM-DD/elemento`):
```python
source_path = f"{custom_id[:4]}/{custom_id[:4]}{custom_id[5:7]}{custom_id[8:10]}/{custom_id[12:]}.html"
source_year = int(custom_id[:4])
```

## Integracion con el pipeline de ingesta

1. El batch prompt incluye `source_path` y `page_number` como campos a extraer
2. `03_build_sqlite.py` guarda los nuevos campos en el INSERT
3. `api_rest.py` incluye `source_path` y `source_year` en los resultados FTS5
4. Los 18,694 registros existentes se actualizaron retroactivamente con un UPDATE masivo
