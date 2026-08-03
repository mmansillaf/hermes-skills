# legaltech-gateway — Estado y detalle del proyecto

Proyecto Go de referencia del usuario (LegalTech Perú). Estado verificado: **COMPLETO y EN PRODUCCIÓN** (desde 29 Jul 2026). No confundir con "en desarrollo" — la comparativa vs Magnar lo listaba como P4 "en desarrollo", pero ya está desplegado.

## Datos clave
- Código: `D:\PyCode\legaltech-gateway` (WSL: `/mnt/d/PyCode/legaltech-gateway`)
- Servidor: 192.168.18.152, puerto 8080 (SSH: cmansilla, sshpass -p '<PASSWORD>')
- **Credenciales canónicas (Ago 2026)**: bloque `DEV_VM_*` en `/mnt/d/PyCode/api-algoritmoConcurrencia/.env` (14 vars: SSH, PG, MySQL, JWT secret, URLs API :8060 y Gateway :8080 — valores SOLO en el .env local; .gitignore ya cubre .env).
- Service systemd: `legaltech-gateway` (active, RAM ~9-14MB)
- Backend Python: api-algoritmo v4 en `http://192.168.18.152:8060` (FastAPI, gunicorn, JWT, 348K docs)
- Redis: localhost:6379 en el server (conectado)
- Tests: 19 tests en 5 paquetes, todos `ok` con `go test ./...`

## Arquitectura
```
[Cliente] → Go Gateway (:8080) → Python api-algoritmo v4 (:8060)
              ├─ Redis cache (TTL 5min)
              ├─ Circuit breaker (gobreaker)
              ├─ Rate limit (httprate 60/min/IP)
              └─ Prometheus + slog JSON + security headers
```
Modo degradado: sin Redis arranca igual sin cache (readyz → degraded 503, no es falla).

## Estructura (~784 LOC)
- `cmd/server/main.go` (195 líneas): rutas, graceful shutdown
- `internal/config/config.go` — env vars
- `internal/middleware/middleware.go` — logging JSON, CORS, security headers
- `internal/cache/redis.go` — wrapper Redis (get/set/delete)
- `internal/proxy/proxy.go` (189 líneas) — proxy HTTP + circuit breaker
- `internal/handler/` — health.go, metrics.go, helpers.go
- `specs/SPEC-001-legaltech-gateway.md` (post-hoc, 10 criterios de aceptación), `specs/SPEC-002-search-by-date.md`
- `Dockerfile` (distroless ~15MB), `docker-compose.yml`, `Makefile`, `README.md`, `EXPLICACION_ARQUITECTURA.md/.txt`, `architecture-diagram.html`

## Env vars
| Variable | Default |
|---|---|
| PORT | 8080 |
| PYTHON_API_URL | http://192.168.18.152:8060 |
| REDIS_URL | localhost:6379 |
| RATE_LIMIT_PER_MINUTE | 60 |
| CACHE_TTL | 5m |
| CB_MAX_REQUESTS | 5 |
| CB_TIMEOUT | 30s |

## Endpoints
- Gateway: /healthz (liveness), /readyz (redis+python+CB), /metrics, /cb-status, /
- Proxied con rate limit: /api/search/vector|hybrid|direct (GET cacheado, POST directo), /api/query, /login, /api/register
- Proxied sin rate limit: /visitas, /health, /api/productos|noticias|carrito|orden|pago|token-usage|logout|refresh, /buscador

## Bugs conocidos (verificados 31 Jul 2026)
1. **Métricas Prometheus muertas**: `gateway_http_requests_total` (CounterVec) y `gateway_http_request_duration_seconds` (HistogramVec) están definidas y registradas en metrics.go pero NADIE las incrementa — no hay middleware Prometheus en el stack. En `/metrics` solo aparecen 4 de las 6 de la spec (cache_hits, cache_misses, cb_open, upstream_errors son Counter planos). Fix: middleware que llame `.WithLabelValues(method, path, status).Inc()` y `.Observe()`.
2. **SPEC-002 (búsqueda por fecha sin query)**: schemas.py parcheado (query: Optional[str], línea 384) y utils_database.py parcheado en el server. **PENDIENTE**: validación en main.py ("Debe proporcionar un término de búsqueda o un rango de fechas" — grep = 0 en el server). Probar el flujo requiere JWT (401 directo).

## Cómo verificar (un comando)
`scripts/verify-legaltech-gateway.sh` — go test local + systemctl + healthz/readyz/cb-status + conteo de métricas registradas.

## Artefactos relacionados
- Evaluación Go vs Rust: `D:\PyCode\hermes-skills\RustGoWebApp\` (INFORME_RUST_VS_GO_2026.md, INTEGRACION_GO_RUST_CON_PROYECTOS.md, GO_PYTHON_HYBRID_TIERHIVE.md)
- Notas Obsidian: `D:\PyCode\Obsidian\Proyectos\` (GoGateway_Construido_Jul2026.md, Decision_Go_Python_Jul2026.md, Estado_Sesion_20260729.md, SDD_TDD_decision.md)
- Historial: sesión 20260728_215111_561bd2 (evaluación), 20260729_040743_130896 (construcción+deploy+SPEC-002)

## Decisión de lenguaje (contexto)
api-algoritmo v4 y LexRAG → quedarse en Python (bottleneck = LLMs externos + ecosistema ML). Nuevos microservicios → Go. Hot paths CPU-bound → Rust vía PyO3 (ONNX export del CrossEncoder ms-marco-MiniLM-L-6-v2 verificado, 87.7MB).
