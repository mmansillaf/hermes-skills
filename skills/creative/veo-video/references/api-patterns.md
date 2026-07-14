# Veo API Call Patterns

## Single clip launch (Fast tier)

```bash
OPERATION=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview:predictLongRunning?key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{"prompt": "DESCRIPTIVE SCENE PROMPT HERE"}],
    "parameters": {"sampleCount": 1, "personGeneration": "allow_all"}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['name'].split('/')[-1])")
echo "Operation: $OPERATION"
```

## Polling for completion

```bash
until curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview/operations/$OPERATION?key=$API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('done') else 1)" 2>/dev/null; do
  sleep 25
done
echo "Done!"
```

## Extract download URI

```bash
VIDEO_URI=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-fast-generate-preview/operations/$OPERATION?key=$API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['response']['generateVideoResponse']['generatedSamples'][0]['video']['uri'])")
echo "URI: $VIDEO_URI"
```

## Download

```bash
curl -s -L "$VIDEO_URI&key=$API_KEY" -o output.mp4
```

## Batch launch + poll + download (Python)

```python
import time, json, urllib.request, os

KEY = "YOUR_KEY_HERE"
MODEL = "veo-3.1-fast-generate-preview"

prompts = {
    "scene1": "Your first scene prompt...",
    "scene2": "Your second scene prompt...",
}

# Launch all in parallel
operations = {}
for name, prompt in prompts.items():
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:predictLongRunning?key={KEY}",
        data=json.dumps({"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1, "personGeneration": "allow_all"}}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    op_id = resp["name"].split("/")[-1]
    operations[name] = op_id
    print(f"[{name}] launched: {op_id}")

# Poll all
pending = set(operations.keys())
while pending:
    for name in list(pending):
        op_id = operations[name]
        resp = json.loads(urllib.request.urlopen(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}/operations/{op_id}?key={KEY}"
        ))
        if resp.get("done"):
            video_uri = resp["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
            filename = f"{name}.mp4"
            urllib.request.urlretrieve(f"{video_uri}&key={KEY}", filename)
            size = os.path.getsize(filename)
            print(f"[{name}] downloaded: {filename} ({size/1024/1024:.1f}MB)")
            pending.remove(name)
    if pending:
        time.sleep(20)

print("All clips downloaded!")
```

## Audio mixing (ffmpeg)

```bash
# Background music + video (loop music if shorter)
ffmpeg -i clips_stitched.mp4 -stream_loop -1 -i background_music.mp3 \
  -shortest -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -metadata:s:a:0 title="Background Music" \
  final_with_audio.mp4

# Voiceover overlay (reduce bgm volume)
ffmpeg -i clips_stitched.mp4 -i background_music.mp3 -i voiceover.wav \
  -filter_complex "[1:a]volume=0.15[bgm];[2:a][bgm]amix=inputs=2:duration=first[audio]" \
  -c:v copy -map 0:v:0 -map "[audio]" final_with_voiceover.mp4
```
