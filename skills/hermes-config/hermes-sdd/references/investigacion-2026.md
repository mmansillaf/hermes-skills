# Contexto de Investigación: SDD y Agentic Engineering (Junio 2026)

Este archivo resume las áreas críticas investigadas que fundamentan el skill
`hermes-sdd`. Úsalo como referencia contextual.

## 1. Agentic Engineering (Karpathy, Sequoia AI Ascent 2026)

- Vibe coding declarado "passé" — reemplazado por **Agentic Engineering**
- **Software 3.0**: El texto en tu context window ES el programa. LLM = intérprete
- **"Ghosts, not animals"**: LLMs no tienen motivación intrínseca. Son summoned.
- **Jagged Intelligence**: Son increíbles en lo que hay RL (código, mates); fallan en
  lo obvio (sentido común físico)
- **Inflexión Diciembre 2025**: Karpathy dejó de corregir outputs de agentes
- **57% de equipos con agentes en producción** (LangChain 2026)
- **89% observabilidad, solo 52% evals** — la brecha donde ocurren las regresiones

## 2. SDD Maturity Model (consenso industria, Junio 2026)

| Nivel | Descripción |
|-------|-------------|
| Spec-First | Specs seed, luego código deriva |
| Spec-Anchored 🎯 | **Sweet spot producción** — specs + tests enforzan alineación |
| Spec-as-Source | Solo specs, código 100% regenerado (aspirational) |

## 3. Tooling SDD 2026

| Herramienta | Tipo | Notas |
|-------------|------|-------|
| GitHub Spec Kit | Open-source CLI | Estándar de referencia, model-agnóstico |
| AWS Kiro | IDE agéntico | Guardrails automáticos, deep AWS |
| Claude Code (cc-sdd) | Slash commands | `/sdd:specify`, `/sdd:plan` nativos |
| Cursor (Plan Mode) | IDE | Inline diff review, MCP support |
| OpenSpec | Markdown+YAML | Ligero, indie devs |
| Tessl | Compliance | Audit trails, fintech/healthtech |
| Google Antigravity | Agent-first | Autonomía con restricción por spec |

## 4. Críticas a SDD (importante para transparencia)

- **"Same Patterns, New Hype" (Brandon Kindred)**: SDD = waterfall rebautizado
- **Thoughtworks**: SDD en "Assess", NO "Adopt". Rechazan "specs alone suffice"
- **Reddit r/AI_Agents**: Specs excesivas atrofian supervisión humana
- **Debate 3h Our Tech Journey**: El problema no es escribir código, es descubrir
  si construyes lo correcto. Specs no reemplazan feedback loops.

## 5. OWASP Top 10 for Agentic Applications 2026 (ASI)

| Código | Riesgo | Mitigación clave |
|--------|--------|------------------|
| ASI01 | Goal Hijack | Inputs externos = no confiables, human-in-the-loop |
| ASI02 | Tool Misuse | Permisos mínimos, validar args antes de ejecutar |
| ASI03 | Identity Abuse | JIT ephemeral tokens, NHI management |
| ASI04 | Supply Chain | Allowlist MCP, pinned deps, signed manifests |
| ASI05 | RCE | Micro-VMs efímeras o Wasm sandbox |
| ASI06 | Memory Poisoning | Memoria por tenant, expirar no verificada |
| ASI07 | Inter-Agent Comm | mTLS, firma criptográfica de mensajes |
| ASI08 | Cascading Failures | Circuit breakers, fan-out caps, tenant isolation |
| ASI09 | Trust Exploitation | Confidence scores, step-up auth fuera del chat |
| ASI10 | Rogue Agents | Baseline de comportamiento, kill switches |

Fuente: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

## 6. Token Optimization Patterns

- **Lazy Tool Loading**: 2-paso — nombres (300-500t) → schema completo solo si
  el modelo lo pide. Ahorro: 30-70%.
- **Frozen Memory Snapshot** (Hermes): MEMORY.md + USER.md congelados al inicio.
  Reduce 75% coste de input en sesiones largas.
- **CACHE_BARRIER** (OpenClaw): Lo estático arriba del barrier se reusa del KV cache.
- **Chain of Draft**: Borrador rápido + crítica + final. 40% menos tokens que CoT.
- **Code-First Tool Discovery**: Una sola tool `execute_code`, descubre otras on-demand.
  98% reducción en schemas.

## 7. Anthropic 2026 Agentic Coding Trends Report

- 60% uso de IA en trabajo, 0-20% delegación completa ("delegation gap")
- 27% del trabajo asistido por IA NO existía antes
- De asistentes individuales a equipos multi-agente
- Agentes que corren horas/días con checkpoints humanos
- El cuello de botella: claridad sobre qué construir, no escribir código

## 8. Testing: Record Decisions, Not HTTP

- `langchain-replay` graba decisiones del LLM (qué tool, qué args)
- Durante replay: tools REALES se ejecutan, no mock HTTP
- Valida razonamiento + implementación sin coste de LLM
- Soluciona el problema de mock HTTP que "congela" el loop del agente

## 9. Routing de Modelos por Fase SDD

| Fase | Modelo | Razón |
|------|--------|-------|
| Spec + EARS | DeepSeek Reasoner / Gemini | Precisión lógica |
| Plan | DeepSeek Reasoner | Trade-offs arquitectónicos |
| Tasks | DeepSeek Flash / Gemini Flash | Desglose mecánico |
| HTML Preview | Modelo output largo | Generar HTML completo |
| Implement | DeepSeek Flash | Velocidad |
| Security Review | Gemini (contexto masivo) | Revisar diff completo |

Fuentes principales:
- https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- https://github.com/github/spec-kit
- https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf
- https://www.langchain.com/state-of-agent-engineering
- https://arxiv.org/abs/2602.00180 (Piskala, Spec-Driven Development)
