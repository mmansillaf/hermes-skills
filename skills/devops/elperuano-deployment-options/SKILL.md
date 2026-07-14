---
name: elperuano-deployment-options
description: "Opciones de despliegue web para El Peruano RAG: Cloudflare Workers+Vectorize+D1+R2, GitHub Pages, Contabo VPS, HuggingFace Spaces. Analisis completo con costos y limites."
---

# El Peruano RAG — Opciones de Despliegue Web (Análisis Completo)

## Referencia: cloudflare-rag (RafalWilinski)

Repo: https://github.com/rafalwilinski/cloudflare-rag (599 stars, 90 forks)

Arquitectura full-Cloudflare:
- Workers (API serverless) + Pages (frontend) 
- D1 (SQLite-compatible DB) + Vectorize (embeddings)
- R2 (file storage) + KV (rate limiting)
- AI Gateway (multi-provider LLM routing: Groq, OpenAI, Anthropic)
- Workers AI como fallback gratuito
- Hybrid RAG: Full-Text Search (D1) + Vector Search (Vectorize)
- Streaming SSE al frontend
- Deploy button: one-click deploy a Cloudflare

## Cloudflare Workers AI — Modelos Disponibles (Mayo 2026)

| Modelo | Tipo | Dims | Multilingüe |
|--------|------|------|-------------|
| `llama-3.1-70b-instruct` | Text Gen | — | ✅ Sí |
| `llama-3.1-8b-instruct-fast` | Text Gen | — | ✅ Sí |
| `llama-4-scout-17b-16e` | Text Gen | — | ✅ Sí |
| `bge-large-en-v1.5` | Embeddings | 1024d | ❌ Solo EN |
| `bge-small-en-v1.5` | Embeddings | 384d | ❌ Solo EN |
| `bge-base-en-v1.5` | Embeddings | 768d | ❌ Solo EN |

**Hallazgo crítico:** Workers AI NO tiene modelo de embeddings multilingüe. MiniLM 384d (nuestro modelo actual, español) no existe en Workers AI. Esto bloquea la migración completa.

## Límites Cloudflare (Free Tier)

### Vectorize
| Límite | Free | Paid |
|--------|------|------|
| Indexes | 100 | 50,000 |
| Vectores/index | 10,000,000 | 10,000,000 |
| Dimensiones máx | 1536 | 1536 |
| Metadata/vector | 10 KB | 10 KB |
| Upsert batch | 5,000 HTTP | 5,000 HTTP |

→ Nuestros 21,584 vectores 384d caben en 1 índice. 5 batches de 5K.

### D1
| Límite | Free | Paid |
|--------|------|------|
| DB size | 500 MB | 10 GB |
| Storage account | 5 GB | 1 TB |
| Rows/table | Ilimitado | Ilimitado |
| Row size | 2 MB | 2 MB |
| Queries/invocation | 50 | 1,000 |

→ Nuestra DB SQLite ~200 MB cabe en Free. 18,694 normas en 1 tabla.

### Workers
| Límite | Free | Paid |
|--------|------|------|
| Requests/día | 100,000 | 10M+ |
| CPU/request | 10 ms | 30-50 ms |
| Duración máx | 10s | 30s |

→ 100K req/día = ~3,300 consultas/día. Suficiente para demo/producción pequeña.

### R2
| Límite | Free |
|--------|------|
| Storage | 10 GB |
| Class A ops | 1M/mes |
| Class B ops | 10M/mes |

→ 80 MB HTMLs + 66 MB SQLite = 146 MB. Sobra espacio.

## Arquitecturas Evaluadas

### A) Full Cloudflare (Workers + Vectorize + D1 + R2 + AI Gateway)

```
┌─────────────────────────────────────────────────────────┐
│                    Cloudflare (Gratis)                    │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Pages   │  │ Workers  │  │Vectorize │  │   R2    │ │
│  │ Frontend │  │ API (JS) │  │Embeddings│  │  HTMLs  │ │
│  └──────────┘  └────┬─────┘  └──────────┘  └─────────┘ │
│                     │         ┌──────────┐              │
│                     ├────────▶│    D1    │              │
│                     │         │  SQLite  │              │
│                     │         └──────────┘              │
│                     │         ┌──────────┐              │
│                     └────────▶│AI Gateway│              │
│                               │ Groq LLM │              │
│                               └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

**Costo: $0/mes**

**Problema crítico:** Workers son JavaScript (no Python). Requiere reescribir TODO api_rest.py (~1800 líneas Python → TypeScript). Workers AI SIN embeddings multilingüe → usaríamos Groq API via AI Gateway igual que ahora.

**Viabilidad:** ⚠️ Alto esfuerzo de migración (JS rewrite), bajo riesgo técnico. El modelo `cloudflare-rag` demuestra que funciona.

### B) Contabo VPS + Cloudflare R2 (Híbrido Recomendado)

```
┌──────────────────────┐     ┌─────────────────────────────┐
│   Cloudflare (Free)  │     │    Contabo VPS ($5.50/mes)   │
│                      │     │                              │
│  ┌────────┐ ┌──────┐ │     │  ┌────────┐ ┌────────────┐  │
│  │  R2    │ │ CDN  │ │     │  │FastAPI │ │  SQLite    │  │
│  │ HTMLs  │ │Cache │ │     │  │Python  │ │  normas    │  │
│  └────────┘ └──────┘ │     │  └────────┘ └────────────┘  │
│                      │     │  ┌────────┐ ┌────────────┐  │
│  ┌──────────────────┐ │     │  │ Qdrant │ │  Neo4j     │  │
│  │  GitHub Pages    │ │     │  │Docker  │ │  Docker    │  │
│  │  Landing + Docs  │ │     │  └────────┘ └────────────┘  │
│  └──────────────────┘ │     │                              │
└──────────────────────┘     └─────────────────────────────┘
```

**Costo: $5.50/mes (solo VPS)**

**Ventajas:** Cero migración de código. Misma API, mismas DBs. Agregar R2 para HTMLs fuente + CDN.

**Viabilidad:** ✅ Inmediata. Ya tienes cuenta Contabo. Solo requiere docker-compose en VPS + deploy del repo.

### C) HuggingFace Spaces + Qdrant Cloud

```
┌──────────────────────────┐     ┌──────────────────────┐
│  HuggingFace Spaces Free │     │  Qdrant Cloud Free   │
│                          │     │                      │
│  ┌────────────────────┐  │     │  1 GB cluster       │
│  │  FastAPI/Gradio    │  │     │  21K vectores       │
│  │  Python runtime    │  │     │                      │
│  │  16 GB RAM         │  │     └──────────────────────┘
│  └────────────────────┘  │
│                          │     ┌──────────────────────┐
│  ┌────────────────────┐  │     │  Cloudflare R2       │
│  │  SQLite (readonly) │  │     │  HTMLs fuente        │
│  └────────────────────┘  │     └──────────────────────┘
└──────────────────────────┘
```

**Costo: $0/mes**

**Problemas:** Sin Docker → sin Neo4j. Qdrant Cloud free 1 GB (nuestros vectores son ~600 MB — caben justo). Spaces duerme después de inactividad.

**Viabilidad:** ⚠️ Para demo. Sin Neo4j se pierde ~20% del scoring.

### D) GitHub Actions + GitHub Pages + Contabo (CI/CD Completo)

```
┌──────────────────────────────────────────────────────┐
│                   GitHub (Gratis)                     │
│                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │   Pages    │  │  Actions   │  │   Container    │  │
│  │  Landing   │  │  Test CI   │  │   Registry     │  │
│  │  Docs HTML │  │  Auto-bateria│ │   Docker img   │  │
│  └────────────┘  └─────┬──────┘  └────────────────┘  │
│                        │ SSH deploy on push           │
└────────────────────────┼─────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────┐
│              Contabo VPS ($5.50/mes)                  │
│  Docker Compose: API + Qdrant + Neo4j + SQLite       │
└──────────────────────────────────────────────────────┘
```

**Ventaja extra:** GitHub Actions ejecuta la batería de 50 preguntas automáticamente en cada push y genera el informe HTML → GitHub Pages.

## Comparativa Final

| Opción | Costo/mes | Migración | Neo4j | Qdrant | Embeddings | LLM |
|--------|-----------|-----------|-------|--------|------------|-----|
| **A) Full Cloudflare** | $0 | Alta (JS rewrite) | ❌ | Vectorize | ❌ SIN multi | Groq |
| **B) Contabo + CF** | **$5.50** | **Nula** | ✅ | ✅ | ✅ MiniLM | Groq |
| **C) HF Spaces** | $0 | Media | ❌ | Qdrant Cloud | ✅ MiniLM | Groq |
| **D) GitHub + Contabo** | **$5.50** | **Nula + CI/CD** | ✅ | ✅ | ✅ MiniLM | Groq |

## Recomendación Final: MVP Auto-contenido en Contabo VPS (Mayo 2026)

**Tras la refactorización F1-F5+D1 (05-may-2026), la estrategia se simplificó:**

1. ~~GitHub Pages~~ — ❌ Ahora requiere registro como empresa + medio de pago. Descartado.
2. ~~Cloudflare R2~~ — ❌ Los 80 MB HTMLs fuente no se usan. Las citas son por número de norma, no por link.
3. ~~GitHub Actions CI/CD~~ — ❌ Exceso para MVP. Posponer.
4. **Contabo VPS** — ✅ Único componente necesario. $5.50/mes.

**Arquitectura final: Todo auto-contenido en el VPS. Sin servicios externos.**

Scripts de despliegue simplificados: `deploy/deploy.sh`, `deploy/install.sh`, `deploy/start.sh`, `deploy/test.sh`

**⚠️ `consultar.py` NO va en el paquete de deploy.** El tar.gz no lo incluye. Hay que copiarlo manualmente al server después del deploy:
```bash
scp scripts/consultar.py cmansilla@192.168.18.217:/opt/elperuano/
ssh cmansilla@192.168.18.217 "chmod +x /opt/elperuano/consultar.py"
```

**⚠️ SSH password auth sin sshpass:** Si `sshpass` no está instalado, usar `SSH_ASKPASS` vía Python subprocess. Ver `references/ssh-askpass-password-auth.md`.

Ver referencia completa: `references/mvp-simplified-deploy.md`

**Costo total: $5.50/mes (solo VPS)**

## Referencias

- `references/mvp-simplified-deploy.md` — MVP auto-contenido (nuevo, Mayo 2026)
- `references/deploy-script-bugs.md` — 12 bugs en scripts deploy/ + diagnóstico (Mayo 2026, actualizado 05-may)
- `references/docker-volume-transfer.md` — Transferir Qdrant + Neo4j entre máquinas via paramiko SFTP
- `references/count-aggregation-fix.md` — Fix para queries COUNT (context injection + tipo_norma filtering)
- `references/security-and-analytics.md` — Auth, rate limiting, JWT, query_log
- `references/performance-optimization.md` — Streaming SSE, paralelización, cache LRU, benchmarks

## Scripts

- `scripts/consultar.py` — Cliente Python para la API (modo argumentos e interactivo). Copiar a `~/consultar.py` y usar: `python3 consultar.py "Ley 32108"`

## Plan de implementacion (simplificado)

1. **Fase 0: VM Ubuntu local** — Validar con scripts `deploy/` (sin costo)
2. **Fase 1: Contabo VPS** — `deploy/deploy.sh --send <IP>` + `install.sh` + `start.sh`
3. **Fase 2 (futuro): GitHub Actions** — CI/CD opcional cuando se necesite

## Servir Web UI junto a la API REST (FastAPI)

Cuando se agrega una interfaz web estatica (HTML+CSS+JS) al mismo puerto que la API REST, NO usar `app.mount("/", StaticFiles(...))`.

**Problema con `app.mount("/")`:** En Starlette/FastAPI, montar en la raiz interfiere con las rutas de la API. Causa `404 Not Found` tanto en la raiz como en otros endpoints en ciertas configuraciones.

**Solucion: Usar `@app.get("/")` con HTMLResponse**

```python
from fastapi.responses import HTMLResponse

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
else:
    INDEX_HTML = None

@app.get("/", include_in_schema=False)
async def serve_ui():
    if INDEX_HTML:
        return HTMLResponse(INDEX_HTML)
    return {"status": "ui_not_available"}
```

**Ventajas:** No conflictua con rutas existentes. Sirve HTML auto-contenido.

**Estructura recomendada:** `static/index.html` (44KB, ~1300 lineas, HTML+CSS+JS embebido). La UI carga datos via fetch() a los endpoints existentes (`/query`, `/health`, `/stats`, `/token-stats`).

## Operaciones en VM Staging (SSH + sshpass)

### Conexión SSH con contraseña
```bash
# Instalar sshpass si no está disponible
sudo apt-get install -y sshpass

# Conexión básica
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no cmansilla@IP "comando"

# Comandos sudo con sshpass (requiere -S flag)
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no cmansilla@IP \
  "echo 'PASSWORD' | sudo -S apt-get install -y python3-venv"
```

### python3-venv: error "ensurepip not available"
En Ubuntu 24.04 minimal, `python3 -m venv` falla porque `python3-venv` no está instalado:
```
The virtual environment was not created successfully because ensurepip is not available.
```
Fix:
```bash
echo 'PASSWORD' | sudo -S apt-get install -y python3-venv python3-pip
```

### .venv inflado por CUDA (5.5 GB sin GPU)
El `.venv` se instala con torch CUDA por defecto, ocupando ~5.5 GB en VMs sin GPU:
- `nvidia/`: 2.7 GB (CUDA libraries — basura sin GPU)
- `triton/`: 641 MB (CUDA kernel compiler — basura sin GPU)
- `torch/`: 1.2 GB (incluye CUDA)

**Solución: Recrear .venv con torch CPU-only:**
```bash
# 1. Eliminar .venv inflado y cache
rm -rf .venv ~/.cache/huggingface/

# 2. Crear venv limpio
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar torch CPU-only (NO CUDA)
pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

# 4. Instalar resto de dependencias
pip install --no-cache-dir sentence-transformers transformers \
  qdrant-client neo4j groq fastapi uvicorn pydantic \
  python-dotenv beautifulsoup4 lxml tqdm markdownify \
  pandas numpy scipy click rich PyMuPDF pdfplumber \
  pyyaml pytest pytest-asyncio
```
**Resultado:** .venv de ~5.5 GB → ~2 GB. Ahorro: ~3.4 GB.

⚠️ `pip install` completo toma 5-10 minutos. Ejecutar en **background**:
```bash
# El flag background=true + notify_on_complete=true en terminal()
# para procesos largos. No intentar en foreground.
```

### Sincronizar código desde repo local a VM (rsync)
Preservar datos (no sobrescribir data/, .venv/ en destino):
```bash
cd /ruta/repo/local
sshpass -p 'PASSWORD' rsync -avz --delete \
  --exclude='.venv/' \
  --exclude='data/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.git/' \
  --exclude='logs/' \
  -e 'ssh -o StrictHostKeyChecking=no' \
  ./ cmansilla@IP:/opt/elperuano/
```

### Docker: Permission denied (usuario no en grupo docker)

**Síntoma:** `docker ps` falla con `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
El socket `/var/run/docker.sock` es `srw-rw---- root:docker`. El usuario no está en el grupo `docker`.

**Fix:**
```bash
echo 'PASSWORD' | sudo -S usermod -aG docker cmansilla
```
Luego abrir NUEVA sesión SSH (el cambio de grupo solo aplica a nuevas sesiones, no a la actual).

### Paquetes faltantes post-venv

Después de recrear el `.venv`, pueden faltar paquetes no listados en `requirements.txt`:

| Paquete | ¿Por qué falta? | Síntoma |
|---------|----------------|---------|
| `requests` | No está en `requirements.txt` (es dependencia transitiva de otros paquetes, pero torch CPU-only no lo arrastra) | Qdrant health check falla con `No module named 'requests'` |

Fix:
```bash
pip install --no-cache-dir requests
```

### Diagnóstico rápido (30 segundos)
```bash
sshpass -p 'PASSWORD' ssh cmansilla@IP "\
  echo '=== Docker ==='; docker compose ps 2>&1; \
  echo '=== API ==='; curl -s --max-time 3 http://localhost:8000/health; \
  echo '=== Errores ==='; tail -5 logs/api.log 2>/dev/null | grep -iE 'error|traceback'; \
  echo '=== Disco ==='; df -h / | tail -1; \
  echo '=== Python ==='; python3 --version; \
  echo '=== Git ==='; cd /opt/elperuano && git log --oneline -1 2>/dev/null || echo 'sin repo'"
```

### Liberar espacio en disco
Cuando el disco está al 99%, el problema suele ser el .venv con CUDA:
```bash
# 1. Eliminar .venv inflado
rm -rf .venv

# 2. Snap old versions
sudo snap remove --revision <REV> <PACKAGE>   # snap list --all para ver versiones

# 3. Cache
sudo apt clean
sudo apt autoremove -y
rm -rf ~/.cache/pip ~/.cache/huggingface/

# 4. Journal logs viejos
sudo journalctl --vacuum-size=100M

# 5. Recrear .venv sin CUDA (ver sección arriba)
```

## Requisitos del Sistema (VM / VPS)

**Mínimo para MVP funcional:**

| Recurso | Mínimo | Recomendado | Nota |
|---------|--------|-------------|------|
| RAM | 8 GB | 16 GB | Modelo embeddings ~500 MB en RAM |
| Disco | 30 GB | 50 GB | DB 1.1 GB + Qdrant 400 MB + Neo4j 850 MB + modelo 500 MB + OS |
| CPU | 4 cores | 8 cores | Vectorización inicial ~30 min en 4 cores |
| SO | Ubuntu 22.04+ | Ubuntu 24.04 | Python 3.11+ requerido |

**⚠️ Compatibilidad Python:** La VM debe usar Python 3.11+. Si usa 3.11,
los f-strings con expresiones multilínea **no funcionan** (PEP 701, solo 3.12+).
El código ya está adaptado para 3.11 (ver Bug 9 en `references/deploy-script-bugs.md`).

**⚠️ Modelo de embeddings (MiniLM):** Ocupa ~470 MB en `~/.cache/huggingface/`.
En VMs con poco disco (< 1 GB libre después de instalar datos), configurar:
```bash
echo 'HF_HOME=/tmp/huggingface' >> .env
```
Esto descarga el modelo en `/tmp` (se pierde al reiniciar pero la VM de staging
no necesita persistirlo). Alternativa: usar un volumen Docker para el cache.

**⚠️ Espacio en disco:** Verificar ANTES de transferir datos:
```bash
df -h /  # Debe tener al menos 5 GB libres para Qdrant + Neo4j + modelo
```

## VM Staging (Fase 0 — Validación Pre-Contabo)

Scripts en `deploy/` (simplificados, sin dependencias externas):

```bash
# En laptop:
./deploy/deploy.sh --prepare
./deploy/deploy.sh --send 192.168.x.x

# En VM:
cd /opt/elperuano
bash install.sh     # Docker + Python + dependencias
bash start.sh       # Iniciar Qdrant+Neo4j+API+landing
bash test.sh        # 10 preguntas de prueba
```

**IMPORTANTE:** `normas_total.db` (1,055 MB) NO se incluye en el paquete. Copiar aparte por SCP.

**⚠️ Bugs conocidos:** Ver `references/deploy-script-bugs.md` — 12 bugs en install.sh/start.sh/test.sh que causan fallos silenciosos en VM staging. El más crítico es **Bug 9** (f-string multilínea en validation_agent.py incompatible con Python 3.11). 

**Diagnóstico rápido (30 segundos):**
```bash
ssh cmansilla@IP && cd /opt/elperuano
sudo docker compose ps 2>&1 | grep -E 'Up|Exit|permission'  # Docker?
curl -s http://localhost:8000/health                         # API?
tail -20 logs/api.log | grep -iE 'error|traceback|syntax'   # Error?
df -h / | tail -1                                            # Disco?
.venv/bin/python3 --version                                  # Python 3.11/3.12?
```

**Preguntas de prueba post-deploy:**
```bash
# Query simple por número
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Ley 32108","profile":"abogado"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:300])"

# Query de agregación (COUNT)
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Cuántas Resoluciones Ministeriales hay en 2024?","profile":"fiscal"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:200])"
```

**⚠️ Datos Docker (Qdrant + Neo4j):** No van en el tar.gz. Transferir por SFTP/SCP desde máquina local. Ver `references/docker-volume-transfer.md`.

API de pago: 238x mas cara que pipeline actual ($510 vs $2.14 para 40K docs). NO conviene.
Open-source: mismo costo en tokens (usa Groq igual). No justifica migrar.
Unico uso viable: Monitor gratuito (500 creditos/mes) para detectar nuevas normas.
API key en .env: SCRAPEGRAPHAI_API_KEY=sgai-998ef23f-...

## Autenticacion y Usuarios (Cloudflare Access)

Cloudflare Access (Zero Trust): login Google/GitHub sin codigo. Gratis hasta 50 usuarios.
Usuario → Cloudflare Access (login) → Workers (auth) → FastAPI :8000

### Implementacion propia (JWT + query_log)

Para >50 usuarios o datos propios de marketing, implementar auth propia.
Ver referencia completa: `references/security-and-analytics.md`
Incluye: rate limiting, JWT auth, schema usuarios + query_log + sessions,
flujo visitante→registrado, captura GeoIP, dashboard admin, datos marketing.

## Optimizacion de Rendimiento

Ver referencia completa: `references/performance-optimization.md`
Incluye: streaming SSE (TTFT 0.34s), paralelizacion asyncio (1.65x),
cache LRU, router 2 modelos (8B+70B), benchmarks reales Groq, veredicto Rust/PyO3.

## Web Fallback: 3+1 Capas

| Capa | Servicio | Costo |
|------|----------|-------|
| 1 | FTS5 89K HTMLs locales | $0 |
| 2 | Serper API | $0 (2.5K/mes) |
| 3 | Tavily API | $0 (free tier) |
| 4 | ScrapeGraphAI (pendiente) | $0 (500/mes) |

Solo se activa cuando confidence < 0.50.
