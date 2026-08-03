# Anti-Detection Playbook (condensado)

Basado en el sistema battle-tested del proyecto claude-linkedin-automation
(27+ días de operación, 0 detecciones, 3.9% engagement rate).
Fuente original: github.com/backpropagation6/claude-linkedin-automation

## Two-Level Architecture

### Level 1: Behavioral Rules (previene flags algorítmicos)

| # | Regla | Implementación |
|---|-------|---------------|
| 1 | **Tool mention limit**: max 2/5 comments mencionan tu servicio/herramienta | Contar menciones por sesión de engagement |
| 2 | **Structure variation**: nunca repetir mismo patrón de comentario consecutivamente | Alternar: opinión → pregunta → dato → experiencia → humor |
| 3 | **Off-topic comment**: al menos 1/5 comments fuera de tu nicho | Comentar en posts de liderazgo, cultura, educación |
| 4 | **Evangelization limit**: max 1 frase promocional por sesión | Una línea como máximo, el resto debe ser valor genuino |
| 5 | **Like-only on agreements**: no extender hilos de acuerdo | Cuando solo concuerdas, un like basta |
| 6 | **Fact-check before asserting**: verificar o reformular como pregunta | Si no estás 100% seguro, haz una pregunta en lugar de afirmar |
| 7 | **High-traffic targeting**: 1+ comment en posts con 200+ reacciones | Mayor visibilidad, menor probabilidad de scrutiny |

### Level 2: Structural Naturalness (previene detección por humanos expertos)

| Tell | Señal | Fix |
|------|-------|-----|
| **Simetría estructural** | Hook → Body (3 bloques) → Cierre | Rotar 6+ estructuras, max 2/semana misma estructura |
| **Paralelismo sintáctico** | Listas con estructura gramatical idéntica | Romper deliberadamente: 1 elemento debe diferir |
| **Informalidad ingenierizada** | Marcadores informales colocados estratégicamente | La informalidad debe emerger de la estructura, no insertarse |
| **Cero imperfecciones** | Sin pensamientos interrumpidos, sin digresiones | Insertar 1 flow-break genuino por post |
| **Casos de estudio cinematográficos** | Setup-payoff perfecto con quotes limpios | Añadir "dirty details": vague memory + hyper-specific detail |
| **Arco emocional predecible** | Todo post: tensión → resolución | 1 post/semana sin resolución, terminando en pregunta abierta |
| **Registro emocional mapeado** | Miércoles = indignación (construida, no reactiva) | Posts emocionales necesitan un trigger real y nombrable |

### 6 Post Structures alternativas (romper el patrón hook-cuerpo-cierre)

1. **Stream of Consciousness** — empieza en medio de un pensamiento, fluye sin estructura rígida
2. **Question Without Answer** — plantea un problema complejo, no lo resuelves, invitas a discutir
3. **Start From the Middle** — abre con el resultado/clímax, luego retrocedes al contexto
4. **Broken List** — lista de items pero 1 está intencionalmente fuera de lugar o incompleto
5. **Micro-post** — 3-4 líneas, un pensamiento, sin elaboración
6. **Response to Something** — reacciona a un evento/thread/noticia, no es contenido original planeado

## Non-Detection Index (NDI)

```
NDI = (L1 × 2 + L2 × 1) / (L1 + L2 + L3) × 10
```

Donde:
- L1 = Level 1 rules cumplidas (0-7)
- L2 = Level 2 tells evitados (0-7)
- L3 = Violaciones activas

| NDI | Estado | Acción |
|-----|--------|--------|
| > 5.0 | Saludable | Continuar monitoreo semanal |
| 3.0 - 5.0 | Atención | Investigar qué está bajando el score |
| < 3.0 | Alerta | Pausar automation 48h, auditar completamente |
| < 4.0 dos semanas | Crítico | Pausar, cambiar estrategia, re-evaluar |

## Pre-Publication Checklist

Antes de publicar cualquier post, verificar 5 de 7:

- [ ] No más de 2 posts seguidos con misma estructura
- [ ] Al menos 1 flow-break o imperfección intencional
- [ ] Sin frases que suenen a template AI ("delve", "leverage",
      "transformative", "game-changer", em dashes excesivos)
- [ ] El registro emocional corresponde al trigger real
- [ ] No es un "case study cinematográfico" sin dirty details
- [ ] Si hay cita legal, está verificada (epistemic gate)
- [ ] Aporta valor sin promocionar explícitamente

## Epistemic Verification Gate (para posts con datos)

Antes de publicar claims factuales:

1. ¿Puedo citar la fuente exacta del dato?
2. ¿El dato es verificable por un tercero?
3. ¿Estoy seguro al 100% o es una interpretación?
4. Si es interpretación, ¿lo señalé como tal?
5. ¿Hay riesgo de que el dato esté desactualizado?
6. ¿El dato podría ser malinterpretado?
7. ¿Pasa el "test del colega experto"? (si un colega del rubro lo lee, ¿coincidiría?)

**7/7** → publicar. **5-6/7** → corregir y publicar. **<5/7** → reescribir.
