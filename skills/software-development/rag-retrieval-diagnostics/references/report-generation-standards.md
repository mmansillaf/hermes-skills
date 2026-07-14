# Estándares de Generación de Reportes

## Regla de oro

Todo informe de análisis, batería de pruebas, o diagnóstico debe entregarse en **3 formatos simultáneos**:
- `.md` — Markdown con dark theme CSS embebido
- `.html` — HTML standalone con GitHub Pages-ready
- `.txt` — Texto plano con Q&A completas (NO truncadas)

## Requisitos por formato

### Markdown (.md)
- Encabezado con fecha, hora, estado del sistema
- Badges de score (PASS/FAIL/WARN)
- Tabla resumen con métricas clave
- Secciones colapsables para detalles extensos
- Links a los otros formatos al inicio

### HTML (.html)
- CSS dark theme por defecto (#1a1a2e fondo, #e0e0e0 texto)
- Misma estructura que el MD, estilizada
- Badges en color (verde PASS, amarillo WARN, rojo FAIL)
- Tablas con bordes y alineación
- Autocontenido (CSS inline, sin dependencias externas)
- Listo para GitHub Pages sin modificación

### Texto (.txt)
- **Preguntas COMPLETAS** — NUNCA truncar `question[:80]`
- **Respuestas COMPLETAS** — NUNCA truncar `answer[:200]`
- Formato legible: `══════ PREGUNTA N ══════`
- Incluir score y sub-scores por pregunta
- Longitud mínima por respuesta: 200 chars (si la hay)

## Anti-patrones

| ❌ NUNCA | ✅ SIEMPRE |
|---------|-----------|
| `question[:80]` al guardar JSON | `question` completa |
| `answer[:200]` en TXT de Q&A | `answer` completa (o truncar a 2000 chars si es extremadamente larga) |
| Solo uno de los 3 formatos | Los 3 formatos |
| CSS claro (fondo blanco) | CSS dark theme |
| Preguntas cortadas a mitad de palabra | Preguntas íntegras |
| Sin badges ni tabla resumen | Badges + tabla + métricas |

## Pitfall: Multi-format JSON schema al combinar lotes

Cuando se combinan resultados de tests ejecutados con DIFERENTES scripts, los JSONs pueden usar campos distintos para la misma información:

| Concepto | Script A (bateria_100q_lote1.json) | Script B (bateria_100q_lote2.json) |
|----------|-------------------------------------|-------------------------------------|
| Pregunta | `q` | `question` |
| Respuesta | `answer` | `answer` |
| Calidad | `quality` ("OK"/"WARN"/"ERROR") | `status` ("ok") |
| Confianza | `conf` (float) | `confidence` (float) |
| Tiempo | `ms` (int) | `timing_ms` (int) |
| Nivel | `nivel` | `level` |

**Síntoma**: preguntas aparecen como `Q: ?`, confianza=0.00, tiempo=0ms en el reporte combinado. El generador busca `q.get('q')` pero el campo se llama `question`.

**Fix**: normalizar con un helper que pruebe ambas llaves al cargar:

```python
def normalize_result(r):
    return {
        'q': r.get('q') or r.get('question') or '?',
        'answer': r.get('answer', ''),
        'quality': r.get('quality') or ('OK' if r.get('status') == 'ok' else 'WARN'),
        'conf': r.get('conf') or r.get('confidence', 0),
        'ms': r.get('ms') or r.get('timing_ms', 0),
        'nivel': r.get('nivel') or r.get('level', '?'),
        'web': r.get('web', False),
        'cached': r.get('cached', False),
    }
```

**Siempre inspeccionar keys de cada JSON antes de combinar** — ejecutar `json.load(f); print(list(data[0].keys()))` por cada archivo.

**Scripts del mismo proyecto pueden usar schemas diferentes** si fueron escritos en fechas distintas o por diferentes personas. NO asumir consistencia interna.

## Template mínimo para script de batería

```python
def save_reports(results, name):
    base = f"reports/{name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    # TXT: Q&A completo
    with open(f"{base}.txt", "w") as f:
        for i, r in enumerate(results):
            f.write(f"{'═'*60}\nPREGUNTA {i+1}: {r['question']}\n")
            f.write(f"RESPUESTA: {r.get('answer', 'SIN RESPUESTA')}\n")
            f.write(f"SCORE: {r['score']} | CONF: {r.get('confidence', 'N/A')}\n\n")
    
    # MD: con dark theme CSS al final
    with open(f"{base}.md", "w") as f:
        f.write(f"# {name}\n\n")
        f.write(f"**Fecha:** {datetime.now().isoformat()}\n\n")
        f.write(f"| Métrica | Valor |\n|---|---|\n")
        f.write(f"| Total preguntas | {len(results)} |\n")
        # ... more metrics ...
        f.write("\n<style>body{background:#1a1a2e;color:#e0e0e0;}</style>\n")
    
    # HTML: standalone dark theme
    with open(f"{base}.html", "w") as f:
        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{{background:#1a1a2e;color:#e0e0e0;font-family:monospace}}
.pass{{color:#4caf50}}.warn{{color:#ff9800}}.fail{{color:#f44336}}
table{{border-collapse:collapse}}td,th{{border:1px solid #444;padding:4px 8px}}
</style></head><body>
<h1>{name}</h1>
<!-- contenido -->
</body></html>""")
```

## Verificación post-generación

```bash
# Verificar que el TXT no tenga preguntas truncadas
grep -c '^PREGUNTA' reports/*.txt  # debe coincidir con total de preguntas
# Verificar que no haya '…' al final de preguntas (señal de truncado)
grep '…$' reports/*.txt  # no debe haber matches
```
