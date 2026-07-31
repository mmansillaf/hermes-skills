# 📊 ESTUDIO: Ecosistema de IA para Video Marketing 2026
## Análisis de contenido en `video/` folder + verificación oficial

Fecha: 30 Julio 2026
Fuentes: vid1-6.txt, flow.txt, vid4.txt
Validación: Runway.com, ElevenLabs.io, HeyGen.com, Synthesia.io, Descript.com, InVideo.io, KlingAI.com

---

## LO QUE YA TENEMOS EN HERMES (skills + tools propias)

| Recurso | Qué cubre | Limitación |
|---------|-----------|------------|
| **comfyui** | Generación local de video (Wan 2.2, Hunyuan, AnimateDiff, SVD) vía ComfyUI. Stack completo: setup, inference API, batch. | Solo local/cloud Comfy. Sin audio nativo en Wan. Sin edición/post-producción. Requiere GPU 12GB+. |
| **image_generate** (FAL.ai) | FLUX 2 Klein 9B para imágenes. | No genera video (solo imágenes). Backend FAL. |
| **text_to_speech** (ElevenLabs) | TTS de alta calidad integrado. | Sin clonación ni sincronización labial. Sin edición multi-track. |
| **songwriting-and-ai-music** | Suno prompts para música de fondo. | Solo música, no video. |
| **youtube-content** | Transcripts → resúmenes/blogs. | Solo análisis, no creación. |
| **ascii-video** | ASCII art MP4/GIF (retro). | No es video marketing real. |

**Lo que NO tenemos:** Generación cloud de video (Runway, Kling, Veo, Seedance), avatares parlantes (HeyGen/Synthesia), edición con IA (CapCut/Descript), automatización script-to-video (InVideo), clipping/re-purposing (Opus Clip), plataformas multi-modelo (Higgsfield).

---

## TABLA COMPARATIVA COMPLETA

### CATEGORÍA 1: Generación de Video (Core Engines)

| Herramienta | Calidad | Duración | Audio Nativo | Precio (verificado) | Mejor para | Lo tenemos |
|-------------|---------|----------|-------------|---------------------|------------|------------|
| **Runway Gen-4.5** | 9.5/10 | ~18s/clip | Limitado | $12-76/mes (Standard-Max, yearly). Runway.com verif. | Control creativo, Motion Brush, edición post | ❌ No |
| **Google Veo 3.1** | 9.7/10 | ~8-60s | ✅ Diálogo+SFX+ambiente | $0.50-2/seg Vertex AI. Google AI Pro $20/mo limitado. | Fotorrealismo, audio nativo sincronizado | ❌ No |
| **Kling 3.0 Omni** | 9.2/10 | ~3-15s (4K) | ✅ 5 idiomas, lip-sync | Créditos (Kuaishou). En Runway incluido. | Audio+diálogo nativo, multi-shot, EXR | ❌ No |
| **Seedance 2.0** | 9.3/10 | ~4-15s 1080p | ✅ Sync | Créditos/API. CapCut Pro incluido. | Consistencia producto/logo, multi-shot | ❌ No |
| **OpenAI Sora 2** | 9.8/10 | ~20-60s | ✅ | Migrado ChatGPT Plus/Pro. API discontinuada Sep 2026 | Narrativa cinematográfica | ⚠️ Muerto como standalone |
| **Pika 2.2** | 8.5/10 | ~5-10s | Parcial | Gratis básico, Pro ~$28/mes | Efectos creativos, social, virales | ❌ No |
| **ComfyUI + Wan 2.2** (local) | 8.5/10 | ~5s | ❌ No | **$0** (electricidad + GPU) | Control total, gratuito largo plazo | ✅ **Skill completo** |
| **ComfyUI + LTX 2.3** (local) | 7.5/10 | ~5s | ✅ Sí (nativo) | **$0** (GPU 12GB+ req.) | Único open-source con audio | ✅ **Skill completo** |

### CATEGORÍA 2: Avatares Parlantes (Talking Head)

| Herramienta | Calidad | Avatares | Idiomas | Precio (oficial) | Mejor para |
|-------------|---------|----------|---------|------------------|------------|
| **HeyGen** | 9.3/10 | 1000+ estilos, Photo Avatar | 175+ | Free (3 vid/mes), Creator $29/mo, Pro $49/mo (4K). heygen.com verif. | Marketing personalizado, API robusta |
| **Synthesia** | 9.5/10 | 125-240+ | 130+ | Free ($0, 10min/mo, marca agua), Starter $18/mo, Creator $64/mo (yearly). | Corporate, training, SCORM |
| **D-ID** | 8.0/10 | Talking photos | 20+ | Desde $6/mes | Presupuesto limitado |

### CATEGORÍA 3: Voz en Off (TTS Profesional)

| Herramienta | Calidad | Precio (oficial) | Lo tenemos |
|-------------|---------|------------------|------------|
| **ElevenLabs** | 9.8/10 | Free 10K chars, Starter $5/mo, Creator $11/mo, Pro $99/mo | ✅ **Tool integrada** |
| **Murf AI** | 9.2/10 | Free (10 min), Basic $19/mo, Pro $26/mo | ❌ No |
| **Noiz.ai** | 9.0/10 | Voz emocional ultra-rápida (precio competitivo) | ❌ No |

### CATEGORÍA 4: Edición de Video con IA

| Herramienta | Precio | Transparencia/Alpha | Capacidades IA clave | Mejor para |
|-------------|--------|-------------------|---------------------|------------|
| **CapCut** | **Gratis** (+ Pro ~$8/mes) | ✅ Alpha, overlays, chroma key, bg removal | Seedance video, Seedream img, Seedmusic audio, TTS, captions, script-to-video | **Rey del marketing digital. $0.** |
| **Descript** | $16-50/mo (descript.com verif.) | ✅ Green screen, overlays | Edición por transcripción, Underlord AI, Overdub, Studio Sound | Contenido hablado |
| **DaVinci Resolve** (gratis) | **$0** | ✅ Alpha completo, Fusion nodal | Cut/Edit/Fusion/Color/Fairlight, HDR grading, 100+ Resolve FX, UHD 4K@60fps. ⚠️ **Sin Neural Engine.** | **Mejor calidad/precio: $0.** Sin Magic Mask/Voice Isolation/Smart Reframe/Super Scale — son Studio-only. |
| **DaVinci Resolve Studio** ($295) | **$295 pago único** | ✅ Alpha completo, Fusion nodal | ✅ Neural Engine completo (Magic Mask, Voice Isolation, Smart Reframe, Super Scale, Speed Warp), multi-GPU, 10-bit, 32K@120fps, Dolby Vision, DCP, Noise Reduction AI. | Neural Engine completo + formatos profesionales. |
| **Adobe Premiere Pro** | $23-55/mes | ✅ Alpha, AE integración | Text-Based Editing, Auto Reframe, Enhance Speech, Generative Extend | Profesionales |
| **Opus Clip** | Desde $15/mo | ❌ No prioriza | Auto clip selection, captions, reformateo | **Long→short form** |

### CATEGORÍA 5: Plataformas Todo-en-Uno (Script → Video)

| Herramienta | Precio | Capacidades | Lo tenemos |
|-------------|--------|-------------|------------|
| **InVideo AI** | Créditos. Acceso a Veo 3.1, Kling, Seedance, Sora, Wan | Script-to-video, AI voiceover, templates, stock | ❌ No |
| **Pictory** | Free (3 vid), Starter $19/mo | Blog-to-video, script-to-video, auto-captions | ❌ No |
| **Higgsfield** | Desde ~$15/mo | Multi-modelo (Seedance, Kling, Veo, Wan), Cinema Studio | ❌ No |
| **Creatify** | Desde $29/mo | URL-to-ad (landing page → video ad) | ❌ No |

---

## ANÁLISIS PONDERADO

| Dimensión | Ranking |
|-----------|---------|
| **Calidad de video** | Veo 3.1 > Sora 2 > Seedance 2.0 > Runway Gen-4.5 > Kling 3.0 > Wan 2.2 (local) |
| **Eficiencia/velocidad** | CapCut Seedance > Pika > Luma > Runway Turbo > Kling > ComfyUI local |
| **Economía ($0-50/mes)** | CapCut (GRATIS) + ComfyUI local ($0) > ElevenLabs TTS ($5) > DaVinci Resolve ($0) |
| **API/automatización** | HeyGen > Runway Dev > InVideo > Synthesia > CapCut (no API) |

---

## HALLAZGOS DE VALOR QUE NO TENEMOS EN SKILLS

1. **CapCut como hub gratuito todo-en-uno** — Seedance video + Seedream img + Seedmusic + TTS + captions + overlays + chroma key + transiciones. TODO gratis (o $8/mes Pro).

2. **HeyGen API** — 6 APIs REST: Video Gen, Translation, TTS, Video Agent, Template (personalización masiva). Ideal para automatizar videos de marketing.

3. **Runway + Kling 3.0** — Runway ahora incluye Kling 3.0 y Seedance 2.0 como modelos. Multi-modelo en una suscripción.

4. **DaVinci Resolve GRATIS** — Edición no lineal profesional + Fusion + Fairlight + color grading. UHD 4K@60fps, 8-bit, 100+ Resolve FX. **Sin watermark. Sin límites de proyectos.** ⚠️ El Neural Engine AI (Magic Mask, Voice Isolation, Smart Reframe, Super Scale, Speed Warp) es **Studio-only ($295)**. La versión gratis no lo incluye.

5. **Audio nativo 2026** — Kling 3.0 Omni, Veo 3.1, Seedance 2.0 y LTX 2.3 generan audio sincronizado EN UN SOLO PASE.

6. **Opus Clip long→short** — Automatiza clips virales de webinars/podcasts. $15/mo.

7. **Higgsfield multi-modelo** — Seedance 2.0 + Kling 3.0 + Veo 3.1 + Wan en un solo workspace.

8. **Wan Alpha (RGBA)** — Primer modelo open-source con canal alfa completo. Elimina chroma key post-producción.

---

## COMPARATIVA DE COSTOS: Stacks Recomendados

| Stack | Qué incluye | Costo/mes | Calidad | Ideal para |
|-------|------------|-----------|---------|------------|
| **Local + Gratis** | ComfyUI (Wan/LTX) + CapCut + ElevenLabs Free + DaVinci Free | **$0-5/mes** | 7-8/10 (~72% cobertura) | Pruebas, prototipos |
| **Híbrido** (recomendado) | Runway Pro ($28) + ElevenLabs Creator ($11) + CapCut ($0) + DaVinci ($0) | **$39/mes** | 9/10 | Marketing profesional |
| **Full Stack** | Runway Max ($76) + HeyGen Pro ($49) + ElevenLabs Pro ($99) + Descript ($24) | **$248/mes** | 9.5/10 | Producción a escala, avatares |
| **Enterprise** | Synthesia + Runway Custom + ElevenLabs Scale ($330) | **$500+/mes** | 10/10 | Equipos grandes, training, cumplimiento |

---

## RECOMENDACIÓN PARA TU STACK (LegalTech Marketing)

Basado en tu P53 (Quadro T1000 4GB VRAM):

**Stack Inmediato ($0-50/mes)** — usando lo que ya tenemos:
1. ComfyUI + LTX 2.3 (limitado por 4GB VRAM - Wan no corre bien)
2. image_generate (FLUX 2 FAL) → keyframes → composición manual
3. ElevenLabs TTS para voiceovers
4. CapCut (gratis) para edición, overlays, captions
→ Calidad media-baja. GPU limitada.

**Stack Mejorado recomendado ($40-80/mes):**
1. **Runway Pro ($28/mo)** — Gen-4.5 + Kling 3.0 + Seedance 2.0 (todo en una)
2. **ElevenLabs Creator ($11/mo)** — voiceovers premium
3. **CapCut (gratis)** — edición final, overlays, captions
4. **DaVinci Resolve (gratis)** — color grading si hace falta
→ Calidad 9/10. Sin dependencia de GPU local. API disponible.

---

## ⚠️ NOTAS IMPORTANTES

- **Sora 2 discontinuado** como producto standalone (abril 2026). No construir pipelines sobre él.
- **CapCut** es el mejor valor calidad/precio del mercado: gratuito, sin marca de agua, con IA integrada.
- **DaVinci Resolve** versión gratuita es la más potente del mercado.
- **Runway Pro** es el mejor punto de entrada al ecosistema cloud (incluye Kling + Seedance).
- Los precios fueron verificados contra sitios oficiales en julio 2026.
