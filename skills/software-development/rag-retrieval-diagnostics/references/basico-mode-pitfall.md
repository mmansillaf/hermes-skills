# BASICO Mode Pitfall — Direct Answer Without LLM

## The Problem

The query router's BASICO mode returns results directly from SQLite without LLM verification. Fast but fragile — the first FTS5 match may be completely unrelated to the query's actual intent.

## Real Failure Case (02-may-2026)

**Query:** "¿Qué porcentaje de distribución le corresponde a la Municipalidad de Santiago de Surco y cuál es el monto exacto a transferirle?" (about ATU transfer distribution)

**Expected:** ATU Resolution Nº 255-2025-ATU/PE.

**Got:** "ORDENANZA Nº 655-MSS — productos pirotécnicos" because FTS5 ranked a firework ordinance first (matched "Santiago de Surco" keyword).

## Root Cause

`directo_sin_llm` mode returns `unique_results[0]` directly. No LLM verification that the document's context matches the query.

## Detection

Check `sources.router.modo`: `"directo_sin_llm"` = returned without LLM (risk). `"llm_fallback"` or `"llm_normal"` = safe.

## Fix Options

1. Raise threshold: require `confidence > 0.90` AND exact `numero` match for direct mode
2. Always use LLM for BASICO (safer, +1s latency)
3. Post-hoc LLM verification: direct → verify context match → if wrong, redo with LLM
