# Background Process Death (tcsetattr) en Hermes

## Síntoma
Cuando Hermes ejecuta un comando largo en background vía `terminal(background=True)`, el proceso muere silenciosamente después del primer output, con exit code 143 (SIGTERM) o 255.

Mensaje típico en stderr:
```
bash: no se puede establecer el grupo de proceso de terminal (-1): Función ioctl no apropiada para el dispositivo
bash: no hay control de trabajos en este intérprete de ordenes
```

## Causa
Hermes lanza comandos background en un contexto sin PTY (pseudo-terminal). Cuando el shell bash interno intenta hacer `tcsetattr()` (necesario para control de trabajos), falla porque no hay terminal real. El shell entonces aborta y mata al proceso hijo.

Esto ocurre con:
- `terminal(background=True)` con cualquier comando que use bash (scripts .sh, pipes, redirects)
- Especialmente con Python que imprime a stdout sin flush

NO ocurre con:
- `execute_code()` — ejecuta Python directamente, sin bash intermediario
- `terminal(foreground)` con timeout alto — funciona hasta el límite de 600s

## Soluciones probadas y su efectividad

### ✅ execute_code() — RECOMENDADO
No tiene el problema. Para batches largos, dividir en lotes de 5-10 docs y ejecutar secuencialmente.

### ⚠️ Redirección a archivo
```bash
PYTHONUNBUFFERED=1 python3 -u script.py > log.txt 2>&1
```
Funciona parcialmente — el script sobrevive pero el output puede bufferearse. Monitorear con `tail -f log.txt` desde otro terminal() call.

### ⚠️ batch_runner.py con subprocess.Popen
Iniciar llama-server como subprocess desde Python puro evita el bash intermediario:
```python
proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
```
Funciona pero Hermes no puede monitorear el progreso en tiempo real.

### ❌ Heredocs, pipes, nohup, &, setsid
Hermes bloquea estos patrones o mueren igual por falta de PTY.

## Patrón de trabajo para batches largos
1. Usar `execute_code()` para sub-batches de 5-10 docs (hasta 600s de timeout)
2. Acumular resultados en JSONs de checkpoint
3. Invocar execute_code() de nuevo para el siguiente sub-batch
4. Opcional: guardar progress file para reanudar si se interrumpe

## Referencia cruzada
Ver SKILL.md → "⚠ Pitfall: Procesos Python en background de Hermes NO flushean output y mueren por tcsetattr."
