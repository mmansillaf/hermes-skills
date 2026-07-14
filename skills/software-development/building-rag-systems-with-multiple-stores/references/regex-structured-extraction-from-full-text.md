# Regex-Based Structured Extraction from Full Text (Mejora 3 Pattern)

## When to Use
Your RAG system has full-text documents in SQLite (or any store) but the extraction pipeline misses key structured fields (DNIs, registration numbers, internal dates, URLs, specific article references). The LLM receives raw text but can't reliably find these details in 4000+ characters of narrative.

## Technique
Add a **post-hoc regex extractor** that runs on `texto_completo` before building the LLM context. Extract 10 categories of structured data with pure Python regex — zero cost, sub-millisecond execution.

## Extractor Function

```python
def extract_structured_metadata(text: str) -> dict:
    """Extrae campos estructurados del texto completo con regex."""
    if not text:
        return {}
    
    import re
    metadata = {}
    
    # 1. DNIs (8 dígitos, excluir años 2020-2035 y números que empiezan con 00)
    dnis_raw = re.findall(r'\b(\d{8})\b', text)
    dnis = [d for d in dnis_raw 
            if not (2020 <= int(d) <= 2035) 
            and not d.startswith('00')
            and d not in ['00000000']]
    if dnis:
        metadata["_dnis"] = list(dict.fromkeys(dnis))[:5]
    
    # 2. CAP (Cuadro de Asignación de Personal)
    caps = re.findall(r'CAP\s*(?:N[°º]\s*)?(\d+)', text, re.IGNORECASE)
    if caps:
        metadata["_cap"] = [f"CAP {c}" for c in caps[:3]]
    
    # 3. Registros COOPAC y otros registros administrativos
    regs_coopac = re.findall(r'(\d{3}-\d{4}-REG\.?\s*COOPAC[^\s,]*)', text, re.IGNORECASE)
    if regs_coopac:
        metadata["_registros"] = regs_coopac[:3]
    
    # 4. URLs
    urls = re.findall(r'(https?://[^\s,;\)]+)', text)
    if urls:
        metadata["_urls"] = [u.rstrip('.') for u in urls[:3]]
    
    # 5. Fechas internas (formato "DD de mes de AAAA")
    meses = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
    fechas = re.findall(r'(\d{1,2})\s+de\s+(' + meses + r')\s+(?:de\s+)?(\d{4})', text, re.IGNORECASE)
    if fechas:
        metadata["_fechas_internas"] = [f"{d} de {m} de {a}" for d, m, a in fechas[:5]]
    
    # 6. Direcciones (Manzana, Lote, Asociación, Av., Jr., Calle)
    dirs = re.findall(
        r'(?:Mz\.?|Manzana|Lt\.?|Lote|Asociaci[oó]n|Av\.?|Avenida|Jr\.?|Calle|Pasaje)\s+'
        r'([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s\d]+?)(?=\s*(?:,|\.|\n|$|en\s+el|del\s+distrito))',
        text, re.IGNORECASE
    )
    if dirs:
        metadata["_direcciones"] = [d.strip()[:60] for d in dirs[:3] if len(d.strip()) > 3]
    
    # 7. Artículos de leyes citadas
    arts_ley = re.findall(
        r'(?:art[ií]culo|art\.?|inciso)\s*(\d+[°º]?(?:[-.]\w+)?(?:\s*inc\.?\s*\d+)?)\s*'
        r'(?:de\s*(?:la|el)\s*)?'
        r'(Ley\s*(?:N[°º]?\s*)?\d+|'
        r'Decreto\s*Legislativo\s*(?:N[°º]?\s*)?\d+|'
        r'DL\s*\d+|'
        r'Constituci[oó]n\s*(?:Pol[ií]tica)?)',
        text, re.IGNORECASE
    )
    if arts_ley:
        metadata["_articulos_citados"] = [f"Art. {a[0]} de {a[1]}" for a in arts_ley[:8]]
    
    # 8. Normas citadas (DS, RM, DA, RS con número)
    normas_cit = re.findall(
        r'((?:Decreto\s*Supremo|DS|Resoluci[oó]n\s*Ministerial|RM|'
        r'Decreto\s*de\s*Alcald[ií]a|DA|Resoluci[oó]n\s*Suprema|RS|'
        r'Resoluci[oó]n\s*SBS)\s*(?:N[°º]?\s*)?\d+[-]\d+[-][A-Z]+(?:/[A-Z]+)?)',
        text, re.IGNORECASE
    )
    if normas_cit:
        metadata["_normas_citadas_detalle"] = list(dict.fromkeys(normas_cit))[:5]
    
    # 9. Nivel Esquema Modular SBS
    nivel_sbs = re.findall(r'Nivel\s*(\d+)\s*(?:del\s*)?Esquema\s*Modular', text, re.IGNORECASE)
    if nivel_sbs:
        metadata["_nivel_sbs"] = [f"Nivel {n}" for n in nivel_sbs[:3]]
    
    # 10. Plazos administrativos (días hábiles)
    plazos = re.findall(r'(\d+)\s*d[ií]as?\s*h[aá]biles', text, re.IGNORECASE)
    if plazos:
        metadata["_plazos_dias"] = [f"{p} días hábiles" for p in plazos[:3]]
    
    return metadata
```

## Context Integration

Inject extracted fields as tagged lines BEFORE the raw text in the LLM context:

```python
if r.get('texto_completo'):
    meta = extract_structured_metadata(r['texto_completo'])
    if meta.get('_dnis'):
        parts.append(f"    DNIs: {', '.join(meta['_dnis'])}")
    if meta.get('_cap'):
        parts.append(f"    CAP: {', '.join(meta['_cap'])}")
    if meta.get('_registros'):
        parts.append(f"    Registros: {', '.join(meta['_registros'])}")
    if meta.get('_urls'):
        parts.append(f"    URLs: {', '.join(meta['_urls'])}")
    if meta.get('_fechas_internas'):
        parts.append(f"    Fechas: {', '.join(meta['_fechas_internas'])}")
    if meta.get('_direcciones'):
        parts.append(f"    Dirección: {', '.join(meta['_direcciones'])}")
    if meta.get('_articulos_citados'):
        parts.append(f"    Artículos citados: {', '.join(meta['_articulos_citados'])}")
    if meta.get('_normas_citadas_detalle'):
        parts.append(f"    Normas citadas: {', '.join(meta['_normas_citadas_detalle'])}")
    if meta.get('_nivel_sbs'):
        parts.append(f"    SBS: {', '.join(meta['_nivel_sbs'])}")
    if meta.get('_plazos_dias'):
        parts.append(f"    Plazo: {', '.join(meta['_plazos_dias'])}")

# THEN the raw text (expanded to 4000 chars instead of 2000)
parts.append(f"    Texto: {r['texto_completo'][:4000]}")
```

## Effect
- LLM sees tagged fields (`DNIs: 06203134, 46238948`) directly — no need to search 4000 chars of narrative
- Combined with expanding `[:2000]`→`[:4000]`, resolves ~5/8 failing queries that were missing data in the 2000-4000 char range
- Cost: $0, sub-millisecond per document

## Verified On
El Peruano RAG (PeruanoSearchEngine02), 2026-04-29. Tested on 4 key documents:
- SBS 03429-2024: DNIs ✅, Registro ✅, Dirección ✅, Nivel SBS ✅
- INDECOPI 000147-2024: CAP ✅, Fecha ✅
- La Molina DA 006-2024: URL ✅, Artículos Constitución/Ley 27972 ✅
- SBS 03416-2024: Fechas viaje ✅, Normas austeridad ✅

## Pitfall
Extraction only helps if the RIGHT document reaches the LLM context. If the search/retrieval stage returns wrong documents, the extracted fields are from irrelevant norms. This technique must be paired with a working retrieval pipeline.
