---
name: cloudflare-r2-source-hosting
description: Análisis de Cloudflare R2 para hosting de archivos fuente HTML de normas legales. Costos, opciones técnicas, desafíos de mapeo.
---

# Cloudflare R2 — Hosting de Fuentes HTML

## Contexto

Sistema El Peruano RAG con 89,967 archivos HTML (80 MB) de normas legales originales. Se evaluó Cloudflare R2 para hostear los HTMLs y generar links clickeables en las respuestas del API.

## Costos

| Concepto | Cantidad | Límite Free | Costo |
|----------|----------|-------------|-------|
| Almacenamiento | 80 MB (0.08 GB) | 10 GB | **$0** |
| Subida inicial | 1 operación | 1M Class A | **$0** |
| Lecturas (~9K/mes) | 300 clics/día | 10M Class B | **$0** |
| **TOTAL** | | | **$0.00/mes** |

## Desafío Técnico

Los HTMLs están en `data/YYYYMMDD/pagina_X.html`. La tabla `normas` en SQLite no tiene columna `source_html`. El `id` tiene formato `2024-06-20/2299514-4` pero no incluye número de página. Se necesita un mapeo `numero` → `pagina_X.html`.

## Opciones Evaluadas

| Opción | Esfuerzo | Resultado |
|--------|----------|-----------|
| A) Re-ingestar con source_path | Alto | Links precisos |
| B) Servir texto_completo como fuente | Bajo | Páginas generadas, no original |
| C) Búsqueda inversa: HTML por numero | Medio | Links al original sin re-ingestar |
| D) Subir HTMLs + endpoint proxy | Medio | URLs predecibles a R2 |

## Recomendación

Híbrido B+D:
1. Endpoint `/norma/{id}/fuente` con texto_completo (inmediato)
2. Subir HTMLs a R2 con paths predecibles
3. Script de mapeo `numero` → `pagina_X.html` (~20 líneas)
4. Links duales en respuestas: [texto completo] + [ver original en R2]