---
name: video-marketing
description: "Creación de videos de marketing con IA — selección de herramientas, flujos de trabajo, stacks por presupuesto, y producción de anuncios, demos, contenido social y corporativo usando modelos cloud y locales."
tags: [video, marketing, ai-video, runway, kling, heygen, synthesia, elevenlabs, capcut, davinci, text-to-video, avatar, video-production, production-planning, ad-formats, regulatory-compliance, gap-analysis]
platforms: [linux, macos, windows]
version: 1.2.0
related_skills: [comfyui, songwriting-and-ai-music]
---

# Video Marketing con IA

Ecosistema completo de herramientas de IA para creación y edición de video orientado a marketing digital (anuncios, demos de producto, contenido social, brand films, training corporativo).

## Cuándo usar este skill

- El usuario necesita crear videos promocionales, anuncios, o contenido de marketing
- El usuario pregunta qué herramienta de IA para video usar según su presupuesto
- El usuario quiere automatizar producción de video (script → video terminado)
- El usuario necesita avatares parlantes, voiceovers, o edición con IA
- El usuario compara opciones cloud vs locales para generación de video
- El usuario necesita evaluar si un set de guiones/activos creativos está completo (gap analysis)

## Stack Hermes existente (lo que ya tenemos)

| Recurso | Para qué sirve | Limitación |
|---------|---------------|------------|
| **comfyui** | Generación local de video (Wan 2.2, Hunyuan, AnimateDiff). Setup completo + API. | Solo local, sin audio nativo en Wan, requiere GPU 12GB+. |
| **text_to_speech** (ElevenLabs) | TTS de alta calidad integrado en tool. Voiceovers premium. | Sin clonación ni sincronización labial. |
| **image_generate** (FAL.ai) | FLUX 2 Klein 9B para keyframes/imágenes base. | No genera video. |
| **songwriting-and-ai-music** | Suno prompts para música de fondo sin copyright. | Solo música, no video. |

## Ecosistema de herramientas (actualizado Jul 2026)

### Generación de Video (Core Engines)

| Herramienta | Calidad | Duración | Audio Nativo | Precio (oficial) | Mejor para |
|-------------|---------|----------|-------------|------------------|------------|
| **Runway Gen-4.5** | 9.5/10 | ~18s/clip | Limitado | $12-76/mes (runway.com) | Control creativo, Motion Brush, edición post-generación |
| **Google Veo 3.1** | 9.7/10 | ~8-60s | ✅ Nativo (diálogo+SFX+ambiente) | $0.50-2/seg Vertex AI. Google AI Pro $20/mo limitado. | Fotorrealismo superior, audio unificado |
| **Kling 3.0 Omni** | 9.2/10 | ~3-15s (4K) | ✅ 5 idiomas, lip-sync | Créditos. Incluido en Runway. | Audio+diálogo nativo, multi-shot, EXR export |
| **Seedance 2.0** (ByteDance) | 9.3/10 | ~4-15s 1080p | ✅ Nativo con sync | CapCut Pro incluido. Créditos/API. | Consistencia producto/logo, multi-shot nativo |
| **ComfyUI + Wan 2.2** | 8.5/10 | ~5s | ❌ No | $0 (GPU requerida) | Control total, gratuito a largo plazo |
| **ComfyUI + LTX 2.3** | 7.5/10 | ~5s | ✅ Nativo | $0 (GPU 12GB+ req.) | Único open-source con audio sincronizado |

> ⚠️ **OpenAI Sora 2**: Discontinuado como producto standalone (abril 2026). API se apaga sep 2026. No construir pipelines sobre él.

### Avatares Parlantes (Spokesperson)

| Herramienta | Calidad | Precio (oficial) | Mejor para |
|-------------|---------|------------------|------------|
| **HeyGen** | 9.3/10 | Free (3 vid/mes), Creator $29/mo, Pro $49/mo. **API Pay-As-You-Go desde $5** (heygen.com) | Marketing personalizado, **API robusta con MCP nativo**, automatización con agentes |
| **Synthesia** | 9.5/10 | Free (10 min/mo con marca), Starter $18/mo, Creator $64/mo (yearly) (synthesia.io) | Corporate training, SCORM, interactivo |
| **D-ID** | 8.0/10 | Desde $6/mes | Presupuesto limitado, talking photos |

### HeyGen API — Integración Programática con Agentes

> **HeyGen es el único proveedor de avatares parlantes con MCP Server nativo**, CLI oficial, y Skills diseñadas para agentes de IA (Claude, Codex, Cursor, Hermes). Synthesia y D-ID no ofrecen MCP.

**Precios API (Pay-As-You-Go, saldo separado del plan web, desde $5):**

| Modelo | Por segundo | Por minuto | Video de 1 min |
|--------|------------|------------|----------------|
| **Video Agent** (one-shot desde prompt) | $0.0333/s | $2.00 | **$2.00 USD** |
| **Avatar V — Digital Twin** (máxima calidad) | $0.0667/s | $4.00 | **$4.00 USD** |
| **Video Translation — Precision** | $0.0667/s | $4.00 | $4.00 |
| **Video Translation — Speed** | $0.0333/s | $2.00 | $2.00 |
| **Lipsync — Precision** | $0.0667/s | $4.00 | $4.00 |
| **Voices — Starfish (TTS)** | $0.000667/s | $0.04 | **$0.04 USD** |

**Autenticación:** API Key via header `X-Api-Key` (saldo API). OAuth 2.0 para MCP (usa créditos del plan web).

**Endpoints principales (base URL: `https://api.heygen.com/v3/`):**

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/videos` | POST | Crear video con avatar (control granular) |
| `/video-agents` | POST | Video Agent one-shot desde prompt |
| `/video-agents/{id}/message` | POST | Pedir revisión |
| `/voices/generate-speech` | POST | TTS (Starfish engine) |
| `/avatars` | GET | Listar avatares |
| `/templates/{id}/generate` | POST | Generar desde plantilla |
| `/video-translations` | POST | Traducción (175+ idiomas) |
| `/webhooks` | POST | Configurar webhooks |

**Integración con Hermes (3 opciones):**

1. **curl directo** (`terminal` tool):
```bash
curl -X POST "https://api.heygen.com/v3/videos" \
  -H "X-Api-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"avatar","avatar_id":"ID","engine":{"type":"avatar_v"},"script":"Texto","voice_id":"ID"}'
```

2. **MCP Server nativo**: Conectar al MCP server de HeyGen — herramientas descubribles automáticamente, OAuth sin API key.

3. **Script Python + Webhooks**: Pipeline automatizado (crear → webhook callback → descargar → publicar).

**SLA:** 99.9% uptime, SOC 2 Type II, GDPR. Procesamiento asíncrono (poller o webhooks).

**Casos de Uso por Vertical:**

| Vertical | Ejemplo | Costo estimado |
|----------|---------|----------------|
| **LegalTech** | Video de bienvenida personalizado para cada cliente | $2-4/video |
| **E-commerce** | Demos de producto en batch | $2/video |
| **Training** | Videos corporativos multi-idioma | $2-4/video (por idioma) |
| **Real Estate** | Tours virtuales con agente parlante | $2/min |
| **Healthcare** | Explicaciones de procedimientos para pacientes | $2-4/video |

**Limitaciones:**
- **Photo Avatar** (desde foto) incluido en planes de pago
- **Digital Twin Creation** (desde video real) solo en Enterprise
- Avatares stock predominantemente caucásicos/asiáticos — crear Photo Avatar personalizado para diversidad
- Saldo API separado del plan web

**vs Synthesia (para integración con agentes):**

| Criterio | HeyGen | Synthesia |
|----------|--------|-----------|
| MCP para agentes | ✅ **Nativo** | ❌ No |
| Pay-as-you-go API | ✅ Desde $5 | ❌ Solo suscripción |
| Precio API (1 min) | $2.00-4.00 | ~$3-5 |
| Webhooks | ✅ Sí | ✅ Sí |

### Voz en Off (TTS)

| Herramienta | Calidad | Precio (oficial) |
|-------------|---------|------------------|
| **ElevenLabs** | 9.8/10 | Free 10k créditos/mes, Starter $5/mo (30k créditos), Creator $22/mo ($11 primer mes, 121k créditos), Pro $99/mo (600k créditos). Créditos, no caracteres. |
| **Murf AI** | 9.2/10 | Free (10 min), Basic $19/mo, Pro $26/mo |
| **Noiz.ai** | 9.0/10 | Precio competitivo (voz emocional ultra-rápida) |

### Edición de Video con IA

| Herramienta | Precio | Capacidades Clave |
|-------------|--------|-------------------|
| **CapCut** | **Gratis** (+ Pro ~$8/mes) | Seedance video + Seedream img + Seedmusic audio + TTS + captions + chroma key + overlays + transiciones. **Hub gratuito más completo.** ⚠️ Edición single-layer nativa (overlays permiten multi-capa limitado). Sin watermark en gratis. |
| **DaVinci Resolve** (gratis) | **$0** | Edición no lineal, Cut/Edit/Fusion/Color/Fairlight pages, 100+ Resolve FX, HDR grading, UHD 4K@60fps, 8-bit. **Fusion nodal, color grading profesional, Fairlight DAW. Sin Neural Engine.** ⚠️ Magic Mask, Voice Isolation, Smart Reframe, Super Scale, Speed Warp son **Studio-only**. |
| **DaVinci Resolve Studio** | **$295 pago único** | ✅ Todo lo gratis + **DaVinci AI Neural Engine** (Magic Mask, Voice Isolation, Smart Reframe, Super Scale, Speed Warp, Object Detection, Face Recognition, Auto Color, Color Match), multi-GPU, 10-bit, hasta 32K@120fps, Dolby Vision, DCP, Noise Reduction AI, Film Grain, Optical Blur, text-based editing. |
| **Descript** | $16-50/mo (descript.com) | Edición por transcripción, Underlord AI, Overdub (clonación voz), Studio Sound. Ideal para contenido hablado. |
| **Opus Clip** | Desde $15/mo | Long→short form: extrae clips virales de webinars/podcasts automáticamente. |
| **Adobe Premiere Pro** | $23-55/mes | Generative Extend, Text-Based Editing, Enhance Speech. Profesional. |

### Plataformas Todo-en-Uno (Script→Video)

| Herramienta | Precio | Capacidades |
|-------------|--------|-------------|
| **InVideo AI** | Créditos (invideo.io) | Acceso a Veo 3.1, Kling, Seedance, Sora, Wan como modelos. Script-to-video completo. |
| **Pictory** | Free (3 vid), Starter $19/mo | Blog-to-video, script-to-video, auto-captions |
| **Higgsfield** | Desde ~$15/mo | Multi-modelo (Seedance 2.0 + Kling 3.0 + Veo 3.1 + Wan). Cinema Studio + Marketing Studio. |
| **Creatify** | Desde $29/mo | URL-to-ad: convierte landing page en video ad automáticamente. |

## Plan de Producción Real (presupuesto, timeline, equipo)

**Qué falta en la mayoría de proyectos:** Un plan ejecutable con fechas, costos y roles. Los briefs creativos y guiones no son un plan de producción.

### Presupuesto estimado (Perú, 2026)

| Partida | Rango costo (S/.) | Rango costo ($) |
|---------|-------------------|-----------------|
| Actor/abogado (1 día) | 200-500 | 50-130 |
| Locación (oficina legal, 1 día) | 100-300 | 25-80 |
| Camarógrafo/DOP (1 día) | 500-1,500 | 130-390 |
| Editor (post) | 300-800 | 80-210 |
| Locutor VO (estudio) | 100-300 | 25-80 |
| Motion graphics (UI animada) | 400-1,200 | 105-310 |
| Música (licencia) | 0-200 (Uppbeat free o Suno) | 0-50 |
| **Total rodaje real** | **~1,600-4,800** | **~415-1,250** |

### Timeline

| Fase | Duración | Actividades |
|------|----------|-------------|
| Pre-producción | 3-5 días | Brief final, casting, locación, storyboard aprobado |
| Rodaje | 1-2 días | Filmación live action + captura de UI |
| Post-producción | 3-7 días | Edición, color grading, motion graphics, VO, SFX |
| Revisiones | 2-3 días | Feedback, ajustes, aprobación final |
| Exportación + subida | 1 día | Versiones por plataforma, captions, thumbnails |

### Roles mínimos

- **Director creativo** — supervisa todo, asegura coherencia narrativa
- **Camarógrafo/DOP** — iluminación, composición, planos
- **Editor** — montaje, ritmo, color grading
- **Motion graphics designer** — UI animada, overlays, texto en pantalla
- **Locutor** — VO profesional
- **Productor** — logística, permisos, pagos, catering

## Plan B: Producción sin rodaje

Cuando no hay presupuesto para actor, locación y equipo de filmación. Tres alternativas viables:

### Opción A — Avatar Parlante (HeyGen/Synthesia)
- Seleccionar avatar de aspecto profesional latino
- Generar VO con ElevenLabs (voz peruana neutra)
- Sincronizar labios con avatar
- **Costo: $2-4 por video de 1 minuto**
- **Stack:** HeyGen ($29-49/mes o API payg $5+) + ElevenLabs (free/$5/mes)

### Opción B — Stock Footage + Motion Graphics
- Fuentes: Pexels (gratis), Pixabay (gratis), Envato Elements ($16/mes), Storyblocks ($30/mes)
- Escenas clave: abogado frustrado, escritorio, juzgado, pantalla de computadora
- UI mockup superpuesto como overlay animado
- **Costo: $0-30/mes**
- **Stack:** CapCut ($0) + DaVinci Resolve ($0) + ElevenLabs Free

### Opción C — Text-to-Video Total (Runway/Kling)
- Generar clips cortos (5-15s) de B-roll con IA generativa
- Combinar con UI mockup animado y TTS
- Sin actores ni locación física
- **Costo: $12-28/mes**
- **Stack:** Runway Pro ($28/mes) + ElevenLabs + CapCut

### Matriz de decisión: Rodaje real vs Plan B

| Factor | Rodaje real | Avatar IA | Stock + Motion | Text-to-Video |
|--------|-------------|-----------|----------------|---------------|
| Costo | $$ (alto) | $ (bajo) | $ (bajo) | $$ (medio) |
| Realismo | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| Control creativo | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| Velocidad | Lento (1-2 sem) | Rápido (1-2 días) | Rápido (2-3 días) | Rápido (1-2 días) |
| Flexibilidad cambios | Baja | Alta | Alta | Alta |
| Diferenciación | Alta | Media | Baja (stock común) | Media-alta |

## Guiones por Formato Publicitario

Los guiones para contenido orgánico son distintos a los de anuncios pagados. Cada formato tiene reglas de duración, estructura y CTA diferentes.

| Formato | Duración | Regla de oro | CTA típico |
|---------|----------|-------------|------------|
| **YouTube Pre-roll (skippable)** | 15s, 30s | Hook en 0-3s o pierdes al viewer. Debe funcionar SIN sonido. | "Más info en el link" / "Prueba gratis" |
| **YouTube Bumper (no skippable)** | 6s | Una sola idea. Un solo mensaje. Logo + CTA al final. | "Busca [marca]" |
| **TikTok In-Feed Ad** | 9-15s, 15-30s | Debe sentirse nativo, no como anuncio. Texto grande visible. | "Link en bio" |
| **LinkedIn Sponsored Content** | 30-45s | Más institucional. Descripción es tan importante como el video. | "Agenda una demo" |
| **Meta Ads (IG Reels/FB)** | 15-30s | Vertical, hook visual fuerte, subtítulos obligatorios. | "Click para más info" |

### Reglas para escribir guiones de anuncios B2B profesionales

1. **Pre-roll de 15s**: Un solo dolor → una sola solución → CTA. Sin desarrollo narrativo.
2. **Pre-roll de 30s**: Hook (3s) → problema (5s) → solución (12s) → validación (5s) → CTA (5s).
3. **Bumper de 6s**: [Marca] te ayuda a [beneficio]. Ej: "[Nombre] encuentra jurisprudencia en segundos."
4. **In-Feed (TikTok/IG)**: Los primeros 2 segundos deben tener texto grande + movimiento. Sin intro.
5. **LinkedIn**: Tono colegial, no vendedor. Validación social o dato concreto en primeros 5s.

## Regulaciones y Cumplimiento para Publicidad de Servicios Profesionales

Cuando el producto es una herramienta para abogados, médicos, contadores u otros profesionales regulados, el contenido publicitario debe cumplir con restricciones adicionales.

### Regulaciones relevantes (Perú)

| Regulación | Impacto en el video | Acción requerida |
|------------|--------------------|------------------|
| **Ley de Protección de Datos (Ley 29733)** | Remarketing con píxeles de seguimiento | Aviso de cookies, consentimiento en landing page |
| **Código de Ética del Abogado Peruano** | No prometer resultados garantizados en casos legales | Disclaimer visible |
| **D.S. 115-2025-PCM (Ley IA Perú)** | Clasificación de riesgo del sistema IA | Evaluar nivel de riesgo del sistema, transparencia algorítmica |
| **Indecopi - Publicidad Comercial** | Afirmaciones sobre capacidad del producto | Toda afirmación debe ser verificable |
| **YouTube Política de IA** | Etiquetado de contenido generado con IA | Marcar "Contenido alterado o sintético" si aplica |

### Disclaimer obligatorio sugerido (LegalTech)

> "Esta herramienta es de apoyo a la investigación jurídica. El profesional es responsable de verificar la vigencia y aplicabilidad de las normas y jurisprudencias consultadas. No garantizamos resultados en casos específicos."

### Checklist de cumplimiento pre-publicación
- [ ] Ninguna afirmación promete resultados garantizados ("gana más casos", "siempre gana")
- [ ] Toda afirmación sobre capacidad del producto es verificable
- [ ] Disclaimer de responsabilidad profesional visible
- [ ] Si hay IA generativa en el video, está etiquetada según política de plataforma
- [ ] Los testimonios son reales y autorizados
- [ ] Datos numéricos (precios, cantidad de documentos, etc.) son actuales y verificables

## Análisis de Brecha (Gap Analysis) para Activos Creativos

Metodología para evaluar si un set de documentos/skills cubre todo lo necesario para producir un video publicitario profesional.

### Dimensiones a evaluar

| Dimensión | Pregunta guía | Peso sugerido |
|-----------|--------------|---------------|
| **Narrativa y guion** | ¿Hay al menos un guion completo con estructura hook→problema→solución→beneficio→CTA? | 20% |
| **Storyboard y planos** | ¿Hay descripción visual de tomas, ángulos, movimientos de cámara? | 15% |
| **Estética y colorimetría** | ¿Hay paleta de colores, tipografía, estilo visual definido? | 10% |
| **Psicología del público** | ¿Se ha definido el dolor, deseo y objeción del target? | 10% |
| **Producción real** | ¿Hay presupuesto, timeline, equipo, locación definidos? | 15% |
| **Stack tecnológico** | ¿Hay herramientas concretas seleccionadas para cada fase? | 10% |
| **Plan B** | ¿Hay alternativa si el plan principal falla (sin actor, sin locación)? | 5% |
| **Copy y distribución** | ¿Hay texto de descripción, título, hashtags por plataforma? | 5% |
| **Métricas** | ¿Hay KPIs, plan de A/B testing, optimización? | 5% |
| **Cumplimiento** | ¿Se han considerado regulaciones aplicables? | 5% |

### Proceso de análisis (usado en esta sesión)

1. **Inventariar**: Listar todos los archivos del folder con líneas y contenido
2. **Identificar duplicados**: Marcar archivos con contenido >80% idéntico
3. **Mapear dimensiones**: Para cada archivo, marcar qué dimensiones cubre
4. **Calcular cobertura**: % de dimensiones cubiertas (ponderado por peso)
5. **Priorizar brechas**: Ordenar lo faltante por peso de dimensión × severidad
6. **Generar informe**: Documentar hallazgos, severidad (🔴🟠🟡⚪), y recomendaciones

### Salidas del análisis

| Tipo | Ejemplo |
|------|---------|
| **Inventario** | "10 archivos, ~1,075 líneas totales, 30% duplicados" |
| **Fortalezas** | "Narrativa ✅, Storyboard ✅, Estética ✅" |
| **Brechas** | "Producción real ❌, Stack tecnológico ❌, Plan B ❌" |
| **Acciones** | "Crear plan de producción, decidir stack, escribir guiones por formato" |

## Flujos de Trabajo Recomendados

### Stack Local + Gratis ($0-5/mes)
Para pruebas, prototipos, contenido simple. **Cubre ~72% de necesidades de video marketing.**

```
ComfyUI (Wan 2.2/LTX 2.3) → CapCut (edición) → ElevenLabs Free (TTS) → DaVinci Resolve Free (color final)
```

Limitaciones: GPU requerida (12GB+ VRAM recomendado), sin audio nativo en Wan 2.2.

### Stack Híbrido Recomendado ($39/mes) ★
Para marketing profesional, ads, contenido social — **mejor relación calidad/precio**.

```
Runway Pro ($28/mo) → ElevenLabs Creator ($11/mo) → CapCut ($0) → DaVinci ($0)
```

Runway incluye Gen-4.5 + Kling 3.0 + Seedance 2.0 en una suscripción. Sin dependencia de GPU local.

### Stack Full ($248/mes)
Para producción a escala con avatares y localización multi-idioma.

```
Runway Max ($76/mo) + HeyGen Pro ($49/mo) → ElevenLabs Pro ($99/mo) → Descript Creator ($24/mo)
```

### Stack Enterprise ($500+/mes)
Para equipos grandes con training, cumplimiento, soporte dedicado.

```
Synthesia Enterprise + Runway Custom + ElevenLabs Scale ($330/mo)
```

### Stack Gratis + Local ($0-11/mes) — Evaluación de Cobertura
Para creadores individuales con presupuesto ultra-ajustado. Cubre ~72% de necesidades de video marketing.

| Componente | Peso | Cobertura | Gap |
|------------|------|-----------|-----|
| Edición y montaje | 20% | 19% (DaVinci casi perfecto) | — |
| Audio / TTS / voz | 15% | 13% (ElevenLabs excelente) | Sin AI Voice Isolation |
| Color / acabado visual | 15% | 13% (DaVinci excelente) | Sin Neural Engine AI |
| Efectos / VFX / motion | 10% | 8% (Fusion potente) | Sin Magic Mask |
| Generación AI (video/img/música) | 15% | 10% (CapCut útil) | Sin avatares parlantes, video limitado |
| Flujo rápido para redes sociales | 15% | 12% (CapCut templates) | — |
| Workflow / formatos / exportación | 10% | 7% (limitado a 4K/8-bit/60fps) | Sin >4K, 10-bit, 120fps |
| **TOTAL** | **100%** | **≈ 72%** | **~28% gap** |

**Gaps principales del stack $0:**
- **DaVinci AI Neural Engine es Studio-only ($295)** — no hay Magic Mask, Smart Reframe, Super Scale, Voice Isolation en la versión gratis
- **No hay avatares parlantes** (talking heads) — agregar HeyGen/Synthesia (~$24-30/mo) lo resuelve
- **Exportación limitada** a UHD 4K@60fps 8-bit; Studio necesario para 10-bit/32K/120fps
- **CapCut es single-layer** nativo — edición multi-pista compleja requiere DaVinci

**Primer upgrade recomendado:** DaVinci Resolve Studio ($295 pago único) → sube cobertura a ~82-85%.

## Proceso Típico de Producción (anuncio 15-30s)

1. **Script + brief de marca** — definir hook, beneficio, CTA
2. **Keyframes o clips base** — image-to-video con producto/persona de referencia
3. **Extender clips** — modelo multi-shot o encadenamiento
4. **Voiceover** — ElevenLabs (mejor calidad externa) o nativo (Kling/Veo/Seedance)
5. **Editar** — CapCut/DaVinci: overlays con transparencia, lower-thirds, logo, transiciones, música, captions
6. **Exportar** — 9:16 vertical (social) o 16:9 horizontal (ads/web)
7. **Probar variaciones** — A/B testing de hooks y CTAs

## Reglas de Decisión

| Si necesitas... | Mejor generación | Mejor voz | Mejor edición | Stack ideal |
|----------------|-----------------|-----------|--------------|-------------|
| Anuncios de producto | Runway / Kling 3.0 | ElevenLabs | CapCut / DaVinci | Runway + ElevenLabs + CapCut |
| Video training corporativo | Synthesia | Murf AI | Descript | Synthesia + Murf + Descript |
| Contenido social masivo | Pika / Veo 3.1 | ElevenLabs | Opus Clip + CapCut | Pika + Opus + CapCut |
| Localización multilingüe | HeyGen | ElevenLabs Dubbing | Descript | HeyGen + ElevenLabs |
| Video desde blog/texto | Pictory / InVideo | ElevenLabs | InVideo | Pictory + ElevenLabs |
| Cinematográfico / B-roll | Veo 3.1 / Kling 3.0 | Noiz.ai | DaVinci Resolve | Veo + Noiz + Resolve |
| Presupuesto $0 | CapCut Seedance | CapCut TTS | CapCut solo | CapCut nada más |

## Pitfalls

1. **Sora 2 está muerto como producto** — no construir pipelines sobre él. API se apaga sep 2026.
2. **No existe una sola herramienta para todo** — video IA son 4-5 categorías distintas (generación, avatares, edición, repurposing, voiceover). Forzar un solo tool produce resultados mediocres.
3. **Los modelos generativos fallan en narrativa larga** — son excelentes para B-roll de 5-15s. Fallan en contenido narrativo con personajes consistentes.
4. **Audio nativo es el diferenciador de 2026** — Kling 3.0 Omni, Veo 3.1 y Seedance 2.0 generan audio sincronizado en un pase. La mayoría requiere post-producción de audio.
5. **Clonación de voz requiere consentimiento** — FCC/FTC endureciendo regulaciones. Solo clonar voces con derechos explícitos.
6. **Captions automáticas fallan con jerga técnica** — siempre revisar captions de contenido B2B o con terminología especializada.
7. **GPU limitada (P53 Quadro T1000 4GB)** — Wan 2.2 no corre eficientemente. LTX 2.3 requiere 12GB. Priorizar stack cloud (Runway) para este hardware.
8. **DaVinci Neural Engine es Studio-only** — La versión gratuita NO tiene Magic Mask, Voice Isolation, Smart Reframe, Super Scale, ni Speed Warp. Son exclusivos de la versión Studio ($295 pago único). Para marketing profesional que necesita reencuadre automático o upscaling, presupuestar la licencia Studio.
9. **Stack $0 no llega al 80%** — CapCut + DaVinci Free + ElevenLabs Free (~$0) cubre ~72% de necesidades de video marketing. No hay avatares parlantes, ni IA de aislamiento de voz, ni upscaling. Para cobertura >80%, agregar DaVinci Resolve Studio ($295) o una herramienta de avatares.

## Referencias

| Archivo | Contenido |
|---------|-----------|
| `references/heygen-api-research.md` | Investigación completa de la API de HeyGen: endpoints, precios pay-as-you-go, casos de uso por vertical (LegalTech, e-commerce, training), integración con agentes vía curl/MCP/webhooks, limitaciones, y comparativa vs Synthesia. Basado en sesión de investigación Jul 2026. |
| `references/estudio-completo.md` | Análisis completo del ecosistema con precios verificados, tablas comparativas, ponderación calidad×eficiencia×economía, y stacks recomendados |
| `references/stack-coverage-evaluation.md` | Metodología para evaluar si un stack de herramientas cubre un % objetivo de necesidades de video marketing. Worked example: CapCut+Davinci Free+ElevenLabs → ~72% coverage con gaps documentados. |
| `references/creative-asset-gap-analysis.md` | Metodología y caso de estudio para analizar brechas en activos creativos de video. Dimensiones, ponderación, identificación de duplicados, y priorización de brechas. Worked example: análisis de 10 archivos de guion legal tech. |

## Plantillas

| Archivo | Contenido |
|---------|-----------|
| `templates/ad-bible-b2b-legaltech.md` | Biblia de producción completa para anuncio B2B de 60s. Plantilla reutilizable con storyboard (15 tomas, planos, ángulos), paleta de colores, tipografía, paisaje sonoro, iluminación, checklist de producción y estrategia por plataforma. Campos entre {CORCHETES} para personalizar. Basado en producción real de anuncio LegalTech peruano (Jul 2026). |
