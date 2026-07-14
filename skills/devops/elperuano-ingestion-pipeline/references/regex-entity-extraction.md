# Extracción Regex de Entidades Legales Peruanas

## Diseño

Extrae 8 tipos de entidades de `texto_completo` usando solo regex (sin API).
Costo $0, velocidad ~650 normas/s.

## Tablas y patrones

### 1. ent_funcionarios — Personas designadas/cesadas/nombradas

```python
# Patrón en encabezado (primeros 2000 chars):
r'(?:Designan?|Nombrar|Encargar|Cesan)\s+a\s+(?:la\s+señora\s+)?([A-Z]{2}[A-Z\s]{6,80}?)(?:\s+en\s+el\s+cargo\s+(?:de\s+)?(.+?))?'

# Patrón en SE RESUELVE:
r'SE\s+RESUELVE:.*?(?:Designar|Nombrar)\s+a\s+([A-Z]{2}[A-Z\s]{6,80}?)'
```

**Filtros de calidad:**
- Mínimo 2 palabras, mínimo 8 caracteres
- Excluir palabras genéricas: LOS, LAS, INTEGRANTES, MIEMBROS, FUNCIONARIOS, SERVIDORES
- Limpiar sufijos ruidosos: " EN EL", " DEL", " DE LA"

**Pitfall:** Las designaciones de cargos institucionales (no personas) generan falsos positivos: "LA COORDINACIÓN DE GESTIÓN DOCUMENTARIA". El filtro de 2 palabras + exclusión de genéricos mitiga ~90%.

### 2. ent_organos — Ministerios, municipalidades, organismos

```python
RE_MINISTERIO = r'(Ministerio\s+(?:de\s+)?[A-Z][A-Za-z]{4,60})(?:\s+(?:y\s+su|consiste|del\s+)|\.|,|\(|;|:|$)'
RE_GOBIERNO_REGIONAL = r'(Gobierno\s+Regional\s+(?:de\s+)?[A-Z][A-Za-z]{4,40})(?:...)'
RE_MUNICIPALIDAD = r'(Municipalidad\s+(?:Distrital|Provincial|Metropolitana|de\s+)?[A-Z][A-Za-z]{4,50})(?:...)'
RE_ENTIDAD = r'(Superintendencia\s+(?:de\s+)?[A-Z][A-Za-z]{4,50})(?:...)'
```

**Pitfall original:** Regex original `{3,60}?` con lazy quantifier paraba en 3 chars ("Superintendencia de Banca" truncado). **Fix:** usar greedy `{4,60}` con boundary stops explícitos.

### 3. ent_montos — Valores monetarios

```python
RE_SOLES = r'S/\s*([\d,]+(?:\.\d{1,2})?)\s*(?:\(([^)]+)\))?'
RE_DOLARES = r'US\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?:\(([^)]+)\))?'
RE_UIT = r'(\d+(?:\.\d+)?)\s*(?:UIT|Unidades?\s+Impositivas?\s+Tributarias?)'
```

**Deduplicación:** Usar `set()` con key `(monto, moneda)` para evitar duplicados del mismo valor en diferente formato en el texto.

### 4. ent_normas_relacionadas — Leyes, decretos, resoluciones citadas

```python
RE_LEY = r'Ley\s+(?:N[°º]\.?\s*)?(\d{4,6})'
RE_DS = r'Decreto\s+Supremo\s+(?:N[°º]\.?\s*)?(\d{2,4}-\d{4}-[A-Z]{2,6})'
RE_DL = r'Decreto\s+Legislativo\s+(?:N[°º]\.?\s*)?(\d{3,5})'
RE_RM = r'(?:Resolución\s+Ministerial|R\.?\s*M\.?)\s+(?:N[°º]\.?\s*)?(\d{2,6}-\d{4}-[A-Z]{2,10})'
```

**Resultado:** 94% de normas tienen al menos 1 norma relacionada. Promedio ~5 por norma.

### 5. ent_viajes — Autorizaciones de viaje

**Enfoque 2-pasos:**
1. Detectar viaje en el título (primeros 800 chars) — la autorización de viaje siempre se anuncia en el encabezado
2. Extraer nombre de la persona del bloque SE RESUELVE

```python
RE_VIAJE_TITULO = r'Autorizan?\s+(?:el\s+)?viaje\s+(?:de\s+)?(.+?)\s+a\s+([A-Z][A-Za-z\s,.]{4,40})(?:,?\s*(?:en\s+comisi[óo]n|en\s+misi[óo]n))?'
```

**Pitfall crítico:** En los títulos de viajes, la persona NO aparece por nombre sino por cargo: "Autorizan viaje de docente de la Universidad Nacional Agraria La Molina a España". El nombre real está en SE RESUELVE. Sin el paso 2, el campo `funcionario_nombre` contiene descripciones de cargo, no nombres.

**Pitfall #2:** El lazy quantifier `{3,40}?` en el grupo de destino capturaba 3-4 chars ("Chil" en vez de "Chile", "EE.U" en vez de "EE.UU."). **Fix:** greedy `{4,40}`.

**Calidad:** Los destinos quedan con ruido al final ("Chile y encargan su Despacho a"). Se limpia con SQL UPDATE post-procesamiento. La información de país/ciudad es recuperable.

### 6. ent_plazos — Días y meses

```python
RE_PLAZO_DIAS = r'(?:plazo\s+(?:de|máximo\s+de)\s+)?(\d+)\s+(?:días|días\s+hábiles|días\s+calendario)'
RE_PLAZO_MESES = r'(?:plazo\s+(?:de|máximo\s+de)\s+)?(\d+)\s+(?:meses|meses\s+calendario)'
```

### 7. ent_procesos — CAS y concursos públicos

```python
RE_CAS = r'(?:Concurso\s+Público\s+)?CAS\s+(?:N[°º]\.?\s*)?(\d{1,4}-\d{4}-[A-Z]{2,10})'
RE_CONCURSO = r'(?:concurso\s+público|proceso\s+de\s+selecci[óo]n)\s+(?:N[°º]\.?\s*)?(\d{1,6})'
```

**Baja cobertura (<1%):** Las normas de 2024 raramente contienen números de CAS o concursos en el texto — estos aparecen en avisos/publicaciones separadas, no en las normas mismas.

### 8. ent_extractos — Sumilla + palabras clave

Generado desde `sumilla` y `palabras_clave` existentes. 100% cobertura.

## Lecciones aprendidas

1. **Greedy vs lazy en regex de entidades:** Usar greedy con boundary stops explícitos, NO lazy quantifiers. `{3,40}?` captura el mínimo posible (3 chars); `{4,40}` con stops captura el nombre completo.

2. **Los nombres NO están en los títulos de viajes:** Las autorizaciones de viaje mencionan cargos ("docente", "oficial"), no nombres. Los nombres están en SE RESUELVE. Extracción en 2 pasos es necesaria.

3. **Deduplicación por tupla:** Para montos, deduplicar por `(valor, moneda)` evita que el mismo monto aparezca 2-3 veces (una con concepto entre paréntesis, otra sin).

4. **Filtros de calidad son críticos:** Sin filtros, ~15% de funcionarios son falsos positivos (cargos institucionales, no personas). Con filtros de 2+ palabras + exclusión de términos genéricos, falsos positivos bajan a ~5%.

5. **No usar `execute_code` para scripts con `groq`:** El sandbox no carga extensiones C (pydantic_core). Usar `terminal` con archivo `.py`.
