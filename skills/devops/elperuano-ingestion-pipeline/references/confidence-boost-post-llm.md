# Confidence Boost Post-LLM (3 factores)

## Problema

La confianza base (`confidence_score()`) penaliza el solapamiento léxico entre query y resultados,
pero no considera que el LLM extrajo la respuesta correcta del `texto_completo`. Queries con baja
superposición léxica pero respuestas CORRECTAS quedaban con confianza 0.10-0.30.

Ejemplo: "¿Quién fue designado como Directora de la Oficina X?" → FTS5 encuentra la norma,
el LLM extrae el nombre, pero la superposición de palabras entre query y sumilla es baja → conf 0.15.

## Solución

Boost de 3 factores aplicado después de que el LLM genera la respuesta (`api_rest.py:1873-1919`):

### Factor 1: Entidades (+0.08 c/u, max +0.30)
Si la respuesta contiene las entidades nombradas en la pregunta (nombres propios, números de norma, años),
el LLM SÍ extrajo datos → boost.

```python
q_entities = set()
# Nombres propios (2+ palabras, sin stopwords)
for n in re.findall(r'\b[A-ZÁÉÍÓÚÑ]{3,}[A-ZÁÉÍÓÚÑ\s]{3,40}?\b', question):
    q_entities.add(clean)
# Números de norma: RM 00275-2021-PRODUCE, DS 184-2020-PCM
for n in re.findall(r'(?:RM|RS|DS|DU|DL)\s*(?:N[°º]\s*)?(\d{2,6}-\d{4}-[A-Z]{2,10})', q):
    q_entities.add(n)
# Años: 2021, 2024
for y in re.findall(r'\b(20\d{2})\b', q):
    q_entities.add(y)

entity_matches = sum(1 for e in q_entities if e in ans.upper())
ent_boost = min(entity_matches * 0.08, 0.30)
```

### Factor 2: Calidad de respuesta (+0.10 a +0.25)
Si la respuesta es sustantiva y estructurada, merece más confianza.

| Condición | Boost |
|-----------|-------|
| `len(ans) > 400` | +0.10 |
| `'FUENTES:' in ans` | +0.05 |
| Montos `S/ XXX` en ans | +0.05 |
| Fechas `15 de enero de 2024` en ans | +0.05 |

### Factor 3: Penalización por negación (-0.15 a -0.40)
Si la respuesta contiene frases derrotistas, penalizar.

```python
neg_patterns = ['no se encontr', 'no se encuentra', 'no se hall', 
                'no hay informaci', 'no se especifica', 'no se proporciona']
neg_hits = sum(1 for p in neg_patterns if p in ans.lower()[:500])
negation_penalty = -0.15 * min(neg_hits, 2)

# Penalización EXTRA si niega la entidad principal de la pregunta
for e in q_entities:
    if re.search(rf'(?:no\s+se\s+encuentr\w+)\s+.*?{re.escape(e)}', ans[:500]):
        negation_penalty -= 0.10
```

## Resultados

| Query | Antes | Después | Δ | Veredicto |
|-------|-------|---------|---|-----------|
| B01 (Directora PRODUCE) | 0.15 | 0.59 | +0.44 | Respuesta correcta boosteada |
| B05 (entidad Beder Camacho) | 0.25 | 0.26 | +0.01 | Incorrecta, NO sube |
| I02 (funciones oficina) | 0.15 | 0.40 | +0.25 | Abstracta pero correcta |
| A03 (cofinanciamiento PNIPA) | 0.47 | 0.61 | +0.15 | Cruza umbral |
| B13 (UISP 2022) | 0.41 | 0.32 | -0.09 | Negación penaliza respuesta parcial |

## Ubicación en código
- `api_rest.py` líneas 1873-1919
- Se ejecuta DESPUÉS de que el LLM genera la respuesta, ANTES de construir el result dict
- Solo aplica si `confidence < 0.85` (no sobre-boostea queries ya confiables)
- Está dentro de un `try/except` para no romper el flujo si hay errores de regex

## Condiciones de activación

```python
if llm_answer and confidence < 0.85:
    # boost code
```

- Solo se activa si hay respuesta del LLM
- Solo si la confianza base es < 0.85 (no modifica queries ya confiables)
- El boost NUNCA reduce la confianza por debajo de 0.05
- El boost NUNCA excede 1.0

## Interacción con otros sistemas

- **Serper**: el boost es post-LLM, así que Serper ya se activó si fue necesario. El boost no afecta la decisión de activar Serper.
- **Graph traversal**: independiente, ambos pueden contribuir.
- **Floor de confianza**: el boost se aplica después del floor y las penalizaciones de defensa.
- **System prompt**: el boost penaliza respuestas con negación ("no se encontró"), reforzando el prompt anti-derrotista.
