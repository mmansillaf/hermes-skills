# MVP Simplificado — Despliegue Auto-contenido (Mayo 2026)

## Contexto

El 05-may-2026, después de la refactorización completa (Fases 1-5 + D1), el usuario decidió simplificar la estrategia de despliegue tras descubrir que GitHub Pages ahora requiere registro como empresa + medio de pago.

## Decisión: MVP auto-contenido en VPS

Se descartaron los siguientes componentes del plan original (Opción D):
- **GitHub Pages** — requiere registro empresarial + tarjeta. No viable para MVP.
- **Cloudflare R2** — los 80 MB de HTMLs fuente no se usan en las respuestas. Las citas son por número de norma, no por link a PDF.
- **GitHub Actions CI/CD** — exceso para MVP. Se puede agregar después.
- **search_local_htmls()** — la función FTS5 de HTMLs fuente quedó en el código pero no aporta valor sin los archivos.

## Arquitectura MVP

```
┌──────────────────────────────────────┐
│       Contabo VPS $5.50/mes          │
│                                      │
│  FastAPI :8000                       │
│  ├── /           Landing page HTML   │
│  ├── /query      API RAG             │
│  ├── /health     Monitoreo           │
│  ├── /stats      Estadísticas        │
│  ├── /token-stats Costos Groq        │
│  └── /search     Búsqueda simple     │
│                                      │
│  Docker Compose:                     │
│  ├── Qdrant :6333 (97K vectores)     │
│  ├── Neo4j :7687  (113K nodos)       │
│  └── SQLite (normas_total.db, 1 GB)  │
└──────────────────────────────────────┘
```

## Scripts de despliegue (deploy/)

Scripts simplificados en `PeruanoSearchEngine02/deploy/`:

| Script | Líneas | Propósito |
|--------|--------|-----------|
| `deploy.sh` | 116 | Empaquetar + enviar desde laptop |
| `install.sh` | 95 | Instalar dependencias (1 sola vez) |
| `start.sh` | 199 | Iniciar Qdrant+Neo4j+API+landing |
| `test.sh` | 84 | Probar 10 preguntas con curl |

### Uso

```bash
# En laptop:
./deploy/deploy.sh --prepare
./deploy/deploy.sh --send 192.168.x.x

# En VM/VPS:
cd /opt/elperuano
bash install.sh     # Docker + Python + dependencias
bash start.sh       # Iniciar servicios + API + landing page
bash test.sh        # 10 preguntas de prueba
```

### Lo que NO incluye el paquete

- `normas_total.db` (1,055 MB) — se copia aparte por SCP
- `src/extraction/` — código legacy de ingesta
- Backups, reportes, tests legacy

### Landing page

`start.sh` genera una landing page HTML en `static/index.html` con:
- Documentación de endpoints
- Health check en vivo (verde/rojo)
- Diseño dark theme, responsivo

## Costo final: $5.50/mes

Solo el VPS Contabo. Sin costos adicionales de Cloudflare, GitHub, ni almacenamiento externo.

## Fase 0 (actual): VM Ubuntu staging

Antes de Contabo, validar en VM Ubuntu local usando los mismos scripts `deploy/`.

## Bugs conocidos en los scripts

Ver `references/deploy-script-bugs.md` — 6 bugs encontrados en sesión 05-may-2026 (VM staging):
- `install.sh`: se congela esperando sudo sin mostrar prompt
- `start.sh`: sale silenciosamente si Docker no existe (`set -e`)
- `start.sh`: línea 159-165 nunca arranca la API (falta `uvicorn.run()`)
- `install.sh`/`start.sh`: corren desde directorio equivocado si el usuario no hace `cd` antes
- `test.sh`: secuencias de escape sin interpretar
- `start.sh`: health check frágil
