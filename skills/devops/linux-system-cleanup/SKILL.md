---
name: linux-system-cleanup
description: Diagnóstico y limpieza lógica de disco en Linux — inventario, categorización por seguridad, ejecución por lotes y verificación posterior.
trigger: El usuario pide "limpiar la PC", "liberar espacio", "revisar el disco", "cleanup", o reporta disco lleno.
tags: [linux, disk, cleanup, maintenance, system]
---

# Linux System Cleanup

## Flujo (3 fases)

### Fase 1: Inventario
Ejecutar en paralelo para tener panorama completo:

```bash
# Disco general
df -h /

# Cachés y temporales principales
du -sh /tmp /var/tmp /var/log /var/cache ~/.cache ~/.local/share/Trash 2>/dev/null | sort -rh

# Paquetes
apt list --upgradable 2>/dev/null
journalctl --disk-usage 2>/dev/null
dpkg -l 'linux-image-*' 2>/dev/null | grep '^ii' | awk '{print $2, $3}'

# Home — directorios visibles y ocultos
du -sh /home/*/ 2>/dev/null | sort -rh | head -20
du -sh /home/*/.[!.]* 2>/dev/null | sort -rh | head -20

# Tool-specific caches
pip cache info 2>/dev/null
npm cache ls 2>/dev/null | tail -1
docker system df 2>/dev/null
snap list --all 2>/dev/null
```

> **Pitfall**: El Escritorio y Descargas suelen tener archivos grandes que requieren decisión del usuario. No los borres sin preguntar.

### Fase 2: Categorizar en 3 niveles

| Nivel | Descripción | Ejemplos |
|---|---|---|
| **Seguro** | Se puede borrar sin riesgo | pip cache, npm cache, papelera, thumbnails, journal viejo, apt clean, kernel inactivo |
| **Requiere cerrar app** | La app debe estar cerrada | Chrome/Edge/Brave caches |
| **Requiere decisión del usuario** | Contenido que el usuario debe revisar | Descargas, Escritorio, snap revisions viejas, Docker images reclaimables |

### Fase 3: Ejecutar por lotes

**Lote seguro** — ejecutar sin preguntar:
```bash
pip cache purge
npm cache clean --force
rm -rf ~/.local/share/Trash/*
rm -rf ~/.cache/thumbnails/*
sudo journalctl --vacuum-time=7d
sudo apt clean
```

**Kernel viejo** (verificar kernel activo con `uname -r` primero):
```bash
sudo apt remove --purge linux-image-<version-vieja>-generic
sudo apt autoremove --purge
```
> Solo borrar kernels anteriores al activo actual. Mantener al menos 1 kernel de respaldo (el más nuevo instalado).

**Lote post-cierre** — pedir al usuario cerrar navegador:
```bash
rm -rf ~/.cache/google-chrome/*
rm -rf ~/.cache/microsoft-edge/*
rm -rf ~/.cache/Brave-Browser/*
```

### Fase 4: Verificación
```bash
df -h /
```
Reportar: espacio antes → espacio después, % usado final, y detalle de cada ítem liberado.

## Archivos que normalmente NO se deben tocar sin preguntar

| Ruta | Razón |
|---|---|
| `~/.linkedin-mcp/` | Perfil de navegación + browser headless para LinkedIn MCP. Borrarlo forza redescarga y re-login |
| `~/.chrome_cej/` | Perfil Selenium aislado para scraper del CEJ. Borrarlo forza recaptcha y re-login |
| `~/.config/google-chrome/` | Perfil completo del navegador (no el cache). Borrarlo pierde sesiones, extensiones, settings |
| `~/.config/Code/` | Configuración de VS Code |
| `~/.hermes/` | Agencia Hermes completa — skills, memoria, config. NO TOCAR |
| `~/.npm/` es cache, seguro. Pero `~/.npm/_npx/` contiene binarios temporales de npx, también seguro. |
| `~/.cache/pip/` es cache — seguro de limpiar siempre |

## Reglas
- Siempre explicar QUÉ se va a borrar y POR QUÉ cabe en su categoría antes de ejecutar
- Ejecutar comandos seguros en paralelo cuando sea posible
- Mostrar `df -h` ANTES y DESPUÉS
- No tocar perfiles de navegador (`.config/*/`) ni datos de aplicaciones activas sin confirmación explícita
- Los directorios de proyecto del usuario (cej-scraper, cej_pdfs, etc.) no se limpian automáticamente
