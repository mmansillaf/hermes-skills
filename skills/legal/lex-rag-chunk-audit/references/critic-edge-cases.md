# Edge Cases del Critic Agent

Verificados durante la sesión del 2026-05-19 con `agents/critic.py`.

| Escenario | Entrada | Resultado | Score |
|-----------|---------|-----------|-------|
| Respuesta vacía | `""` | passed=True, 0 citas | 100% |
| Sin citas | Texto legal sin referencias | passed=True, 0 citas | 100% |
| Cita real | `(Jurisprudencia/1308950.html)` | detectada, verified=1 | 100% |
| Cita fake | `(Jurisprudencia/9999999.html)` | detectada, hallucinated=1 | 0% |
| Ley de 5 dígitos | `Ley N.º 27803` | ignorada (5 dígitos) | 100% |
| Número suelto de 5 dígitos | `12345` | ignorado (5 dígitos) | 100% |
| Doc ID de 6 dígitos | `1308950` | capturado como cita | verificable |
| Doc ID de 7 dígitos | `1014883` | capturado como cita | verificable |

## Lecciones

1. **No existen doc_ids de 5 dígitos** en el corpus (64K docs). Pattern 6 debe usar `\d{6,7}`, no `\d{5,7}`. Esto elimina de golpe los falsos positivos de leyes (27803, 28706).
2. **Score 0% sin citas** es confuso. Debe ser 100% (nada que verificar = nada incorrecto).
3. **Fuzzy matching deshabilitado** — causaba matches falsos (EXP. N° 1308950 → 965300.html). Solo coincidencias exactas en `id2doc`.
