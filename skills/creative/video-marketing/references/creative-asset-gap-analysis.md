# Análisis de Brecha para Activos Creativos de Video

## Caso de estudio: Buscador Legal con IA (Perú)

Producto: Buscador legal con IA. 90K jurisprudencias, actualización diaria.
Audiencia: Abogados peruanos (TikTok, YouTube Shorts, LinkedIn).

## Metodología aplicada

### 1. Inventario

Se analizaron 10 archivos en carpeta FormatoGuiob/ (~1,075 líneas totales).

| Archivo | Líneas | Contenido | Estado |
|---------|--------|-----------|--------|
| guion.txt | 279 | Prompt integral: 60-90s, objetivo, plataformas, público, estructura 6 segmentos, guion escena por escena, colorimetría, tipografía, storyboard 15 tomas, escenografía, iluminación, checklist, KPIs | ✅ |
| gion1.txt | 59 | Optimización de prompt. Storyboard 35s, 5 segmentos | ⚠️ Typo nombre |
| guion2.txt | 72 | Biblia de Producción: 60s, psicología público, identidad visual, paisaje sonoro, storyboard 7 segmentos | ✅ |
| guion3.txt | 100 | Video corto (22-28s TikTok, 30-45s Shorts) | ✅ |
| guion4.txt | 165 | Meta-prompt framework. 12 secciones | ✅ Framework |
| guion5.txt | 255 | Del Error Fatal a la Confianza Jurídica. Sanciones, alucinaciones, contexto peruano real | ✅ Más avanzado |
| guion6.txt | 34 | Voiceover focus, 38s, estilo Hormozi | ⚠️ Duplicado |
| gion7.txt | ~26KB | Diseño Integral y Meta-Prompting. Análisis ecosistema jurídico peruano | ⚠️ Typo, oculto |
| guion8.txt | 77 | Voiceover focus (casi idéntico a guion6) | 🔴 Duplicado |
| guion9.txt | 34 | Voiceover focus (idéntico a guion6) | 🔴 Duplicado |

### Archivos adicionales (form*, agregados después del análisis inicial)

| Archivo | Líneas | Contenido | Aporte nuevo |
|---------|--------|-----------|-------------|
| form.txt | 97 | "Master Prompt" con prompts Midjourney para imágenes base | ✅ Prompts ejecutables |
| form1.txt | 97 | **IDÉNTICO a form.txt** | 🔴 Duplicado |
| form2.txt | 124 | "Production Bible": Pantone 19-4052, Rack Focus, Whip Pan, variante 15s | ✅ Técnicas cámara, disclaimer legal |
| form3.txt | 96 | Flujo concreto: Midjourney→Photoshop→Runway→ElevenLabs→CapCut. Easter Egg Legal | ✅ Pipeline paso a paso |
| form4.txt | 86 | Prompt 28s exactos, guion sincronizado, restricciones (cero inglés, actor mestizo) | ✅ Restricciones calidad |
| form5.txt | 61 | Blueprint 30-35s, pregunta destino CTA | ⚠️ Menor |
| form6.txt | 121 | **Blueprint Jurídico**: estadísticas (92% sin sonido, 73% retención), 4 actos, producción real, registro lingüístico formal, validación experto | ✅ Más valioso de form* |

### 2. Identificación de duplicados

- guion6 ≈ guion8 ≈ guion9 (mismo contenido voiceover focus)
- form.txt ≈ form1.txt (idénticos)
- form2.txt y form3.txt comparten ~50% con guion2.txt
- ~30% del folder total es redundante
- gion1.txt y gion7.txt tienen typo en el nombre ("gion" vs "guion")

### 3. Mapeo por dimensiones

| Dimensión | Peso | Cubierto por | Brecha |
|-----------|------|-------------|--------|
| Narrativa y guion | 20% | guion.txt, gion1, guion2-5 | — |
| Storyboard y planos | 15% | guion.txt, guion2, guion3 | — |
| Estética y colorimetría | 10% | guion.txt, guion2, guion3 | — |
| Psicología del público | 10% | guion5, gion7 | — |
| Producción real | 15% | — | ❌ Nadie |
| Stack tecnológico | 10% | form3.txt, form4.txt ✅ | Resuelto por form* |
| Plan B | 5% | form.txt, form3, form4 (prompts IA) 🟡 | Parcial (faltan costos) |
| Copy y distribución | 5% | guion.txt (parcial) | 🟡 Incompleto |
| Métricas | 5% | guion.txt (KPIs) | 🟡 Sin plan testing |
| Cumplimiento | 5% | guion5 (parcial) | 🟡 Sin checklist |

### 4. Cobertura calculada

**Cobertura total:** ~65% (ponderado por peso de dimensión) — subió 10% vs análisis inicial por los form*
**Brecha principal:** 35% — concentrado en producción real (15%), copy (5%), métricas (5%) y cumplimiento (5%).

### 5. Priorización de brechas (actualizada)

| Prioridad | Brecha | Peso × Severidad | Acción |
|-----------|--------|-----------------|--------|
| 🔴 Crítico | Producción real (presupuesto, timeline, equipo) | 15% × 3 = 45 | Crear plan de producción |
| 🟠 Alta | Guiones por formato publicitario (6s, 15s, 30s bumper) | 5% × 3 = 15 | Escribir variantes para ads pagados |
| 🟡 Media | Copy y descripción por plataforma | 5% × 2 = 10 | Crear textos optimizados |
| 🟡 Media | Métricas y A/B testing | 5% × 2 = 10 | Definir plan de testing |
| ⚪ Baja | Regulaciones y cumplimiento | 5% × 1 = 5 | Checklist legal |
| ⚪ Baja | Contenido seriado (plan editorial) | 5% × 1 = 5 | Calendario de contenido |

**Resuelto por form*:** Stack tecnológico (✅), Plan B (🟡 parcial), Pipeline IA (✅).

## Lecciones aprendidas para futuros análisis

1. **Siempre contar con un archivo maestro** que organice y referencie a los demás
2. **Nombrar consistentemente**: guion_v1, guion_v2, etc. Sin typos.
3. **Dimensionalizar antes de analizar**: definir las 10 dimensiones primero
4. **Ponderar por criticidad**: no todo peso es igual (producción real pesa más que métricas)
5. **Documentar severidad por color**: 🔴 Crítico / 🟠 Alta / 🟡 Media / ⚪ Baja
6. **Incluir acciones concretas** para cada brecha, no solo diagnosis
7. **Identificar duplicados temprano**: ahorra tiempo de lectura
