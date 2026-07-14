# Reverse Validation — Técnica de validación inversa

## Concepto

Validación inversa: tomar una **respuesta** del sistema, extraer su **concepto clave**,
convertirlo en **pregunta**, enviarla a la API, y verificar que la nueva respuesta
**contenga** la misma información.

Si el sistema es internamente consistente, preguntar por lo que acaba de responder
debería producir una respuesta que mencione los mismos conceptos.

```
Respuesta original: "Ley 30077 regula el crimen organizado"
         ↓ (extraer concepto clave)
Pregunta inversa:   "¿qué ley regula el crimen organizado?"
         ↓ (enviar a API)
Respuesta nueva:    "Ley 30077, Ley Contra el Crimen Organizado..." ✅
```

## Métricas

| Métrica | Definición |
|---------|------------|
| overlap% | % de palabras clave de la respuesta original presentes en la nueva |
| entity_match | Número de entidades (leyes/decretos) que coinciden |
| OK | overlap >= 15% o entity_match >= 1 |
| PARTIAL | respuesta existente pero overlap < 15% |
| FAIL | sin respuesta o error |

## Estrategias de generación de preguntas

Prioridad de mayor a menor calidad:

1. **Ley + acción**: extraer número de ley y su acción en la respuesta
   → "¿qué hace la Ley N° 30077?"
2. **Persona + cargo**: extraer nombre y cargo mencionado
   → "¿qué cargo ocupa [Nombre]?"
3. **Definición**: extraer término definido
   → "¿qué es [término]?"
4. **Monto concreto**: extraer cifra monetaria
   → "¿cuál es el monto de [concepto]?"
5. **Primer enunciado**: resumir la primera oración como pregunta genérica

## Script de referencia

`reports/test_reverse_validation.py` en el proyecto.

```bash
cd PeruanoSearchEngine02
python3 reports/test_reverse_validation.py
```

Genera:
- `reports/reverse_v2_resultados.json` — datos crudos
- `reports/reverse_v2_reporte.txt` — reporte legible

## Resultados típicos

| Versión | Preguntas | OK | PARTIAL | Observaciones |
|---------|-----------|-----|---------|---------------|
| v1 | 50 | 84% | 16% | Preguntas con muletillas, respuestas truncadas |
| v2 | 30 | 100% | 0% | Preguntas mejoradas, respuestas completas, max_tokens 3K |

## Pitfalls

1. **Respuestas cacheadas**: si la pregunta ya fue hecha, la respuesta viene del cache
   sin pasar por el validador (`validation_result: None`)
2. **Muletillas**: no usar "según los datos disponibles..." como inicio de pregunta inversa.
   Limpiar el texto antes de extraer el concepto.
3. **Género gramatical**: "que hace **el** Decreto" no "que hace **la** Decreto".
   Detectar con regex si es Ley/Resolución (femenino) o Decreto/Acuerdo (masculino).
4. **Truncamiento en scripts**: no truncar respuestas en el JSON de resultados.
   Guardar `new_ans` completo, no `new_ans[:300]`.
5. **max_tokens insuficiente**: si max_tokens es bajo, las respuestas inversas
   serán cortas y tendrán bajo overlap. Aumentar a ≥3000 para AVANZADO/INTERMEDIO.
