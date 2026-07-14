# OWASP Top 10 for Agentic Applications 2026 (ASI)

Referencia rapida para incluir seguridad en specs SDD.
Fuente: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

## Los 10 Riesgos

| # | Riesgo | Descripcion | Mitigacion Clave |
|---|--------|-------------|------------------|
| ASI01 | **Agent Goal Hijack** | Manipulacion multi-step del objetivo del agente via instrucciones en documentos, RAG, o tool outputs | Inputs externos = no confiables. HITL para cambios de objetivo. Semantic firewall. |
| ASI02 | **Tool Misuse & Exploitation** | Uso destructivo de tools autorizadas (composicion insegura, loops recursivos, budget exhaustion) | Permisos minimos. Validar args antes de ejecutar. Rate limiting. |
| ASI03 | **Identity & Privilege Abuse** | Delegacion de autoridad, impersonacion entre agentes, "confused deputy" | JIT ephemeral tokens. Scopes por endpoint. NHI management. |
| ASI04 | **Agentic Supply Chain** | MCP servers maliciosos, poisoned templates, schema manipulation, registry poisoning | Allowlist MCP. Pinned deps por hash. Signed manifests. |
| ASI05 | **Unexpected Code Execution (RCE)** | Codigo generado por el agente ejecutado sin validacion (vibe coding runaway) | Micro-VMs efimeras o Wasm sandbox. No eval(). |
| ASI06 | **Memory & Context Poisoning** | Envenenamiento de memoria persistente o RAG que sesga decisiones futuras | Memoria por tenant. Expirar datos no verificados. Tracking de procedencia. |
| ASI07 | **Insecure Inter-Agent Comm** | Spoofing, MITM, message injection entre agentes | mTLS. Firma criptografica de mensajes. Zero-trust entre agentes internos. |
| ASI08 | **Cascading Failures** | Fallo unico que propaga por cadenas de agentes (financial cascade, cloud bloat) | Circuit breakers. Fan-out caps. Tenant isolation. |
| ASI09 | **Human-Agent Trust Exploitation** | Agentes explotando sesgo de autoridad para que humanos autoricen operaciones riesgosas | Confidence scores. Step-up authentication fuera del chat para acciones irreversibles. |
| ASI10 | **Rogue Agents** | Agentes que derivan de su funcion (goal drift, reward hacking, self-replication) | Baseline de comportamiento. Monitoreo de drift. Kill switches automaticos. |

## Diferencias Clave vs OWASP LLM Top 10

| Aspecto | LLM Top 10 (2025) | ASI Top 10 (2026) |
|---------|-------------------|-------------------|
| Alcance | Aplicaciones LLM individuales | Agentes autonomos multi-step |
| Riesgos nuevos | — | ASI07 (Inter-Agent), ASI08 (Cascading), ASI10 (Rogue) |
| Vector principal | Prompt injection | Goal hijack + tool misuse + identity abuse |
| Memoria | Sin estado | Persistente entre sesiones (ASI06) |
| Autonomia | Limitada | Planifica, decide, ejecuta sin supervision |

## Checklist Rapido para Specs SDD

```
## Security Considerations (OWASP ASI 2026)

### Alto Riesgo (aplica siempre)
- [ ] [ASI05] Codigo generado se ejecuta en sandbox
- [ ] [ASI06] Memoria aislada por tenant, datos no verificados expiran

### Medio Riesgo (tools/APIs)
- [ ] [ASI01] Inputs externos tratados como no confiables
- [ ] [ASI02] Tools con scopes minimos y rate limiting
- [ ] [ASI03] JIT ephemeral tokens
- [ ] [ASI04] Dependencias pinned, allowlist MCP

### Multi-Agente
- [ ] [ASI07] Comunicacion con mTLS
- [ ] [ASI08] Circuit breakers configurados

### Monitoreo
- [ ] [ASI09] Confidence scores visibles
- [ ] [ASI10] Log de objetivos, deteccion de drift
```
