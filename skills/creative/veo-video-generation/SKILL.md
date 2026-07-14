---
name: veo-video-generation
description: "Google Veo 3.1 AI video generation via Gemini API — promotional clips, overlay post-processing, YouTube Shorts/TikTok format"
version: 1.0.0
platforms: [linux]
---

# Veo 3.1 Video Generation Pipeline

## When to use

Generate short promotional videos (8-10s clips) for social media using Google's Veo 3.1 API. Best for: product demos, SaaS promos, brand storytelling, before/after comparisons. Supports 720p h264 with built-in AAC audio.

## Prerequisites

- Google AI Studio API key with billing enabled
- `curl`, `ffmpeg`, Python 3 with `PIL` (`pip install pillow`)

## Veo 3.1 Models (via Gemini API)

| Model | Price/sec | Resolution | Audio | Notes |
|-------|-----------|------------|-------|-------|
| `veo-3.1-lite-generate-preview` | $0.05 | 720p | ✅ Built-in | Fastest, cheapest |
| `veo-3.1-fast-generate-preview` | $0.10 | 720p-1080p | ✅ Built-in | Best quality/price |
| `veo-3.1-generate-preview` | $0.40 | 720p-4K | ✅ Built-in | Highest quality |

All generate max **8-second clips**. Stitch multiple clips with ffmpeg for longer videos.

## API Workflow

### 1. Launch generation

```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview:predictLongRunning?key=$KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "prompt": "Your cinematic scene description in Spanish"
    }],
    "parameters": {
      "sampleCount": 1,
      "personGeneration": "allow_all"
    }
  }'
```

Returns an operation ID: `{"name": "models/veo-3.1-fast-generate-preview/operations/abc123"}`

### 2. Poll for completion

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview/operations/OPERATION_ID?key=$KEY"
```

When `done: true`, response contains `generateVideoResponse.generatedSamples[0].video.uri`.

### 3. Download

```bash
curl -s -L "URI?key=$KEY" -o clip_name.mp4
```

## Prompt Structure (8-part framework)

| Component | Description |
|-----------|-------------|
| **Visual scene** | What the camera sees — setting, subject, objects |
| **Action/movement** | Specific motion (walking, typing, nodding) |
| **Subject/character** | Who, attire, expression, demeanor |
| **Mood/style** | Elegant, urgent, professional, dynamic |
| **Lighting** | Natural, cold/blue, warm, cinematic |
| **Camera** | Wide shot, medium, close-up, over-shoulder |
| **Audio cues** | Ambient sounds (footsteps, typing, office chatter) — describe in prompt text |
| **Duration** | "8 seconds" at end of prompt |

### Spanish prompt template (professional/legal contexts)

```
[Camera] de [subject] con [attire] [action] en [setting].
A su alrededor [background activity].
Expresión [emotion descriptor: seria, concentrada, satisfacción contenida].
Iluminación [lighting type] con tonos [color tone].
Ambiente [atmosphere]. Estilo cinematográfico. 8 segundos.
```

**Key tone rules for professional ads:**
- "Satisfacción contenida" NOT "sonrisa" — subtle professional nod, not commercial smile
- "Determinación" NOT "felicidad"
- Expressions like "vamos bien" — task-completed satisfaction
- Always specify tonos fríos/azulados for technology/legal vibe

## 3-Act Structure for 10s Promo Videos

| Act | Seconds | Content | Purpose |
|-----|---------|---------|---------|
| **1. Problem** | 0-3s | Professional walking fast, looking at phone, urgent | Hook — "cada minuto cuenta" |
| **2. Solution** | 3-7s | Close-up hands + phone with UI | Show product solving problem |
| **3. Result** | 7-10s | Confident nod, satisfaction, "vamos bien" | Resolution — trust, authority |

## UI Overlay Technique (post-processing)

Veo alucinates text on screens — always overlay real UI screenshots.

### Step 1: Crop phone screenshot

```python
from PIL import Image
import numpy as np

img = Image.open("screenshot.jpg")
arr = np.array(img)
h, w, _ = arr.shape

# Detect black bezels automatically
center_col = arr[:, w//2, :]
is_black = np.all(center_col < 30, axis=1)
top = int(np.argmax(~is_black[:h//2]))
bottom = h - 1 - int(np.argmax(~is_black[::-1][:h//2]))
center_row = arr[h//2, :, :]
is_black_side = np.all(center_row < 30, axis=1)
left = int(np.argmax(~is_black_side[:w//2]))
right = w - 1 - int(np.argmax(~is_black_side[::-1][:w//2]))

cropped = arr[top:bottom, left:right]
Image.fromarray(cropped).save("overlay.png")
```

### Step 2: Resize and overlay

```bash
# Scale overlay to phone screen size (adjust 220 width as needed)
# Position centered on frame (1280x720 video)
ffmpeg -y -i clip.mp4 -i overlay_resized.png \
  -filter_complex "[0:v][1:v]overlay=X:Y:format=auto[out]" \
  -map "[out]" -map 0:a -c:v libx264 -crf 23 -preset fast -c:a copy \
  clip_with_overlay.mp4
```

Where X,Y = ((1280-overlay_w)//2, (720-overlay_h)//2) for center, or adjust manually.

### Step 3: Stitch multiple clips

```bash
# Create concat file
echo "file 'clip1.mp4'" > concat.txt
echo "file 'clip2.mp4'" >> concat.txt
echo "file 'clip3.mp4'" >> concat.txt

ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final_video.mp4
```

## Known Quirks & Pitfalls

- **`"audio": true` parameter NOT supported** on Veo 3.1 Fast preview — returns 400 error. Audio is generated automatically built-in (AAC 48kHz stereo, ~139 kbps). Just omit the field.
- **`personGeneration": "allow_all"`** required in parameters for videos with people
- **Text on screens is always hallucinated** in English even with Spanish prompt. Always overlay real UI.
- **Operation IDs are one-shot** — if you lose the ID before polling completes, you can't recover it. Save it immediately.
- **Max 8 seconds per clip** — cannot produce longer clips. Stitch in post.
- **720p h264 output** — enough for social media, not broadcast quality.
- **Model names change** (preview → stable). Check available models with list endpoint.
