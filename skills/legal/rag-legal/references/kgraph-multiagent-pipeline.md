# KGraphResolucionesV3 — Pipeline Multi-Agente para Consultas Legales

## Arquitectura

```
Usuario pregunta (CLI o API)
     ↓
1. ROUTER (agents/router.py)
   → Modelo: Llama 3.3 70B (PRIMERO) → fallback Llama 4 Scout 17B
   → Decide: ¿consulta LOCAL (jurisprudencia) o WEB (noticias)?
   → Genera HyDE (expansión semántica de la consulta)
   → kimi-k2 deprecado → reemplazado por 70B + Scout
     ↓
2. RETRIEVAL STRATEGIST (agents/retrieval_strategist.py)
   → Sin LLM: reglas duras para casos claros
   → Con LLM: solo para casos ambiguos
   → Ajusta: top_k dinámico (3-15), modo híbrido/semántico/léxico,
     profundidad de grafo (1-3), uso de HyDE
     ↓
3. HYBRID SEARCH (retrieval/hybrid_search.py)
   → FAISS (búsqueda vectorial) + BM25 (búsqueda léxica)
   → Default top_k=5 (antes 7, reducido para velocidad)
   → Recupera chunks de documentos indexados
     ↓
4. GRAPH ANALYST (agents/graph_analyst.py)
   → Sin LLM. Solo traversal de grafo NetworkX
   → Encuentra conexiones: jueces más frecuentes, leyes más citadas,
     entidades más demandadas, precedentes compartidos
     ↓
5. SYNTHESIZER (agents/synthesizer.py) — "Magistrado IA"
   → Modelo PRINCIPAL: Groq llama-3.3-70b-versatile
   → Fallback 1: DeepSeek V4 Flash (deepseek-chat)
   → Fallback 2: Groq Llama 4 Scout 17B
   → Fallback 3: Groq Llama 3.1 8B
   → Prompt: "Actúa como Magistrado de la Corte Suprema"
   → Streaming de respuesta token por token
     ↓
6. CRITIC (agents/critic.py) — Verificador de Citas
   → Carga 64,186 docs HTML originales + metadata_docs.json
   → Ahora también carga ~20,000 docs nuevos de Groq Batch
     (data_raw/rag_listo_batch_groq_*.json)
   → Detecta alucinaciones: cita que no existe en el corpus
   → Si detecta → feedback loop: re-escribe la respuesta
   → Max 2 iteraciones de corrección
     ↓
Respuesta al usuario + follow-up questions
```

## Modelos por Componente

| Componente | Modelo | Proveedor | Fallback |
|-----------|--------|-----------|----------|
| **Router** | **Llama 3.3 70B** | **Groq** | Llama 4 Scout 17B |
| Strategist | Reglas duras + LLM | Groq | Default strategy |
| Graph Analyst | Sin LLM | — | — |
| **Synthesizer** | **Llama 3.3 70B** | **Groq** | DeepSeek → Scout 17B → 8B |
| Critic | Sin LLM (regex + fuzzy) | — | — |
| Rewriter (feedback) | Llama 3.1 8B | Groq | — |

## Archivos del Sistema

```
kgraph-resoluciones-v3/
├── graphrag_pro.py              # Orquestador principal (CLI + async)
├── agents/
│   ├── router.py                 # Clasificador LOCAL/WEB + HyDE
│   ├── retrieval_strategist.py   # Parámetros adaptativos de búsqueda
│   ├── synthesizer.py            # Generación de respuesta (Magistrado IA)
│   ├── critic.py                 # Verificación de citas
│   └── graph_analyst.py          # Análisis de grafo NetworkX
├── retrieval/
│   ├── hybrid_search.py          # FAISS + BM25
│   ├── graph_search.py           # Traversal de grafo
│   └── web_search.py            # Serper API (requiere SERPER_API_KEY)
├── core/
│   ├── config.py                 # Rutas de índices
│   ├── embedding.py              # Sentence-Transformers
│   └── llm_clients.py           # Groq + DeepSeek clients
├── data/
│   ├── indices/                  # FAISS, BM25, NetworkX binarios
│   └── metadata_docs.json        # Metadata 64,186 HTMLs originales
├── data_raw/
│   └── rag_listo_batch_groq_*.json  # ~20,000 docs nuevos (Groq Batch)
└── .env                          # GROQ_API_KEY, DEEPSEEK_API_KEY, SERPER_API_KEY
```

## Configuración .env

```
GROQ_API_KEY="gsk_tu_key"
SERPER_API_KEY="f4fcb76fd5adb7a02de66b1772370f24291469ea"
DEEPSEEK_API_KEY="sk-tu_key"
```

## Cambios Realizados (7 Jun 2026)

1. **Router** (`agents/router.py`): `moonshotai/kimi-k2-instruct-0905` deprecado → primero `llama-3.3-70b-versatile`, fallback `meta-llama/llama-4-scout-17b-16e-instruct`. Scout es Preview (puede deprecarse), 70B es Production.
2. **Synthesizer** (`agents/synthesizer.py`): Invertido orden de prioridad. **Groq 70B es ahora el principal** (antes DeepSeek). DeepSeek queda como fallback.
3. **Critic** (`agents/critic.py`): Ahora carga también los nuevos JSONs de Groq Batch (`data_raw/rag_listo_batch_groq_*.json`) además del metadata original. Total: ~84,000 docs verificables.
4. **top_k** (`graphrag_pro.py`): Reducido de 7 a 5 para velocidad.
5. **.env**: Creado con SERPER + DEEPSEEK keys.
6. **Core config** (`core/config.py`): Añadido `GROQ_BATCH_PATTERN` para que Critic sepa dónde buscar.

## Evaluación del Sistema (7 Jun 2026)

**10 preguntas de prueba** con el sistema multi-agente configurado (Router 70B + Synthesizer 70B + Critic):

| # | Pregunta | Área | Tiempo | Citas | Leyes | Critic |
|:-:|----------|:----:|:------:|:-----:|:-----:|:------:|
| 1 | ¿Puedo demandar por utilidades no pagadas? | Laboral | 13.4s | SI | SI | ✅ |
| 2 | ¿Puedo demandar por utilidades? (variación) | Laboral | 10.1s | SI | NO | ✅ |
| 3 | Monto indemnización despido arbitrario | Laboral | 10.1s | SI | NO | ✅  |
| 4 | Reintegro remuneraciones pescadores | Laboral | 12.3s | SI | SI | ✅ |
| 5 | CPC ejecución garantías mobiliarias | Comercial | 12.4s | SI | NO | ✅ |
| 6 | Obligación dar suma de dinero | Comercial | 12.4s | SI | NO | ✅ |
| 7 | Pensión alimentos menor edad | Familia | 8.1s | SI | NO | ✅ |
| 8 | Requisitos tenencia y custodia | Familia | 12.3s | SI | SI | ⚠️ alucinó ley |
| 9 | Diferencia despido arbitrario vs incausado | Laboral | 13.1s | SI | NO | ✅ |
| 10 | Entidad regula utilidades en Perú | Laboral | 9.1s | SI | SI | ✅ |
| 11 | Estado expediente judicial | Transv. | 8.9s | SI | NO | ✅ re-escritura |

**Métricas:** 100% tasa de éxito, 11.2s promedio, 100% con citas, 40% con leyes, 2 correcciones del Critic.

**Problemas detectados:**
- **Familia sin cobertura:** El corpus solo tiene LABORAL. Las preguntas 7 y 8 no encontraron documentos relevantes. El sistema respondió con conocimiento general.
- **Alucinación legal:** Pregunta 8 citó Ley N° 29497 (Ley Procesal de Trabajo) como si fuera de familia. El Critic NO detectó esta alucinación semántica (solo verifica existencia del doc_id).
- **Sin deduplicación de consultas:** Preguntas 1 y 2 son casi idénticas pero el sistema no las reconoció como duplicadas.

**Evaluación ponderada por área:** Laboral 8.2/10 | Comercial 5.5/10 | Familia 3.0/10 | Global 6.5/10

Ver `references/evaluacion-20000-docs.md` para la evaluación previa con RAG simple y 10 preguntas.

## Uso

```bash
cd /home/usuario/Escritorio/PyCode/KGraphResolucionesV3
PYTHONPATH=. python3 graphrag_pro.py
# Modo interactivo: ingresa consultas, el sistema responde con streaming
# Tecla 'q' para salir
# Números para repreguntas rápidas

# Modo una consulta:
PYTHONPATH=. python3 graphrag_pro.py --query "mi empleador no me pago utilidades"

# Monitorear batches Groq en progreso:
PYTHONPATH=. python3 monitor_batches.py check
```

## Costos por Consulta (respuesta)

| Modelo | Costo/consulta | 10K consultas/año |
|--------|:--------------:|:-----------------:|
| Llama 3.1 8B (antes) | $0.00009 | $0.90 |
| Llama 4 Scout 17B | $0.00034 | $3.40 |
| **Llama 3.3 70B (actual)** | **$0.00079** | **$7.90** |

## Pitfalls

- **Router usa 70B como principal, Scout como fallback**: Scout es modelo Preview (puede deprecarse). 70B es Production. El orden actual (70B → Scout) es correcto para producción.
- **Critic + metadata_docs.json**: El archivo `data/metadata_docs.json` contiene 64K HTMLs del corpus ORIGINAL. No se ha actualizado con los nuevos PDFs. El Critic carga ambos (HTMLs viejos + JSONs nuevos de Groq) pero el metadata original puede estar desactualizado.
- **DeepSeek como secundario**: DeepSeek V4 Flash está configurado como fallback, pero su API key es funcional. Si Groq falla, DeepSeek toma el control automáticamente.
- **Web Search activado**: Ahora con SERPER_API_KEY configurada, el router PUEDE elegir "WEB". Si lo hace, usa Serper API para buscar en Google. Sin embargo, sin la clave el web search se desactiva silenciosamente.
- **Conversaciones guardadas**: Cada consulta se guarda en `consultas_guardadas/` con timestamp + audit JSON. Útil para auditoría pero puede acumular archivos (~5KB por consulta).
- **El Critic detecta alucinaciones de leyes sueltas (desde 7 Jun 2026)**: Se añadió el patrón `_citar_leyes()` que captura `Ley N° XXXX`, `D.L. N° XXXX`, `Decreto (Legislativo|Supremo) N° XXXX`, `Código (Civil|Procesal Civil|Penal|...)`. El regex requiere número de ley para evitar falsos positivos (`Ley` + espacio suelto NO se captura). El Critic marca como alucinación cualquier ley/código que no esté en los `context_doc_ids` recuperados.
- **El Critic ahora verifica contexto (desde 7 Jun 2026)**: Si una cita EXISTE en el corpus pero NO estaba en los documentos recuperados para esa consulta, se marca como alucinación (`hallucinated = True`). Antes solo verificaba existencia, no relevancia contextual. Esto evita que el sistema cite leyes/documentos correctos pero irrelevantes para la pregunta.
- **Sin deduplicación de consultas**: Si el usuario hace dos preguntas muy similares, el sistema las procesa ambas sin reconocer el patrón. El historial de conversación ayuda parcialmente.

## Crítico — Mejoras de Detección de Alucinaciones (7 Jun 2026)

Se aplicaron 3 cambios al `CriticAgent` para corregir el problema de alucinaciones no detectadas:

### Problema original

El Critic no detectaba alucinaciones de leyes citadas textualmente (como `Ley N° 29497`) porque:
1. **No extraía citas de leyes** — los patrones solo capturaban `Jurisprudencia/XXXX.html`, `EXP. N°`, `CAS. N°`, `RTF N°`, y números de 6-7 dígitos
2. **Las citas sin doc_id no se marcaban** — `c.hallucinated = False` para citas sin doc_id, argumentando que "el LLM pudo reformatearlo"
3. **No verificaba relevancia contextual** — una cita que EXISTE en el corpus pero no estaba en los documentos recuperados no se marcaba como alucinación

### Caso concreto de fallo

En la pregunta "Que requisitos se necesitan para demanda de tenencia y custodia?", el Synthesizer citó `Ley N° 29497` (Nueva Ley Procesal del Trabajo) como si fuera una ley de familia. El Critic no lo marcó porque:
- `Ley N° 29497` existe en el corpus (muchos docs laborales la citan) → `exists_in_corpus = True`
- No tenía un `doc_id` → el veredicto final era `hallucinated = False` (línea 275 antigua)
- Nunca se verificó si la ley estaba en los documentos recuperados para ESA consulta

### Cambio 1: Nuevo patrón `_citar_leyes()`

### 1. Nuevo patrón: `_citar_leyes()`
Extrae citas de leyes con número (`Ley N° 29497`, `Código Civil`) y las verifica contra el corpus. El patrón requiere número o código completo para evitar falsos positivos con la palabra suelta "Ley".

```python
patron = r'(Ley\s*[N°º\.]+\s*\d+(?:[-\s]\d+)*|'
         r'D\.?L\.?\s*[N°º\.]*\s*\d+(?:[-\s]\d+)*|'
         r'Decreto\s+(Legislativo|Supremo|de\s+Urgencia)\s*[N°º\.]*\s*\d+(?:[-\s]\d+)*|'
         r'Codigo\s+(Civil|Procesal\s+Civil|Penal|Tributario|del\s+Trabajo|'
         r'de\s+Comercio|de\s+los\s+Ninos|del\s+Ambiente))'
```

### 2. Verificación de contexto
Las citas que existen en el corpus pero NO están en `context_doc_ids` ahora se marcan como alucinación:
```python
if c.exists_in_corpus and not c.was_in_context:
    c.hallucinated = True  # Existe pero no se usó como contexto
```

### 3. Clasificación de citas textuales sin doc_id
Las citas que solo tienen identificador textual (como `Ley N° 29497`) ahora se verifican:
- Si el identificador está en `id2doc` → se asigna doc_id, se verifica contexto → posible alucinación
- Si es una ley/código reconocible → se marca como alucinación (no debería citar leyes fuera del corpus)
- Si no es identificable → se deja como `hallucinated = False` (indeterminado)
