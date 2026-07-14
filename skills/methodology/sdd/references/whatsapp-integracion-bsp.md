# WhatsApp Business API: Estrategia de Integracion para CRM/Intake

*Investigacion realizada junio 2026. Basada en documentacion oficial de Meta, Twilio y 360dialog.*

## Realidad: No hay "alternativas" — solo intermediarios

La **WhatsApp Business Cloud API** (Meta) es la UNICA via oficial para integracion programatica. 
Twilio, 360dialog y otros BSP (Business Solution Providers) NO son APIs alternativas — son 
intermediarios que te dan acceso a la misma API de Meta. No hay "Evolution API gratis" ni 
"Baileys" como alternativa legal de produccion.

**Regla de oro:** Cualquier solucion que emule WhatsApp Web (Baileys, whatsapp-web.js, 
Evolution API, OpenWA) es NO OFICIAL y conlleva riesgo de baneo del numero. Solo usarlas 
para prototipos internos sin clientes reales.

## Arquitectura

```
Tu Backend ──HTTP──> BSP ──> Meta WhatsApp Cloud API ──> Cliente
```

**Costo base:** Mensajes entrantes y respuestas dentro de ventana de 24hs son GRATIS.
Solo se paga por mensajes salientes iniciados por la empresa (Marketing, Utility, Authentication).

## Comparativa de BSPs

| Aspecto | Twilio | 360dialog | Meta Directo |
|---------|--------|-----------|--------------|
| Costo fijo mensual | $0 | €49/mes | $0 |
| Markup por mensaje | $0.005/msg (adicional a tarifa Meta) | 0% (solo tarifa Meta) | 0% |
| Tarifa Meta (ej. Peru) | ~$0.035/msg (marketing) | ~$0.035/msg | ~$0.035/msg |
| SDK Python | Excelente (`twilio` package) | REST basico | Facebook Graph API |
| Sandbox gratis | Si (WhatsApp Sandbox, sin WABA) | No (necesita WABA real) | No (necesita WABA real) |
| Configuracion inicial | 15 min (cuenta + sandbox) | 1-3 dias (aprobacion WABA) | 3-7 dias (registro Meta) |
| Ideal para | MVP, prototipos, equipos chicos | Produccion volumen medio-alto | Equipos con experiencia Meta |

## Recomendacion por etapa

| Etapa | BSP | Por que |
|-------|-----|---------|
| **MVP / Prototipo** | Twilio | Sandbox gratis, SDK Python, configuracion inmediata. Sin esperar aprobacion de WABA. |
| **Produccion inicial** | Twilio | $0 fijo, pagas solo lo que usas. El markup de $0.005/msg es irrelevante para <1000 msg/mes. |
| **Escalamiento** | 360dialog o Meta Directo | Eliminar markup de Twilio cuando el volumen justifique el costo fijo. |

## Costos Reales para Estudio Legal

Escenario tipico: ~100 conversaciones entrantes/mes, ~20 respuestas fuera de ventana 24h.

| Concepto | Twilio | 360dialog |
|----------|--------|-----------|
| Costo fijo | $0 | €49 |
| 100 msgs entrantes | $0 | $0 |
| 20 msgs marketing salientes | $0.80 | $0.70 |
| **Total mensual** | **~$0.80** | **~€49** |

Para un estudio legal, Twilio es la opcion mas economica hasta superar ~5000 msg/mes.

## Setup Basico con Twilio (Python)

```python
from fastapi import FastAPI, Request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()
twilio_client = Client(account_sid, auth_token)

@app.post("/api/v1/webhook/whatsapp")
async def webhook_whatsapp(request: Request):
    data = await request.form()
    mensaje = data.get("Body", "")
    remitente = data.get("From", "").replace("whatsapp:", "")
    
    # Procesar con IA (Groq, OpenAI, etc.)
    lead_data = await procesar_con_ia(mensaje, remitente)
    
    # Crear lead en DB
    lead = await crear_lead(lead_data)
    
    # Responder
    resp = MessagingResponse()
    resp.message(f"Gracias por contactarnos. Su codigo es {lead.codigo}. Lo atenderemos en breve.")
    return str(resp)
```

## Anti-patrones (NO hacer)

- **NO** Evolution API / Baileys / whatsapp-web.js — riesgo de baneo del numero
- **NO** whatsapp-web.js aunque "solo sea para pruebas" — el numero puede ser baneado igual
- **NO** asumir que la API no-oficial es "gratis" — el costo es el numero de telefono
- **NO** olvidar configurar el webhook con verificacion de firma (Twilio valida con tu Auth Token)
- **NO** responder fuera de la ventana de 24h sin plantilla aprobada por Meta
