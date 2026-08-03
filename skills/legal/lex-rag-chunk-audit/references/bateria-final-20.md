# Batería Final — 20 Consultas

**Fecha:** 2026-05-20 12:42
**Script:** `scripts/bateria_final_20.py`
**Reporte:** `data/bateria_final_20_consolidado.txt`

## Resultados

| Métrica | Valor |
|---------|-------|
| Consultas | 20/20 exitosas |
| Tiempo total | 737.0s (12.3 min) |
| Promedio | 36.8s/consulta |
| Precisión clasificación | 85% (17/20) |
| Crítico 100% | 18/20 |

## Precisión por nivel

| Nivel | Aciertos | Notas |
|-------|----------|-------|
| Simple | 5/5 (100%) | k=4, sin grafo |
| Media | 2/5 (40%) | 3 errores por threshold < 7 palabras |
| Compleja | 7/7 (100%) | k=10-11, graph_depth=2 |
| Estadística | 3/3 (100%) | k=12, graph_depth=2 |

## Crítico de citas

- 18/20 score 100% — sin hallucinationes
- 2 consultas con hallucinationes: números de 5 dígitos residuales
- 0 hallucinationes reales (citas inventadas)

## Estrategias aplicadas

| Estrategia | Veces | Consultas |
|------------|-------|-----------|
| simple k=4 g=N | 8 | S01-S05, M01, M04, E04 (mal clasificada) |
| media k=7-10 g=S1 | 2 | M02, M03 |
| compleja k=10-11 g=S2 | 7 | C01-C05, E04, E05 |
| estadistica k=12 g=S2 | 3 | E01-E03 |

## Trazabilidad generada

```
consultas_guardadas/
├── 20 × .md    (query + respuesta + contexto)
├── 20 × .txt   (idem, completo)
└── 20 × _audit.json  (trazabilidad completa)
```
