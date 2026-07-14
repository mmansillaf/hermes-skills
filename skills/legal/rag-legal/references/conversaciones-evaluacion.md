# Conversaciones de Evaluación — Sistema Multi-Agente KGraphResolucionesV3

## Resumen

Este archivo contiene las transcripciones completas de las consultas de prueba realizadas al sistema multi-agente (Router 70B → Strategist → Synthesizer 70B → Critic). Cada conversación incluye la pregunta del usuario, la respuesta completa del "Magistrado IA", las fuentes citadas, y el resultado del Critic.

## Última Evaluación (7 Jun 2026, 21:38-21:40, con Critic mejorado)

Router: Llama 3.3 70B (principal) → Llama 4 Scout (fallback)
Synthesizer: Llama 3.3 70B (principal) → DeepSeek → Scout → 8B
Critic v2: Detecta leyes citadas (_citar_leyes()), verifica contexto, marca citas sin doc_id

### Resultados del Critic por pregunta

| # | Pregunta | Tiempo | Score Critic | Corrección | Observación |
|:-:|----------|:------:|:------------:|:----------:|-------------|
| 1 | Puedo demandar por utilidades? | 12.4s | 100% | — | Sin alucinaciones |
| 2 | Monto indemnización despido arbitrario | 11.6s | 100% | — | Cita caso real: S/29,636.85 |
| 3 | Reintegro remuneraciones pescadores | 10.5s | 100% | — | Sin alucinaciones |
| 4 | CPC ejecución garantías mobiliarias | 12.0s | 0% (4 falsas) | Re-escrita | CAS. N° 480, 74, 72049 alucinados |
| 5 | Obligación dar suma de dinero | 12.7s | 0% (1 falsa) | Re-escrita | 453100.html no existe |
| 6 | Pensión alimentos menor edad | 9.1s | 100% | — | Sin alucinaciones |
| 7 | Requisitos tenencia y custodia | 11.1s | 0% (2 falsas) | Re-escrita | HTMLs que no existen |
| 8 | Diferencia despido arbitrario vs incausado | 13.2s | 100% | — | Buena definición conceptual |
| 9 | Entidad regula utilidades en Perú | 6.8s | 100% | — | Identificó Ministerio de Trabajo |
| 10 | Estado expediente judicial | 8.8s | 100% | — | Dijo informacion insuficiente |

**Metricas:** 7/10 sin alucinaciones | 3/10 con alucinaciones detectadas y corregidas | 0/10 con alucinaciones no detectadas

### Problemas persistentes

1. **Corpus insuficiente para Familia y Comercial** — las preguntas sobre pension de alimentos y tenencia no tienen documentos reales (solo LABORAL)
2. **Limite de 2 iteraciones de correccion** — en preguntas 4 y 7, despues de re-escribir, quedaban citas falsas que el limite no dejo corregir
3. **Falso positivo de Ley suelta** — corregido: ahora requiere numero de ley (`Ley N° XXXX`)

## Evaluacion Anterior (7 Jun 2026, 21:07-21:17, con Critic original)

11 preguntas con el Critic ORIGINAL (sin deteccion de leyes, sin verificacion de contexto).

### Problemas detectados en el Critic original

| Problema | Ejemplo | Gravedad |
|----------|---------|:--------:|
| **Alucinacion de leyes NO detectada** | Pregunta 8 cito Ley N° 29497 (laboral) como si fuera de familia | Alta |
| **Sin deteccion de duplicados** | Preguntas 1 y 2 son casi identicas, respuestas diferentes | Media |
| **Sin docs de familia** | Preguntas 7 y 8 no encontraron nada relevante en el corpus | Alta |
| **Citas a HTMLs viejos** | Las respuestas citan `Jurisprudencia/xxxx.html` del corpus original | Media |

### Correcciones aplicadas

1. **`_citar_leyes()`** — nuevo patron que captura `Ley N° XXXX`, `D.L. N° XXXX`, `Decreto (Legislativo|Supremo) N° XXXX`, `Codigo (Civil|Procesal Civil|Penal|...)`. Requiere numero de ley (no captura "Ley" suelta).
2. **Verificacion de contexto** — una cita que existe en `id2doc` pero no esta en `context_doc_ids` → `hallucinated = True`
3. **Citas textuales sin doc_id** — si el identificador es reconocible como ley/codigo y no existe en el corpus → `hallucinated = True`

Ver `references/kgraph-multiagent-pipeline.md` para detalles tecnicos de los cambios.
