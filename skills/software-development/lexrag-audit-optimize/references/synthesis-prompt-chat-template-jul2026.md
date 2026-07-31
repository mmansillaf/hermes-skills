# Synthesis Prompt Templates — api-algoritmoConcurrencia v4 (Jul 2026)

## Contexto

Proyecto: api-algoritmoConcurrencia v4. Servidor 192.168.18.152, /opt/api-algoritmo/.
Pipeline: FAISS (1024d) + BM25 + RRF → Groq synthesis. Modelos: llama-3.1-8b-instant.

## Problema Original

El prompt "Magistrado de la Corte Suprema" producía respuestas de 3000-4000 chars con 4 secciones
formales. El usuario dijo: *"no veo respuestas como serian en el chat (de 1 o 2 parrafos con la idea de la pregunta atendida)"*.

## Cambio Aplicado

### Antes (formal — rechazado por usuario)
```
System: "Eres un Magistrado de la Corte Suprema de Justicia de la República del Perú..."
Prompt: "ACTÚA COMO MAGISTRADO DE LA CORTE SUPREMA DEL PERÚ"
Output: 4 secciones (Síntesis + Análisis + Nexo + Conclusiones) → ~3500 chars
```

### Después (chat-style — aprobado)
```
System: "Eres un asistente legal experto en derecho peruano."
Prompt: "ACTÚA COMO ASISTENTE LEGAL EXPERTO EN DERECHO PERUANO"

INSTRUCCIONES:
1. RESPONDE EN 1-2 PÁRRAFOS: estilo conversacional tipo chat, directo al punto.
   No uses títulos ni secciones. Una introducción breve + el análisis con citas.
2. CITAS OBLIGATORIAS: Cada afirmación debe tener su [Doc: ID_REAL].
   Solo usa IDs que aparecen en el CONTEXTO. NUNCA inventes IDs.
3. LENGUAJE CLARO: Usa español jurídico pero comprensible.
   Como si un abogado experto le explicara a un colega.
4. Si el contexto es insuficiente, indica qué falta y da una respuesta preliminar con lo que hay.
```

## Feedback Loop (agregado)

Ubicación: en `query_graphrag_pro()` en synthesis.py, después de la post-verificación.

```python
if grounding['grounding_score'] < 0.8 and grounding['total_citations'] > 0:
    feedback_prompt = f"""La respuesta anterior tiene grounding score de {score}.
Motivo: {claims} afirmaciones sin cita documental.

REESCRIBE la respuesta manteniendo el mismo contenido pero asegurando que CADA
afirmación relevante esté respaldada por un [Doc: ID_REAL]. Las citas deben parecer
naturales dentro del texto, no forzadas. Responde en 1-2 párrafos máximo.

Respuesta anterior a reescribir:
{ans}"""

    response_fix = groq_client.chat.completions.create(
        model=SYNTHESIS_MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente legal experto. Reescribe respuestas jurídicas asegurando que cada afirmación tenga su cita documental correspondiente."},
            {"role": "user", "content": feedback_prompt}
        ],
        temperature=0.1
    )
```
