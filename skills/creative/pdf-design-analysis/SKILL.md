---
name: pdf-design-analysis
description: Analyze reference PDFs to extract their design system.
---

# PDF Design Analysis

Extract a document family's design system from a folder of reference PDFs and synthesize a replication guide. Proven on a 77-PDF folder of CB Insights reports + Marsh/Talentlab benchmarks + KPMG/Deloitte proposals (2026-07). Works WITHOUT vision: everything is inferred from text coordinates, font sizes, render colors, and vector drawings — the human validates via a generated contact sheet.

## Triggers
- "Revisa los diseños de estos informes/benchmarks/presentaciones"
- "Extrae el estilo de X para replicarlo en mis informes"
- Any folder of PDFs the user wants reverse-engineered into a style guide

## Workflow

1. **Inventario técnico** — loop `pdfinfo` over every PDF: pages + page size. Size immediately classifies the family: 960x540 (16:9 digital report), 842x595 (A4 landscape book), 595x842 (A4 formal), 612x792 (letter). Spot " (1)" duplicate suffixes.
2. **Tipografía** — `pdffonts` per doc, unique font names = design identity (Roboto Black = CB Insights; Slate Pro + Chronicle Text = Economist-style editorial; Calibri/Arial = corporativo; CIDFont = vectorized/no fonts).
3. **Jerarquía + estructura** (pymupdf): `page.get_text("dict")` blocks → spans carry `size`, `font`, `bbox`, `color`. Keep spans with `size >= 24` as headlines (records the typographic scale in pt). Portada text = first ~600 chars. TOC detection: pages 1-4, lines matching `r'\d{1,3}\s*$'`. Image density per page via `page.get_images(full=True)` → top-5 pages are the "typical data pages" to sample.
4. **Render**: `page.get_pixmap(dpi=110)` → PNG (covers + 2-3 interiors per doc). 110 dpi is enough for palettes/regions.
5. **Paletas**: PIL `Image.quantize(colors=16, method=Image.Quantize.MEDIANCUT)` → `Counter` → hex + % per color.
6. **Composición vectorial**: `page.get_drawings()` — count `type=="f"` (rects = cards), `"c"` (circles = market-map bubbles), `"s"/"l"` (lines = bar charts); Counter of fill colors tells the per-section accent palette.
7. **Color de texto**: span `color` as `#%06X`.
8. **Layout sin visión**: average color per 3x3 region of the rendered cover → infer dark/light background, color bands, gradient direction.
9. **Contact sheet HTML**: covers + palette swatches + 3x3 region table per doc → the USER validates visually (agent may have no vision this session).
10. **Síntesis**: style guide as .md + .txt — palette hexes, typography, pt hierarchy, document structure, components, replication recipe ("receta para replicar").

## Pitfalls
- **pymupdf >= 1.27 `get_fonts(full=True)`**: tuple index 4 is the font NAME (string), not size — `round(f[4])` throws `type str doesn't define __round__`. Use `f[3]` (basefont) for display; don't unpack pairs unless you confirmed the shape.
- **Vectorized PDFs** (e.g. Deloitte): `pdffonts` shows only `CIDFont+F1..F12`, `get_text` returns fragments, portada shows 90+ images → the doc is text-as-curves, NOT editable. Report it as such instead of failing.
- MuPDF warnings `No common ancestor in structure tree` are harmless — filter them out of output (`grep -v MuPDF`).
- PIL >= 12 deprecates `getdata()` (warning only; use `get_flattened_data()` if you want silence).
- **Never read every page**: sample covers, TOC, 3-5 interiors, densest-image pages. 9 docs / ~2,100 pages took minutes via sampling.
- Duplicate files "X.pdf" and "X (1).pdf" — analyze one, note the duplicate.
- Don't trust `pdfinfo` output ordering for large folders — sort by size column to group families.

## Delivery (user preferences, embedded)
- Deliver the style guide as **.md + .txt** (plain text, no markdown in the .txt).
- Always emit the **contact sheet HTML** — the human validates what the agent inferred.
- Declare the analysis limit honestly: "no pude ver las páginas; composición inferida de coordenadas/colores/dibujos" — user demands scope transparency.
- Progress update every 5-10 min on long runs; token estimate at the end.
- If the user picks a style to adopt, offer: save the extracted system as a `references/` file under this skill + generate a demo report in that style.

## References
- `references/cb-insights-design-system.md` — full extracted spec: CB Insights (16:9, Roboto, purple/teal palette, TL;DR cards, market maps), Marsh benchmark (Slate Pro + Chronicle), Talentlab DE&I (gradient blue/magenta), KPMG proposal (Arial Narrow, gradient blue/violet), Deloitte (navy + green, vectorized), plus the replication recipe.
