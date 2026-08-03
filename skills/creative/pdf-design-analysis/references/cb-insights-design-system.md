# CB Insights & familias de informes — sistema de diseño extraído (jul 2026)

Fuentes: 9 documentos analizados de D:\Descargas\CBInsight (2,099 págs. muestreadas):
CB Insights State of AI 2024 (162p), 2025 Tech Trends (93p), State of Venture 2022 (279p),
Strategy Maps Coffee Table Book 2022 (67p), Marsh Benchmark Riesgos Latam v15 (50p),
INcluye/Talentlab Benchmark DE&I 2022 (114p), KPMG QuoVadis 2025 (13p),
KPMG Propuesta Auditoría 2024 (80p), Deloitte Propuesta Auditoría 2025 (50p).

## 1. CB INSIGHTS — el estándar (informes de datos 16:9)

FORMATO
- Lienzo 16:9 (960x540 pt). Diseñado para pantalla. Variante "libro": A4 apaisado (842x595).

TIPOGRAFÍA (identidad completa)
- Roboto Black — portadas y titulares gigantes (70-84pt)
- Roboto Bold — títulos de sección (24-42pt), números destacados
- Roboto Medium/Regular — subtítulos (16-18pt) y cuerpo (10-14pt)
- Roboto Mono — etiquetas de datos, ejes, cifras técnicas
- Arial (fallback) + Segoe UI Symbol (iconos). Máx. 3 pesos por página.

JERARQUÍA (medidas reales extraídas)
- Portada 70-84pt | Headline sección 35-42pt (1 línea de impacto) | Título página 24-28pt
- Subtítulo/lead 16-18pt | Cuerpo 10-14pt (línea ~60-70 chars) | Número de stat 78pt | Footer 8-9pt

PALETA (renders reales)
- Púrpura marca #72116F / #390937 (fondo oscuro portada y secciones)
- Azul #006699 | Teal #007D93 / #328396 | Celeste #E5F9FD (tarjetas) / #8ED9FF (azul cielo)
- Gris #7F8A8C, #9B9C9C | Blanco #FFFFFF
- Regla: 1 fondo oscuro saturado + 1 acento claro + grises. Máx 3-4 colores por página.

ESTRUCTURA (State of AI 2024 como plantilla)
1. Portada: título 2-4 líneas izq, subtítulo descriptivo, 1 imagen, logo
2. Página institucional ("Make smarter tech decisions" + CTA demo)
3. TL;DR: 2-4 tarjetas con stat gigante (78pt) + explicación 3-5 líneas
4. Secciones: divisores página completa de color de marca
5. Páginas de datos: titular → lead → gráfico grande → "Source: CB Insights" → CTA plataforma
   ("Track 16,000+ AI companies", "Get a demo")
6. Cierre: CTA + colofón

COMPONENTES (15-35 rects/página detectados)
- Tarjeta de stat (rect blanco/celeste, número 78pt + texto 13pt + etiqueta)
- Gráficos: barras apiladas, líneas, mapas de calor, market maps de burbujas (tamaño=funding,
  color=categoría — el formato firma), donas. Ejes limpios, sin gridlines, Roboto Mono, fuente siempre.
- Header "Sección | N°" 9pt en misma línea
- CTA recurrente 1 por página de datos

## 2. BENCHMARKS — dos escuelas

MARSH (benchmark-v15, 50p letter) — consultora tradicional
- Slate Pro (Black/Bk/Bold títulos) + Chronicle Text G1 (cuerpo, fuente de The Economist)
- Paleta: blanco/grises #F0F0F1 #98999D, azul acero #48768A, azul marino #101C24 #243572, cian datos #00A8C8 #016D9E
- TOC numerado 01-09 (Prefacio, Resumen ejecutivo, Información demográfica, secciones)
- Header repetido EN TODA página: nombre estudio + fecha + "N Marsh"
- Dashboard: 91 rects + 32 líneas, barras horizontales apiladas cian/azul
- Cian SOLO para datos destacados

INCLUYE/TALENTLAB (114p 16:9) — narrativa vibrante
- Clinton Bold (títulos) + Lato (Light/Regular/Bold/Black)
- Paleta: azul eléctrico #084ED6, magenta #F6037F, azul marino #000742,
  acentos #270062 púrpura, #FFB652 ámbar, #FF5B00 naranja. Portada = gradiente azul→magenta.
- Estructura NARRATIVA: "Nuestro sueño" (misión) → "Quiénes somos" → "Nuestra historia" →
  agenda 01-05 (Benchmark, Pilares evaluados, Relación con el negocio, Conclusiones, Siguientes pasos) → "el reporte"
- Footer legal cada página; página de datos con 127 imágenes embebidas

## 3. PROPUESTAS COMERCIALES

KPMG Propuesta 2024 (80p 16:9)
- Arial Narrow Bold portada 73-76pt + Arial/Calibri cuerpo
- Paleta: gradiente azul→violeta #1D48E2 #5A22E7 #5E1EE6, cian acento #05CEF9, azul profundo #00149A
- Portada = mensaje de venta directo completo ("¡Ser La mejor Opción para X!")
- TOC 01-06 (mejor propuesta, clientes ven la diferencia, credenciales, enfoque innovador, enfoque auditoría, aporte de valor)
- Páginas: mosaico 25 tarjetas blancas sobre fondo de color, texto 69-94pt
- Footer legal 3 líneas cada página; divisores "01 | Título sección"

DELOITTE Propuesta 2025 (50p A4 vertical)
- Documento VECTORIZADO (CIDFont, texto como curvas — no editable)
- Paleta: blanco, azul marino #00193A #010D24, verde #86BC25 #046A38, naranja #EA6237
- Portada: fondo claro + banda central azul marino, título blanco gigante + acento verde
- Header "Deloitte" + título sección repetido; CONTENIDOS numerado 01+; legal 6pt

## 4. RECETA PARA REPLICAR

INFORME DE DATOS ESTILO CB INSIGHTS:
1. Lienzo 16:9, fondo blanco con secciones de color saturado
2. Roboto: Black portada/headlines, Bold títulos, Regular cuerpo, Mono datos
3. Portada: fondo púrpura #390937 (o claro si cliente joven/tech), título 80pt izq, subtítulo 16pt
4. TL;DR 2-4 tarjetas: número 78pt + texto 13pt
5. Cada página de datos: headline 28pt 1 línea → lead 16-18pt → gráfico con fuente → CTA
6. Divisores sección: página completa en #72116F, #006699, #007D93, #8ED9FF (rotar)
7. Header continuo "Sección | N°" + footer legal 8-9pt
8. Gráficos: barras apiladas, líneas, market maps; ejes limpios, Roboto Mono, "Source:" siempre

BENCHMARK CORPORATIVO: letter vertical, Slate Pro + Chronicle, TOC numerado 01-09,
header repetido, cian solo para datos.
PROPUESTA COMERCIAL: 16:9, portada-mensaje, TOC numerado, mosaico tarjetas, footer legal 3 líneas,
gradiente azul/violeta.
