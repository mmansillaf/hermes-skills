---
name: go-microservices
description: "Go microservices: build, deploy, verify (gateway/proxy)."
---

# Go Microservices (gateways / proxies)

## Contexto (stack del usuario)
Decisión Jul 2026 (evaluación Rust vs Go en D:\PyCode\hermes-skills\RustGoWebApp\):
- Python se QUEDA para el core: RAG (api-algoritmo v4, LexRAG), scraping (Scrapy), ML/embeddings.
- GO es la opción para NUEVOS microservicios: gateways, cache, auth, proxy.
- Rust solo vía PyO3 para hot paths CPU-bound (CrossEncoder, BM25 tipo tantivy).
- Proyecto de referencia ya en producción: **legaltech-gateway** (ver references/legaltech-gateway.md).

## Patrón: gateway Go delante de un backend Python/FastAPI
```
[Cliente] → Go Gateway (:8080) → Python FastAPI (:8060)
              ├─ Redis cache        (GETs cacheados, TTL 5min, <5ms en HIT)
              ├─ Circuit breaker    (gobreaker: N fallos >60% → abre 30s → half-open → cierra)
              ├─ Rate limit         (httprate: 60 req/min por IP → 429 + Retry-After)
              └─ Prometheus metrics + logging JSON + security headers
```
- Valor: resolver rate limiting/cache/CB/métricas SIN tocar una línea del código Python.
- **Modo degradado**: si Redis no está, el gateway arranca igual sin cache (log WARN, `/readyz` reporta `degraded` 503 — no es falla).
- Stack: Go 1.22+, Chi v5 (router), go-redis v9, sony/gobreaker, prometheus/client_golang, go-chi/httprate.
- Cache SOLO en GETs; POSTs pasan directo. Header `X-Cache: HIT/MISS` en respuestas cacheadas.

## Workflow (SDD+TDD MANDATORIO — directiva del usuario)
1. SPEC primero: `specs/SPEC-XXX.md` con comportamiento esperado (Dado/Cuando/Entonces), endpoints, criterios de aceptación.
2. TDD: tests RED→GREEN por paquete (config, middleware, health, proxy, cache).
3. `go vet` + `go test ./...` ANTES de tocar el servidor.
4. Deploy: `go build` → scp binario → systemd service (enabled, active) → verificación en vivo.
5. El usuario prefiere PARCHAR sobre reescribir; deploy = patch local → scp → systemctl restart.

## Verificación EN VIVO (obligatoria antes de reportar estado)
Nunca reportar el estado de un proyecto de memoria: las notas y la memoria se desactualizan rápido (lección real: se reportó legaltech-gateway como "recién empezado" cuando estaba completo y en producción). El usuario exige cero falsos positivos.
- Local: `go test ./...` (todos los paquetes `ok`).
- Servidor: `systemctl is-active <svc>` + `curl /healthz /readyz /cb-status /metrics`.
- `/readyz` debe reportar checks: `redis`, `python-backend`, `circuit-breaker`.
- Script listo: `scripts/verify-legaltech-gateway.sh` (local + SSH en un comando).
- Detalle del proyecto: `references/legaltech-gateway.md`.

## Pitfalls
1. **Prometheus Vecs no emiten series hasta la primera observación**: `CounterVec`/`HistogramVec` con labels solo aparecen en `/metrics` después de al menos un `.WithLabelValues(...).Inc()/.Observe()`. Los `Counter` planos emiten siempre. Si una métrica está registrada pero nadie la incrementa (falta middleware), NO existe en `/metrics` — exactamente el bug encontrado en legaltech-gateway (requests_total y duration nunca incrementadas). Diagnóstico: `curl /metrics | grep '^# HELP'` y comparar contra la spec.
2. **`grep '^gateway_'` cuenta LÍNEAS, no métricas**: un histograma genera muchas líneas (bucket/sum/count). Para contar métricas registradas usar `grep '^# HELP'` y filtrar.
3. **httprate limita por IP**: 61 requests rápidos → el 61º da 429. En pruebas eso es comportamiento esperado, no un bug.
4. **Auth se delega al backend Python**: probar endpoints protegidos directo contra el backend da 401 sin JWT — esperado. Probar el flujo completo requiere token.
5. **Go no tiene PyO3**: para integrar Go con Python usar HTTP proxy, Redis compartido, o gRPC. NUNCA shared library cgo + ctypes (frágil, sin maturin equivalente). FFI in-process = Rust.
6. **GOMEMLIMIT en contenedores**: sin él, OOM kills en VPS con RAM limitada.
7. **Graceful shutdown**: registrar SIGINT/SIGTERM y `srv.Shutdown(ctx)` con timeout — perder requests en deploy es inaceptable.

## Archivos de soporte
- `references/legaltech-gateway.md` — estado del proyecto, layout, endpoints, env vars, bugs conocidos, SPEC-002 pendiente.
- `scripts/verify-legaltech-gateway.sh` — verificación completa local (go test) + servidor (systemd + endpoints) en un solo comando.
