# RAG Settings UI Pattern

## When to use this pattern

You're building a RAG system for END USERS (not developers). Users cannot and should not edit `.env` files or set environment variables. They need a GUI to:
- Switch between LLM providers (Groq, OpenAI, Gemini, Ollama)
- Enter/manage their own API keys
- Customize response style (temperature, formality, verbosity)
- Choose model per provider
- Test provider connectivity

## Architecture Overview

```
/settings            → FastAPI endpoint that reads from .env + SQLite preferences table
/settings-page       → Renders the HTML settings UI
POST /settings/llm   → Change provider + model, re-initializes LLM client
POST /settings/api_key → Write API key to .env (never expose in frontend)
POST /settings/preferences → Save temperature, style, citation format, etc.
POST /settings/test  → Test connection to current provider
```

## Data Storage

### .env file (for secrets and core config)
```ini
# Written by POST /settings/api_key and POST /settings/llm
LLM_PROVIDER=groq
GROQ_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

### SQLite `settings` table (for preferences)
```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Example rows:
-- temperature | 0.3
-- style | formal
-- max_tokens | 2048
-- top_k | 5
-- citation_format | inline
```

## API Keys — Security

API keys are the most sensitive data. Follow these rules:

1. **Never send keys to frontend**: The GET /settings endpoint returns `{provider: "groq"}` but NEVER the key value itself
2. **Password input**: API key fields use `<input type="password">` — displayed as `••••••••`
3. **Write to .env server-side**: POST /settings/api_key writes to `.env` via Python's `pathlib.Path.write_text()`
4. **File permissions**: `.env` should have `600` permissions (owner read-only)
5. **Connection test**: POST /settings/test calls the provider with a minimal prompt — does NOT expose the key in error messages

```python
@app.post("/settings/api_key")
async def set_api_key(provider: str = Form(...), api_key: str = Form(...)):
    # Read current .env
    env_path = BASE_DIR / ".env"
    lines = env_path.read_text().splitlines()
    
    # Find and update or append the key
    key_name = f"{provider.upper()}_API_KEY"
    found = False
    for i, line in enumerate(lines):
        if line.startswith(key_name + "="):
            lines[i] = f"{key_name}={api_key}"
            found = True
            break
    if not found:
        lines.append(f"{key_name}={api_key}")
    
    # Write back (only .env, never expose to frontend)
    env_path.write_text("\n".join(lines) + "\n")
    os.environ[key_name] = api_key
    
    # Re-initialize LLM client if active provider changed
    if provider == os.getenv("LLM_PROVIDER"):
        global llm
        llm = LLMClient()
    
    return {"status": "ok"}
```

## Provider Switching

When the user switches providers, the LLM client must be RE-INITIALIZED:

```python
@app.post("/settings/llm")
async def set_llm(provider: str = Form(...), model_name: str = Form(None)):
    # Validate provider
    valid = ["groq", "openai", "gemini", "ollama"]
    if provider not in valid:
        return {"status": "error", "message": f"Provider invalido: {provider}"}
    
    # Update .env
    env_path = BASE_DIR / ".env"
    lines = env_path.read_text().splitlines()
    
    # Set provider
    for i, line in enumerate(lines):
        if line.startswith("LLM_PROVIDER="):
            lines[i] = f"LLM_PROVIDER={provider}"
            break
    else:
        lines.append(f"LLM_PROVIDER={provider}")
    
    # Set model (if provided)
    if model_name:
        model_key = f"{provider.upper()}_MODEL"
        for i, line in enumerate(lines):
            if line.startswith(model_key + "="):
                lines[i] = f"{model_key}={model_name}"
                break
        else:
            lines.append(f"{model_key}={model_name}")
        os.environ[model_key] = model_name
    
    env_path.write_text("\n".join(lines) + "\n")
    os.environ["LLM_PROVIDER"] = provider
    
    # Re-initialize globally
    global llm, orchestrator
    llm = LLMClient()
    orchestrator = Orchestrator(store, embedder, reranker, llm)
    
    return {"status": "ok"}
```

## Response Customization

User preferences (temperature, style, etc.) modify the SYSTEM PROMPT sent to the LLM:

```python
# Preference → prompt modifier mapping
STYLE_PROMPTS = {
    "formal": "Responde en un tono formal y tecnico, propio de un informe legal.",
    "concise": "Responde de forma concisa, maximizando informacion en minimas palabras.",
    "detailed": "Responde de forma exhaustiva, desarrollando cada punto con detalle.",
    "default": "",  # No modifier
}

CITATION_FORMATS = {
    "inline": 'Formato: [Documento: "nombre", Seccion: "seccion", Lineas: X-Y]',
    "footnote": 'Usa numeros de nota al pie para las citas. Ej: Texto¹\n\n¹Documento X, Seccion Y',
    "end": 'Lista las citas al final como [1], [2], etc.',
}
```

The orchestrator's `process_query()` reads these preferences from the store and injects them into the system prompt:

```python
# In orchestrator.process_query()
prefs = {
    "temperature": store.get_preference("temperature") or 0.3,
    "style": store.get_preference("style") or "formal",
    "citation_format": store.get_preference("citation_format") or "inline",
    "max_tokens": store.get_preference("max_tokens") or 2048,
}
llm.temperature = float(prefs["temperature"])
llm.max_tokens = int(prefs["max_tokens"])
# Style and citation format are injected into the system prompt
```

## Connection Testing

```python
@app.post("/settings/test")
async def test_connection():
    """Test current provider with a minimal generation call."""
    try:
        result = llm.generate(
            system_prompt="Responde solo SI, NO o ERROR.",
            user_prompt="Responde SI si puedes leer este mensaje.",
            temperature=0.0,
            max_tokens=10,
        )
        return {"status": "ok", "message": f"Conectado. Respuesta: {result[:50]}"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}
```

## UI Implementation

The settings page (`/settings-page`) should include:

### Provider Selection
```html
<select id="llmProvider">
    <option value="groq">Groq (default, rapido)</option>
    <option value="openai">OpenAI (ChatGPT)</option>
    <option value="gemini">Google Gemini</option>
    <option value="ollama">Ollama (local)</option>
</select>
```

### Model Dropdown (per-provider)
```javascript
const MODELS = {
    groq: ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
    openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    gemini: ["gemini-2.0-flash", "gemini-2.0-pro"],
    ollama: ["llama3.2:3b", "qwen2.5:7b", "llama3.1:8b"],
};

function onProviderChange() {
    const provider = document.getElementById('llmProvider').value;
    const select = document.getElementById('llmModel');
    select.innerHTML = MODELS[provider].map(m =>
        `<option value="${m}">${m}</option>`
    ).join('');
}
```

### Preferences Sliders and Selects
```html
<label>Temperature (0.0 - 1.0)</label>
<input type="range" id="temperature" min="0" max="1" step="0.1" value="0.3">

<label>Estilo de respuesta</label>
<select id="style">
    <option value="formal">Formal (default)</option>
    <option value="concise">Conciso</option>
    <option value="detailed">Detallado</option>
</select>

<label>Max tokens</label>
<input type="range" id="maxTokens" min="256" max="8192" step="256" value="2048">

<label>Formato de citas</label>
<select id="citationFormat">
    <option value="inline">Inline [Documento, Seccion, L X-Y]</option>
    <option value="footnote">Nota al pie</option>
    <option value="end">Citas al final</option>
</select>
```

### Flash Messages for Feedback
After saving, show a brief notification:
```javascript
async function saveSettings() {
    const resp = await fetch('/settings/preferences', {
        method: 'POST',
        body: new FormData(document.getElementById('settingsForm'))
    });
    const data = await resp.json();
    showFlash(data.status === 'ok' ? '✅ Guardado' : '❌ Error');
}
```

## Pitfalls

1. **.env file corruption**: When multiple concurrent requests write to `.env`, lines can interleave. Read the entire file, modify in memory, write back atomically. A file lock (`flock` on Linux) adds safety but may be overkill for single-user apps.

2. **Browser caching of settings page**: The GET /settings-page may be cached. Add `Cache-Control: no-cache` header.

3. **API key validation**: Some keys look valid but have expired. Always test with a real API call, not just format check.

4. **Ollama local not running**: When the user switches to Ollama but doesn't have it running, the test connection should clearly say "Ollama no disponible" rather than a generic error.

5. **Provider model names change**: Groq regularly adds/removes models. The model list should be fetched dynamically when possible, or kept in a configuration that's easy to update.
