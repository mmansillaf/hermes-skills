# AVANZADO Borrador Pattern — No bloquear, generar con advertencia visible

**Fecha:** 2026-05-02
**Fix applied:** `api_rest.py` — unified AVANZADO_CREACION + AVANZADO_ANALISIS into borrador mode

## Problem

Queries containing "dictamen", "proponga", "formule", "redacte", "diseñe", "hipótesis" were BLOCKED entirely:

```
"⚠️ CONSULTA DE ANÁLISIS JURÍDICO AVANZADO — No se genera respuesta 
automática para preservar la seguridad jurídica."
```

Only normas were listed, no analysis generated. 22% of AVANZADO queries were blocked.

## Solution

Generate a "borrador" with:
1. **Prominent warning banner** (ASCII box ╔═╗)
2. **Normas relevantes** section (top 8 results)
3. **Full LLM analysis** with `max_tokens=1200`
4. **FUENTES** section

## Code

```python
if _nivel == "AVANZADO_CREACION":
    llm_answer = generate_answer(question, req.profile, unique_results, sources)
    borrador_header = (
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  ⚠️  BORRADOR DE ANÁLISIS JURÍDICO — NO CONSTITUYE       ║\n"
        "║  ASESORÍA LEGAL PROFESIONAL. Este es un borrador          ║\n"
        "║  generado por IA para orientar la investigación.          ║\n"
        "║  Debe ser revisado y validado por un abogado              ║\n"
        "║  especializado antes de cualquier uso profesional.        ║\n"
        "╚══════════════════════════════════════════════════════════╝\n\n"
    )
    normas_section = (
        "📋 **Normas relevantes identificadas:**\n\n" +
        "\n\n".join(normas_contexto) +
        "\n\n─── BORRADOR DE ANÁLISIS ───\n\n"
    )
    llm_answer = borrador_header + normas_section + llm_answer

elif _nivel == "AVANZADO_ANALISIS":
    llm_answer = generate_answer(question, req.profile, unique_results, sources)
    disclaimer = (
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  ⚠️  ANÁLISIS JURÍDICO ASISTIDO POR IA                   ║\n"
        "║  No constituye asesoría legal profesional.               ║\n"
        "║  Verifique las normas citadas y consulte con un          ║\n"
        "║  abogado para su caso específico.                        ║\n"
        "╚══════════════════════════════════════════════════════════╝\n\n"
    )
    llm_answer = disclaimer + llm_answer
```

## Results (150-question test)

| Metric | Before | After |
|--------|--------|-------|
| Blocked AVANZADO | 5/23 (22%) | **0/23 (0%)** |
| Avg response length | ~400 chars | **1,800 chars** |
| With FUENTES | ~50% | **100%** |

## Dynamic max_tokens

Paired fix: `max_tokens` varies by router level:

```python
router_nivel = sources.get("router", {}).get("nivel", "INTERMEDIO")
max_tok = 1200 if router_nivel in ("AVANZADO_CREACION", "AVANZADO_ANALISIS", "INTERMEDIO") else 800
```

- BÁSICO: 800 tokens (~1 página)
- INTERMEDIO/AVANZADO: 1200 tokens (~2 páginas)
