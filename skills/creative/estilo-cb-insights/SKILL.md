---
name: estilo-cb-insights
description: Use when generating CB Insights-style 16:9 reports or decks.
---

# Estilo CB Insights — Informes de datos 16:9

Replica el lenguaje visual de CB Insights (State of AI/Venture, Tech Trends) para informes de datos, benchmarks y presentaciones. Analizado de 9 PDFs reales (jul 2026): CB-Insights AI 2024 (162p), Tech Trends 2025 (93p), State of Venture 2022 (279p), Strategy Maps (67p), Benchmark Marsh v15 (50p), Benchmark INcluye DE&I (114p), KPMG/Deloitte propuestas.

## Formato
- Lienzo 16:9 por página (1920x1080 px recomendado para HTML/slides). Diseñado para pantalla.
- Alternativa "libro": A4 apaisado (842x595) para reportes impresos.

## Tipografía (Roboto — identidad CB Insights)
- Roboto Black — portadas y titulares gigantes (70-84pt)
- Roboto Bold — títulos de sección (24-42pt), números destacados
- Roboto Medium/Regular — subtítulos (16-18pt) y cuerpo (10-14pt)
- Roboto Mono — etiquetas de datos, ejes, cifras técnicas
- Fallback: Arial. Iconos: Segoe UI Symbol.
- Regla: máx. 3 pesos por página. Contraste fuerte título/cuerpo.

## Jerarquía tipográfica (medidas reales)
- Portada: 70-84pt | Headline sección: 35-42pt (1 línea de impacto) | Título página: 24-28pt
- Lead/subtítulo: 16-18pt | Cuerpo: 10-14pt | Número de stat en tarjetas: 78pt | Footer: 8-9pt

## Paleta oficial (hex extraídos de renders)
- Púrpura marca: #72116F / #390937 (fondos oscuros de portada/secciones)
- Azul: #006699 | Teal: #007D93 / #328396
- Celestes: #E5F9FD (fondo tarjetas), #8ED9FF (azul cielo)
- Grises: #7F8A8C, #9B9C9C | Blanco: #FFFFFF
- Regla: 1 fondo oscuro saturado + 1 acento claro + grises. Máx 3-4 colores/página.

## Estructura de documento (plantilla State of AI)
1. Portada: título 2-4 líneas izq (Roboto Black 80pt), subtítulo 16pt, 1 imagen, logo
2. Página institucional (opcional): propuesta de valor + CTA
3. TL;DR: 2-4 tarjetas con stat gigante (78pt) + explicación 3-5 líneas (13pt)
4. Secciones: divisores de página completa de color (rotar #72116F, #006699, #007D93, #8ED9FF)
5. Páginas de datos: headline 28pt (1 línea) → lead 16-18pt → gráfico → "Source: ..." → CTA
6. Cierre: CTA ("Get a demo") + colofón

## Componentes
- Header continuo: "SECCIÓN | N° página" 9pt, misma línea
- Tarjeta de stat: rect blanco/celeste #E5F9FD, número 78pt + texto 13pt
- Gráficos: barras apiladas/agrupadas, líneas, mapas de calor, market maps (burbujas tamaño=valor, color=categoría)
- Ejes limpios sin gridlines ruidosos, etiquetas Roboto Mono
- "Source: X" siempre en cada gráfico

## Mejoras Paquete A (narrativa + verificacion — nivel "superar al original")
- Hero stat en portada: un dato clave gigante bajo el subtítulo ("348K docs verificados")
- Badge de severidad en cada tarjeta TL;DR (🔴🟠🟡⚪ con fondo de color: verde #1E7A3C, rojo #C62828, ámbar #E65100, gris #757575)
- Bloque "Qué significa para ti" (fondo #E5F9FD) al final de cada página de datos: convierte el dato en decisión
- "Key takeaways" numerados (caja #F6EDF6 con borde izquierdo #72116F) bajo cada gráfico: 1 línea por hallazgo
- Fuentes verificadas con enlace real (file:/// o URL) bajo cada página: "Fuente verificada: archivo §sección" — es la diferenciación de mercado (CriticAgent)
- Glosario de métricas compacto al pie (peso, score, ponderado, n)
- Semáforo en columnas de comparación: valores positivos verdes .pos, negativos rojos .neg
- Regla de oro: cada stat del informe debe poder rastrearse a su fuente; si no, no se publica

## Proceso de generación (HTML → render)
1. HTML autocontenido 1920x1080 por página (display:block, page-break), Roboto vía Google Fonts + fallback Arial
2. Renderizar a PNG/PDF con Playwright chromium (headless): `python3 -c "from playwright.sync_api import sync_playwright; ..."`
   - Playwright disponible en ~/.cache/ms-playwright/chromium-1223
3. Verificar visualmente el PNG renderizado antes de entregar (regla: probar como humano)
4. Copiar a /mnt/d/... (Windows) cuando el destino sea Windows

## Pipeline datos → informe (Paquete C) — USAR SIEMPRE para informes recurrentes
Ubicación de referencia: /mnt/d/Descargas/CBInsight/_demos/pipeline/
- `generador.py datos/<nombre>.json` → produce HTML + PNG + PDF + PPTX + MD con el mismo nombre en la carpeta destino (hermana de pipeline/)
- JSON = fuente de verdad: meta (titulo, hero, tema oscuro/claro), paginas de tipos: tldr, barras, cols, verdict
- Tipos de página: tldr (stats con badges), barras (filas a/b con diff y tooltips), cols (comparativa 2 columnas con colfoot), verdict (párrafos + PILLS:["...","..."] como pills)
- Cada página soporta: decision ("Qué significa para ti"), takeaways, gloss (glosario), fuente {archivo, seccion, ruta file:///}
- `--skip-render` omite PNG/PDF (debug rápido de HTML/PPTX/MD)
- PDF se renderiza SIEMPRE en tema claro (forzar data-theme=light antes de page.pdf)
- PPTX: 1 slide por página 16:9, formas nativas editables (barras = rectángulos con fill)
- Dependencias: playwright, python-pptx (pip install --break-system-packages si PEP 668 bloquea)

## Paquete B — interactivo (ya integrado en template.html)
- Toggle tema oscuro/claro (CSS variables + localStorage, botón fijo abajo-derecha, oculto en print)
- Tooltips: atributo data-tip en cualquier elemento → div.tooltip sigue al cursor
- Índice: dots fijos a la izquierda, auto-generado desde .page[data-title], scroll suave + flechas ← →
- Animaciones: .bar con data-w crecen al entrar en viewport (IntersectionObserver, respeta prefers-reduced-motion)
- Heatmap plotly: botón .heat-btn + overlay (CDN plotly 2.35.2, lazy-load al click) — datos en JSON "heatmap": {"filas":[{"dim","me","mg","peso"}]}
- Verificación JS con playwright: toggle light→dark, conteo de [data-tip], .bar[data-w], 0 errores de consola

## Otras familias (contexto)
- Benchmark corporativo (Marsh): letter vertical, Slate Pro + Chronicle Text, TOC numerado 01-09, header repetido, cian #00A8C8 solo para datos
- Benchmark vibrante (Talentlab): 16:9, gradiente azul→magenta (#084ED6/#F6037F), estructura narrativa (misión→quienes somos→agenda 01-05)
- Propuesta KPMG: 16:9, portada = mensaje de venta directo (Arial Narrow Bold 73-76pt), gradiente azul/violeta (#1D48E2/#5A22E7), mosaico tarjetas blancas, footer legal 3 líneas
- Propuesta Deloitte: A4 vertical, azul marino #00193A + verde #86BC25, CONTENIDOS numerado, header "Deloitte" repetido

## Pitfalls
- No usar position:absolute en contenedores .page — el elemento sale del flujo, el full-page screenshot colapsa (mide 3 páginas cuando hay 4) y cubre páginas anteriores. Si una página de color es "fondo completo", dale height:1080px + position:relative, no absolute.
- PDFs generados en /mnt/d/ pueden quedar LOCKED si Windows los tiene abiertos: renderizar a nombre temporal y renombrar, o avisar al usuario que cierre el visor.
- No usar más de 4 colores por página — CB Insights es minimalista pese a parecer colorido
- El número gigante en tarjeta ES el diseño del TL;DR: sin él, no parece CB Insights
- Headlines de sección: UNA línea, frase corta de impacto, no descriptiva
- Todo gráfico con fuente ("Source: CB Insights") — es marca registrada del estilo
- En HTML para lectura (no slides), respetar preferencia de usuario: base 13px mín. 12px (aplica a informes de lectura, no a slides 16:9)
