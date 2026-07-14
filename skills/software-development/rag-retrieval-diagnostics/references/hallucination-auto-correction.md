# Defensa Anti-Alucinacion en 4 Capas para RAG Legal

## Descubrimiento Clave (06-may-2026)

**El prompt grounding NO funciona con Llama.** Aunque le digas explicitamente "NO menciones Ley 29158", el LLM sigue citandola porque aparece en el contexto de las resoluciones como base legal boilerplate. La solucion requiere post-procesamiento con regex.

## Arquitectura de 4 Capas (D -> C -> B -> A)

### Capa D: LeyBooster (retrieval)
Si la pregunta contiene "ley"/"leyes", priorizar resultados tipo=LEY sobre otros:
```python
if any(w in question.lower().split() for w in ['ley', 'leyes', 'legislativo']):
    _ley_results = [r for r in unique_results if ((r.get('tipo') or '').upper()) in
                   ('LEY', 'DECRETO LEGISLATIVO', 'DECRETO LEY')]
    for r in _ley_results:
        r['relevance'] = min(r.get('relevance', 0.3) + 0.3, 1.0)
    unique_results = _ley_results + [r for r in unique_results if r not in _ley_results]
```

### Capa C: Contexto Enriquecido
- 15 resultados al LLM (era 10)
- Scores visibles: `(score=0.80, src=sqlite)`
- Sumillas 500 chars (era 300)
- Neo4j tipo=None fix: regex fallback desde sumilla para extraer LEY/DECRETO

### Capa B: Prompt Grounding + Enumeracion
```
INSTRUCCIONES:
- Menciona TODAS las leyes relevantes de NORMAS ENCONTRADAS
- Si la pregunta dice 'que leyes', ENUMERA cada ley sin omitir
- SOLO citar leyes cuyo numero aparezca en NORMAS ENCONTRADAS
- Una ley organizativa NO es relevante a menos que la pregunta sea sobre eso
```

### Capa A: Cleaner + Validator (post-procesamiento)
Regex cleaner que elimina leyes organizativas de la respuesta:
```python
LEYES_ORGANIZATIVAS = [
    (r'Ley\s+N?°?\s*29158[^.]*', 'Ley 29158 (Poder Ejecutivo)'),
    (r'Ley\s+N?°?\s*27594[^.,;]*', 'Ley 27594 (designacion)'),
    (r'Ley\s+N?°?\s*27444[^.,;]*', 'Ley 27444 (Proc. Admin)'),
    (r'Decreto\s+Legislativo\s+N?°?\s*1266[^.,;]*', 'DL 1266 (MININTER)'),
]

if not es_pregunta_organizativa and llm_answer:
    for pattern, name in LEYES_ORGANIZATIVAS:
        llm_answer = re.sub(pattern, '', llm_answer, flags=re.IGNORECASE)
    # Limpiar residuos: "se basan en , ."
    llm_answer = re.sub(r'\bse\s+basan?\s+en\s*,?\s*\.?', '', llm_answer)
```

**Pitfall critico:** `re.sub('', llm_answer)` — el primer argumento debe ser el PATTERN:
```python
# MAL:  re.sub('', llm_answer, flags=re.IGNORECASE)  -> TypeError
# BIEN: re.sub(pattern, '', llm_answer, flags=re.IGNORECASE)
```

## Resultado verificado
Pregunta: "que ley o leyes mencionan o modifican el crimen organizado?"
- Ley 29158: NO (antes SI) | Ley 27594: NO (antes SI)
- Ley 30077: SI | Ley 32108: SI (antes omitida)
- Leyes mencionadas: 6+ (antes 3)

## Prerrequisitos
- max_tokens >= 3000 para espacio de enumeracion
- 15 resultados en contexto (era 10)
- sumillas 500 chars (era 300)