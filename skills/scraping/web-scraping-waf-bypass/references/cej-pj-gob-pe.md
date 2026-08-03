# CEJ - Poder Judicial del Perú (cej.pj.gob.pe)

## Perfil del sitio

| Atributo | Valor |
|---|---|
| URL base | https://cej.pj.gob.pe/cej/forms/ |
| WAF | Radware Bot Manager (perfdrive.com) |
| Captcha externo | hCaptcha (sitekey: `ae73173b-7003-44e0-bc87-654d0dab8b75`) |
| Captcha interno | Texto PNG (4 caracteres alfanuméricos, imagen `#captcha_image`) |
| Backend | Java (JBWEB — JBoss/Tomcat inferido) + Angular (compilado) |
| Server header | `server: rdwr` |
| Tracking | Stormcaster JS + Google Analytics UA-47013024-7 |

## Rutas conocidas

| Ruta | Método | Descripción |
|---|---|---|
| `/cej/forms/busquedaform.html` | GET | Página principal de búsqueda (por filtros) |
| `/cej/forms/busquedacodform.html` | POST | Búsqueda por código de expediente (GET da 405) |
| `/cej/forms/detalleform.html` | POST | Detalle del expediente + documentos |
| `/cej/forms/preguntasFrecuentes.html` | GET | FAQ |

## Campos del formulario de búsqueda por código

```
cod_expediente  - Número de expediente (text, 5 dígitos)
cod_anio        - Año (text, 4 dígitos)
cod_incidente   - Incidente (text, normalmente "0")
cod_distprov    - Código de distrito/provincia (text, ej: "0401")
cod_organo      - Órgano jurisdiccional (text, ej: "JP", "JR")
cod_especialidad- Especialidad (text, ej: "CI", "PE", "LA", "FC", "DC")
cod_instancia   - Instancia (text, ej: "01", "02", "03")
```

Formato de código completo: `NNNNN-AAAA-I-DDDD-OO-EE-II`

## Flujo de acceso

1. GET a `busquedaform.html` → (normalmente no dispara Radware)
2. Click en tab "Por Código de Expediente" (selector `[href="#tabs-2"]` o `[title="Por código de expediente"]`)
3. Llenar 7 campos del formulario `#busquedaPorCodigo`
4. Click en `#consultarExpedientes`
5. Si hay captcha de texto: resolver con 2Captcha ImageToTextTask o ddddocr
6. Esperar resultado y parsear tabla de resultados

## Documentos

Los documentos tienen link con `title="Descargar"` y href relativo. La descripción (Sumilla) está en el HTML circundante con patrón `roptionss > Sumilla: </div>.*?fleft > ([^<]+)`.

Filtro de documentos importantes:
```python
DOC_KEYWORDS = ['SENTENCIA', 'RESOLUCION', 'AUTO FINAL', 'FUNDADA',
                'INFUNDADA', 'ARCHIVO DEFINITIVO', 'CONCLUSION']
```

## Proxy/VPN recomendados

| Proveedor | Precio/GB | IPs Perú | Notas |
|---|---|---|---|
| Decodo (ex Smartproxy) | $2.75-3.75 | Sí | Cupón DECODO5 |
| DataImpulse | $1.00 | Sí | Más barato para alto volumen |
| Bright Data | $4.00 | Pool enorme | Cupón PROXYWAY60 |
| Byteful | $2.75-3.25 | 116K+ IPs Perú | Cupón PROXYWAY10 |

## Estadísticas del proyecto (38,242 expedientes)

- A (2021): 19,121 exp (LA 9,661 + DC 9,460)
- B (2023): 19,121 exp (LA 9,699 + DC 9,422)
- Ritmo: ~5-8 exp/hora por instancia
- Tasa de captcha fail: ~65% con 2Captcha ImageToTextTask
- Scripts: `run_A.py`, `run_B.py`, `runner.py` (auto-reinicio), `stats.py`
- Chrome profiles separados para A y B (puertos remote-debugging independientes)
