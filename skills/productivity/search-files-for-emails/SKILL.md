---
name: search-files-for-emails
title: "Search Files for Emails"
description: "Buscar direcciones de correo electrónico en archivos dentro de una carpeta (TXT, DOCX, DOC, PDF, HTML, XML). Usa PowerShell desde WSL para acceder a unidades Windows sin montar."
category: productivity
toolsets: ["terminal", "file"]
version: 1.0
---

# Search Files for Emails

Busca direcciones de correo electrónico en todos los archivos de una carpeta y subcarpetas.

## Soporte de formatos

| Formato | Método | Notas |
|---------|--------|-------|
| TXT, HTML, XML, INI | `Select-String` directo | Rápido |
| DOCX | Abre ZIP, extrae `word/document.xml`, parsea texto | .NET nativo |
| DOC | Word COM object | Requiere Word instalado en Windows |
| XLSX | Abre ZIP, lee `xl/sharedStrings.xml` + `xl/worksheets/sheet*.xml` | .NET nativo |
| XLS (binary) | Excel COM object | Requiere Excel instalado en Windows |
| PDF | Lectura raw de primeros 512KB, busca `@` en binario | Sin librerías externas |

## Cuándo usarlo

- Cuando necesites encontrar emails en archivos de una carpeta en Windows
- Cuando la unidad no esté montada en WSL (ej: tarjeta SD F:)
- Para escanear archivos recuperados (recup_dir.*)

## Script

El script completo vive en `scripts/buscar_emails.ps1` dentro de este skill.

### Cómo ejecutar desde WSL

Dado que PowerShell se ejecuta en Windows y no ve rutas UNC de WSL, hay que copiar el script a una ruta Windows primero:

```powershell
# 1. Copiar el script al Temp de Windows
cp ~/.hermes/skills/productivity/search-files-for-emails/scripts/buscar_emails.ps1 /mnt/c/Users/usuario/AppData/Local/Temp/

# 2. Ejecutar desde WSL
cmd.exe /c "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File C:\Users\usuario\AppData\Local\Temp\buscar_emails.ps1 -Path 'F:\Ruta\Deseada'"
```

O desde un cmd.exe directamente en Windows:

```cmd
powershell.exe -ExecutionPolicy Bypass -File C:\Users\usuario\Temp\buscar_emails.ps1 -Path "F:\Ruta\Deseada"
```

### Parámetros

- `-Path`: ruta a escanear (default: `F:\Rescate_Raw_Rec`)

### Salida

Lista de emails únicos encontrados, número de archivos donde aparece cada uno, y archivos específicos.

## Limitaciones conocidas

- PDFs corruptos (de herramientas de recuperación) pueden hacer lento el escaneo
- Word COM falla si el .doc está muy dañado
- El script lee solo primeros 512KB de cada PDF (suficiente para metadatos/texto temprano)
- El escaneo de 800+ PDFs en SD lenta puede tomar 10+ minutos
- Falsos positivos en PDFs por ruido binario (ej: `n@m.fy`, `r@nk.vn`). El script filtra TLDs de 2 letras y local-parts de 1 carácter
- Bug conocido v1.0: `$_.File` en scope anidado no capturaba el archivo correcto (corregido en v1.1)
