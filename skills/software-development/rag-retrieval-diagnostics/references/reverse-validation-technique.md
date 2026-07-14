# Reverse Validation — QA por preguntas inversas (Mayo 2026)

## Concepto

Técnica para verificar la consistencia interna del sistema RAG sin depender de un ground truth externo:

1. Tomar N respuestas del sistema (de un test previo)
2. Extraer el concepto clave de cada respuesta (ley, cargo, definicion)
3. Formular una pregunta inversa que APUNTE a ese concepto
4. Enviar la pregunta inversa al sistema
5. Verificar si la nueva respuesta contiene el concepto original

**Ejemplo:**
```
Respuesta original: "Ley 32108 modifica el Codigo Penal..."
Pregunta inversa:   "que ley modifica el crimen organizado?"
Respuesta nueva:    "...Ley 31989, Ley 31166, Ley 32108..."
→ Contiene Ley 32108 → OK
```

## Resultado (session 06-may-2026)

- 30 preguntas inversas generadas automaticamente de 100 respuestas
- **30/30 OK (100%)** — overlap >15% o entidad match
- El sistema es internamente consistente

## Script template

Ver `templates/reverse_validation.py` en este mismo skill.

## Estrategias de generacion de preguntas

1. **Ley + accion**: extraer ley y su verbo → "que hace la Ley N° X?"
2. **Persona + cargo**: extraer nombre y cargo → "que cargo ocupa X?"
3. **Definicion**: detectar "es un/una" → "que es X?"
4. **Monto**: detectar S/ o cifras → "cual es el monto de X?"
5. **Default**: primera oracion limpia → "que informacion hay sobre X?"

## Pitfalls

1. **Preguntas con muletillas**: evitar que empiecen con "Segun los datos disponibles..." — limpiar antes de formular
2. **Genero incorrecto**: "que hace la Decreto" → corregir a "que hace el Decreto"
3. **Truncamiento en respuestas**: guardar respuestas COMPLETAS (no `answer[:200]`) para que el overlap sea significativo
4. **Tipo vacio en Neo4j**: resultados de graph traversal pueden tener `tipo=None` → aplicar fallback regex desde sumilla antes de la pregunta inversa
