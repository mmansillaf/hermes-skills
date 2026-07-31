# Migration Guide: 2captcha v1 → v2 for CEJ Scraper

## ⚠️ Critical: Verify Captcha Type Before Changing `numeric`

**The CEJ captcha is 4-character alphanumeric (letters + numbers).**
The user confirmed: *"el captcha veo que tiene letras y numeros"*.

This means:

| Setting | Effect on CEJ | 
|---------|---------------|
| `numeric: 0` (default) | Any character types — ✅ correct for alphanumeric |
| `numeric: 1` | Only numbers — ❌ guarantees failure on letter-containing captchas |
| `numeric: 4` | MUST contain numbers AND letters — 🔶 over-restrictive |

**ALWAYS verify the captcha content before setting a non-zero numeric constraint.**
If in doubt, use `numeric: 0`.

## Image Quality Matters More Than API Version

Before blaming the API version, check image quality. The captcha capture uses:

```javascript
// Current: PNG at natural resolution — preserves ALL background noise
var c = document.createElement('canvas');
c.width = img.naturalWidth;    // May be 2x on HiDPI (400 instead of 200)
c.height = img.naturalHeight;
c.getContext('2d').drawImage(img, 0, 0);
return c.toDataURL('image/png').split(',')[1];
```

Two issues with the current approach:

1. **`naturalWidth`/`naturalHeight`** captures at intrinsic resolution — on HiDPI displays this can be 2x the display size, making the image larger and noisier.
2. **`image/png`** preserves ALL background noise (lines, gradients, artifacts). JPEG compression smooths this out.

**Recommended fix** (works with both v1 and v2):

```javascript
c.width = img.width;         // CSS display size, not intrinsic
c.height = img.height;
c.getContext('2d').drawImage(img, 0, 0);
return c.toDataURL('image/jpeg', 0.85).split(',')[1];  // JPEG compresses noise
```

## Current code (v1 — in.php)

In `spiders/poder_opt.py`, method `_get_captcha_code()`:

```python
upload = requests.post(
    'https://2captcha.com/in.php',
    data={
        'key': self.captcha_api_key,
        'method': 'base64',
        'body': captcha_b64,
        'numeric': 0,          # ← 0=any char (correct for alphanumeric captcha)
        'min_len': 4,
        'max_len': 4,
        'json': 1,
    }
).json()
```

Even with v1, fixing `numeric: 0` → `numeric: 1` will improve success rate.

## Option A: Quick fix (v1, keep numeric=0)

The CEJ captcha is alphanumeric (letters + numbers). `numeric: 0` (any character) is the correct setting.

## Option B: Full migration (v2 — createTask)

Replace the ENTIRE `_get_captcha_code()` method, adding JPEG encoding and display-resolution canvas:

```python
def _get_captcha_code(self):
    self.logger.info('Esperando captcha...')
    sleep(2)
    
    # Improved captcha image capture: JPEG at display resolution
    captcha_b64 = self.driver.execute_script("""
        var img = document.getElementById('captcha_image');
        if (!img || !img.complete || img.naturalWidth === 0) return null;
        var c = document.createElement('canvas');
        c.width = img.width;           /* CSS dimensions - display size */
        c.height = img.height;
        c.getContext('2d').drawImage(img, 0, 0);
        return c.toDataURL('image/jpeg', 0.85).split(',')[1];  /* JPEG compresses noise */
    """)
    if not captcha_b64:
        # fallback via requests...
        pass
    
    self.logger.info(f'Enviando captcha a 2captcha API v2 ({len(captcha_b64)}b)...')
    
    # API v2: createTask — numeric=0 for alphanumeric captcha
    payload = {
        "clientKey": self.captcha_api_key,
        "task": {
            "type": "ImageToTextTask",
            "body": captcha_b64,
            "numeric": 0,            # ← 0=any char (alphanumeric captcha)
            "minLength": 4,
            "maxLength": 4,
            "comment": "captcha CEJ Peru 4 caracteres alfanumericos"
        }
    }
    
    resp = requests.post(
        'https://api.2captcha.com/createTask',
        json=payload, timeout=30
    )
    
    try:
        result = resp.json()
    except:
        self.logger.error(f'2captcha createTask parse fail: {resp.text[:200]}')
        return '0000'
    
    if result.get('errorId', 0) != 0:
        self.logger.error(f'2captcha error: {result.get("errorDescription", result)}')
        return '0000'
    
    task_id = result.get('taskId')
    self.logger.info(f'2captcha task ID: {task_id}')
    
    # Poll for result
    poll_payload = {"clientKey": self.captcha_api_key, "taskId": task_id}
    
    for attempt in range(30):
        sleep(5)
        poll = requests.post(
            'https://api.2captcha.com/getTaskResult',
            json=poll_payload, timeout=30
        ).json()
        
        status = poll.get('status')
        if status == 'ready':
            code = poll['solution']['text']
            self.logger.info(f'Captcha OK: {code}')
            return code
        elif status == 'processing':
            continue
        else:
            self.logger.error(f'2captcha error: {poll}')
            return '0000'
    
    self.logger.error('2captcha timeout')
    return '0000'
```

## Verification

After migration, the captcha success rate should jump from ~35% to ~85-95%.
Monitor via:

```bash
# Count successes vs failures in the debug_captcha dir
ls debug_captcha/ | wc -l   # failures
grep -c 'Captcha OK' output/*.csv  # successes (indirect) - not great
```

Better: run a quick test loop of 20 captchas and count:

```python
# test_captcha_v2.py — manual test
import requests, time, base64

API_KEY = '1e563a7dfcc437d276d896fdebf88497'
# Use a known captcha image
with open('debug_captcha/fail_xxx.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

successes = 0
for i in range(20):
    payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": b64,
            "numeric": 0,            # ← 0=any char (alphanumeric CEJ captcha)
            "minLength": 4,
            "maxLength": 4,
        }
    }
    r = requests.post('https://api.2captcha.com/createTask', json=payload)
    tid = r.json().get('taskId')
    time.sleep(10)
    poll = requests.post('https://api.2captcha.com/getTaskResult', json={
        "clientKey": API_KEY, "taskId": tid
    })
    if poll.json().get('status') == 'ready':
        successes += 1
    time.sleep(2)

print(f'{successes}/20 success = {successes*5}%')
```

## Rollback

If v2 causes issues, revert to the existing v1 code. v1 still works — it's just slower and more expensive.
