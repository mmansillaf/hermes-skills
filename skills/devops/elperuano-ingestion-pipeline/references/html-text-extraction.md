# HTML Text Extraction for El Peruano Normas

## Problem

Solo 2024 (18,694 normas) tiene `texto_completo` poblado. 2021-2023 y 2025 (79,115 normas) tienen el campo NULL. La causa: el pipeline Groq batch para esos años solo extrajo metadatos, no texto completo. Los `.md` no sirven porque 2021-2023 no los tienen y 2025 usa `pagina_X.md` (multinorma).

**Solución**: extraer texto directamente de los HTML fuente en `data/YYYYMMDD/*.html`.

## Extractor (stdlib, sin dependencias)

```python
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.skip_tags = {'script', 'style', 'meta', 'link', 'head', 'title'}
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip = True
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags: self.skip = False
        if tag in ('p','br','div','h1','h2','h3','h4','h5','h6','li','tr','td'):
            self.text.append('\n')
    
    def handle_data(self, data):
        if not self.skip:
            t = data.strip()
            if t: self.text.append(t)

# Uso:
extractor = TextExtractor()
extractor.feed(html_content)
text = ' '.join(extractor.text)
text = re.sub(r'\n\s*\n', '\n', text)
text = re.sub(r' +', ' ', text).strip()
```

## Métricas (test con 500 normas)

| Métrica | Valor |
|---------|-------|
| Velocidad | 644 normas/s (solo parseo) |
| Tasa éxito | 98.8% (494/500) |
| HTML faltantes | 1.2% (6/500) |
| Errores parse | 0 |
| Texto promedio | 9,282 chars |
| Texto mediana | 6,452 chars |
| Rango | 437 — 118,852 chars |

## Proyección para 79,115 normas

- Tiempo parseo: ~2 minutos
- Tiempo con DB updates (batch 500): ~5-8 minutos
- Total chars: ~734 MB

## Optimizaciones para producción

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

# Batch de 500 UPDATEs
batch = []
for i, (text, norma_id) in enumerate(rows):
    batch.append((text, norma_id))
    if len(batch) >= 500:
        cur.executemany(
            "UPDATE normas SET texto_completo = ? WHERE id = ?", batch
        )
        conn.commit()
        batch = []
```

## Ubicación de archivos

- **HTML fuente**: `data/YYYYMMDD/*.html` (89,967 archivos, 1.5 GB)
- **DB objetivo**: `data/normas_total.db` (tabla `normas`, columna `texto_completo`)
- **Mapeo**: `source_path` en DB → ruta relativa al archivo HTML
  - `20210222/1929333-1.html` → `data/20210222/1929333-1.html`
  - `2024/20240620/2299514-4.html` → `data/20240620/2299514-4.html` (sin prefijo `2024/` en filesystem)

## Pitfall: HTMLs multi-norma

Los HTMLs de El Peruano contienen MÚLTIPLES normas por página. El extractor extrae TODO el texto — incluyendo normas adyacentes. Esto es aceptable para `texto_completo` (contexto extra no daña la búsqueda), pero NO para `sumilla` (los primeros 500 chars incluyen la norma anterior).

**Para sumillas**: usar Groq con el texto_completo ya extraído como input (~$25-30 para 33K sumillas vacías).

## Problem
- `normas_total.db` has `texto_completo` NULL for 80.9% of normas (79,115/97,809)
- Only 2024 normas have text; 2021-2023 and 2025 are missing
- `.md` files exist but don't map 1:1 — 2025 uses `pagina_X.md` (multi-norm), 2021-2023 have no individual `.md`
- HTML source files are available for 100% of normas at `data/YYYYMMDD/*.html`

## Approach: stdlib HTMLParser (no dependencies)

```python
from html.parser import HTMLParser
import re

class TextExtractor(HTMLParser):
    SKIP_TAGS = {'script', 'style', 'meta', 'link', 'head', 'title'}
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip = True
    
    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip = False
        if tag in ('p', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'td'):
            self.text.append('\n')
    
    def handle_data(self, data):
        if not self.skip:
            t = data.strip()
            if t:
                self.text.append(t)

def extract_text(html_content):
    extractor = TextExtractor()
    extractor.feed(html_content)
    text = ' '.join(extractor.text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()
```

## Performance (tested 02-may-2026)

| Métrica | Valor |
|---------|-------|
| Velocidad | 644 normas/segundo |
| Tiempo/norma | 0.8ms mediana (1.6ms avg, 4.8ms P95) |
| Éxito | 98.8% (6/500 HTMLs faltantes) |
| Texto extraído | 9,282 chars avg (mediana 6,452, max 118,852) |
| Proyección 79K | ~2 min solo parseo, ~5-8 min con DB writes |

## Pitfalls

### HTMLs contienen múltiples normas
El Peruano publica varias normas por página. Un solo HTML puede contener 3-5 normas. Los primeros 500 caracteres del HTML NO son una sumilla confiable — mezclan contenido de normas adyacentes.

**Solución**: usar el texto extraído solo como `texto_completo`. Para sumillas, usar Groq batch (envía el texto_completo ya extraído en vez del HTML completo = menos tokens = más barato).

### Source path format
- 2021-2023: `YYYYMMDD/NNNNNNN-N.html` → `data/YYYYMMDD/NNNNNNN-N.html`
- 2024: `2024/YYYYMMDD/NNNNNNN-N.html` → `data/2024/YYYYMMDD/NNNNNNN-N.html` (verificar si el prefijo `2024/` existe en disco)
- 2025: `YYYYMMDD/pagina_N.html` → `data/YYYYMMDD/pagina_N.html`

### DB update: usar batches
No hacer UPDATE por registro. Usar `executemany` con batches de 100-500:

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
cursor.executemany(
    "UPDATE normas SET texto_completo = ? WHERE id = ?",
    [(text, norma_id) for text, norma_id in batch]
)
conn.commit()
```
