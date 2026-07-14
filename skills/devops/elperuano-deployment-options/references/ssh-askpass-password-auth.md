# SSH Password Auth sin sshpass (SSH_ASKPASS + Python)

Cuando `sshpass` no está instalado ni hay sudo para instalarlo, y el servidor solo acepta password auth (no key-based), usar este patrón.

## Técnica: SSH_ASKPASS vía Python subprocess

Crear script temporal que devuelve la contraseña, setear `SSH_ASKPASS` + `DISPLAY` en el entorno, y ejecutar ssh/scp con ese entorno.

```python
import subprocess
import os

# 1. Crear script que devuelve la password
with open('/tmp/askpass.sh', 'w') as f:
    f.write('#!/bin/bash\necho PASSWORD_HERE\n')
os.chmod('/tmp/askpass.sh', 0o755)

# 2. Configurar entorno
env = os.environ.copy()
env['SSH_ASKPASS'] = '/tmp/askpass.sh'
env['DISPLAY'] = ':0'

# 3. Ejecutar SSH (sin setsid — subprocess.run maneja todo)
result = subprocess.run(
    ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
     'user@host', 'comando_remoto'],
    capture_output=True, text=True, timeout=15, env=env
)
print(result.stdout)
```

## Por qué funciona

- SSH intenta key auth primero → falla
- SSH busca `SSH_ASKPASS` → ejecuta el script → obtiene la password
- `DISPLAY=:0` engaña a SSH haciéndole creer que hay un display gráfico (necesario para que SSH_ASKPASS se active en non-TTY)
- `subprocess.run` no tiene TTY → SSH no puede hacer prompt interactivo → cae a SSH_ASKPASS

## SCP también funciona

```python
subprocess.run(
    ['scp', '-o', 'StrictHostKeyChecking=no', src, 'user@host:/ruta/dst'],
    capture_output=True, text=True, timeout=15, env=env
)
```

## Fallos conocidos

- **`setsid` bloqueado por Hermes**: No usar `setsid ssh ...`. Usar `subprocess.run` directamente.
- **`ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory`**: Significa que SSH_ASKPASS no está seteado, o el script no es ejecutable. Verificar `chmod +x`.
- **`Permission denied (publickey,password)`**: La password es incorrecta. Verificar credenciales en memoria.
