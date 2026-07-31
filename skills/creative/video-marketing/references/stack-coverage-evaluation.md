# Stack Coverage Evaluation — Metodología

## Cuándo usar
El usuario pregunta: "¿Este stack cubre el X% de mis necesidades?" o "Evalúa si estas herramientas juntas son suficientes".

## Metodología: 4 pasos

### 1. Investigar cada herramienta por separado
Usar browser_navigate para webs oficiales + Wikipedia para feature comparison + pricing pages.
- Buscar features GRATIS vs PAID — el gap más importante
- Verificar pricing actual (no asumir)
- Buscar límites: resolución, fps, bit-depth, watermark, créditos, formatos de exportación

### 2. Identificar gaps por categoría funcional
Categorías típicas para video marketing:
- Edición y montaje (cortes, transiciones, capas, multi-track)
- Audio / TTS / voiceover / voice cloning
- Color grading / acabado visual
- Efectos / VFX / motion graphics
- Generación AI (texto-a-video, imagen-a-video, avatares)
- Flujo rápido para redes (templates, captions automáticos)
- Exportación / formatos / resolución

### 3. Ponderar por peso e impacto
Asignar peso a cada categoría según prioridad del usuario (suma = 100%).
Puntuar cada categoría: ¿qué % cubre el stack? → multiplicar peso × cobertura

### 4. Reportar con tabla y veredicto
Formato recomendado:

```
| Componente | Peso | Cobertura |
|------------|------|-----------|
| ... | X% | Y% |
| **TOTAL** | **100%** | **≈ N%** |
```

Siempre incluir:
- Los gaps principales (lo que NO cubre el stack)
- El upgrade más rentable para cerrar el gap
- Opciones de stack alternativas

## Worked Example: CapCut (free) + DaVinci Resolve (free) + ElevenLabs ($5-11/mo)

**Resultado:** ~72% coverage.

**Hallazgo crítico:** DaVinci AI Neural Engine (Magic Mask, Voice Isolation, Smart Reframe, Super Scale, Speed Warp) es **Studio-only ($295)** — la versión gratis NO lo tiene. Esto fue el gap más grande.

**Upgrade más rentable:** DaVinci Resolve Studio ($295 one-time) → sube a ~82-85%.

**Ver análisis completo en:** conversación del 29 Jul 2026 (sesión de evaluación de stack de video marketing).
