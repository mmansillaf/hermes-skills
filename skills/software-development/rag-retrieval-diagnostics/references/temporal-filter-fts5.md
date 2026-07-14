# Temporal Filter: Año+Mes en FTS5

**Problema:** Queries temporales ("normas del año 2020", "normas de setiembre 2024") obtienen confianza alta (0.72-0.76) porque FTS5 matchea "2020" o "2024" en el texto_completo de normas de CUALQUIER año. Ej: "Aprueban Estados Financieros del Año Fiscal 2020" (norma de 2021) matchea "2020".

**Causa raíz:** FTS5 busca tokens en todo el texto_completo sin distinguir entre "menciona el año" y "fue publicada en ese año". Sin filtro temporal, cualquier mención del año produce un falso positivo.

**Fix (02-may-2026, 12 líneas, $0):**

```python
# En search_sqlite(), antes del _fts_query (api_rest.py ~línea 817)
_temporal_filter = ""
_year_m = _re_fts.search(r'\b(20\d{2})\b', question)
if _year_m:
    _year = _year_m.group(1)
    _meses = {'enero':'01','febrero':'02','marzo':'03','abril':'04','mayo':'05',
              'junio':'06','julio':'07','agosto':'08','setiembre':'09','septiembre':'09',
              'octubre':'10','noviembre':'11','diciembre':'12'}
    _mes_num = None
    for _mn, _mc in _meses.items():
        if _mn in question.lower():
            _mes_num = _mc
            break
    if _mes_num:
        _temporal_filter = f" AND n.fecha_publicacion LIKE '{_year}-{_mes_num}%'"
    else:
        _temporal_filter = f" AND n.fecha_publicacion LIKE '{_year}%'"

# En el _fts_query:
WHERE normas_fts MATCH ?{_temporal_filter}
```

**Importante:** No depende del clasificador de query type. Detecta el año directamente de la pregunta con regex. Esto funciona incluso si el clasificador falla la clasificación temporal.

**Resultados (02-may-2026):**

| Query | Sin filtro | Con filtro |
|-------|-----------|------------|
| "normas setiembre 2024" | 18,104 (todo el año) | 1,193 (solo sept) — 15x mejor |
| "designaciones febrero 2024" | 18,104 | 737 — 25x mejor |
| "presupuesto 2027" | 3 FP | 0 ✅ FP eliminado |
| "normas emitidas en 2010" | conf 0.60 FP | conf 0.10 ✅ |
| "normas del año 2020" | conf 0.72 | conf 0.72 (854 normas reales de 2020) |

**Limitación:** "primer trimestre 2024" solo filtra por año, no por trimestre. Para trimestres se requiere lógica adicional (mes 1-3, 4-6, etc.).

**Pitfall:** `import re as _re_fts` en la función oculta el módulo `re`. Usar `_re_fts.search()`, no `re.search()`.
