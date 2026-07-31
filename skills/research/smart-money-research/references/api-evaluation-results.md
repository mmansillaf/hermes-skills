# Evaluación de APIs Financieras — Smart Money Detection
## Resultados de pruebas en vivo (Jul 2026)

---

## 1. Unusual Whales API (https://unusualwhales.com/public-api)

**Estado:** Documentado pero no probado (requiere token pago)
**Documentación:** `curl -H "Accept: text/plain" https://api.unusualwhales.com/docs` — Markdown completo
**MCP Server:** https://unusualwhales.com/public-api/mcp
**Skill.md (AI):** https://unusualwhales.com/skill.md

**100+ endpoints documentados incluyendo:**
- `/api/stock/{ticker}/gex-levels` — GEX profesional
- `/api/stock/{ticker}/greek-exposure/strike` — GEX por strike
- `/api/option-trades/flow-alerts` — Options Flow en tiempo real
- `/api/darkpool/{ticker}` — Dark Pool trades
- `/api/congress/recent-trades` — Congress trading
- `/api/crypto/whale-transactions` — Crypto whales
- `/api/companies/{ticker}/earnings-estimates` — Earnings
- `/api/alerts/configuration` — Crear alertas
- `/api/stock/{ticker}/technical-indicator/{function}` — RSI, MACD, VWAP, etc.

**Costo:** Plan pago (ver https://unusualwhales.com/pricing?product=api)
**Veredicto:** MEJOR OPCIÓN — reemplaza 70% del código casero

---

## 2. Massive API (api.massive.com)

**API Key:** `vME3VzHxYaiUDGU6LI6BI9_V2yG1v5Zg` (funcional Jul 2026)

**Endpoints que funcionan:**
- `GET /v3/reference/dividends?apiKey=...` — Datos de dividendos OK ✅
- `GET /v3/reference/tickers?search=...` — Datos de tickers OK ✅

**Endpoints que NO existen (404):**
- `/v3/financials` — No existe
- `/v3/earnings` — No existe
- `/v3/option-chains` — No existe
- `/v3/options` — No existe
- `/v3/stocks` — No existe
- `/v3/crypto` — No existe
- `/v3/news` — No existe

**Costo:** Gratis (key funcional)
**Veredicto:** VALOR BAJO — solo reference data (tickers, dividends). No tiene options ni earnings. Complemento menor.

---

## 3. MCP Capitol Trades (anguslin/mcp-capitol-trades)

**Instalación:** `npm install -g @anguslin/mcp-capitol-trades` ✅ (70 packages, 12s)
**Ubicación:** `/home/usuario/.hermes/node/lib/node_modules/@anguslin/mcp-capitol-trades/`

**Funciones del scraper:**
- `getTopTradedAssets()` — Tops por volumen
- `getBuyMomentumAssets()` — Momento de compra
- `getAssetStats(ticker)` — Estadísticas por activo
- `getPoliticianStats(name)` — Estadísticas por político
- `getPartyBuyMomentum()` — Momento por partido

**Estado:** BLOQUEADO por Vercel Security Checkpoint (429)
El sitio capitolttrades.com tiene Cloudflare anti-bot. Incluso con User-Agent, el scraper falla.

**Alternativa:** Usar `/api/congress/recent-trades` de Unusual Whales API (requiere token pago)
**Costo:** Gratis
**Veredicto:** Instalado pero no funcional por Cloudflare. Alternativa via Unusual Whales.

---

## 4. CryptoQuant (https://cryptoquant.com)

**Estado:** El link de insight específico retornó 404.
**Plataforma:** On-chain analytics (exchange flows, MVRV, SOPR, whale positions)
**Costo:** Tier gratuito limitado, Pro ~$79-199/mes
**Veredicto:** Posible expansión Fase 3 para crypto on-chain avanzado.

---

## 5. Apify (https://apify.com)

**Plataforma:** Web scraping como servicio (pay-per-use)
**Actores relevantes:**
- `saswave/capitol-trades-scraper` — Congress trades (alternativa paga al MCP gratuito)
- Múltiples scrapers de e-commerce, redes sociales, noticias

**Costo:** ~$0.01-0.05 por ejecución de actor
**Veredicto:** Alternative data Fase 3. No prioritario para MVP.

---

## 6. Market Chameleon (https://marketchameleon.com/Home/Developer)

**Estado:** No accesible via curl (requiere JavaScript rendering). 
**Potencial:** Datos de opciones (IV rank, unusual activity)
**Veredicto:** Zona gris — no se pudo evaluar.

---

## Resumen de Stack Recomendado

```
MVP (Fase 1): yfinance (OHLC) + Unusual Whales API (GEX, Flow, Dark Pool, Congress, Crypto, Earnings)
Fase 2: + Massive API (reference data complemento)
Fase 3: + CryptoQuant (on-chain) + Apify (alternative data scraping)
```

**Nota:** Unusual Whales requiere plan pago. Es la inversión más importante — reemplaza 70% del código que se escribiría desde cero.
