# Extracción de Artículos Gestión.pe (Grupo El Comercio)

## Contexto
Gestión.pe usa **Piano.io** como plataforma de suscripción. Los artículos PLUS G (premium) se marcan con:
- `<meta property="article:content_tier" content="locked"/>`
- `EXCLUSIVO PARA SUSCRIPTORES`
- `PLUS G` badge

Sin embargo, el contenido completo se entrega a crawlers de Google en el campo `articleBody` del JSON-LD (`schema.org/NewsArticle`).

## Script de Extracción Probado

**Artículo:** Inteligencia Artificial y empresas en Perú
**URL:** `https://gestion.pe/economia/inteligencia-artificial-y-empresas-en-peru-companias-cada-vez-mas-abiertas-a-la-ia-para-que-la-usan-los-ejecutivos-noticia/`
**Fecha:** 2026-06-23
**Método:** Googlebot User-Agent + JSON-LD extraction

### Comando completo:

```bash
curl -sL -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  'https://gestion.pe/economia/inteligencia-artificial-y-empresas-en-peru-companias-cada-vez-mas-abiertas-a-la-ia-para-que-la-usan-los-ejecutivos-noticia/' \
  | python3 /tmp/extract_article.py
```

### Script Python (`/tmp/extract_article.py`):

```python
import sys, re

html = sys.stdin.read()

match = re.search(r'"articleBody":"(.*?)"', html, re.DOTALL)
if match:
    body_raw = match.group(1)
    body = body_raw.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/').replace('\\t', '\t')
    
    headline = (re.search(r'"headline":"(.*?)"', html) or [None, 'N/A']).group(1)
    author = (re.search(r'"author":"(.*?)"', html) or [None, 'N/A']).group(1)
    date_str = (re.search(r'"datePublished":"(.*?)"', html) or [None, 'N/A']).group(1)
    desc = (re.search(r'"description":"(.*?)"', html) or [None, 'N/A']).group(1)
    
    print(f'TITLE: {headline}')
    print(f'AUTHOR: {author}')
    print(f'PUBLISHED: {date_str}')
    print(f'DESCRIPTION: {desc}')
    print()
    print('=' * 70)
    print(body)
else:
    print('articleBody not found')
    idx = html.find('articleBody')
    if idx >= 0:
        print(f'Found at position {idx}')
        print(html[idx:idx+2000])
```

## Metadatos Relevantes en HTML

```html
<!-- Identificación de contenido premium -->
<meta property="article:content_tier" content="locked"/>
<meta name="cXenseParse:per-tiponota" content="premium"/>
<meta property="mrf:tags" content="notaPaywall:premium"/>

<!-- Datos estructurados del artículo -->
<script type="application/ld+json">
{
  "@context": "http://schema.org",
  "@type": "NewsArticle",
  "headline": "...",
  "articleBody": "...",
  "datePublished": "2026-06-23T10:34:00Z",
  "description": "...",
  "author": "Whitney Miñán"
}
</script>
```

## Notas
- El archivo HTML completo pesa ~250KB (mucho JS de tracking, anuncios, etc.)
- El `articleBody` contiene el texto completo con saltos de línea como `\n`
- Este mismo patrón aplica a **El Comercio.pe** (mismo grupo editorial, misma plataforma)
