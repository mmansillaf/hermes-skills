# Scribd / Everand — Descarga sin Cuenta (Julio 2026)

> Referencia técnica para el skill `bypass-paywall`. Cubre métodos verificados, pitfalls, y batalla de gato-ratón con las defensas de Scribd.

## Arquitectura de Protección de Scribd

Scribd NO sirve PDFs descargables. El contenido se renderiza en el navegador:

1. **Canvas-based rendering**: páginas dibujadas en `<canvas>`, no imágenes estáticas
2. **Fragmentación tipo rompecabezas**: Scribd parte cada página en múltiples tiles. El changelog de HugoAleOlguin lo confirma: "Scribd divide la página en Múltiples Fragmentos formando un rompecabezas"
3. **Tokens de sesión + URLs firmadas**: sin sesión válida → HTTP 401/403
4. **Ofuscación de JS**: el código del visor cambia frecuentemente
5. **Lazy loading**: las páginas se cargan bajo demanda al hacer scroll

## Realidad (Ground Truth Julio 2026)

- **NADIE puede bajar contenido premium/de pago sin cuenta**. Todo lo existente funciona solo con docs públicos
- Es una **carrera armamentista**: Scribd actualiza defensas cada pocos meses, las herramientas sin mantenedor activo mueren en semanas
- **Phoenix124 (397★)** era el más popular, ahora está abandonado: 28 issues abiertas, sin respuesta desde 2023

## Método Verificado: fullstackusama/scribd-downloader

### Repo y enfoque

- **GitHub**: `fullstackusama/scribd-downloader` (97★, activo Abr-May 2026)
- **Tecnología**: Python + Selenium + Chrome DevTools Protocol (CDP)
- **Sin login requerido** — solo docs públicos
- **Mecanismo**: convierte URL de Scribd a URL embed, abre en Chrome, scrollea para lazy-load, imprime a PDF vía CDP

### Embed URL Pattern

```
Entrada: https://www.scribd.com/document/705594168/Directorio-MINJUS
Embed:   https://www.scribd.com/embeds/705594168/content
```

La función `convert_scribd_link()` hace esta transformación con regex:
```python
re.search(r"https://www\.scribd\.com/(?:document|doc)/(\d+)/", url)
```

### Pitfalls Encontrados (Julio 2026)

#### ⚠️ PITFALL 1: Subdominio `es.scribd.com` no matchea el regex

El regex solo acepta `www.scribd.com`. Si las URLs tienen `es.scribd.com`, normalizar antes:
```python
normalized = re.sub(r'https://[\w.-]+\.scribd\.com/', 'https://www.scribd.com/', url)
```

#### ⚠️ PITFALL 2: CDP `ReturnAsStream` roto en Chrome 149

`Page.printToPDF` con `transferMode: "ReturnAsStream"` produce `"Invalid stream handle"` en Chrome for Testing 149. Usar `ReturnAsBase64`:
```python
pdf_opts = {
    "transferMode": "ReturnAsBase64",  # NO "ReturnAsStream"
    "paperWidth": ...,
    "printBackground": True,
    "displayHeaderFooter": False,
    "marginTop": 0, "marginBottom": 0,
    "marginLeft": 0, "marginRight": 0,
}
result = driver.execute_cdp_cmd("Page.printToPDF", pdf_opts)
pdf_data = base64.b64decode(result["data"])
```

#### ⚠️ PITFALL 3: Documentos gigantes (1000+ páginas)

Algunos "documentos" de Scribd son hojas de cálculo enormes (directorios, bases de datos). Scrollear 1000+ páginas puede tomar 30+ minutos. Poner límite:
```python
MAX_PAGES = 200  # saltar hojas de cálculo gigantes
if pages > MAX_PAGES:
    print(f"SKIP: BIG ({pages}p)")
    continue
```

#### ⚠️ PITFALL 4: Lazy loading incrementa el conteo de páginas

El script reporta inicialmente N páginas, pero al scrollear descubre más (lazy loading):
```
Found 21 pages, scrolling...
Detected 27 pages after lazy loading, continuing...
```
El conteo final puede ser mayor que el inicial.

### Batch Wrapper (59 documentos)

Template completo verificado: `/mnt/d/PyCode/SkillScribidDown/batch_wrapper.py`

Estructura clave:
```python
# 1. Una sola sesión de Chrome para todos los docs (no abrir/cerrar por cada uno)
with tempfile.TemporaryDirectory() as pdir:
    opts = build_chrome_options(pdir)
    opts.binary_location = CHROME_BIN  # ~/chromium/chrome-linux64/chrome
    driver = webdriver.Chrome(options=opts)
    configure_command_timeout(driver, 600)  # CDP timeout para PDFs grandes

    for url in urls:
        normalized = re.sub(r'https://[\w.-]+\.scribd\.com/', 'https://www.scribd.com/', url)
        converted = convert_scribd_link(normalized)
        if converted == "Invalid Scribd URL": skip
        driver.get(converted)
        # scroll, prepare, print...
```

**Resultados de prueba real (59 URLs, Jul 2026):**
- 31 PDFs descargados OK (docs ≤200 págs)
- 8 saltados por >200 págs (hojas cálculo enormes)
- 0 fallos — todos los que scrollean completo generan PDF correctamente
- Docs restantes: probablemente también >200 págs o bloqueados

**Parámetros óptimos para batch:**
- `DEFAULT_SCROLL_DELAY_SECONDS = 0.08` (default 0.15 es conservador)
- `DEFAULT_RENDER_SETTLE_TIMEOUT_SECONDS = 10` (default 30 es excesivo)
- `MAX_PAGES = 200` (docs con 1000+ págs son hojas Excel, no directorios útiles)
- `transferMode: "ReturnAsBase64"` (NO "ReturnAsStream" — roto en Chrome 149)
- Reutilizar sesión Chrome: ~3 min de setup una vez, luego cada doc ~30-60s

### Rendimiento Observado

| Páginas | Tiempo estimado | Tamaño PDF |
|---------|----------------|------------|
| ~25     | ~23s           | ~4 MB      |
| ~50     | ~40s           | ~6-10 MB   |
| ~100-200| ~1-3 min       | ~15-30 MB  |
| 300+    | Saltar (MAX_PAGES) | —       |

## Herramientas Verificadas (Julio 2026)

### Funcionando
| Herramienta | Tipo | Estado |
|-------------|------|--------|
| `fullstackusama/scribd-downloader` (97★) | Python + Selenium + CDP | ✅ Funciona (con fixes) |
| `HugoAleOlguin/Scribd-Downloader-Premium` (82★) | Extensión Chrome/Firefox | ✅ Mantenido (v2.9.0, Mar 2026) |
| `swappedphantom-cmd` (0★) | Python + Camoufox | ✅ Nuevo (Jun 2026) |

### Caídas / Muertas
| Herramienta | Causa |
|-------------|-------|
| `scribdown.netlify.app` | Backend Deta Space caído (Jul 2026) |
| `scribd.vdownloaders.com` | Redirige a casino — malware |
| `scribd.vpdf.com` | DNS muerto |
| `DLSCRIB` | DNS muerto |
| `Phoenix124/scribd-downloader` (397★) | Abandonado 2023, 28 issues abiertas |

## Alternativas para Producción (LegalTech)

Para un sistema RAG/documental, NO depender de Scribd como fuente. Las herramientas son frágiles. Alternativas robustas:
- Fuentes gubernamentales peruanas directas (SPC Indecopi, TC, Sunarp, OSCE)
- Convenios con editoriales jurídicas
- APIs de repositorios académicos (SciELO, Redalyc, Alicia CONCYTEC)
