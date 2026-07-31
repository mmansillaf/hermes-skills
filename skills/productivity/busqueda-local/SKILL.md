---
name: busqueda-local
description: Buscador local de archivos en WSL (D:/ C:/ F:) sin consumir tokens LLM. Script bash autónomo.
category: productivity
---

# Búsqueda Local de Archivos

Script autónomo que busca archivos en los discos montados en WSL sin necesidad de que el agente Hermes intervenga — **cero tokens consumidos**.

## Instalación

El script está en `D:\PyCode\busqueda_local.sh` (accesible desde WSL en `/mnt/d/PyCode/busqueda_local.sh`).

Ya está ejecutable (`chmod +x`).

## Uso desde terminal WSL

```bash
/mnt/d/PyCode/busqueda_local.sh <patrón> [opciones]
```

### Por nombre de archivo

```bash
# Buscar archivos con "historia" en D:\ (por defecto)
/mnt/d/PyCode/busqueda_local.sh historia

# Buscar imágenes JPG
/mnt/d/PyCode/busqueda_local.sh "*.jpg"

# Buscar en C:\Users\usuario\
/mnt/d/PyCode/busqueda_local.sh historia -c

# Buscar en la SD (F:\)
/mnt/d/PyCode/busqueda_local.sh "peru*" -f

# Buscar en todos los discos
/mnt/d/PyCode/busqueda_local.sh informe -a
```

### Por contenido de archivo (más lento)

```bash
/mnt/d/PyCode/busqueda_local.sh "inclusion financiera" -t
```

### Ruta personalizada

```bash
/mnt/d/PyCode/busqueda_local.sh "foto*" /mnt/d/Descargas
```

## Opciones

| Opción | Descripción |
|---|---|
| `-c` | Buscar en C:\Users\usuario\ |
| `-d` | Buscar en D:\ (por defecto) |
| `-f` | Buscar en F:\ (SD card) |
| `-a` | Buscar en todos los discos accesibles |
| `-t` | Buscar por CONTENIDO (grep), no por nombre |

## Ventajas

- **No consume tokens** — corre directo en tu terminal
- **No necesita internet**
- **Excluye automáticamente** `.venv/`, `node_modules/`, `__pycache__/`, `.git/`
- **Límite de profundidad** de 5 niveles para no colgarse
- **Modo contenido** busca dentro del texto de los archivos

## alias recomendado

Agrega esto a `~/.bashrc`:

```bash
alias buscar='/mnt/d/PyCode/busqueda_local.sh'
```

Después recarga con `source ~/.bashrc` y usas:

```bash
buscar historia
buscar "*.jpg" -f
buscar "machine learning" -t
```
