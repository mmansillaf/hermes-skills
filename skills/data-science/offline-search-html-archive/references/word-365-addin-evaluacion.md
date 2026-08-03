# Evaluación: add-in Word 365 "Jurisprudencia TC" (v4 → Word)

Fecha: 2026-08-02 · Sesión: html_casos_v4 + evaluación de plugin Word 365

## Contexto

El usuario (Christian Mansilla, LegalTech Perú) pidió evaluar si es viable llevar
el buscador offline TC (html_casos_v4, 8,794 sentencias) a un plugin de Word 365.
Tiene Office 365 instalado en la misma PC (WSL/Windows 10).

## Entorno verificado (comandos reales, desde WSL)

- `ls "/mnt/c/Program Files/Microsoft Office/root/Office16/"` → instalación Click2Run
- `powershell.exe -NoProfile -Command "(Get-Item '...WINWORD.EXE').VersionInfo.ProductVersion"` → 16.0.20228.20124
- COM probe: `New-Object -ComObject Word.Application; $o.Version` → 16.0 (build 20228)
- WebView2: `ls "/mnt/c/Program Files (x86)/Microsoft/EdgeWebView/Application/"` → Edge 151 (requisito de add-ins web, YA instalado)
- Node v24.16.0 + npm 11.13.0 → tooling completo
- Conclusión: Office 365 Click2Run canal Current, Windows 10 64-bit, cero bloqueadores.

## Las 4 vías de extensión (matriz ponderada)

Pesos: Desarrollo 25% · Capacidades/UI 25% · Integración con buscador TC 20% ·
Distribución 15% · Mantenimiento 10% · Robustez 5%

| Dimensión | Add-in web (Office.js) | VBA | COM/VSTO | Plantillas |
|-----------|------------------------|-----|----------|------------|
| Desarrollo (25%) | 8 | 5 | 3 | 9 |
| Capacidades/UI (25%) | 9 | 5 | 8 | 2 |
| Integración TC (20%) | 9 | 4 | 7 | 1 |
| Distribución (15%) | 8 | 8 | 4 | 9 |
| Mantenimiento (10%) | 8 | 6 | 3 | 7 |
| Robustez (5%) | 7 | 8 | 6 | 8 |
| **TOTAL** | **8.30 🥇** | **5.30** | **5.25** | **4.30** |

GANADOR: Add-in web de Office (Office.js) con Task Pane.

## Por qué gana Office.js para ESTE caso

1. Reutiliza ~80% del buscador HTML existente (mismo HTML/CSS/JS, `<script src>` file://)
2. Word 365 Click2Run + WebView2 ya instalados → cero requisitos extra
3. Office.js API: `Word.run()` para insertText, `getSelectedText()` para "buscar selección"
4. Distribución local sin tienda: manifest.xml + carpeta
   (Word → Insertar → Complementos → Mis complementos → Agregar desde archivo)
5. Aislado de Office (proceso WebView2 separado) → no rompe Office (a diferencia de COM)

## Menú/capacidades propuesto (3 tabs en Task Pane de 350px)

- **TAB Buscar**: sintaxis idéntica al buscador (frases, OR/NOT, campos numero/tipo/
  distrito/año/sentencia/fallo/derecho/ponente/demandado/materia/ley/ds/art/
  vinculante/voto), resultados paginados 10/pág con badges (★ vinculante, 🗳 voto
  singular), acciones INSERTAR CITA COMPLETA / CITA CORTA / VER CASO / SIMILARES,
  "buscar selección", chips de co-ocurrencia.
- **TAB Caso**: parte resolutiva destacada, fallos citados, ⚡ casos similares,
  botones INSERTAR RESOLUTIVA / TEXTO COMPLETO / SOLO EXPEDIENTE / COPIAR.
- **TAB Herramientas**: plantilla de escrito legal (EXPEDIENTE/DEMANDANTE/DEMANDADO/
  MATERIA), Top-10 leyes citadas, exportar a tabla de Word.

Formato de cita propuesto:
- Completa: `STC N.° {expediente} ({fundamento}): {texto}. — Tribunal Constitucional, publicado en El Peruano el {fecha}.`
- Corta: `STC N.° {expediente}, {fecha}.`

## Datos: cómo carga el add-in

Empaquetar datos.js (10 MB) + indice.js (15.5 MB) + cooc.js (0.5 MB) en `assets/`
del add-in, cargados con `<script src>` (mismo mecanismo file:// que el buscador —
fetch() está CORS-bloqueado). Carga inicial 2-4 s, todo offline, Permission:
ReadWriteDocument, sin llamadas externas.

## Plan SDD+TDD (resumen — detalle completo en word-addin/PLAN-WORD-ADDIN.md)

- FASE 0: usuario elige mockup (3 variantes en word-addin/sketches/) — gating
- FASE 1: SPEC (RF1-RF9 + formato exacto de citas + empaquetado)
- FASE 2: TDD RED — 17 tests node puro: format_cita (4), query_parser (5),
  search_engine con datos.js real (5, incl. rendimiento <50ms), manifest XML (3)
- FASE 3: GREEN — portar query-parser/search-engine del v4 + office-utils.js
  (Office.onReady, Word.run, insertText, getSelection) + ui-panel.js
- FASE 4: build (copia assets, valida manifest)
- FASE 5: pruebas en Word REAL (TC1-TC8: botón cinta, insertar cita, buscar
  selección, parte resolutiva, persistencia A−/A+ y tema)
- Estimación: ~1 día · Riesgos: confianza de catálogo local (marcar carpeta
  confiable, 2 min); fallback plan B = VBA (5.30)

## Mockups (3 variantes, word-addin/sketches/)

- 001-sobrio-editorial: serif/azul marino, preview de cita, formal
- 002-utilitario-denso: Segoe UI, filtros pill, badges, 3 acciones/resultado, toast
- 003-moderno-split: lista + detalle a la derecha (parte resolutiva destacada)

Nota: la decisión de diseño quedó PENDIENTE de elección del usuario al cierre de
la sesión. El flujo de mockups siguió el skill `sketch` (2-3 variantes, verificar
en navegador, README por variante, head-to-head).

## Archivos creados

- word-addin/PLAN-WORD-ADDIN.md (plan completo SDD+TDD)
- word-addin/sketches/001-sobrio-editorial/{index.html,README.md}
- word-addin/sketches/002-utilitario-denso/{index.html,README.md}
- word-addin/sketches/003-moderno-split/{index.html,README.md}
- html_casos_v4/INFORME-PLUGIN-WORD.md y .txt (informe de evaluación)
