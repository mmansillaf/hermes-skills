---
name: hermes-multi-model-routing
description: Configuración de 3 perfiles Hermes con modelos DeepSeek Flash/Pro y Groq. Comandos flash, hpro, groq para cambiar de modelo sin salir de la terminal.
category: devops
---

# Hermes Multi-Model Routing

Tres perfiles para cambiar de modelo según la tarea sin reconfigurar.

## Comandos

| Comando | Modelo | Provider | Para |
|---------|--------|----------|------|
| `flash` | deepseek-v4-flash | deepseek | Default, rápido, barato, diario |
| `hpro` | deepseek-v4-pro | deepseek | Programar, análisis profundo |
| `groq` | llama-3.3-70b-versatile | groq | Tareas generales, segunda opinión |

`hermes` sin perfil = Flash (default).

## Cómo se creó

```bash
# Crear perfiles
hermes profile create pro --clone
hermes profile create flash --clone
hermes profile create groq --clone

# Asignar modelos
hermes --profile pro config set model.default deepseek/deepseek-v4-pro
hermes --profile flash config set model.default deepseek/deepseek-v4-flash
hermes --profile groq config set model.default groq/llama-3.3-70b-versatile

# Crear alias (wrapper scripts)
hermes --profile pro profile alias pro --name hpro
hermes --profile flash profile alias flash
hermes --profile groq profile alias groq

# Default global = Flash
hermes config set model.default deepseek/deepseek-v4-flash
```

## Cambiar modelo dentro de una sesión

Sin salir de Hermes, con `/model`:

```
/model deepseek-v4-flash     → Flash
/model deepseek-v4-pro       → Pro
/model gemini-2.5-flash      → Gemini
/model groq/llama-3.3-70b    → Groq
```

Aplica desde el siguiente mensaje. No se pierde contexto.

**Pitfall — `/model` es un comando separado, no inline**: Escribí `/model deepseek-v4-pro` en su propia línea y presiona Enter. NO aggregates tu pregunta en la misma línea. El flujo correcto es:

```
> /model deepseek-v4-pro
[Enter — Hermes confirma cambio]
> [aquí escribes tu pregunta]
```

## API Keys requeridas

En `~/.hermes/.env`:
- `DEEPSEEK_API_KEY` — para Flash y Pro
- `GOOGLE_AI_STUDIO_API_KEY` — para Gemini
- `GROQ_API_KEY` — para Groq

## Modelos DeepSeek disponibles

- `deepseek/deepseek-v4-flash` — rápido, barato (~10x menos que Pro). Default.
- `deepseek/deepseek-v4-pro` — potente, para razonamiento complejo.
- `deepseek/deepseek-reasoner` — modelo razonador (R1). Ideal para análisis jurídico profundo, preguntas multi-salto, desambiguación legal. Lento y caro. Usar con `/model` por sesión, NO como default global.

**Pitfall — `/model` en la RAG del repo NO funciona**: `/model` es un comando de Hermes Agent, no del RAG Legal. Si el usuario pregunta "cómo cambio al razonador?" en contexto del RAG Legal (repositorio), responde sobre el RAG. Si pregunta en contexto de Hermes chat, responde con `/model`. Preguntar primero si hay ambigüedad — NO asumir.
