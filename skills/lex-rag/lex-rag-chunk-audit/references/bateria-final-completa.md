# Batería Final Completa — 20 Consultas Nuevas

Resultados de la batería final ejecutada el 2026-05-20 con 20 consultas inéditas.

## Resultados globales

```
20/20 exitosas · 858.7s total (14.3 min) · 42.9s promedio
Critic 100%: 19/20 (95%)
Feedback loop activado: 0 consultas
```

## Precisión de clasificación

```
Simple:      5/5 (100%)  k=4, sin grafo          ✅
Media:       5/5 (100%)  k=7-10, grafo somero    ✅
Compleja:    5/5 (100%)  k=10-11, graph_depth=2  ✅
Estadística: 3/5 ( 60%)  2 errores de keywords   🔶
```

## Estrategias aplicadas

| Estrategia | Veces | Queries |
|---|---|---|
| simple k=4 g=N | 5 | S01-S05 |
| media k=7 g=S1 | 4 | M01, M03, M04, M05 |
| compleja k=10 g=S2 | 2 | M02 (arras), C02 (control difuso) |
| compleja k=11 g=S2 | 5 | C01, C03, C04, C05, E05 |
| estadistica k=12 g=S2 | 2 | E03 (sala), E04 (indemnización vs reposición) |
| media k=10 g=S1 | 1 | E01 (demandado más frecuente) — debería ser estadística |
| simple k=5 g=N | 1 | E02 (materia más litigada) — debería ser estadística |

## Crítico

- 19/20 score 100% ✅
- 1/20 score 71% (E02, "materia más litigada" — 2 hallucinated por números de 6 dígitos malinterpretados)

## Problemas detectados y corregidos

1. **E01 clasificado como "media"**: "mas demandada" sin tilde no estaba en keywords. Añadido.
2. **E02 clasificado como "simple"**: "mas litigada" sin tilde no estaba en keywords. Añadido.

## Archivos generados

```
data/bateria_final_completa.txt            → Reporte consolidado (565 líneas)
consultas_guardadas/20*_audit.json        → 20 audits individuales
consultas_guardadas/20*.md                → 20 respuestas markdown
consultas_guardadas/20*.txt               → 20 respuestas texto plano
```

## Tiempos por nivel

| Nivel | Tiempo | Promedio |
|---|---|---|
| Simple | 192.8s | 38.6s |
| Media | 222.4s | 44.5s |
| Compleja | 265.5s | 53.1s |
| Estadística | 178.0s | 35.6s |
