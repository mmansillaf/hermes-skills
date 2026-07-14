# Batería 100 Preguntas — Resultados 02-may-2026

## Resumen

| Métrica | Valor |
|---------|-------|
| Fecha | 2026-05-02 17:36 |
| Total preguntas | 100 |
| ✅ PASS | 73 (73.0%) |
| ❌ FAIL | 6 (6.0%) |
| ⚠️ WARN | 21 (21.0%) |
| 🔸 BORDE | 0 |
| Confianza promedio | 0.5068 |
| Score promedio | 3.89/5 |
| Tiempo total | 330s |
| Tiempo/query | 3.0s |
| Falsos positivos | 6 |
| Falsos negativos | 21 |
| Frases prohibidas | 13 |

## Fuentes activas

| Fuente | Queries | % |
|--------|---------|---|
| SQLite FTS5 | 100 | 100% |
| Qdrant | 69 | 69% |
| Neo4j entity | 48 | 48% |
| Neo4j graph | 0 | 0% (BUG — corregido post-test) |
| Web fallback | 0 | 0% |

## Por categoría

| Cat | Descripción | Tipo | PASS | FAIL | WARN | Avg Conf | Avg Score |
|-----|-------------|------|------|------|------|----------|-----------|
| A | IDs Exactos | OK | 10/10 | 0 | 0 | 0.902 | 4.5/5 |
| B | Cruzadas Semánticas | OK | 6/8 | 0 | 2 | 0.588 | 4.4/5 |
| C | Temporales | OK | 8/10 | 0 | 2 | 0.659 | 4.5/5 |
| D | Emisor + Acción | OK | 5/10 | 0 | 5 | 0.506 | 3.5/5 |
| E | Modificaciones | OK | 5/8 | 0 | 3 | 0.552 | 3.9/5 |
| F | Acrónimos | OK | 9/10 | 0 | 1 | 0.700 | 4.8/5 |
| G | Casos Borde | OK | 5/8 | 0 | 3 | 0.549 | 3.6/5 |
| H | Narrativas | OK | 1/6 | 0 | 5 | 0.315 | 3.0/5 |
| I | Temas Inexistentes | TRAMPA | 8/8 | 0 | 0 | 0.113 | 4.1/5 |
| J | IDs Falsos | TRAMPA | 5/6 | 1 | 0 | 0.208 | 3.5/5 |
| K | Fuera de Rango | TRAMPA | 2/6 | 4 | 0 | 0.552 | 2.0/5 |
| L | Combinaciones Imposibles | TRAMPA | 4/5 | 1 | 0 | 0.320 | 3.4/5 |
| M | Jailbreak | TRAMPA | 5/5 | 0 | 0 | 0.110 | 4.0/5 |

## Falsos positivos (6)

Todos con confianza ≥0.75 sin web fallback:
- DS 501-2028-SA presupuesto (conf=0.75)
- normas del año 2020 (conf=0.76)
- decretos supremos del año 2019 (conf=0.75)
- presupuesto general de la república 2027 (conf=0.75)
- normas emitidas en 2010 sobre medio ambiente (conf=0.75)
- arrendamiento de naves espaciales en Perú (conf=0.75)

## Problemas identificados (y corregidos post-test)

1. **Neo4j graph traversal en 0%** — bug triple (seen_ids/indentación/clasificador). Corregido.
2. **Frases prohibidas (13)** — system prompt con instrucciones derrotistas. Corregido.
3. **Cat H Narrativas (1/6)** — LLM 8B débil para síntesis. Parcialmente mitigado con graph traversal.
4. **Cat K Fuera de rango (2/6)** — floor de confianza 0.75 deja pasar falsos positivos. Recomendación: bajar a 0.60.

## Archivos

- MD: `reports/informe_100_queries_20260502_173609.md`
- HTML: `reports/informe_100_queries_20260502_173609.html`
- TXT: `reports/informe_100_queries_20260502_173609.txt`
- JSON: `reports/raw_100_queries_20260502_173609.json`
