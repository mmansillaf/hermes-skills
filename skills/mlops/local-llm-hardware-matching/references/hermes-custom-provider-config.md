# Hermes Custom Provider Configuration

Configurar un modelo local (llama.cpp, vLLM, Ollama, LM Studio) para usarlo con Hermes requiere configurar un provider custom. Esta referencia cubre el formato actual y los pitfalls comunes.

## Formato Actual (config.yaml)

Desde Hermes v12+, `custom_providers` debe ser una **lista YAML** con entradas `- name:`, no un diccionario:

```yaml
custom_providers:
  - name: local-llama
    base_url: http://localhost:8080/v1
    api_key: sk-no-key-required  # algunos endpoints requieren una dummy
    models:
      - qwen2.5-coder-7b-q4
      - deepseek-coder-6.7b-instruct

  - name: deepseek-api
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
    models:
      - deepseek-chat
      - deepseek-reasoner
```

### Formato antiguo (YA NO funciona)

```yaml
# ❌ DICT — Hermes lo ignora completamente. get_compatible_custom_providers() retorna []
custom_providers:
  local-llama:       # ← error: no es lista
    base_url: ...
```

Si ves el warning `custom_providers is a dict — it must be a YAML list`, es porque tu config aún usa el formato viejo.

## Cambiar de Provider en Hermes

**CRÍTICO:** `hermes config set model` solo cambia el nombre del modelo, NO el provider activo.

```bash
# ✅ Cambiar ambos — funciona
hermes config set provider local-llama
hermes config set model qwen2.5-coder-7b-q4
```

```bash
# ❌ Esto solo cambia el string del modelo, no el provider
hermes config set model local-llama/qwen2.5-coder-7b-q4
# El provider activo sigue siendo el anterior (deepseek, zai, etc.)
# → Error: "Unknown Model" (el modelo no existe en el provider anterior)
```

Para cambiar provider + modelo de una sola vez:

```bash
hermes config set provider local-llama && hermes config set model qwen2.5-coder-7b-q4
```

## Verificar Configuración

```bash
hermes status                    # muestra provider y modelo activos
hermes config                    # muestra toda la config
```

## Volver a un Provider Cloud

```bash
hermes config set provider deepseek
hermes config set model deepseek-v4-flash
```

## Pitfalls

| Problema | Causa | Solución |
|----------|-------|----------|
| `HTTP 400: Unknown Model` | Provider activo no tiene ese modelo | Cambiar provider + modelo, no solo modelo |
| `custom_providers is a dict` | Formato YAML obsoleto | Convertir a lista con `- name:` |
| `Unknown provider 'local-llama'` | Provider no encontrado en config | Verificar que `custom_providers` (o `providers:`) tenga la entrada y esté en formato lista |
| Servidor local no responde | llama-server / vLLM caído | `curl http://localhost:8080/v1/models` para verificar |
