# Deploy Scripts — Bugs Encontrados y Correcciones

Sesión: 05-may-2026 (VM staging Ubuntu). Scripts en `deploy/`.

## Bug 1: `install.sh` se congela esperando sudo

**Línea 22-23**: `sudo apt-get update -qq` y `sudo apt-get install -y -qq` esconden el prompt `[sudo] password:`.

**Síntoma**: Sale `[✓] Actualizando paquetes del sistema...` y script queda bloqueado para siempre.

**Fix**: Agregar al inicio del script:
```bash
sudo echo "sudo OK" >/dev/null || { echo "Necesitas sudo. Ejecuta: sudo echo test"; exit 1; }
```
O mejor, verificar al principio si el usuario tiene sudo sin pedir contraseña.

## Bug 2: `start.sh` sale silenciosamente si Docker no existe

**Línea 8**: `set -e` + **línea 24**: `docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null`

**Síntoma**: Script imprime `[✓] Iniciando Qdrant + Neo4j (Docker)...` y vuelve al prompt. No hay mensaje de error.

**Causa**: Ambos comandos Docker fallan → `||` encadena el fallo → `set -e` mata el script sin mensaje.

**Fix**: Verificar Docker ANTES:
```bash
if ! command -v docker &>/dev/null; then
    err "Docker no instalado. Ejecuta: bash install.sh"
    exit 1
fi
docker compose up -d || err "Docker Compose falló. ¿Existe docker-compose.yml?"
```

### Bug 2a: Variante — Permission denied (usuario no está en grupo docker)

**Mismo síntoma** que Bug 2. El script imprime `[✓] Iniciando Qdrant + Neo4j (Docker)...` y muere.

**Causa**: El usuario ejecuta `docker compose up -d` sin `sudo` y no está en el grupo `docker`. El `2>/dev/null` se traga el mensaje `permission denied while trying to connect to the docker API`. `set -e` mata el script.

**Detección**: `docker compose ps` → `permission denied`.

**Fix inmediato**: `sudo docker compose up -d`

**Fix permanente**: `sudo usermod -aG docker $USER` + re-login.

## Bug 3: `start.sh` línea 159-165 — API nunca arranca en primer intento

```python
nohup python3 -c "
import uvicorn, os, sys
sys.path.insert(0, '.')
from fastapi.staticfiles import StaticFiles
from api_rest import app
app.mount('/', StaticFiles(directory='static', html=True), name='static')
" > logs/api.log 2>&1 &
```

**Problema**: Importa y monta static files pero **NUNCA llama a `uvicorn.run(app)`**. El proceso Python importa, monta, y sale inmediatamente. La API no se inicia.

**Consecuencia**: Siempre cae al fallback de línea 171 (`nohup python3 api_rest.py`). El primer método es código muerto.

**Fix**: O bien arreglar el one-liner para incluir `uvicorn.run(app, host='0.0.0.0', port=8000)`, o simplemente eliminar el primer intento y usar solo el fallback.

## Bug 4: `install.sh` corriendo desde directorio equivocado

Scripts usan rutas relativas (`requirements.txt`, `data/normas_total.db`, `.venv`). Si el usuario ejecuta `install.sh` desde un subdirectorio (ej: `data/`), el `.venv` y `docker-compose.yml` se crean ahí, no en `/opt/elperuano/`.

**Fix**: Agregar al inicio de install.sh y start.sh:
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
```

## Bug 5: `test.sh` — secuencias de escape sin interpretar

**Línea con `$GREEN`/`$RED`**: Las variables de color no se expanden correctamente en el resumen, produciendo texto como `\033[0;32m0 OK\033[0m` en vez de texto coloreado.

**Fix**: Usar `echo -e` o `printf` en vez de `echo`.

## Bug 6: `start.sh` — health check no detecta bien el formato

**Línea 169**: `grep -q '\"ok\"'` — espera `"ok"` pero el endpoint `/health` devuelve `{"status": "ok"}`. El grep con `\"ok\"` sí matchea, pero es frágil.

**Fix**: Usar `grep -q '"status": *"ok"'` o `python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('status')=='ok' else 1)"`.

## Bug 7: `logs/` directory no existe — nohup falla con exit 1

**Línea**: `nohup python3 api_rest.py > logs/api.log 2>&1 &`

**Síntoma**: `[1]+ Salida 1` inmediatamente después del nohup. API no arranca.

**Causa**: El directorio `logs/` no existe. `nohup` redirige stdout a `logs/api.log` pero el shell no puede crear el archivo en un directorio inexistente → el proceso Python muere antes de ejecutarse. El error real se pierde porque la redirección falla antes de que Python emita nada.

**Fix**: Agregar `mkdir -p logs` al inicio de start.sh, antes de cualquier nohup.

## Bug 8: `.venv/bin/python3` vs `python3` — el venv no persiste en subshells

**Síntoma**: Usuario hace `source .venv/bin/activate`, escribe cualquier subshell (`bash`, `su`, screen/tmux nuevo), y `python3` vuelve a apuntar al sistema. `pip install` instala en el Python del sistema, no en el venv.

**Causa**: `source` solo afecta al shell actual. Cualquier subshell pierde la activación. Si además el `$PATH` del usuario tiene `/usr/bin/python3` antes que `.venv/bin/python3`, los comandos `python3` y `pip` van al sistema.

**Detección**: `which python3` → `/opt/elperuano/.venv/bin/python3` pero `.venv/bin/python3 -c "import fastapi"` falla. `pip list | grep fastapi` sale vacío aunque se instaló requirements.txt (se instaló en el sistema).

**Fix**: Usar rutas absolutas al venv en vez de confiar en `source activate`. Esto es inmune a subshells:

```bash
# CORRECTO (funciona siempre):
.venv/bin/pip install -r requirements.txt
nohup .venv/bin/python3 api_rest.py > logs/api.log 2>&1 &

# INCORRECTO (frágil, se rompe con subshells):
source .venv/bin/activate
pip install -r requirements.txt
bash  # ← el venv se pierde aquí
nohup python3 api_rest.py ...
```

**Fallout**: Si el usuario ya instaló requirements.txt con el pip del sistema, las dependencias están en `/usr/lib/python3/dist-packages/`, no en `.venv/lib/python3.*/site-packages/`. Hay que reinstalar con `.venv/bin/pip`.

## Bug 9: `validation_agent.py:365` — SyntaxError en f-string multilínea (doble causa)

**Síntoma**: `api_rest.py` importa `src/agents/validation_agent.py` → `SyntaxError: unterminated string literal (detected at line 365)`.

**Causa A (obvia)**: El f-string está truncado — le faltan `:.1f}%"` al cierre:

```python
# ROTO (le falta el cierre):
"rejection_rate": f"{((self.stats['rules_rejections'] + 
                      self.stats['embedding_rejections'] + 
                      self.stats['llm_rejections']) / total * 100):>
```

**Causa B (raíz, más sutil)**: Aun reparando el cierre, la expresión matemática `((self.stats[...] + self.stats[...] + ...) / total * 100)` OCUPA MÚLTIPLES LÍNEAS DENTRO DEL `{}` DEL F-STRING. Python 3.11 **NO** permite newlines dentro de expresiones f-string. Esto solo funciona en Python 3.12+ (PEP 701).

La VM staging corre Python 3.11.15 → la sintaxis correcta sigue fallando.

**Detección**:
```bash
.venv/bin/python3 --version  # Python 3.11.x = no soporta expresiones multilínea en f-strings
sed -n '363,370p' src/agents/validation_agent.py
```

**Fix correcto (compatible 3.11+)**: Extraer los valores a variables antes del f-string:

```python
reject_val = (self.stats["rules_rejections"] + 
              self.stats["embedding_rejections"] + 
              self.stats["llm_rejections"]) / total * 100
rules_val = self.stats["rules_rejections"] / total * 100
llm_val = self.stats["llm_calls"] / total * 100
return {
    **self.stats,
    "rejection_rate": f"{reject_val:.1f}%",
    "rules_rejection_rate": f"{rules_val:.1f}%",
    "llm_usage_rate": f"{llm_val:.1f}%"
}
```

**Fix alternativo (si se usa Python 3.12+)**: Todo en una sola línea:
```python
"rejection_rate": f"{((self.stats['rules_rejections'] + self.stats['embedding_rejections'] + self.stats['llm_rejections']) / total * 100):.1f}%",
```

## Bug 10: Venv movido de ubicación — shebangs rotos en pip/python

**Síntoma**: `.venv/bin/pip3` falla con `no se ha encontrado el fichero requerido`, o `.venv/bin/python3` es solo un symlink a `/usr/bin/python3` (venv no aislado).

**Causa**: El venv fue creado en una ruta (ej: `/media/usuario/ARCHVOS01/PyCode/...`) y luego movido a otra (`/home/usuario/...`). Los scripts en `.venv/bin/` tienen shebangs hardcodeados a la ruta original:

```
head -1 .venv/bin/pip3
#!/media/usuario/ARCHVOS01/PyCode/PeruanoSearchEngine02/.venv/bin/python3
```

Y `pyvenv.cfg` referencia el `home` y `command` originales:
```
home = /usr/bin
command = /usr/bin/python3 -m venv /media/usuario/ARCHVOS01/...
```

**Fix**: Recrear el venv en la ubicación final:
```bash
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Workaround temporal si no se puede recrear**: Usar `python3 -m pip` en vez de `pip` directamente:
```bash
.venv/bin/python3 -m pip install fastapi uvicorn  # funciona (no usa el shebang roto)
.venv/bin/pip install fastapi                     # falla (shebang roto)
```

## Bug 11: `requirements.txt` falta `fastapi` y `uvicorn`

**Síntoma**: `ModuleNotFoundError: No module named 'fastapi'` después de instalar requirements.txt.

**Causa**: `requirements.txt` no incluye `fastapi` ni `uvicorn`. Solo están las dependencias de datos/NLP (qdrant-client, sentence-transformers, neo4j, groq, streamlit, etc.).

**Fix**: Agregar a `requirements.txt`:
```
fastapi>=0.100.0
uvicorn>=0.23.0
```

O instalar manualmente después del deploy:
```bash
.venv/bin/python3 -m pip install fastapi uvicorn
```

## Bug 12: Paquete de deploy (`elperuano_mvp.tar.gz`) contiene archivos stale

**Síntoma**: Después de corregir bugs en la VM, el siguiente deploy desde el tar.gz original reintroduce los mismos errores.

**Causa**: `deploy/deploy.sh --prepare` genera un tar.gz con el estado actual del repo. Si se corrige un archivo en la VM pero no en la máquina local, el próximo deploy revierte el fix.

**Fix**: Después de cualquier fix en la VM, aplicar el mismo fix en la máquina local Y regenerar el paquete:
```bash
# En máquina local (ThinkPad):
cd ~/el_peruano_rag/PeruanoSearchEngine02
# ... aplicar fix en archivos fuente ...
bash deploy/deploy.sh --prepare    # regenera elperuano_mvp.tar.gz
```

**⚠️ Python 3.12 local vs Python 3.11 VM**: La máquina local usa Python 3.12 donde los f-strings multilínea funcionan. El código que compila en local puede fallar en la VM (Python 3.11). Siempre verificar con `python3 --version` en ambos entornos.


## Bug 13: COUNT aggregation no llega al LLM

**Síntoma**: Queries como "¿Cuántas RM en 2024?" devuelven ejemplos sueltos sin el total numérico.

**Causa**: `_build_context(results)` no recibe `sources`. El COUNT se ejecuta y guarda en `sources["sql_count"]` pero nunca se inyecta en el prompt del LLM.

**Fix**: `_build_context(results, sources=None)`. Cuando `sources` tiene `sql_count`, inyectar bloque `[DATOS AGREGADOS]` con total+breakdown. Afecta `generate_answer()` y `generate_answer_stream()` en `api_rest.py`.

## Bug 14: `consultar.py` no se incluye en el paquete de deploy

**Síntoma**: Después del deploy, `ls /opt/elperuano/consultar.py` → no existe. El usuario no encuentra el script cliente.

**Causa**: El `deploy/deploy.sh --prepare` genera el tar.gz con `src/`, `api_rest.py`, scripts `deploy/`, pero `scripts/consultar.py` (o `consultar.py` suelto en la raíz del proyecto) no se incluye.

**Fix**: Copiarlo manualmente después del deploy:
```bash
scp consultar.py cmansilla@192.168.18.217:/opt/elperuano/
ssh cmansilla@192.168.18.217 "chmod +x /opt/elperuano/consultar.py"
```

O mejor: agregar `consultar.py` a la lista de archivos en `deploy/deploy.sh --prepare`.

## Orden de diagnóstico (si la API no responde)

1. `docker --version` → ¿Docker instalado?
2. `docker compose ps` → ¿Permisos docker OK? (si sale "permission denied" → Bug 2a)
3. `ls docker-compose.yml` → ¿Existe?
4. `ls .venv/bin/python3` → ¿Entorno Python creado?
5. `.venv/bin/python3 --version` → ¿Python 3.11 o 3.12? (influye en Bug 9)
6. `.venv/bin/python3 -c "import fastapi; print('OK')"` → ¿Dependencias en el venv? (si falla → Bug 8/10)
7. `head -1 .venv/bin/pip3` → ¿Shebang apunta a ruta que aún existe? (si no → Bug 10)
8. `ls -lh data/normas_total.db` → ¿DB copiada?
9. `ls -d logs/` → ¿Directorio logs existe? (si no → Bug 7, `mkdir -p logs`)
10. `cat logs/api.log` → ¿Error real de Python?
11. Si el error es `SyntaxError` en `validation_agent.py:365` → Bug 9 (dos posibles causas, ver arriba)
12. Si `ModuleNotFoundError: No module named 'fastapi'` → Bug 8 o Bug 10, revisar venv
