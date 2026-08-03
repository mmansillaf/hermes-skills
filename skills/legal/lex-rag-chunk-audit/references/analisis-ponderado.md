# Metodología de Análisis Ponderado para Decisiones Técnicas

Usada para evaluar opciones del Retrieval Strategist (Fase 2 del plan multi-agente).

## Proceso

### 1. Definir baseline
Ejecutar N consultas representativas con la configuración actual. Medir:
- Precisión de clasificación
- LLM calls/query
- Tiempo de respuesta
- Costo estimado

### 2. Listar opciones
Cada opción debe tener: nombre, descripción, esfuerzo, costo, precisión estimada.

### 3. Ponderar criterios
Asignar pesos a cada criterio (total = 1.0):

```python
weights = {
    "precision": 0.35,  # impacto en calidad de respuesta
    "costo": 0.20,      # costo monetario de LLM
    "esfuerzo": 0.15,   # tiempo de implementación
    "latencia": 0.15,   # velocidad de respuesta
    "mantenimiento": 0.15  # facilidad de mantener
}
```

### 4. Puntuar cada opción (1-5, 5=mejor)
Para cada criterio, asignar puntaje:

```python
scores = {
    "Opción A: Prompt Engineering": {
        "precision": 3, "costo": 5, "esfuerzo": 5,
        "latencia": 5, "mantenimiento": 4
    },
    ...
}
```

### 5. Calcular weighted score
```python
weighted = sum(scores[opt][c] * weights[c] for c in criteria)
```

### 6. Recomendar
La opción con mayor weighted score gana. Documentar trade-offs.

## Cuándo usar
- Decisiones con múltiples alternativas y criterios en conflicto
- Cuando el equipo necesita justificación objetiva
- Para evitar sesgo por "la opción más obvia" o "la más reciente"

## Template de reporte
Ver `data/analisis_strategist.txt` para un ejemplo completo.
