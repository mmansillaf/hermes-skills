# Estrategias de Chunking para Documentos Judiciales Peruanos

Tres estrategias implementadas para particionar resoluciones/sentencias respetando la estructura natural del documento. Nunca corta un párrafo a la mitad ni pierde el fallo (RESUELVE).

## Problema

El truncado por posición fija (7K chars) corta el documento en medio de una idea. En el ejemplo de una resolución laboral de 8,659 chars, se pierden **1,659 caracteres** que contienen el RESUELVE completo (fallo), los nombres de los jueces firmantes y notas al pie.

## Estrategias

### 1. Chunking multi-pasada con overlap (RECOMENDADA para indexación completa)

Divide el documento en chunks que respetan **límites de párrafo** (doble salto de línea). Los chunks se solapan en ~500 chars para mantener contexto entre fragmentos.

```
Documento original (17K chars) → 6 chunks de ~4,000 chars

Chunk 1: [encabezado + inicio fundamentos]
Chunk 2: [inicio fundamentos + fund. medios]  ← overlap 500 chars
Chunk 3: [fund. medios + fund. finales]       ← overlap 500 chars
...
Chunk 6: [fund. finales + RESUELVE + firmas]  ← SIEMPRE contiene el fallo
```

**Cuándo usar:** Cuando necesitas TODO el contenido del documento indexado (análisis profundo, búsqueda semántica completa).
**Ventaja:** No pierde información, cualquier tamaño de documento.
**Desventaja:** Cada documento produce N chunks → N llamadas al LLM → N veces más costo/tiempo.

### 2. Priorizar fallo (RECOMENDADA para extracción rápida)

Toma los últimos párrafos (donde está el RESUELVE) y completa con los primeros párrafos del documento. Pierde los fundamentos del medio.

```
[inicio contexto] + ... + [RESUELVE] + [firmas]
         [fundamentos medios] → se pierden
```

**Cuándo usar:** Cuando solo necesitas el fallo para indexar en un RAG. Una sola pasada de LLM por documento.
**Ventaja:** Una llamada, siempre captura el fallo.
**Desventaja:** Pierde ~50% del contenido del documento.

### 3. Sub-chunking (para párrafos muy largos)

Para párrafos individuales que exceden el límite de chars. Los divide por saltos de línea manteniendo overlap.

**Cuándo usar:** Documentos con párrafos de 3,500+ chars (ej: fundamentos legales extensos).
**Ventaja:** Nunca deja un párrafo sin procesar.
**Desventaja:** Puede producir chunks muy pequeños.

## Detección de párrafos

```python
import re

def detectar_parrafos(texto):
    """Divide texto en párrafos usando saltos de línea múltiples.
    Retorna lista de dicts: {texto, start, end, es_titulo, lines, chars}"""
    # Detectar títulos (líneas cortas en mayúscula o con RESUELVE/CONSIDERANDO)
    es_titulo = any(
        line.strip().isupper() and 3 < len(line.strip()) < 80
        for line in p.split('\n')[:3]
    ) or any(kw in p.upper() for kw in [
        'RESUELVE:', 'CONSIDERANDO:', 'FALLO:', 'S.S.',
        'VISTOS:', 'ASUNTO:', 'MATERIA:', 'EXPEDIENTE',
        'AUTO EMITIDO', 'SENTENCIA'
    ])
```

## Implementación

Ver `/home/usuario/Escritorio/PyCode/QwenLegalExtractor/chunking_demo.py` para implementación completa con las 3 estrategias.
