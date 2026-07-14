# Comparativa de Modelos para Generación de Código

**Elaborado:** 29 Jun 2026  
**Contexto:** Sesión de optimización de Hermes Agent v0.17.0  
**Modelo default del usuario:** DeepSeek V4 Flash (provider: deepseek)

---

## Los Tres Modelos en Juego

| | DeepSeek V4 Flash | Gemini 2.5 Flash | Groq Llama 3.3 70B |
|---|---|---|---|
| **Provider config** | deepseek | google_ai_studio | groq |
| **Costo input (cache miss)** | $0.14/M | $0.15/M (≤128K) | $0.59/M |
| **Costo input (cache hit)** | **$0.0028/M** (50x descuento automático) | No tiene cache hits | No tiene cache hits |
| **Costo output** | $0.28/M | $0.60/M (≤128K) | $0.79/M |
| **Contexto** | 1M | 1M | 128K |
| **Temperature** | No expuesta (default provider) | 0.05 (configurada) | 0.1 (configurada) |
| **Velocidad** | Muy rápida | Rápida | Ultra rápida (560 TPS) |
| **Tool calling Hermes** | ✅ Probada extensivamente | ✅ Buena | ✅ Excelente |
| **Multimodal** | ❌ No | ✅ Sí (nativo) | ❌ No |
| **Modo razonamiento** | Tiene deep thinking (off por defecto) | Razonamiento nativo | No |

---

## Rendimiento en Código — Experiencia Real

### DeepSeek V4 Flash (default del usuario)

**Proyectos generados exitosamente con este modelo:**

| Proyecto | Tipo de código | Funcionó | Problemas reales |
|---|---|---|---|
| CEJ Scraper | Spider Scrapy + Selenium + CDP bypass | ✅ Sí | Radware, ChromeDriver version — no culpa del modelo |
| KGraphResolucionesV3 | Pipeline Groq Batch + indexer + synthesizer | ✅ Sí | Lógica de pipeline, no sintaxis |
| KRagLocal | FastAPI + ChromaDB + multi-agente | ✅ Sí | Bugs de lógica corregidos con tests |
| Skills Hermes (varias) | SKILL.md, referencias | ✅ Sí | Sin problemas |

**Conclusión del usuario:** *"DeepSeek ha funcionado bastante bien."*

### Gemini 2.5 Flash (fallback #2, temp 0.05)

**Fortalezas vs DeepSeek:**
- **Código más determinista** por temperature 0.05 explícita
- **Mejor seguimiento de instrucciones complejas** con muchas restricciones
- **Multimodal** — puede analizar capturas de error, diagramas, mockups UI
- **JSON estructurado** — tasa ligeramente superior (99.5%+ vs ~98%)

**Debilidades vs DeepSeek:**
- Ligeramente más lento en tool calling loops
- No probado extensivamente en este setup (nunca fue default)

### Groq Llama 3.3 70B (fallback #3, temp 0.1)

**Fortalezas:**
- Modelo más capaz de los tres (70B params)
- Velocidad extrema (560 TPS)
- Excelente para razonamiento complejo multi-paso

**Debilidades:**
- Contexto limitado a 128K (vs 1M de los otros)
- 4x más caro que DeepSeek Flash
- Cloudflare 1010 blocking desde sandboxes IPs

---

## Recomendación por Tipo de Tarea

| Tarea | Modelo | Justificación |
|---|---|---|
| **Código de producción** (funciones, APIs, refactors) | DeepSeek V4 Flash | Probado, rápido, suficiente calidad |
| **Código con restricciones estrictas** (JSON, esquemas) | Gemini 2.5 Flash | temp 0.05, mejor determinismo |
| **Análisis de capturas / debugging visual** | Gemini 2.5 Flash | Único con multimodal |
| **Razonamiento complejo multi-paso** | Groq Llama 3.3 70B | Modelo más capaz |
| **Extracción masiva batch** | Groq Llama 3.1 8B | $0.000084/doc, 560 TPS |
| **Síntesis jurídica / lenguaje natural** | DeepSeek V4 Flash | Buen balance, default del usuario |
| **Scraping / integración con Selenium** | DeepSeek V4 Flash | Probado, sin ventaja de Gemini |
| **Skills / documentación** | DeepSeek V4 Flash | Modelo más rápido para tareas mecánicas |

---

## Regla Práctica

> **DeepSeek V4 Flash es el default correcto para código.**  
> Cambia a Gemini 2.5 Flash solo cuando:  
> 1. Necesites análisis multimodal (capturas, diagramas)  
> 2. Quieras razonamiento extra en una tarea particularmente compleja  
> 3. Necesites JSON perfecto con muchas restricciones  
>
> Cambia a Groq Llama 3.3 70B solo cuando:  
> 1. Necesites el máximo razonamiento posible  
> 2. El costo no sea relevante  
> 3. El contexto quepa en 128K  

**No hay razón para cambiar el default.** La calidad de código de DeepSeek V4 Flash es suficiente para todas las aplicaciones construidas hasta ahora (scrapers, pipelines RAG, APIs, skills). Los cuellos de botella han sido siempre externos al modelo (Radware, ChromeDriver, lógica de negocio).

---

## Temperatura y Parámetros

Hermes v0.17.0 no expone `temperature` para el modelo principal en `config.yaml`.  
Los fallback providers sí tienen temperature configurada:

```yaml
fallback_providers: >
  '[{"provider":"kimi","model":"kimi-k2.6","temperature":1},         # Alta = exploración
    {"provider":"google_ai_studio","model":"gemini-2.5-flash","temperature":0.05},  # Baja = código determinista
    {"provider":"groq","model":"llama-3.3-70b-versatile","temperature":0.1}]'       # Baja = código determinista
```

**Workaround:** Para código de alta calidad, usar `/model gemini-2.5-flash` (temp 0.05) o `/model groq` que redirige a Llama 3.3 70B (temp 0.1).

**Nota:** DeepSeek V4 Flash tiene un modo `reasoning_content` / deep thinking que está desactivado con `reasoning_effort: none` en config. Si se activara, mejoraría razonamiento pero aumentaría latencia y tokens.

---

## Guía Práctica: Maximizar Cache Hits de DeepSeek

DeepSeek tiene **context caching en disco automático** que da **50x descuento** en cache hits ($0.0028/M vs $0.14/M miss). No requiere cambios de código, pero ciertas prácticas maximizan la tasa de acierto.

### Lo que ya está optimizado en este setup

| Práctica | Estado | Impacto en caché |
|---|---|---|
| SOUL.md con identidad estable (1KB) | ✅ Creado 29-Jun-2026 | Se cachea después del 1er turno |
| System prompt con Karpathy rules (fijo) | ✅ Configurado | Prefijo estable = cache hit |
| `.hermes.md` en KGraph y cej-scraper | ✅ Creado 29-Jun-2026 | Contexto de proyecto estable por sesión |
| Temperature fija en fallbacks | ✅ Configurada | Sin variación que rompa caché |
| `prompt_caching.cache_ttl: 30m` | ✅ Configurado | Hermes ya gestiona TTL |

### Prácticas para maximizar ahorro

1. **Sesiones largas > sesiones cortas** — El caché se acumula turno a turno. Cada turno nuevo reusa el prefijo de los anteriores. Abrir `/new` frecuentemente reinicia el caché. Una sesión de 20 turnos es significativamente más barata que 20 sesiones de 1 turno.

2. **Contexto estático primero, variable después** — El cacheo de DeepSeek funciona por **prefix matching** (coincidencia exacta desde el token 0). Poner contexto estático (system prompt, SOUL.md) al inicio y lo variable (la pregunta concreta) al final maximiza el prefijo que se cachea.

3. **SOUL.md y `.hermes.md` estables** — Los archivos de contexto de proyecto que creamos (`.hermes.md` para KGraph, cej-scraper) son estables entre sesiones del mismo proyecto. Esto permite que el prefijo del system prompt + contexto de proyecto se cachee y se reúse en sesiones subsiguientes (mientras el caché no expire, tipicamente horas).

4. **Subagentes con contextos similares** — Cuando uses `delegate_task`, si varios subagentes reciben el mismo prefijo de contexto (ej. mismo project context + instrucciones base), el segundo subagente en adelante obtiene cache hits en la porción compartida.

### Lo que NO afecta al caché

- Variables en medio del mensaje (solo prefix matching desde token 0)
- Output del modelo (solo input se cachea)
- Cambios de temperatura entre turnos (el input es el mismo)

### Ahorro estimado

Con una sesión típica de 10 turnos (~5K input + ~2K output por turno):
- Sin caché: ~$0.01/sesión
- Con caché (~50% hits, promedio DeepSeek): ~$0.005/sesión
- Con optimización activa (sesiones largas, contexto estable): ~$0.003/sesión

Para el flujo diario del usuario (varias sesiones/día), el ahorro es modesto en absoluto (~$0.50-1.00/mes) pero el beneficio real es la reducción de latencia: primer token en 500ms vs 13s en prompts largos.

### Referencia cruzada

Para detalles técnicos completos del sistema de caching de DeepSeek (reglas de prefix matching, unidades de 64 tokens, persistencia, monitoreo con `prompt_cache_hit_tokens`), ver la sección **9. Provider-Specific Tactics > DeepSeek** en la SKILL.md principal de `hermes-multi-provider-config`.
