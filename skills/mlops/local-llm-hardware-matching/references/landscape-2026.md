# Panorama LLMs Locales 2026 — Condensado

Fuentes: PromptQuorum, Atomic Chat, Qwen Blog, GenDesigns, SitePoint, ACM DL, arXiv, BentoML, Spheron, SWE-bench Leaderboard, Reddit r/LocalLLaMA, HuggingFace.
Ver informe completo: `/home/cmansilla/Pycode/ModeloLocal/INFORME-LLMS-LOCALES-2026-COMPLETO.md`

## Ranking modelos locales para código (Junio 2026)

| # | Modelo | Tamaño | VRAM req. | SWE-bench | HumanEval | Ideal para |
|---|--------|--------|-----------|-----------|-----------|------------|
| 1 | Kimi K2.6 | 1T MoE (32B active) | 24-32 GB | 58.6% Pro | — | Agentic coding LARGA duración |
| 2 | Qwen3.6-27B | 27B dense | 16 GB | **77.2%** | **92.1%** | Mejor dense local |
| 3 | Qwen3-Coder-30B | 30B | 16-24 GB | ~80% | ~89% | 220 tok/s, 256K ctx |
| 4 | Devstral Small 24B | 24B | 14 GB | ~73% | 90.1% | Agentes multi-step |
| 5 | GLM-5.2 | ? | 16 GB | ~74% | — | Nuevo contender |
| 6 | DS-R1-0528-Qwen3-8B | 8B | 5 GB | — | — | Razonamiento en HW limitado |
| 7 | Qwen3-8B | 8B | 5 GB | — | 72% | 8GB VRAM, modo híbrido |

**Observaciones clave:**
- Qwen3.6-27B supera a Qwen3.5-397B-A17B (15x parámetros) en SWE-bench
- Qwen3-Coder-30B fue el más rápido en test (220 tok/s), recomendado por comunidad
- Kimi K2.6 hizo 4000+ tool calls en 12h autónomas — nuevo estándar agentic

## Benchmark generación UI (GenDesigns, Jun 2026)

10 prompts → HTML+Tailwind CSS, panel de 3 evaluadores:

| Rank | Modelo | Score | Acceso | Mejor en |
|------|--------|-------|--------|----------|
| 1 | Claude 4 (Opus) | 8.4/10 | API pago | Layout logic, code quality, data viz |
| 2 | GPT-4o | 8.2/10 | API pago | Visual design, consistencia, estilos |
| 3 | Gemini 2.5 Pro | 7.8/10 | API pago | Material Design 3 |
| 4 | DeepSeek V3 | 7.4/10 | API/cloud | Budget, functional UIs |
| 5 | Llama 4 (405B) | 7.0/10 | Open-source | Layout structure |

**Conclusión:** Ningún modelo open-source/local iguala a Claude 4 para UI. DeepSeek V3 es el mejor open-source (~7.4). v0.dev sigue siendo top.

## Legal — Stack local validado

Arquitectura multi-agente (ACM 2025):
```
Controller → Risk Agents (Legal, Commercial, Technical)
  → Enterprise Contract Knowledge Base (RAG)
  → Fusion Agent → Unified Risk Profile
```
MA-RAG supera 40% a single-agent en detección de cláusulas de riesgo.

**arXiv 2026:** Deliberación multi-agente para razonamiento legal — múltiples LLMs debaten un caso (defensa, acusación, juez).

Stack local recomendado:
```
PDF → OCR → Chunking → embeddings (bge-m3/e5-mistral)
  → Qdrant/ChromaDB → RAG híbrido → LLM local (DS-R1-0528-Qwen3-8B)
  → Frontend: Open WebUI o Streamlit
```

## Arquitecturas híbridas — 40-70% ahorro vs API-only

```
LiteLLM Gateway → Router Inteligente
  ├── Local (Ollama/llama.cpp): Tareas simples, privadas, offline
  ├── Cloud API (DeepSeek/OpenAI): Razonamiento complejo, UI, gran contexto
  └── Fallback mutuo
```

Costos ejemplo (dev individual, ~500K tok/día): API-only $45-90/mes → Híbrido $10-20/mes.

## Fine-tuning — <$5 por sesión (7B con LoRA/QLoRA)

| Técnica | Params entrenables | VRAM | Convergencia | Para qué |
|---------|-------------------|------|-------------|----------|
| LoRA | 0.1-1% | 8-12 GB | Estándar | Default |
| QLoRA | 0.1-1% | 5-8 GB | Similar a LoRA | Hardware limitado |
| **PiSSA** (SVD) | 0.1-1% | 8-12 GB | **+5% vs LoRA** | Inicialización con componentes principales |
| DoRA | 0.1-1% | 9-13 GB | +1-2% vs LoRA | Accuracy crítica |
| VeRA | <0.1% | 5-8 GB | Similar a LoRA | Edge, máxima eficiencia |
| GRPO | 100% (RL) | 5-16 GB | Lento, razonamiento | Entrenar razonamiento (DeepSeek-style) |

**PiSSA:** Descompone matriz original con SVD, inicializa adaptadores con componentes principales (no aleatorio). GSM8K Mistral-7B: 72.86% vs LoRA 67.7%.

**LoRAFusion (2026):** Fine-tuning multi-job concurrente, 1.96× speedup vs Megatron-LM. Relevante para entrenar múltiples adaptadores legales sobre mismo modelo base.

**GRPO vs PPO:** GRPO eliminó el modelo Crítico, reduciendo VRAM drásticamente. Genera grupo de respuestas y las normaliza entre sí. Habilitó DeepSeek-R1 en hardware antes imposible.

## Optimización de inferencia

| Técnica | Beneficio | Cómo |
|---------|-----------|------|
| **RadixAttention (SGLang)** | 80-90% menos VRAM en multi-agente | KV cache en árbol de prefijos. Cache compartido entre agentes que usan mismo system prompt |
| **Speculative Decoding (EAGLE-3)** | 2-3× más rápido | Mini-cabezal predictor de features. Tasa aceptación 0.8-0.9 |
| **JPQD (OpenVINO)** | Comprimir 4-8× sin pérdida | Joint Pruning, Quantization, Distillation en un paso |

**Orden correcto P-KD-Q:** Pruning → Knowledge Distillation → Quantization. NUNCA Q→KD (aumenta perplexity ×10).

## RAG avanzado para legal

| Técnica | Beneficio | Implementación |
|---------|-----------|---------------|
| **Contextual Retrieval** (Anthropic) | +49% retrieval | Pre-inyectar resumen del doc padre a cada chunk antes de embedding |
| **GraphRAG** | Razonamiento multi-hop | Neo4j + LangChain + Qdrant híbrido |
| **Multi-Agent RAG (MA-RAG)** | +40% detección cláusulas riesgo | Controller → Risk Agents → Fusion Agent |

## Innovaciones disruptivas

- **Qwen3-Coder-Next 80B en 8GB VRAM** (GitHub nalexand): offloading extremo + quant 2-bit, 26 tok/s
- **Kimi K2.6 Agent Swarms:** Múltiples instancias colaborando, 4000+ tool calls sin intervención
- **GRPO local en 5GB VRAM:** Unsloth permite entrenar razonamiento en hardware de consumo
