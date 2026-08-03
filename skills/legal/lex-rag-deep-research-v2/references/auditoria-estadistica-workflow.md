# Auditoría de Trabajos Estadísticos - Metodología

## Cuándo usar
Cuando el usuario pida revisar, auditar, evaluar o mejorar un trabajo de investigación estadística, análisis de datos, modelos ML, o estudio cuantitativo.

## Pipeline de auditoría (5 fases)

### Fase 1: Mapeo del proyecto
1. Leer plan de investigación (si existe)
2. Identificar fuentes de datos y métodos usados
3. Identificar variable objetivo (target) y predictores
4. Listar todos los archivos relevantes (scripts, datasets, informes)

### Fase 2: Revisión de datos
- Verificar cobertura real vs reportada (contar nulos manualmente)
- Detectar outliers y evaluar si son reales o errores
- Verificar correlaciones entre variables simuladas y sus predictores
- Identificar variables eliminadas por colinealidad

### Fase 3: Revisión de modelos
| Modelo | Qué revisar | Señales de alerta |
|---|---|---|
| OLS | R² train vs test, ratio obs/predictores | R² train > 0.95 con n<50 y p>5 |
| Ridge/Lasso | Valor de alpha, R² | No reportar coeff sin intervalos |
| Random Forest | R² CV, importancia de variables | Importancia >90% en 1 variable |
| PCA | Varianza explicada, cargas factoriales | PC1 > 60% (1 dimensión domina) |
| K-Means | Silhouette score, interpretación clusters | Silhouette < 0.3 |

### Fase 4: Detección de inconsistencias
Buscar discrepancias entre:
- Informe técnico vs datos reales (correlaciones, nulos)
- Diccionario de datos vs dataset real (columnas, tipos)
- Código vs documentación (scripts que no se ejecutaron)

### Fase 5: Recomendaciones priorizadas
Clasificar hallazgos en:
- 🔴 CRÍTICO: Bloqueante para publicación
- 🟡 ALTA: Mejora significativa
- ⚪ MEDIA: Mejora moderada
- 🔵 BAJA: Cosmética/documental

## Formato de entrega
Siempre guardar como `.md` (para lectura) y `.txt` (para portabilidad).
Incluir: puntaje global, tabla de valoración por dimensión, análisis por componente, inconsistencias detalladas, recomendaciones priorizadas por fase, y conclusión final.

## Ejemplo de tabla de puntuación
```
| Dimensión | Puntaje | Nivel |
|---|---|---|
| Documentación | 92/100 | Excelente |
| Pipeline datos | 85/100 | Muy bueno |
| Modelos ML | 65/100 | Bueno |
| Rigor estadístico | 68/100 | Bueno |
| Consistencia interna | 60/100 | Mejorable |
| **Global** | **73/100** | **Bueno** |
```

## Checklist de validación para n<30
- [ ] LOOCV implementado (no 80/20 simple)
- [ ] Ridge/Lasso considerado (regularización)
- [ ] PLS considerado (Partial Least Squares)
- [ ] Intervalos de confianza reportados
- [ ] Outliers analizados (no eliminados sin justificación)
- [ ] Variables simuladas con correlación controlada (<0.90 con predictoras)
- [ ] Limitaciones de tamaño muestral documentadas
