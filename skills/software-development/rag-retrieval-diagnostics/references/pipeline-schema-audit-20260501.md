# Auditoría de Schema: Pipeline de Extracción → SQLite

**Fecha:** 2026-05-01 | **Impacto:** 4 nuevas columnas + 2 campos en batch prompt

## Campos que el Batch API EXTRAE vs SQLite GUARDA

| Campo Batch | ¿En SQLite? | ¿Dónde? |
|------------|-------------|---------|
| tipo_norma | ✅ | tipo_norma |
| numero | ✅ | numero |
| fecha | ✅ | fecha_publicacion |
| emisor | ✅ | emisor |
| sumilla | ✅ | sumilla |
| materia | ✅ | materia |
| funcionarios | ⚠️ | norma_entities (tabla aparte) |
| entidades | ⚠️ | norma_entities (tabla aparte) |
| **base_legal** | ❌ **NO SE GUARDABA** | — |
| **normas_citadas** | ❌ **NO SE GUARDABA** | — |
| montos | ⚠️ | norma_entities |
| **source_path** | ❌ **NO EXISTÍA** | — |
| **source_year** | ❌ **NO EXISTÍA** | — |

## Fix aplicado (01-may-2026)

### 1. Batch prompt — 2 campos nuevos:
```json
{
  ...campos existentes...,
  "source_path": "ruta relativa del archivo fuente",
  "page_number": "número de página si aparece en el encabezado, null si no"
}
```

### 2. SQLite — 4 columnas nuevas:
```sql
ALTER TABLE normas ADD COLUMN source_path TEXT;
ALTER TABLE normas ADD COLUMN source_year INTEGER;
ALTER TABLE normas ADD COLUMN normas_citadas TEXT;
ALTER TABLE normas ADD COLUMN base_legal TEXT;
```

### 3. build_sqlite.py — INSERT actualizado:
```python
source_path = data.get("source_path") or f"{custom_id}.html"
source_year = int(custom_id[:4])
# INSERT incluye source_path, source_year, normas_citadas, base_legal
```

### 4. 18,694 registros existentes actualizados:
```sql
UPDATE normas SET source_path = '2024/' || replace(substr(id,1,10),'-','') || '/' || substr(id,12) || '.html',
                 source_year = 2024
WHERE source_path IS NULL;
```

## Beneficio

Cada norma ahora tiene ruta a su HTML fuente, permitiendo links directos a Cloudflare R2:
```
https://pub-xxx.r2.dev/normas/2024/20240620/2299514-4.html
```

Y las normas citadas y base legal ahora son consultables directamente desde SQLite.
