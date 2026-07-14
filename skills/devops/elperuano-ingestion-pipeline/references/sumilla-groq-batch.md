# Fase 2: Groq Batch → Sumilla

## Contexto

Después de Fase 1 (extraer `texto_completo` desde HTML), 33,255 normas (34%) quedaron sin sumilla.
La DB `normas_total.db` ya tiene 97,809 normas con `texto_completo` al 100%.
El pipeline batch original (`02_groq_batch_pipeline.py`) extraía todos los metadatos a la vez,
pero re-ejecutarlo completo costaría ~$2.89.

## Enfoque: sumilla-only

Script: `scripts/fase2_sumilla_groq.py` — pipeline focalizado que solo pide sumilla,
reduciendo tokens y costo drásticamente.

**Diferencias vs `02_groq_batch_pipeline.py`:**

| Aspecto | 02 (original) | fase2 (sumilla-only) |
|---------|--------------|---------------------|
| Fuente | Archivos .md | DB SQLite directa |
| Schema pedido | 13 campos JSON | Solo `{"sumilla": "..."}` |
| Tokens input | ~900/doc | ~2,000/doc (texto_completo más largo) |
| Tokens output | ~400/doc | ~50/doc |
| Costo/doc | $0.000039 | ~$0.000052 |
| Costo total | $2.89 (75K docs) | ~$1.73 (33K docs) |

## Costo real (batch pricing, 50% descuento)

| Concepto | Cálculo | USD |
|----------|---------|-----|
| Input | 33,255 × ~2,000 tokens = 66.5M | ~$1.66 |
| Output | 33,255 × ~50 tokens = 1.66M | ~$0.07 |
| **Total** | | **~$1.73** |

La estimación anterior de $25-30 asumía sync API pricing y más tokens por norma.
El batch API (50% descuento) más el prompt focalizado reducen el costo 15x.

## Diseño del prompt

```
Eres un experto en derecho peruano. Genera una sumilla concisa
de la norma legal proporcionada. La sumilla debe:

- Tener entre 80 y 200 caracteres
- Describir el propósito principal de la norma
- Incluir actores clave (entidad que emite, personas designadas si aplica)
- Usar lenguaje jurídico preciso

Responde ÚNICAMENTE con un objeto JSON con el campo "sumilla".
Ejemplo de respuesta: {"sumilla": "Designan a Juan Pérez como Director..."}
```

**Pitfall crítico**: Groq requiere que el prompt contenga la palabra "json" (en cualquier forma)
cuando se usa `response_format: {"type": "json_object"}`. Sin esto, devuelve `400 Bad Request`.
La frase "objeto JSON" en el prompt satisface este requisito.

## Optimizaciones de costo

| Parámetro | Valor | Impacto |
|-----------|-------|---------|
| `MAX_TEXT_CHARS=8000` | Trunca textos largos | El prompt de sumilla solo necesita encabezado + considerandos, no el texto completo de 500K chars |
| `max_tokens=150` | Limita output | Sumilla de 80-200 chars ≈ 50 tokens. 150 da margen |
| `temperature=0.0` | Determinístico | Sin variabilidad entre batches |
| `model=llama-3.1-8b-instant` | Más barato en batch | 8B suficiente para resumir texto legal |

## Subcomandos

```bash
python3 scripts/fase2_sumilla_groq.py              # Estado actual
python3 scripts/fase2_sumilla_groq.py generate     # DB → 67 JSONL batches
python3 scripts/fase2_sumilla_groq.py upload       # Subir a Groq (4-5 min)
python3 scripts/fase2_sumilla_groq.py status       # Verificar progreso
python3 scripts/fase2_sumilla_groq.py download     # Descargar + actualizar DB
python3 scripts/fase2_sumilla_groq.py full         # Pipeline completo
python3 scripts/fase2_sumilla_groq.py cancel       # Cancelar batches activos
```

## Tracking stateful (resume-safe)

Archivo: `data/sumilla_tracking.json`

```json
{
  "batch_001.jsonl": {
    "file_id": "file_xxx",
    "batch_id": "batch_xxx",
    "status": "completed",
    "normas": 500,
    "uploaded_at": "2026-05-02T15:17:00",
    "downloaded": false
  }
}
```

- `upload` es idempotente: skippea lotes con batch_id existente
- `download` es idempotente: skippea lotes con `downloaded: true`
- Si hay corte de energía, reanudar con `upload` o `download` es seguro
- `cancel` solo afecta batches en `in_progress`/`validating`/`finalizing`

## Recuperación de fallos individuales en batch

El batch API de Groq ocasionalmente falla en requests individuales (499/500 completados).
Las normas fallidas quedan sin sumilla en la DB y el count final muestra algunos pendientes.

**Técnica de recuperación** (usada 02-may-2026 — 4/5 recuperadas):

```bash
cd PeruanoSearchEngine02 && python3 -c "
import sqlite3, json, os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv('.env')
from groq import Groq

DB = 'data/normas_total.db'
client = Groq(api_key=os.getenv('GROQ_API_KEY'), timeout=60)
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute('''SELECT id, texto_completo FROM normas 
    WHERE (sumilla IS NULL OR sumilla = '')
    AND LENGTH(texto_completo) >= 50''')
rows = cur.fetchall()

PROMPT = 'Eres un experto en derecho peruano. Genera una sumilla concisa (80-200 chars). Responde SOLO con JSON: {\"sumilla\": \"...\"}'

for norm_id, texto in rows:
    try:
        resp = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {'role': 'system', 'content': PROMPT},
                {'role': 'user', 'content': texto[:6000]}
            ],
            response_format={'type': 'json_object'},
            temperature=0.0, max_tokens=200
        )
        sumilla = json.loads(resp.choices[0].message.content).get('sumilla','').strip()
        cur.execute('UPDATE normas SET sumilla=? WHERE id=?', (sumilla, norm_id))
        conn.commit()
        print(f'OK {norm_id}')
    except Exception as e:
        print(f'FAIL {norm_id}: {e}')
conn.close()
"
```

**Pitfalls de recuperación:**
- Si falla con `json_validate_failed` + `max completion tokens reached`, subir `max_tokens=200` y truncar input a 6,000 chars
- Normas con `texto_completo < 50 chars`: imposibles de resumir, ignorar
- Usar `terminal` para ejecutar — NUNCA `execute_code` (ver abajo)

## Pitfall: execute_code no puede con groq

El sandbox de `execute_code` ejecuta en un entorno aislado que NO puede cargar extensiones C compiladas.
Cualquier script que importe `groq` (→ pydantic → pydantic_core) falla con:
`ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`

**Solución**: escribir el script inline con `python3 -c "..."` ejecutado vía `terminal`. 
El Python del sistema SÍ tiene groq instalado correctamente.

Ejemplo correcto:
```
terminal: cd ... && python3 -c "from groq import Groq; ..."
```

Ejemplo INCORRECTO:
```
execute_code: from groq import Groq  # ❌ ModuleNotFoundError
```

| Métrica | Valor |
|---------|-------|
| Normas procesadas | 33,254 |
| Sumillas generadas | 33,249 (99.985%) |
| Errores de parseo | 0 |
| Pendientes (errores Groq) | 5 (3 errores batch + 2 texto <50 chars) |
| Tiempo Groq batch | ~45 minutos (67 lotes × 500) |
| Costo estimado | ~$1.73 USD |
| Lotes | 67 (66 × 500 + 1 × 254) |
| Velocidad de descarga | ~2 lotes/min en burst inicial |

## Monitoreo manual (NO usar cronjobs)

Los cronjobs de Hermes NO son confiables. Monitorear manualmente:

```bash
# Verificar cada 10-15 min:
python3 scripts/fase2_sumilla_groq.py status

# Descargar incrementalmente (lotes ya procesados se saltan):
python3 scripts/fase2_sumilla_groq.py download
```
