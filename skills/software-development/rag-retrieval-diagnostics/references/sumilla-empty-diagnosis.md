# Diagnóstico: Documentos con Sumilla Vacía

## Síntoma

El sistema responde "no se encontró información" o "no se especifica quién firmó" para preguntas sobre documentos que SÍ existen en la base de datos (97,809 normas). La verificación directa contra SQLite confirma que el documento está indexado pero FTS5 no lo recupera.

## Verificación

```sql
-- Verificar si el documento existe
SELECT tipo_norma, numero, fecha_publicacion, sumilla 
FROM normas WHERE numero LIKE '%000303-2023%';

-- Si sumilla = '' (vacía), el documento NO será encontrado por FTS5
-- porque FTS5 indexa principalmente sumilla, tipo_norma, numero, emisor
```

## Causa raíz

El extractor Groq (`02_groq_batch_pipeline.py`) no pudo extraer la sumilla de ciertos documentos:
- Resoluciones Administrativas del Poder Judicial (~300 docs con sumilla vacía)
- Decretos de Alcaldía municipales (~500 docs con sumilla vacía)
- Ordenanzas distritales (~1000 docs con sumilla vacía)

El texto completo SÍ está almacenado en `texto_completo`, pero FTS5 indexa `sumilla` como campo principal.

## Solución (2 pasos)

### Paso 1: Agregar texto_completo al índice FTS5

```sql
-- Destruir y recrear FTS5 incluyendo texto_completo
DROP TABLE IF EXISTS normas_fts;
CREATE VIRTUAL TABLE normas_fts USING fts5(
    tipo_norma, numero, emisor, sumilla, materia, texto_completo, 
    content=''
);
INSERT INTO normas_fts(rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo)
SELECT rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo FROM normas;
```

### Paso 2: Re-extraer sumillas con Groq

Para los ~3,000 documentos con sumilla vacía:
```python
# Usar texto_completo ya almacenado como input
# Enviar a Groq Batch para extraer sumilla
# Actualizar campo sumilla en SQLite
```

## Impacto estimado

- **Antes:** 44% acierto en batería PJ/Callao
- **Después:** ~75% acierto (elimina 6/6 incorrectas + mejora 10/22 parciales)
