# Fixes de Confianza para Queries Analiticas Largas — 01-may-2026

## Diagnostico

Bateria 50q SET1: queries avanzadas con respuestas excelentes (1400+ chars, analisis constitucional) reportaban confianza 0.10-0.23. Queries basicas fallando reportaban 0.75. Confianza INVERTIDA.

## Causa raiz (4 bugs simultaneos)

1. Floor 0.75 demasiado permisivo: _has_real_overlap -> 0.75 se activaba con ratio>=0.5. I30 (vacia) y B01 (correcta) recibian el mismo floor.
2. Post-hoc bypass en conf=0.75: confidence < 0.75 (estricto). Con floor=0.75 exacto, la negacion no se penalizaba.
3. Capa 4 sobre-penaliza: db_ratio < 0.40 muy alto. db.execute fallaba silenciosamente (db no inicializado).
4. debug_conf vacio: Imposible diagnosticar sin monkey-patching.

## Traza quirurgica (I30, B15, A38)

Todas las queries tienen base identica (0.800 = 0.55+0.15+0.10). El unico diferenciador es fp_penalty y el floor.

## Post-fix

| Query | Antes | Despues | Cambio |
|-------|-------|---------|--------|
| I30 (FP) | 0.75 | 0.50 | Corregido |
| B15 (FN) | 0.28 | 0.35 | Mejorado |
| A38 (FN) | 0.23 | 0.61 | Corregido |
| B01 (OK) | 0.75 | 0.75 | Protegido |
