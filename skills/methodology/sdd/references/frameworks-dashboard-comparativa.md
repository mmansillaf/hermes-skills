# Comparativa: Frameworks Python para Dashboards / Data Apps

*Investigacion realizada en junio 2026 para elegir framework de dashboard para sistema Intake CRM.*

## Candidatos Evaluados

| Framework | Version | RAM tipica | React/JS? | Curva | Estado | Ideal para |
|-----------|---------|-----------|-----------|-------|--------|------------|
| **Streamlit** | 1.40+ | ~150MB | No (rerun total) | Baja | Produccion | Prototipos rapidos, dashboards simples |
| **Gradio** | 5.x | ~120MB | No (Blocks API) | Baja | Produccion | Demos ML/IA, chatbots |
| **Shiny for Python** | 1.10+ | ~200MB | No (reactividad selectiva) | Media | Produccion | Dashboards reactivos, apps multi-pagina |
| **Taipy** | 4.x | ~250MB | No | Media | Beta-Prod | Dashboards + pipelines de datos |
| **Panel** | 1.9+ | ~180MB | Opcional (ipywidgets) | Media-Alta | Produccion | Dashboards cientificos, ecosistema HoloViz |
| **Solara** | 1.40+ | ~200MB | React-style (puro Python) | Media-Alta | Estable | Apps grandes, estado complejo |
| **Plotly Dash** | 2.18+ | ~250MB | Si (callbacks React) | Alta | Produccion | Dashboards enterprise, graficos complejos |

## Criterios de Evaluacion para Proyectos de Gestion/CRM

Para un sistema de gestion (formularios + tabla de datos + filtros + pipeline de estados), los criterios clave son:

1. **Reactividad eficiente** — evitar rerun total del script en cada interaccion (mata rendimiento con DB queries)
2. **Multi-pagina / routing nativo** — leads, detalle, config, reportes sin hacks
3. **Formularios y CRUD nativo** — inputs, selects, validacion, tablas editables
4. **Ligereza** — RAM, dependencias, facilidad de despliegue on-premise
5. **Comunidad y madurez** — errores conocidos, documentacion, ejemplos

## Puntuacion Ponderada para CRM/Intake

| Criterio | Peso | Streamlit | Gradio | Shiny | Taipy | Panel | Solara | Dash |
|----------|------|-----------|--------|-------|-------|-------|--------|------|
| Simplicidad inicial | 20% | 10 | 9 | 8 | 6 | 5 | 4 | 4 |
| Reactividad eficiente | 20% | 3 | 5 | 9 | 7 | 8 | 9 | 8 |
| Multi-pagina / routing | 15% | 5 | 3 | 9 | 6 | 5 | 7 | 8 |
| Formularios + CRUD nativo | 20% | 7 | 5 | 8 | 7 | 4 | 6 | 7 |
| Comunidad / docs / madurez | 15% | 9 | 8 | 7 | 4 | 7 | 5 | 9 |
| Ligereza (RAM, deps) | 10% | 8 | 9 | 7 | 6 | 7 | 6 | 5 |

| **PUNTAJE PONDERADO** | | **6.95** | **6.40** | **8.10** | **6.10** | **5.90** | **6.15** | **6.85** |

## Conclusion

**Shiny for Python** es la mejor opcion para sistemas de gestion/CRM por:
- Reactividad selectiva (solo re-ejecuta fragmento cambiado, no todo)
- API Express para prototipado rapido + Core API para escalar
- Multi-pagina nativa sin hacks
- 10+ anos de madurez del ecosistema Shiny (R + Python)
- Auth y sesiones built-in
- Funciona bien en VPS de 1GB RAM

**Usar Gradio** solo si el caso de uso principal es chatbot/demo ML.
**Usar Dash** solo si ya tienes equipo con experiencia en Plotly + React y necesitas dashboards analiticos avanzados.
**Evitar Streamlit** en produccion con DB — el rerun total degrada severamente con consultas a DB.
