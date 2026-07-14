---
name: veo-video
description: "Generate AI video clips with Google Veo 3/3.1 via Gemini API — async predictLongRunning, polling, download, audio handling."
---

# Veo Video Generation

## When to use

Use when the user wants to generate short AI video clips (5–8 seconds each) from text prompts using Google's Veo 3 or Veo 3.1 models via the Gemini Developer API. Best for: promotional videos, B-roll, concept visualization, scene-by-scene storyboards.

## Limitations

- **Audio IS embedded in the MP4** (AAC, 48kHz, stereo, ~139kbps). There is no separate `audioContainer` key — the audio track is inside the video file. For external music/voiceover, extract and mix with ffmpeg instead.
- **`audio` parameter NOT accepted** by the API — passing `"audio": true` returns HTTP 400. Audio is auto-generated from the scene prompt description.
- **Clips are short** (~8 seconds max per generation)
- **No person persistence** — a character in clip 1 won't look the same in clip 2
- **Scene-by-scene only** — Veo cannot handle multi-scene narrative prompts. Break every storyboard into individual clips.
- **Cost accrues per second**, not per clip
- **AI-generated text on screens is inaccurate** — Veo hallucinates text in English. For Spanish UI overlay, use the text-on-screen strategy (post-production overlay).

## Models & Pricing (as of June 2025)

| Model | Endpoint suffix | Price/seg | Best for |
|-------|----------------|-----------|----------|
| `veo-3.1-lite-generate-preview` | Lite | $0.05 | Testing, quick drafts |
| `veo-3.1-fast-generate-preview` | Fast | $0.10 | Good quality, production drafts |
| `veo-3.1-generate-preview` | (standard) | $0.40 | Highest quality |
| `veo-3.0-generate-001` | Veo 3 | $0.40 | Stable, non-preview |
| `veo-3.0-fast-generate-001` | Veo 3 Fast | $0.10 | Fast stable |
| `veo-2.0-generate-001` | Veo 2 | $0.35 | Legacy |

All require the `predictLongRunning` method (not `generateContent`).

## Workflow

```
STORYBOARD → BREAK INTO CLIPS → LAUNCH ALL → POLL → DOWNLOAD → STITCH → ADD AUDIO
```

### Step 1: Storyboard → Clip prompts

The user will likely give you a narrative. **Break it into individual scene prompts.** Each prompt should be self-contained and describe what's visible in the frame.

Veo prompt tips:
- Describe the **shot type** (close-up, wide, over-shoulder, drone shot)
- Describe **lighting, colors, atmosphere**
- Include **character appearance and action** in every clip
- Keep it under 200 words
- Use `"personGeneration": "allow_all"` if people appear

### Step 2: Launch generation

POST to the predictLongRunning endpoint. Each clip gets its own operation.

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview:predictLongRunning?key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "prompt": "Your descriptive scene prompt here. Describe shot type, lighting, character action, atmosphere. ~8 second clip."
    }],
    "parameters": {
      "sampleCount": 1,
      "personGeneration": "allow_all"
    }
  }'
```

Returns an operation ID immediately.

### Step 3: Poll for completion

Veo is async. Poll the operation URL every 20–30 seconds:

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview/operations/$OPERATION_ID?key=$API_KEY"
```

Check `response.generateVideoResponse.generatedSamples[0].video.uri` in the JSON. When `done: true` appears, it's ready.

### Step 4: Download

```bash
curl -s -L "https://generativelanguage.googleapis.com/v1beta/files/$FILE_ID:download?alt=media&key=$API_KEY" -o output.mp4
```

### Step 5: Stitch clips

Use ffmpeg concat:

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final_stitched.mp4
```

Where concat.txt:
```
file 'clip1.mp4'
file 'clip2.mp4'
```

### Step 6: Add external audio (optional)

Audio is already embedded in each Veo clip. This step is only needed if you want:
- **Background music** layered on top
- **Voiceover narration**
- **Sound effects** that weren't in the original scene

**Background music:**
```bash
ffmpeg -i final_stitched.mp4 -i music.mp3 -shortest -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output_with_audio.mp4
```

**Voiceover:**
- Generate TTS using Gemini TTS models (`gemini-2.5-flash-preview-tts`) or another TTS API
- Mix with ffmpeg as above

## Cost Estimation

For a 30-second promo split into 6 clips at ~8s each:

| Tier | Clip cost (8s) | Total (6 clips) |
|------|----------------|-----------------|
| Lite ($0.05) | $0.40 | $2.40 |
| Fast ($0.10) | $0.80 | $4.80 |
| Standard ($0.40) | $3.20 | $19.20 |

## Spanish-language Prompts for Latin American Markets

When the target audience is Spanish-speaking (e.g., legaltech for Peru), write prompts entirely in Spanish. Veo 3.1 handles Spanish prompts well — it generates matching visuals, ambient audio, and on-screen text that at least looks Spanish (though text is never accurate — see overlay strategy below).

### Prompt structure (8-part framework)

| Component | Spanish example |
|-----------|----------------|
| Shot type | "Toma amplia / plano medio / primer plano de..." |
| Character | "una abogada peruana profesional con atuendo elegante deportivo (blazer cómodo, zapatos bajos de vestir)" |
| Action | "caminando con paso rápido y firme, mirando su teléfono con expresión concentrada" |
| Environment | "a través de un lobby moderno de oficinas con otros profesionales trabajando" |
| Lighting | "Iluminación natural con tonos fríos azulados" |
| Mood | "Ambiente profesional dinámico. Estilo cinematográfico." |
| Duration | "8 segundos" |
| Audio context | Mention sounds explicitly in the prompt: "sonido ambiente de oficina: pasos, conversaciones" |

### Full Spanish prompt example

```
Toma amplia de una abogada peruana profesional caminando con paso rápido y firme 
a través de un lobby moderno y transitado de oficinas. A su alrededor se ven otros 
abogados y asistentes caminando, conversando, trabajando en laptops. Ella mira su 
teléfono con expresión concentrada y seria. Iluminación natural con tonos fríos 
azulados. Ambiente profesional dinámico. Estilo cinematográfico. 8 segundos.
```

### Text-on-screen overlay strategy (Spanish UI)

Veo **cannot** render accurate text on screens (phone UIs, laptops, signage). It defaults to English gibberish. For Spanish-language product demos:

1. **Generate the human+device scene without specific text**:
   *"Primer plano de manos femeninas sosteniendo un smartphone moderno con la pantalla encendida. El teléfono muestra un brillo de pantalla sin texto legible. Ambiente profesional."*

2. **Prepare your UI image** Phone screenshots from Android/iOS are typically ~600x1320. You'll need to:
   - Crop out the phone bezel/notch so only the screen content remains
   - Resize to match the phone screen area in your clip (e.g., ~400x850 for a 1280x720 clip)
   - Save as PNG with transparency if possible

3. **Find the phone position** in your clip by extracting a frame, then overlay with ffmpeg:
   ```bash
   # First, extract a frame to find phone position:
   ffmpeg -i clip.mp4 -vframes 1 frame.png

   # Then overlay the resized UI image (adjust X,Y to match phone position):
   ffmpeg -i clip.mp4 -i interfaz_recortada.png \
     -filter_complex "[0:v][1:v]overlay=440:100:enable='between(t,0,8)'" \
     -c:a copy output_overlay.mp4
   ```
   Adjust position (X,Y: top-left corner of the phone screen area) and the UI image size based on your specific clip.

## Promotional Video Structure (YouTube Shorts / TikTok / Reels)

For SaaS/tech product promos targeting Latin American professionals, use the **3-act micro-video** structure optimized for 10-15 seconds:

### Act 1: Hook (0-3s) — The Problem
Show the user in their environment with urgency. No product yet.
- Visual: Professional walking/moving with purpose
- Expression: Concentrated, determined (not smiling)
- Text overlay: "Cada minuto cuenta." or "Tiempo es poder."

### Act 2: Solution (3-8s) — Product in Action
Show the tool being used. This is where you overlay your UI.
- Visual: Hands holding phone/laptop with product visible
- Action: Typing, swiping, voice command
- Text overlay: "Encuentra las normas exactas."

### Act 3: CTA (8-10/12s) — Result
Show satisfaction and brand.
- Expression: "Vamos bien" — asentimiento leve, satisfacción contenida (NOT a big smile)
- Visual: Subject looks up from device, continues forward with confidence
- Text overlay: "Algoritmo Jurídico."

### Multiple-video strategy

Instead of one 40s video, create **3 independent 10-12s videos**, each self-contained:
| Video | Hook | Focus |
|-------|------|-------|
| #1 "Tiempo es Poder" | Speed, efficiency | Walking + phone → satisfaction |
| #2 "Encuentra, No Busques" | Search precision | Phone UI overlay → results |
| #3 "La IA del Derecho Peruano" | Trust, authority | Office + laptop + confident call |

Each video works standalone on YouTube Shorts / Instagram Reels / TikTok.

## Competitive Landscape: Legaltech AI in Peru (June 2025)

When creating promos for a Peruvian legal AI product, these competitors exist:

| Platform | Pitch | Price | Differentiator |
|----------|-------|-------|----------------|
| **Litis.ai** | 1.2M resoluciones verificadas | Freemium | Research-focused, academic tone |
| **DOXS.AI** | Suite completa (escritos, análisis, voz) | S/29/mes | Most features per dollar |
| **Juztina** | Multi-país (PE, CO, CL, MX) | ~S/38/mes | TikTok-friendly, educational |
| **Lexius** | 18 países, multimedia | S/37.99/mes | Video podcasts, PowerPoint |
| **Magnar** | Integración Word, análisis documental | ~S/38.50/mes | Corporate workflows |

**Key insight:** None of these competitors have AI-generated promotional videos with actors. This is an open space for video marketing differentiation.

## Pitfalls

- **Don't write one long narrative prompt.** Veo cannot execute multi-scene stories. One clip = one prompt.
- **No character continuity.** If your storyboard has the same person in multiple scenes, accept they'll look different.
- **Audio is embedded in the MP4** — no need for external audio layering unless you want voiceover/music on top
- **Veo 2.0** says "requires billing on Google Cloud Platform" — it won't work with a plain AI Studio API key. Use Veo 3.x instead.
- **Rate limits:** Preview models have stricter rate limits. If you get 429s, add delay between launches.
- **API key matters:** The Gemini AI Studio key works for Veo 3.x preview models. Veo 2 requires Vertex AI.

## Reference files

| File | Contents |
|------|----------|
| `references/api-patterns.md` | Exact curl and Python call templates for launch, poll, download, batch, and audio mixing |

## Testing

Always run one test clip first before launching a batch of 6+. Check the output quality, then proceed.
