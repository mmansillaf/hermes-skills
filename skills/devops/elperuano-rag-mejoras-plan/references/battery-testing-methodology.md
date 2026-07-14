# Metodología de Baterías de Test

## Estructura de una batería

```python
TESTS = [
    ("ID","Pregunta","patron_regex_keywords"),
    # 15 básico + 15 intermedio + 10 avanzado = 40
]
```

## Función de grading

```python
def has_content(answer):
    """Detecta respuestas 'no se encontró'."""
    nocontent = ["no se encontr", "no hay", "no existe", 
                 "lamentablemente", "desafortunadamente"]
    return not any(p in answer[:200].lower() for p in nocontent)

def check_keywords(answer, pattern):
    """Verifica que la respuesta contenga términos esperados."""
    return bool(re.search(pattern, answer, re.IGNORECASE))

def grade_query(conf, content, kw_match, answer):
    if content and kw_match:
        return "PASS"
    elif content != kw_match:
        return "WARN"
    else:
        return "FAIL"
```

## Métricas clave

- **PASS rate:** % de queries con respuesta correcta y keywords
- **Keyword match:** % de queries con vocabulario jurídico relevante (mide comprensión)
- **Confianza promedio:** calidad del scoring interno
- **Web fallback:** % de queries que recurren a búsqueda externa (debe ser bajo)
- **FAIL count:** debe ser 0 — un FAIL es una respuesta "no se encontró" sin keywords

## Ejecución

```bash
cd PeruanoSearchEngine02
python3 /tmp/battery_nuevo_set.py
# Guarda resultados en reports/battery_40q_*.json
```

## Análisis post-batería

1. Revisar FAILs primero — son bugs del pipeline
2. Revisar WARNs — son respuestas parciales o genéricas
3. Comparar confianza por nivel — debe ser consistente
4. Verificar sources (sqlite/qdrant/neo4j/serper) — qué stores se usan
