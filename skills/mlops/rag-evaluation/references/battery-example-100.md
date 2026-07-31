# Example: 100-Query Battery for Criminal Law RAG (Corte Suprema Peruana)

This battery tests a legal RAG corpus containing ~23K Corte Suprema criminal cases (files 1014870-1014980.html). Questions are organized by complexity level.

## Query Design Pattern

```python
QUERIES = [
    # === NIVEL BASICO (hechos literales) ===
    ("B01","Cual es el numero de expediente del caso en el que se anula la sentencia absolutoria de Edilberto Dionisio Moya por corrupcion de funcionarios"),
    ("B05","Cuantos anos de pena privativa de libertad se impusieron inicialmente a Wilder Aguirre Caldas por trafico ilicito de drogas"),

    # === NIVEL INTERMEDIO (valoracion probatoria) ===
    ("I36","Por que la Corte Suprema considera insuficientes las declaraciones testimoniales de descargo en el caso Moya para mantener la absolucion"),
    ("I46","Por que se reclasifica a Luis Americo Ayala Gonzales de coautor a complice secundario"),

    # === NIVEL AVANZADO (comparativo/doctrina) ===
    ("A61","Compare las causales de nulidad en los casos Moya y Quispe Rojas en que se diferencian las deficiencias probatorias que motivan la anulacion en cada uno"),
    ("A71","Por que en el caso Moya se anula una sentencia absolutoria por insuficiencia probatoria mientras que en el caso Zavaleta Rodriguez se confirma otra absolutoria ante una sindicacion contradictoria"),
]
```

## File Reference

The complete 100-query battery is at:
- `scripts/run_100_preguntas.py` — executable script
- `data/prueba_100_preguntas_20260519.txt` — results output

## Key Metrics Captured

| Metric | How |
|--------|-----|
| Escenario (A/B/WEB) | Detected from response content |
| Tiempo por consulta | time.time() before/after |
| Rutas a archivos | resp.count("Jurisprudencia/") |
| Response length | Lines or chars after cleanup |

## Expected Results Profile

| Corpus quality | Escenario A rate |
|----------------|------------------|
| Well-covered topics (constitucional, laboral general) | 60-80% |
| Niche topics (JNE, municipal specific) | 10-30% |
| Recent events (2025 laws) | 0% (router should activate WEB) |
