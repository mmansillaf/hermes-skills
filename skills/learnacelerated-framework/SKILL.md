---
name: learnacelerated-framework
title: "🧠 Learnacelerated Framework — Aprendizaje Acelerado con IA"
description: "Marco Universal de Aprendizaje Acelerado con IA: 9 módulos para aprender cualquier tema en 20 horas basado en ciencia cognitiva (CLT, metacognición, dificultades deseables, doble codificación)."
category: software-development
version: 1.0.0
author: mmansillaf
triggers:
  - "aprender [tema]"
  - "learning plan for [topic]"
  - "acelerated learning [topic]"
  - "framework aprendizaje [tema]"
  - "learn [topic] fast"
  - "20-hour plan [topic]"
---

## Cuándo usar este skill

El usuario quiere aprender **cualquier tema nuevo** de forma rápida y estructurada, o quiere generar un plan de aprendizaje personalizado usando principios de ciencia cognitiva. Úsalo cuando diga frases como:

- "Quiero aprender [tema] en 20 horas"
- "Créame un plan de aprendizaje para [tema]"
- "Enséñame [tema] desde cero"
- "How do I learn [topic] fast?"
- "Dame un framework para aprender [tema]"

## Cómo usarlo

### Paso 1: Obtén el contexto del usuario

Pregunta o extrae del contexto:
1. **Tema**: ¿Qué quiere aprender exactamente?
2. **Nivel actual**: ¿Principiante absoluto, algo de experiencia, intermedio?
3. **Contexto**: ¿Profesión, proyecto específico, examen?
4. **Tiempo disponible**: ¿Horas por día/semana?
5. **Objetivo concreto**: ¿Qué debería poder hacer al final?

### Paso 2: Ejecuta el Prompt de 9 Módulos

Copia y llena el siguiente prompt con el tema y contexto del usuario. Se ejecuta con cualquier LLM:

```
Actúa como un arquitecto de aprendizaje de clase mundial que combina
principios de ciencia cognitiva, pedagogía, y experiencia práctica en [TEMA].

MI CONTEXTO: [profesión, nivel actual, objetivo concreto y restricciones de tiempo].

Diseña un programa de aprendizaje completo en 9 módulos. Cada módulo
debe ser autocontenido, accionable y construir sobre el anterior.
Usa lenguaje directo, sin relleno. Prioriza profundidad sobre amplitud.

═══════════════════════════════════════════════
MÓDULO 0: DIAGNÓSTICO DEL PUNTO DE PARTIDA
═══════════════════════════════════════════════
Hazme 5 preguntas diagnósticas que revelen:
- Qué creo que sé (detectar ilusiones de competencia)
- Qué modelos mentales incorrectos podría tener
- Mi motivación real (calibrar profundidad necesaria)
- Mi estilo de procesamiento (visual, narrativo, kinestésico)

═══════════════════════════════════════════════
MÓDULO 1: EL PLAN 80/20 RECURSIVO
═══════════════════════════════════════════════
Construye un plan de 20 horas dividido en 10 bloques de 2 horas.
Cada bloque incluye:
1. OBJETIVO MICRO: Habilidad concreta demostrable
2. EL 20% QUE GENERA EL 80%: Justificación
3. RECURSO PRINCIPAL: Recurso específico con timestamp
4. PRÁCTICA ACTIVA: Tarea de producción (mínimo 40 min del bloque)
5. CHECK DE RETENCIÓN (15 min): 3 preguntas de verificación
6. CONEXIÓN FORWARD: Cómo este bloque habilita el siguiente
Incluye calendario de REPETICIÓN ESPACIADA (Día 1, 3, 7, 14, 30).

═══════════════════════════════════════════════
MÓDULO 2: EL MAPA DE UNA PÁGINA (V2)
═══════════════════════════════════════════════
Comprime [TEMA] en un mapa conceptual jerárquico:
- NIVEL 1: 3-5 ideas madre
- NIVEL 2: Sub-conceptos con relaciones (causa, contradice, potencia)
- NIVEL 3: Ejemplo REAL y memorable por sub-concepto
- ZONA DE PELIGRO: 3 errores comunes con antídoto
- FRASE-ANCLA: Una oración que encapsule la esencia

═══════════════════════════════════════════════
MÓDULO 3: EXPLICACIÓN ADAPTATIVA EN 3 CAPAS
═══════════════════════════════════════════════
Explica en tres capas:
CAPA 1 — NIÑO DE 10 AÑOS: Solo analogías físicas y cotidianas. Cero jerga.
CAPA 2 — ADULTO SIN FORMACIÓN: Vocabulario técnico definido en contexto.
CAPA 3 — PRACTICANTE COMPETENTE: Tensiones, debates abiertos, fronteras.
Al final de cada capa: 2 preguntas de comprensión.

═══════════════════════════════════════════════
MÓDULO 4: LA ESCALERA DE COMPETENCIA
═══════════════════════════════════════════════
Mapa [TEMA] en 5 niveles con hitos verificables.
Cada nivel: nombre, demostración, estudio, tiempo estimado, prueba de paso, señal de estancamiento.

═══════════════════════════════════════════════
MÓDULO 5: ANTI-PATRONES Y TRAMPAS COGNITIVAS
═══════════════════════════════════════════════
7 errores más costosos. Cada uno: nombre, señal de alerta, causa raíz, costo real, antídoto, ejemplo.

═══════════════════════════════════════════════
MÓDULO 6: LABORATORIO DE TRANSFERENCIA
═══════════════════════════════════════════════
5 escenarios aplicando principios a campos diferentes + 1 contraejemplo.

═══════════════════════════════════════════════
MÓDULO 7: SISTEMA DE PRÁCTICA DELIBERADA
═══════════════════════════════════════════════
10 ejercicios progresivos con dificultad (1-10), habilidad específica, criterio de éxito, variación.

═══════════════════════════════════════════════
MÓDULO 8: EXAMEN INTEGRADOR FINAL
═══════════════════════════════════════════════
5 preguntas profundas + caso de estudio + pregunta "abogado del diablo" + meta-pregunta. Rúbrica de autoevaluación.
```

### Paso 3: Opcional — Añade el "Mecánico de Emergencia" (para programación)

Cuando el tema es programación específicamente, añade:

```
PILAR ADICIONAL — MECÁNICO DE EMERGENCIA:
1. Lee tracebacks de abajo hacia arriba
2. Usa print() para inspeccionar variables
3. Comenta código para aislar errores
4. Pide a la IA solo pistas, no soluciones completas
```

### Paso 4: Guarda el resultado

Tras ejecutar, guarda el plan generado como `learn-[tema]-plan.md` en la ubicación que el usuario prefiera, e incluye el calendario de repetición espaciada.

## Principios pedagógicos (para referencia)

| Principio | Aplicación en el framework |
|---|---|
| **Carga Cognitiva (CLT)** | Bloques de 2h, checkpoints de 15min, una página de resumen |
| **Metacognición (SRL)** | Módulo 0 (diagnóstico), señales de estancamiento, meta-pregunta final |
| **Dificultades Deseables (Bjork)** | Práctica activa (no consumo pasivo), recuperación activa en checkpoints |
| **Doble Codificación (Paivio)** | Mapa de una página (verbal + visual), analogías, diagramas |
| **Repetición Espaciada (Ebbinghaus)** | Calendario Días 1, 3, 7, 14, 30, 60, 90 |
| **Práctica Deliberada (Ericsson)** | 10 ejercicios progresivos con feedback, borde de zona de confort |

## Archivos del proyecto

### Proyecto fuente (`/mnt/d/PyCode/hermes-skills/learnacelerated/`)
- `learn.txt` — Fundamento teórico (artículo académico)
- `learn1.txt` — Framework 9 módulos + demo Pensamiento Estratégico
- `learn2.txt` — Meta-prompt 7 capas + demo Python
- `_papers_raw.json` — 65+ referencias académicas
- `LEARNACELERATED.md` — Reporte consolidado
- `index.html` — Web app interactiva single-page

### Skill support files (este directorio)
- `templates/index.html` — Web app reusable: despliega el framework completo como app interactiva. Ábrelo directo en el navegador, sin servidor.
- `references/single-page-html-patterns.md` — Patrones de construcción de HTML single-page: IIFE + window._, post-render init, localStorage, y el bug crítico de `</script>` en template literals.

## Pitfalls

- ❌ **No saltar el Módulo 0**: El diagnóstico es esencial para calibrar — sin él la IA asume nivel por defecto y el plan no sirve.
- ❌ **No omitir la práctica activa**: Leer el plan sin hacer los ejercicios produce ilusión de competencia.
- ❌ **No saltar checkpoints**: Son la única forma de verificar retención real vs. familiaridad.
- ❌ **No usar para temas que requieren feedback físico**: Deportes, instrumentos musicales, cirugía — este framework es para conocimiento conceptual y procedimental.
- ❌ **No generar el plan en una sola llamada sin contexto**: Siempre preguntar nivel y objetivo primero.
