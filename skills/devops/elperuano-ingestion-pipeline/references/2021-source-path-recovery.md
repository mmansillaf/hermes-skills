# Recuperación de source_path corruptos en 2021

**Descubierto**: 02-may-2026 durante Fase 1 de extracción texto_completo.

## Problema

12,882 normas de 2021 tienen `source_path` corrupto en `normas_total.db`. El pipeline Groq batch original almacenó valores incorrectos en vez del path real al archivo HTML fuente.

## Categorías de source_path corruptos

| Categoría | Count | % | Ejemplo |
|-----------|-------|-----|---------|
| `alt_path` | 6,775 | 52.6% | `decreto-alcaldia-011-2021-alc/mves` |
| `other` | 4,089 | 31.7% | `RESOLUCIÓN MINISTERIAL Nº 00180-2021-PRODUCE` |
| `placeholder` | 1,466 | 11.4% | `ruta relativa` |
| `title_as_path` | 364 | 2.8% | `RESOLUCIÓN ADMINISTRATIVA Nº 000139-2021-P-CSJLI-PJ` |
| `no_date` | 188 | 1.5% | `1935364-1.html` (falta directorio de fecha) |

## Estrategia de recuperación

El campo `id` en la DB tiene el formato correcto: `YYYY-MM-DD/NNNNNNN-N`. Reconstruyendo:

```python
parts = norma_id.split('/')       # "2021-03-18/1935364-1"
date_part = parts[0].replace('-', '')  # "20210318"
file_part = parts[1]              # "1935364-1"
reconstructed = f"{date_part}/{file_part}.html"  # "20210318/1935364-1.html"
```

**Tasa de recuperación**: 100% (todos los HTMLs existen en `data/YYYYMMDD/NNNNNNN-N.html`).

## Script de recuperación

`scripts/fase1b_recuperar_2021.py`:
- Lee normas 2021 con texto_completo NULL
- Reconstruye path desde ID
- Extrae texto con stdlib HTMLParser
- Actualiza `texto_completo` Y corrige `source_path` simultáneamente
- Batch 500 UPDATEs con WAL mode

## Lección aprendida

El `source_path` no es confiable para 2021. Para cualquier operación que necesite localizar el HTML fuente, **siempre derivar del ID** como fallback primario, no del `source_path`.

Query SQL para detectar source_path corruptos:
```sql
SELECT source_path FROM normas 
WHERE source_year = 2021 
  AND source_path NOT LIKE '20%/%'
  AND source_path != 'ruta relativa'
LIMIT 10;
```
