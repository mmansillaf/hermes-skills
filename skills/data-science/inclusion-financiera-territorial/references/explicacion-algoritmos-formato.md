# Formato de Explicación de Algoritmos — Inclusión Financiera Territorial

**Generado en:** Sesión 2 junio 2026
**Archivos fuente:** Papers/explicacion_algoritmos_completa.md / .txt + 5 diagramas .excalidraw

---

## Formato estructurado para cada algoritmo

Cada uno de los 18 algoritmos del pipeline debe documentarse con esta estructura fija:

```
## N. ALGORITMO

RAZON DE APLICACION:
Por que se usa AQUI y no otro algoritmo.

SUPERVISADO: SI / NO / Post-hoc

FORMULA CLAVE:
[Formula matematica resumida]

ANALOGIA:
[Analogia concreta del dominio CMAC/Peru]

EJEMPLO CONCRETO:
[Datos reales del proyecto: distritos, departamentos, valores numericos]

PRECISION DOCUMENTADA:
[RMSE, AUC, p-valor, u otra metrica del plan]
```

## Clasificación usada

```
NO-ML (6): IPF, Proporcional Simple, IVCD, AHP, Moran's I/LISA, Huff, MCLP
NO SUPERVISADO (1): K-Means + Haversine
SUPERVISADO (9): SAE Fay-Herriot, Ridge, XGBoost, RF, Double ML, LogReg, CART, Boruta + SHAP
```

## Diagramas asociados

Los 5 diagramas Excalidraw se crearon en `Papers/` fuera del skill por contener datos de sesión. Si se regeneran:
- `diagrama_pipeline_completo.excalidraw` — 6 fases + fórmulas + sesgos
- `diagrama_arbol_algoritmos.excalidraw` — árbol supervisado/no-supervisado/no-ML
- `diagrama_sae_shrinkage.excalidraw` — mecanismo SAE Fay-Herriot
- `diagrama_doubleml_causal.excalidraw` — inferencia causal 3 pasos
- `diagrama_4_sesgos_wmd.excalidraw` — 4 sesgos + mitigaciones

Cada diagrama se abre arrastrando el archivo .excalidraw a excalidraw.com

## Archivos generados (Papers/)

| Archivo | Contenido |
|---------|-----------|
| `explicacion_algoritmos_completa.md` | Markdown con formato, tablas, fórmulas |
| `explicacion_algoritmos_completa.txt` | Texto plano sin formato |

## Auto-auditoría

Cada explicación termina con una tabla de auditoría que verifica cada afirmación contra su fuente documental (archivo .md del plan, línea específica). Esto previene alucinaciones y permite trazabilidad.

## Preferencia de entrega del usuario

Cuando se pide una explicación de técnicas/algoritmos en este proyecto:
- Proveer formato .md (con tablas y formato) + .txt (texto plano)
- Acompañar con diagramas visuales (Excalidraw preferido)
- Cada técnica: razón + clasificación + fórmula + analogía + ejemplo + precisión
- Incluir auto-auditoría al final con fuentes verificadas
