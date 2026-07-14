# Fix Definitivo: Modo BÁSICO con Validación de Entidades

## Problema

El modo BÁSICO `directo_sin_llm` devolvía texto crudo de la primera norma encontrada por FTS5 sin verificar que realmente respondiera a la pregunta. Esto causaba respuestas como "Ordenanza de pirotécnicos" para preguntas sobre transferencias de la ATU.

## Causa

La validación original solo chequeaba keywords genéricas (`_match_count >= len(_q_words) * 0.6`). Palabras como "Santiago", "Surco", "monto" matcheaban tanto en la resolución de la ATU como en la ordenanza de fuegos artificiales.

## Fix (3 validaciones)

```python
# 1. Extraer entidades clave de la pregunta
_q_entities = set()
_q_entities.update(re.findall(r'\b([A-ZÁÉÍÓÚÑ]{2,8})\b', question))  # siglas: ATU, ANA
_q_entities.update(re.findall(r'\b(\d{3,6}-\d{4,6})\b', question))    # nums: 255-2025
_q_entities.update(re.findall(r'\bN[°º]\s*(\d{3,6})\b', question))    # N° 538

# 2. Verificar que entidades aparezcan en la respuesta directa
_entity_match = sum(1 for e in _q_entities if e.lower() in _direct_answer.lower())
_entity_ok = _entity_total == 0 or _entity_match / _entity_total >= 0.5

# 3. Exigir confianza mínima
_conf_ok = confidence >= 0.85

# Solo aceptar si TODO pasa
_ok_direct = (
    len(_q_words) >= 2 
    and _match_count >= len(_q_words) * 0.6 
    and _entity_ok
    and _conf_ok
)
```

## Resultados

| Batería | Antes (sin fix) | Después (con fix) |
|---------|-----------------|-------------------|
| 100q Rímac+ATU | 8 falsos positivos | 0 falsos positivos |
| 50q VIVIENDA | 5 falsos positivos | 0 falsos positivos |
| 50q PJ/Callao | N/A (nueva) | 1/50 modo directo, 0 falsos positivos |

## Casos emblemáticos corregidos

| Pregunta | Antes | Después |
|----------|-------|---------|
| "% distribución Santiago de Surco ATU" | "Ordenanza 655-MSS pirotécnicos" ❌ | "No se encontraron normas" ✅ |
| "Artículo Constitución autonomía SJM" | "Art. 137 Estados Emergencia" ❌ | "Art. 194 autonomía municipal" ✅ |
| "Vigencia autorización chatarreo" | "GNV 2 años" ❌ | "No se encuentra en las normas" ✅ |
