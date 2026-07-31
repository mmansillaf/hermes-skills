---
name: smart-money-research
description: Use when investigating Smart Money (capital inteligente) — institutional capital flows, SMC/ICT trading concepts, order flow analysis, on-chain tracking, SWFs, hedge funds, regulation, and global capital rotation. Covers markets tradicionales (13F, COT, Wyckoff) y crypto/blockchain (Nansen, Arkham, stablecoins).
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, trading, crypto, macro, regulation, smart-money]
    related_skills: [research-synthesis, web-deep-research, youtube-research]
---

# Smart Money Research

## Overview

Investigar el Smart Money (Capital Inteligente) requiere un enfoque **multidimensional en 3 canales paralelos**: (a) canal transparente retrasado (13F, COT — datos públicos con lag), (b) canal en tiempo real (order flow, footprint charts, CVD), (c) canal on-chain (wallets etiquetadas, stablecoins, whales).

Este skill define el marco para una investigación exhaustiva que combina material local, arXiv, GitHub, reportes institucionales (IIF, IMF, SEC, CFTC) y plataformas especializadas.

## When to Use

- Usuario pide "investiga Smart Money" o "dinero inteligente" en cualquier contexto
- Usuario tiene carpeta con archivos .txt sobre Smart Money/SMC/ICT/Wyckoff
- Necesitas investigar flujos de capital institucional a mercados emergentes
- Necesitas analizar herramientas de order flow, on-chain, o SMC
- Usuario pregunta sobre regulación de stablecoins, SWFs, o hedge funds

## Investigación — 8 Dimensiones (3 canales + 5 dominios)

### Dimensión 1: Material Local
1. Buscar carpeta `SmartMoney/` o archivos con smart*.txt
2. Leer TODOS los archivos con read_file (posiblemente 5-6 archivos progresivos)
3. Identificar: definiciones, actores, conceptos SMC, datos de flujos, herramientas
4. Crear tabla de inventario: archivo × tema × tamaño × hallazgos clave
5. Buscar progresión (los archivos pueden ser iteraciones del mismo prompt)

### Dimensión 2: Papers Académicos (arXiv)
Buscar estos queries en arXiv:

| Query | Resultados Esperados |
|-------|---------------------|
| `market microstructure institutional order flow` | 6-10 papers |
| `informed trading order flow prediction` | 20-23 papers |
| `institutional investors price impact liquidity` | 4-5 papers |
| `smart money wyckoff accumulation` | 0 resultados (ir a queries más amplios) |

Papers clave a buscar:
- **Kang S. (2026)**: `arXiv:2512.18648` (Matched Filter Order Flow) + `arXiv:2601.11602` (Physics of Price Discovery)
- **Nechepurenko M. (2026)**: `arXiv:2605.02287` (ILS Framework, Polymarket)
- **Zhong et al. (2026)**: `arXiv:2604.18046` (EvoMarket Simulator)
- **Adverse Selection SMC**: `arXiv:2510.27334` (RL Market Making — base académica SMC)
- **Deep Learning LOB**: `arXiv:2505.22678` (Siamese LOB + OFI)
- **Square-Root Law**: `arXiv:2502.17906` (Brownian motion + order flow), `arXiv:2606.24019`
- **VVG Classifier**: ~~`arXiv:2605.11423`~~ ⚠️ **NOT FOUND on arXiv** — this paper ID returned empty/parse error on arXiv API query (July 2026). Possibly withdrawn, unpublished, or an incorrect ID. Do not include in reports without re-verifying. If it remains unfindable, cite the concept neutrally as "a regime classifier for MNQ intraday" without the arXiv reference.

### Dimensión 3: GitHub y Herramientas Open-Source
Buscar en `github.com/search?q=...&type=repositories&s=stars&o=desc`:

| Query | Esperado |
|-------|----------|
| `smart money concepts trading` | joshyattridge/smart-money-concepts (⭐1,873) |
| `order flow analysis trading` | TapeFlow, OrderFlow-Analysis-Pro |
| `smart money tracker order flow` | crypto-liquidity-ai-trading-bot (84 stars) |

### Dimensión 4: Flujos Macro (IIF, SWFs, IMF)
- **IIF Capital Flows Tracker**: iif.com/Research/Capital-Flows-Tracker — datos mensuales a EM
- **Global SWF**: globalswf.com — SWF transaction database, AUM, activity
- **IMF GFSR**: imf.org — Global Financial Stability Report
- **SEC EDGAR**: sec.gov/edgar — Form 13F, Form SHO
- **CFTC COT**: cftc.gov/MarketReports — Commitments of Traders
- **SWFI**: swfinstitute.org — Sovereign Wealth Fund Institute

### Dimensión 5: Crypto y On-Chain
- **CoinGecko**: api.coingecko.com — precios en vivo (rate limits: varias consultas antes de 429)
- **DefiLlama**: defillama.com — stablecoins total market cap
- **Nansen**: nansen.ai — Smart Money tags, Signal alerts
- **Arkham Intelligence**: arkham.com — entity de-anonymization, whale alerts
- **Glassnode**: glassnode.com — macro on-chain metrics
- **Blog Nansen**: artículos sobre Agentic Trading, Hyperliquid/Base/Solana integrations

### Dimensión 6: Herramientas de Order Flow y Trading
| Herramienta | Web | Precio | Uso |
|-------------|-----|--------|-----|
| ATAS | atas.net | $30-70/mes | Footprint + cluster analysis (recomendado r/OrderFlow 2025) |
| Sierra Chart | sierrachart.com | $25-125/mes | Footprint, DOM, Volume Profile |
| Bookmap | bookmap.com | $50-150/mes | Mapa de calor de liquidez |
| Quantower | quantower.com | $0-50/mes | DOM, CVD, footprint multi-mercado |
| Jigsaw Daytradr | jigsawtrading.com | $97/mes | Order flow específico para futuros |

**Alternativas gratuitas** (no olvidar mencionarlas): Dune Analytics (gratis queries básicas), TensorCharts (Solana on-chain), TradingView plan free (limitado), NinjaTrader (gratis simulación), CoinGecko API (gratis con rate limits). Ver `references/free-tools-apis.md` para tabla completa de alternativas gratuitas, repos GitHub verificados y APIs funcionales con código Python de ejemplo.

**Open-source alternatives para GEX** (descubiertas Jul 2026 — mejores que código casero):
| Proyecto | ⭐ | Fuente | Lo que hace |
|----------|-----------|--------|-------------|
| Matteo-Ferrara/gex-tracker | 205⭐ | Scraping CBOE | GEX para SPX, gráficos por strike y expiración |
| aaguiar10/gflows | 106⭐ | CBOE API | GEX + VEX + CHEX para SPX/NDX/RUT, cada 15 min, UI Dash |
| FlashAlpha-lab/gex-explained | 7⭐ | CBOE + Datos públicos | Teoría + código Python funcional para GEX |

**Stack budget-conscious recomendado** (alternativa a Unusual Whales a $150+/mes):
```
GEX:      gex-tracker (gratis) + código yfinance (gratis)   → $0/mes
Options:  Polygon.io Basic ($29/mes) o Unusual Whales        → $29-150/mes
Crypto:   Binance WS + CoinGecko (gratis)                    → $0/mes
Congress: Unusual Whales endpoint o Capitol Trades scraping   → $0-150/mes
Earnings: yfinance + Finnhub free                             → $0/mes
```
Ver `references/api-evaluation-methodology.md` para metodología completa de evaluación de APIs, tabla de resultados de pruebas en vivo, y recomendación detallada de stack.

### Dimensión 7: Alternative Data (la nueva frontera)

Los hedge funds top ya no ganan solo con order flow. Más del 60% de los hedge funds gastan entre $5M–$50M+ anuales en datos alternativos (Eagle Alpha, Neudata, BattleFin). Este skill incluye un reference exhaustivo: `references/alternative-data-hedge-funds.md`.

**Las 5 categorías principales** (por gasto, Eagle Alpha/Neudata 2024):

| # | Categoría | % Gasto | Señal típica | Costo comercial | Alternativa gratuita/bajo costo | Hedge fund que la usa | Dificultad |
|---|-----------|---------|--------------|----------------|-------------------------------|----------------------|-----------|
| 1 | **Geolocalización / foot traffic** | 27% | Conteo de carros en estacionamientos → SSS | $50K–$500K/año | SafeGraph Open Data (gratis US), Google Earth Engine, Sentinel Hub | Citadel, D.E. Shaw, Muddy Waters | Alta (ML+CV) |
| 2 | **Credit card transactions** | 22% | Ingresos en tiempo real pre-earnings | $30K–$300K/año | Affinity Solutions (bajo costo), Envestnet Yodlee, FRED macro | Point72, Citadel, Two Sigma | Media (licencias) |
| 3 | **Web scraping / e-commerce** | 18% | Precios, reviews, inventario online | $20K–$200K/año | Keepa API free tier, scraping propio ($1K/mes proxies) | Point72, Citadel | Baja (técnicamente simple) |
| 4 | **Job postings scraping** | 11% | Hiring trends pre-anuncio | $25K–$40K/año | Indeed API limited, scraping propio ($500/mes) | Palantir Apollo, Two Sigma, Millennium | Baja-Media |
| 5 | **Satellite imagery** | 9% | Actividad agrícola/industrial global | $100K–$1M/año | ESA Sentinel Hub (gratis 1TB), NASA Landsat (gratis), Google Earth Engine | Renaissance, Citadel, Commodity funds | Alta (infraestructura) |

**6-8 adicionales:** App store rankings (4%, fácil de scrapear gratis), Supply chain shipping (7%, AIS data gratuito limitado), Social media sentiment (2%, señal débil post-2021 excepto cripto).

**Caso concreto:** Second Measure detectó caída del 40% en transacciones de Peloton 3 semanas antes del earnings miss Q1 2022 → shorts ganaron ~30% en 3 semanas. Thinknum detectó duplicación de job postings en Tesla Gigafactory TX 3 meses antes del ramp-up productivo.

**Ver reference completo** para: proveedores específicos, costos reales, 8+ papers académicos con DOIs, presupuesto por tamaño de fondo (bootstrapper $0 → top tier $5M+), alternativas gratuitas por categoría, y recomendaciones de implementación (scraping propio vs compra).
### Dimensión 8: Behavioral Finance — Motor Mecanicista del Smart Money

⚠️ **CRÍTICO**: El componente psicológico NO es un añadido cosmético — es el mecanismo causal que explica la transferencia de valor del retail al institucional. Sin esto, el informe describe flujos pero no explica el *por qué*.

**Fórmula de transferencia de valor:**
> *Ganancia Smart Money ≈ (Volumen retail) × (Frecuencia overtrading) × (Spread + Costos) + (Liquidaciones por stops predecibles) + (Distribución en tops de euforia)*

Papers fundacionales y datos duros (obligatorio incluirlos en informe):

| # | Sesgo | Paper Clave | Dato Cuantitativo | Explotación Smart Money |
|---|-------|-------------|-------------------|------------------------|
| 1 | **Sobreconfianza** | Barber & Odean (2001) *QJE* 116(1), 261-292 | Hombres tradean 67% más → -2.65% anual extra vs mujeres | Market Makers amplían spreads vs rotación retail |
| 2 | **Efecto Disposición** | Odean (1998) *JF* 53(5), 1775-1798 | Venden ganadores 1.5x más que perdedores; pierden ~4.4% anual | Distribución Wyckoff en tops; caza de stops en bottoms |
| 3 | **Aversión a Pérdida** | Kahneman & Tversky (1979) *Econometrica* 47(2), 263-291 | Ratio 2.25:1 pérdida vs ganancia | Stops retail en niveles predecibles → liquidity sweeps |
| 4 | **Exceso de Trading** | Barber & Odean (2000) *JF* 55(2), 773-806 | Retail activo: -3.8% anual neto vs mercado +17.9% | HFT front-runs órdenes retail; spread es ganancia directa |
| 5 | **Herding (Manada)** | Banerjee (1992) *QJE* 107(3), 797-817 | >$15B perdidos en meme stocks (SEC 2021) | Wyckoff Distribution: venden cuando retail compra FOMO |
| 6 | **Anclaje (Anchoring)** | Tversky & Kahneman (1974) *Science* 185 | 72% de false breakouts en round numbers revierten en 5d | False breakouts + distribution en niveles ATH |
| 7 | **Necesidad de Acción** | Barber, Lee, Liu & Odean (2014) *JFM* 18, 1-24 | 80% day traders abandonan en 2 años; solo 1% gana neto | Algoritmos detectan cuentas retail y ajustan spreads |
| 8 | **Sesgo de Confirmación** | Nickerson (1998) *Rev Gen Psych* 2(2) | Perdedores buscan confirmación 3x más que ganadores | Smart Money ignora señales opuestas, coloca órdenes contrarias |

**EVIDENCIA CONTRARIA (obligatorio incluir — sin esto el informe es incompleto):**
- **EMH (Fama 1970)**: Si el mercado es eficiente, no hay Smart Money identificable — los retornos anómalos son ruido
- **Coval, Hirshleifer & Shumway (2005)**: Ciertos retail traders SÍ predicen retornos de corto plazo (aunque costos eliminan la ventaja)
- **Pompian (2006)**: El Smart Money también tiene sesgos: herding profesional, sobreconfianza en modelos cuantitativos
- **O'Hara (2015)**: Market makers proveen liquidez valiosa — no es extracción pura de rentas
- **Limitación temporal**: Estudios Barber & Odean usan datos 1991-1996; comisiones cero y apps modernas (Robinhood, 0-comission brokers) cambian magnitudes aunque no la dirección

**Archivo de referencia**: `references/behavioral-finance-smart-money.md` — investigación completa con tabla de 8 sesgos, datos duros agregados por sesgo, papers clave, evidencia contraria, y 5 mecanismos concretos de explotación.

## Subagentes Recomendados (Parallel Research)

Para una investigación completa, lanzar 3 subagentes en paralelo con delegate_task:

```
delegate_task(tasks=[
  {goal: "SMC avanzado + arXiv + GitHub", context: "..."},
  {goal: "Crypto on-chain + stablecoins + whales", context: "..."},
  {goal: "Flujos macro + SWFs + regulación global", context: "..."}
])
```

Cada subagente debe:
- Usar toolsets=["web"] (para web_search)
- RETORNAR texto solamente (NO escribir archivos)
- Output en español

## Investigación Directa del Padre

MIENTRAS los subagentes trabajan, investigar directamente con el **orden de preferencia** (más eficiente primero):

1. `terminal(curl)` para: **raw.githubusercontent.com** (GitHub READMEs crudos — bypassa la UI de GitHub), **arXiv API** (export.arxiv.org/api/query — nunca bloquea), **CRYPTO exchange REST APIs** (Binance, Bybit, Kraken — públicos, sin clave), **CoinGecko API**, **DefiLlama**, **Solana RPC público**
2. `browser_navigate` para: páginas web que requieren renderizado JS (TradingView, plataformas de herramientas)
3. `browser_navigate` a arXiv para papers de microestructura (si la API XML no es suficiente)
4. `browser_navigate` a GitHub para herramientas open-source (sin login se ven README y estructura de archivos)
5. `browser_navigate` a sitios de plataformas (ATAS, Bookmap, Sierra Chart)

**Recomendación fuerte**: Para contenido plano (raw READMEs, arXiv XML, REST API JSON), usa `terminal(curl)` — es 5-10x más rápido que el browser, no activa bot detection, y retorna datos estructurados parseables con `python3 -c`.

APIs públicas verificadas funcionales (sin API key, Jul 2026):

| API | URL Base | Endpoint de ejemplo | Rate Limit | 
|-----|---------|---------------------|------------|
| Binance REST | api.binance.com | /api/v3/ticker/24hr?symbol=BTCUSDT | 1200/min (sin clave) |
| Bybit REST | api.bybit.com | /v5/market/tickers?category=spot&symbol=BTCUSDT | 50/min (sin clave) |
| Kraken REST | api.kraken.com | /0/public/Ticker?pair=XBTUSD | ~1/s (sin clave) |
| CoinGecko | api.coingecko.com | /api/v3/simple/price?ids=bitcoin&vs_currencies=usd | ~30/min (sin clave) |
| DefiLlama | stablecoins.llama.fi | /stablecoins?includePrices=true | ~100/min (sin clave) |
| Solana RPC | api.mainnet-beta.solana.com | POST {"jsonrpc":"2.0",...,"method":"getLatestBlockhash"} | 40/call (sin clave) |
| DeBank | api.debank.com | /chain/list | ~30/min (sin clave) |

## Estructura del Informe

Estructura estándar de 18 secciones:

1. **Resumen Ejecutivo** — 7-8 hallazgos clave destilados
2. **Definición y Origen** — historia, evolución, características
3. **Actores del Ecosistema** — SWFs ($15T), Hedge Funds ($5T), Family Offices ($3T), Pensiones ($35T), Bancos Centrales
4. **Smart Money Concepts (SMC)** — 8 principios ICT + base académica + GitHub tools
5. **Ciclo Wyckoff** — 4 fases con señales actualizadas
6. **Order Flow y Microestructura** — Matched filter, Price Discovery, herramientas
7. **Detección y Monitoreo** — 13F, COT, tracker de 5 pasos
8. **Flujos Globales 2025-2026** — IIF EM, SWFs, guerra Irán impacto
9. **Smart Money en Cripto** — Panorama mercado, stablecoins, plataformas on-chain
10. **Marco Regulatorio** — GENIUS Act, MiCA, BEPS 2.0, SEC 13F cambios
11. **Países Receptivos** — India (~50% crédito privado EM), EAU, Singapur, Brasil
12. **Herramientas y Plataformas** — ATAS, Nansen, Arkham, TapeFlow
13. **Investigación Académica** — 13+ papers arXiv analizados
14. **Behavioral Finance: El Motor Psicológico** — 8 sesgos con datos duros, papers (Barber & Odean, Kahneman & Tversky, Thaler), y mecanismos de explotación
15. **Estrategias Prácticas** — 3 niveles, screeners, señales entrada/salida
16. **Riesgos** — EM, NBFI-banca, confirmation bias SMC
17. **Tríada GEX + Options Flow + Earnings Revision** — 3 dimensiones tácticas con código Python funcional, 6 estrategias cuantitativas, y framework de backtesting con KPIs
18. **Conclusiones** — 7 conclusiones + matriz prioridades 🔴🟠🟡⚪
19. **Referencias** — papers, institucionales, herramientas, libros

## Archivos de Salida

- `INFORME_SMART_MONEY_V2.md` — Informe V2 fortalecido (formato legible con tablas, enlaces, Behavioral Finance, Alternative Data, DeFi MEV)
- `INFORME_SMART_MONEY_COMPLETO.md` — Formato legible (tablas, enlaces)
- `INFORME_SMART_MONEY_COMPLETO.txt` — Formato plano portable
- Ambos en la misma carpeta que los archivos fuente (ej: SmartMoney/)
- `references/informe-v2-fortalecido.md` — Referencia a la versión V2 y archivos relacionados

## Data Source Note: DuckDuckGO Search

Cuando busques artículos web vía DuckDuckGo (browser_navigate), el **snapshot de accesibilidad solo muestra la interfaz de navegación** (menús, botones, temas) — **NO renderiza los resultados de búsqueda reales**. El árbol de accesibilidad no contiene los enlaces ni descripciones de los resultados.

**Alternativa preferida**: Usar `terminal(curl)` para consultar sitios directamente, o navegar directamente a URLs específicas de artículos/blogs con `browser_navigate`. Para contenido académico, usar la API de arXiv vía `curl` (ver Dimensión 2 + Pitfall 4).

### Dimensión 9: DeFi MEV — El Order Flow de Blockchain

El MEV (Maximal Extractable Value) es al blockchain lo que el order flow a los mercados tradicionales: el valor de controlar el orden de las transacciones en un bloque. Originalmente definido por Daian et al. (2019) — \"Flash Boys 2.0\" (Cornell/IC3).

**Datos clave 2025-2026:**

| Tipo de MEV | Vol. Anual Est. | % | Impacto Retail |
|-------------|----------------|---|----------------|
| Arbitraje DEX | $350-500M | 40-45% | Mejora precios (beneficio indirecto) |
| Sandwich Attacks | $200-350M | 20-30% | **0.1-5% pérdida por swap** |
| Liquidaciones | $150-250M | 15-20% | Compran colateral con 5-10% descuento |
| NFT + Cross-chain | $100-200M | 10-20% | Arbitraje entre chains |
| **TOTAL** | **$800M-$1,300M/año** | 100% | |

**Sandwich Attack** (mecanismo):
1. Bot detecta swap pendiente en mempool
2. Coloca compra ANTES (front-run)
3. Swap víctima se ejecuta a peor precio
4. Bot vende DESPUÉS (back-run)

**Protección gratuita:** Flashbots Protect RPC, CoW Swap, Uniswap X, límite de slippage bajo.

**PBS (Proposer-Builder Separation):** Post-Merge, PBS separó proponer bloques (validadores) de construirlos (builders). PBS **no redujo el MEV** — lo institucionalizó. ~5-10 builders controlan >70% de la construcción de bloques.

**Conexión LegalTech:** Validadores son \"notarios digitales\" — su ordenamiento de transacciones tiene valor económico. Posible nicho para auditoría forense de MEV (detectar manipulación en DEXs, probar front-running en smart contracts).

**Herramientas gratuitas:** Etherscan (orden de tx), Flashbots Protect (RPC gratuito), Dune Analytics (dashboards MEV), EigenPhi free tier, Jito (Solana), Tenderly (simulación de tx).

### Dimensión 10: Evidencia de Backtesting — SMC Falsificado

⚠️ **ADVERTENCIA CRÍTICA**: Esta dimensión reemplaza y corrige cualquier afirmación de validación académica de SMC hecha en versiones anteriores del informe.

**El estudio más riguroso disponible** (AaroNLaU0307/quant-backtest-framework, 2025, GitHub) **FALSIFICA** el SMC como sistema:

| Métrica | Resultado SMC | Resultado TSMOM (mismo autor) |
|---------|--------------|------------------------------|
| Walk-forward OOS | **−0.339 R** (negativo, 95% CI [−0.45, −0.22]) | **Sharpe ~0.75** (positivo) |
| Grid multi-instrumento (42 configs × 5 inst.) | **0/210** sobreviven corrección BH-FDR | Confirmado |
| Random-entry null | Indistinguible de moneda | Supera aleatorio |
| Pooled correlation-aware | **−0.000 R** (p ≥ 0.50) | — |

**Tabla de verdad por concepto SMC:**

| Concepto | Lo que SMC promete | Veredicto real |
|----------|-------------------|----------------|
| **Order Blocks** | Zonas de reversión institucional | ❌ Falsificado. 0/210 configs sobreviven. Sin papers que los validen. |
| **Fair Value Gaps** | Gaps de 3 velas que el precio busca llenar | ❌ Falsificado. Sin papers. Backtests positivos muestran sobreoptimización (Sharpe IS 1.42 → OOS 0.97). |
| **Liquidity Sweeps** | Caza de stops, luego reversión | ❌ Sin evidencia. Sin backtests públicos independientes. |
| **CHoCH / BOS** | Cambios de estructura de mercado | ❌ Falsificado. Indistinguible de aleatorio. |
| **CVD / OFI** | Divergencia precio-volumen | ⚠️ Concepto respaldado académicamente (Cont, Kukanov & Stoikov 2010) pero funciona en **tick-data de order book**, NO en OHLC de 1m/5m como lo usa SMC. |
| **SMC como sistema** | Metodología completa de price action | ❌ **FALSIFICADO**. El mismo autor validó momentum multi-asset (Sharpe 0.75) después de refutar SMC. |

**Corrección de la sección 4.4 del informe V1**: Los mappings anteriores (\"Order Blocks → Kyle 1985\", \"FVG → Cont 2010\") eran INCORRECTOS. Kyle no menciona order blocks; Cont no menciona FVGs. Reescribir para decir: \"No existe validación académica de estos conceptos\".

### Dimensión 11: Gamma Exposure (GEX) — La Radiografía del Dealer Positioning

El GEX mide el valor en dólares de acciones que los market makers deben comprar/vender por cada movimiento del 1% en el subyacente para mantenerse delta-neutrales. NO predice dirección — describe el **régimen de volatilidad**.

**Fórmula Black-Scholes:** `GEX = Γ × OI × 100 × S² × 0.01`  
Calls → GEX+, Puts → GEX- (asumiendo modelo estándar de dealer short gamma).

**Dos regímenes:**
- **GEX+ (Long Gamma):** Dealers compran caídas, venden alzas → suprime volatilidad, mean reversion
- **GEX- (Short Gamma):** Dealers compran alzas, venden caídas → amplifica volatilidad, breakouts

**Niveles críticos:** Gamma Flip (cruce por cero), Call Wall (resistencia), Put Wall (soporte).

**6 estrategias cuantitativas** (condiciones en `references/gex-strategies-six.md`): Gamma Pin, Gamma Flip Breakout, TSLA Squeeze, Post-FOMC Vanna Rally, 0DTE Charm Drift, Expiry Friday Pin.

**Código Python funcional:** `scripts/gex-calculator.py` — yfinance + scipy Black-Scholes → Gamma Flip + Call/Put Walls.

### Dimensión 12: Options Flow — Huella Transaccional Institucional

Rastreo en tiempo real de opciones para detectar actividad inusual. ~45M contratos/día en EE.UU., ~90% ruido, ~1-2% señales de alta convicción.

**Clasificación de órdenes:** Sweep (urgencia máxima), Split (acumulación paciente), Block (cobertura/ambivalente).

**Framework 6 criterios para señal de alta convicción:** Premium ≥$500K + Sweep + Aggressive (ask/bid) + Opening (Vol/OI >2) + 30-90 DTE + ATM/OTM cercano.

**Límites:** Ambigüedad de motivación (cobertura vs direccional), piernas ocultas de spreads, spoofing institucional.

### Dimensión 13: Earnings Revision — Momentum Fundamental

Cambios en estimaciones de EPS de analistas sell-side. No es el resultado actual — es la **velocidad del cambio en el consenso**.

**Smart Money no espera revisiones:** usan Alternative Data para calcular ganancias antes del reporte, compran en silencio, venden cuando los analistas revisan al alza (sell the news). Las revisiones son **confirmación, no descubrimiento**.

**Uso práctico:** Screener percentil 90 revisiones al alza, combinar con valuation forward, horizonte semanas-meses.

### Dimensión 14: Tríada de Convergencia — GEX + Flow + Revisions

La convergencia de las 3 produce señales de alta convicción:

```
NIVEL 1: FUNDAMENTAL (Earnings Revision → semanas-meses) — "las ganancias mejoran"
NIVEL 2: TÁCTICA (Options Flow → minutos-horas) — "alguien grande apuesta"
NIVEL 3: ESTRUCTURAL (GEX → intradía) — "el mercado absorberá o amplificará"

SEÑAL DE ALTA CONVICCIÓN = las 3 capas alineadas
```

### Dimensión 15: Arquitectura de Backtesting para Apps

Cuando el objetivo sea construir una app de alertas (SDD+TDD), usar esta arquitectura:

**Data Schema point-in-time:** (1) Earnings Revisions históricas con companies delistadas (survivorship bias), (2) OPRA tick-level, OI diario, IV surface, (3) OHLCV + GEX histórico.

**Control de sesgos:** Survivorship bias (universo reconstructivo dinámico), Look-ahead bias (OI usa t+1), Lee-Ready algorithm para determinar agresión en GEX.

**KPIs cuantitativos:** Sharpe >1.8 | Sortino >2.5 | Max DD <12% | Win Rate >52% | Profit Factor >1.85.

**Validación robusta:** Walk-Forward Analysis (IS 2a → OOS 6m), Monte Carlo permutations, Parametric Sweep.

### Estrategia de Investigación: Framework de Señales Integradas (5 Capas)

Al sintetizar hallazgos de múltiples dimensiones, usar este framework para organizar el análisis. Adaptado de material profesional (Conceptos_v2):

```
1. MACRO: Yield curve + Credit Impulse + Leading Indicators → régimen de mercado
2. FLUJOS: Flow of Funds + 13F positioning + rotaciones sectoriales → dónde va el capital
3. MICROESTRUCTURA: Order Flow + Gamma Exposure + Volume Profile → timing de entrada/salida
4. SENTIMIENTO: VIX + Put/Call Ratio + Breadth → temperatura del mercado
5. FUNDAMENTAL: Earnings Revision + FCF Yield + Insider Activity → convicción en el activo
```

### Stack de Herramientas Gratuito Verificado

APIs funcionales probadas (sin API key, Jul 2026) para un stack de análisis completo por $0/mes:

```python
# Stack gratuito funcional
pip install yfinance smartmoneyconcepts pandas numpy
```

| API | Endpoint | Rate Limit | Uso |
|-----|----------|------------|-----|
| yfinance | yf.download(\"SPY\") | Ilimitado | OHLC histórico |
| Binance | api.binance.com/api/v3/ticker | 1200/min | Order book tick-data en vivo |
| CoinGecko | api.coingecko.com/api/v3 | 30 calls/min | Crypto precios + market cap |
| DefiLlama | stablecoins.llama.fi | ~100/min | Stablecoins total supply |
| Solana RPC | api.mainnet-beta.solana.com | 40/llamada | On-chain datos |
| Alpha Vantage | alphavantage.co | 5 calls/min | Equities + forex |
| Reddit Pushshift | api.pushshift.io/reddit | Ilimitado (histórico) | Posts/comentarios para sentiment |

#### Evaluación de APIs Financieras — Metodología y Resultados

Cuando el usuario proporcione API keys o URLs de servicios financieros, evaluarlas sistemáticamente antes de integrarlas:

**Metodología de evaluación:** (probada Jul 2026 con Massive, Unusual Whales, Capitol Trades, CryptoQuant, Apify, Market Chameleon)

1. **Probar endpoint básico primero**: `curl -s "URL_BASE/v3/status?apiKey=..."` o el endpoint de health check
2. **Endpoint de referencia**: `/reference/tickers` para datos de empresas, `/reference/dividends` para fundamentos
3. **Endpoint de opciones** (si existe): probar con SPY + fecha de expiración cercana
4. **Endpoint de earnings/fundamentals**: probar con AAPL o MSFT (alta cobertura)
5. **Endpoint streaming/MCP**: verificar si tienen MCP Server o WebSocket
6. **Documentar** qué endpoints funcionan, cuáles dan 404, y cuáles requieren JS/rendering

**Resultados de pruebas (Jul 2026) — guardar en `references/api-evaluation-results.md`:**

| API | Endpoints funcionales | Endpoints 404 | Costo | Veredicto |
|-----|---------------------|---------------|-------|-----------|
| **Unusual Whales** | 100+ documentados (GEX, Flow, Dark Pool, Congress, Crypto, Earnings, Alertas). TIENE MCP Server + skill.md para AI. | Ninguno verificado (requiere token pago) | Plan pago ver pricing | **MEJOR OPCION** — GEX profesional, Options Flow, Dark Pool, Congress trading, Crypto whales. Reemplaza 70% del código casero. |
| **Massive API** | `/v3/reference/dividends`, `/v3/reference/tickers` | `/v3/financials`, `/v3/earnings`, `/v3/option-chains`, `/v3/options`, `/v3/stocks`, `/v3/crypto` | Gratis (key funcional) | **Valor bajo** — solo reference data. No tiene options ni earnings. Complemento menor. |
| **mcp-capitol-trades** | MCP Server instalable via npm | Bloqueado por Vercel Cloudflare (429) | Gratis | **Alternativa fallback**: Apify actor `saswave/capitol-trades-scraper` ($0.50-2/mes pay-per-event, 83K runs) por si el MCP sigue bloqueado |
| **CryptoQuant** | No probado (insight dio 404) | El link expiró | $79-199/mes | Posible expansión Fase 3 |
| **Apify** | Plataforma de scraping como servicio | No aplica | Pay-per-use | Alternative data Fase 3 |
| **Market Chameleon** | No accesible via curl (requiere JS) | No probado | No determinado | Zona gris |

**Recomendación de stack financiero:**

```
FUENTES PRINCIPALES (MVP):
  Unusual Whales API — GEX, Options Flow, Dark Pool, Congress, Crypto, Earnings
  + yfinance — backup OHLC, complemento gratuito
  + Massive API — reference data (tickers, dividends)

FUENTES EXPANSION (Fase 2-3):
  MCP Capitol Trades — Congress (si resuelven Cloudflare)
  CryptoQuant — on-chain avanzado BTC/ETH
  Apify — alternative data scraping
```

**Pitfalls adicionales:**
- Capitol Trades y sitios similares pueden tener Vercel/Cloudflare Security Checkpoint — el scraper MCP fallará con 429 hasta que se resuelva
- Massive API suena a "todo-en-uno" pero solo es reference data — verificar cada endpoint individualmente
- Unusual Whales requiere token pago — NO asumir acceso gratuito. Documentar que es el mejor recurso PERO requiere inversión
- Muchas APIs financieras tienen tier gratuito limitado que oculta precios reales — la página de pricing es la única fuente confiable

## 3 Estrategias Donde el Retail Gana (evidencia empírica)

Sección obligatoria en informes para cerrar el gap QUÉ→CÓMO — no solo describir el poder del SM, sino decir cómo competir:

1. **Small-Cap Value**: Fama-French confirma alfa de 3-5% anual sobre el mercado. Hedge funds NO pueden invertir en micro-cap ilíquidas (no caben con su capital). Implementación: IWN (Russell 2000 Value ETF).
2. **Event-Driven Special Sits**: Spin-offs, mergers, bankruptcies — retail sin benchmark puede holdear 2-3 años. Fondos con restricciones de liquidez no pueden.
3. **Buy & Hold sin Fees**: ~85% de hedge funds NO baten al S&P 500 en 10 años (SPIVA). Después de fees 2/20 (~3% anual), la diferencia compuesta es masiva: 7% vs 10% anual → en 20 años: 3.87x vs 6.73x (+74% de riqueza).

## Cómo Analizar Manuales SMC/ICT (PDFs, Cursos)

Cuando el usuario proporcione PDFs o manuales de trading SMC (ej: "La Realidad del Método Smart Money Concepts", 110 páginas):

1. **Son fuentes de REGLAS, no de VERDAD** — estos manuales enseñan metodología, NO presentan evidencia. Nunca citarlos como validación de conceptos.
2. **Verificar siempre si incluyen backtesting** — si no hay datos cuantitativos (win rate, Sharpe, profit factor, número de trades), el manual no valida la estrategia. El PDF analizado (110 págs) tenía CERO datos de performance.
3. **Buscar contradicciones internas** — ej: "8/10 trades deben ser de continuación" (página 95) contradice la premisa de que SMC detecta reversiones institucionales.
4. **Identificar reglas codificables** — los manuales suelen tener reglas operacionales claras (ej: 4 reglas de OB válido) que SÍ se pueden implementar para backtesting automatizado. Pero implementar no implica que generen edge.
5. **Documentar el lenguaje pseudocientífico** — términos como "IPDA" (Interbank Price Delivery Algorithm) no existen en literatura académica. Señalarlos como invención del creador.
6. **Conexión con falsificación**: Los manuales SMC proveen el "cómo". Nuestra investigación (Dimensión 10) provee el "por qué no funciona". Cruzar ambos.

**Método de Validación en Vivo: Testear, No Confiar**

Cada vez que se obtenga código de una fuente (subagente, PDF, GitHub), **ejecutarlo y verificar resultados reales** antes de integrarlo en un informe o app. La validación en vivo durante esta investigación detectó:

1. **Bug en Gamma Flip de sm11.txt**: El código usa `Net_GEX` directo para buscar el cruce por cero, pero el GEX de SPY/AAPL está fuertemente sesgado hacia calls (todo positivo). El Net GEX nunca cruza cero. **Corrección:** Usar `GEX_Cumulative` (cumsum) en vez de Net_GEX directo, o detectar el cambio de pendiente. Ver `references/gex-backtest-kpis.md`.

2. **API deprecada en yfinance**: `ticker.expirations` ya no existe. Cambiar a `ticker.options`. Y la iteración requiere `list(expirations)[:n]` porque las tuplas no soportan slicing directo.

3. **Rendimiento real**: Procesar 3 vencimientos de opciones de SPY (~730 contratos) toma ~15s en total. Aceptable para monitoreo periódico pero no para tiempo real.

**Procedimiento de validación:**
```
1. Obtener código (subagente, PDF, GitHub)
2. Identificar dependencias y API calls
3. Ejecutar en vivo con un instrumento real
4. Verificar que los outputs tengan sentido (rangos, signos, magnitudes)
5. Documentar bugs encontrados Y cómo corregirlos
6. Solo entonces integrar en informe o app
```

### SDD+TDD: Construyendo una Aplicación de Alertas Smart Money

Cuando el objetivo final sea construir una aplicación (no solo investigar), aplicar SDD+TDD.

**Archivos de referencia en la carpeta del proyecto:**
- `D:\PyCode\hermes-skills\SmartMoney\PRE_INFORME_APP.md` (32 KB, 379 líneas) — Pre-informe compilatorio con glosario, herramientas, KPIs, arquitectura 5 capas, stack gratuito
- `D:\PyCode\hermes-skills\SmartMoney\INFORME_FINAL_APP.md` (9.6 KB, 229 líneas) — Informe final post-auditoría con auto-crítica, matriz de priorización, y 4 outputs concretos de la app
- `references/pre-report-app-framework.md` — Resumen ejecutivo de la tríada de señales y stack gratuito
- `references/tdd-selectivo-decision-framework.md` — TDD Selectivo: decision framework for SDD+TDD hybrid on data-dependent projects (en skill spec-driven-development)
- `references/analisis-pdf-smc-manual.md` — Análisis detallado del PDF SMC (110 págs)

**La aplicación produce 4 outputs concretos:**
1. **Alertas de Convergencia**: Cuando 2+ de 3 capas (GEX + Options Flow + Earnings Revision) se alinean. Objeto JSON con score de convicción (0-10) + señales convergentes + acción sugerida.
2. **Dashboard de Régimen**: Tabla en tiempo real: Instrumento, Spot, Net GEX, Call Wall, Put Wall, Régimen Gamma (Long/Short).
3. **Señales Estratégicas**: 6 estrategias cuantitativas (Gamma Pin, Flip Breakout, Gamma Squeeze, Post-FOMC Vanna, 0DTE Charm, Follow the Whale) + TSMOM, cada una con estado activa/standby/sin señal.
4. **Reportes de Backtesting**: Sharpe, Sortino, Max DD, Win Rate, Profit Factor, WFA gap, p-value Monte Carlo por estrategia validada.

**Fase SDD (Specification-Driven Development):**
1. Definir qué señales implementar basado en las 5 capas del framework y las dimensiones con respaldo académico (OFI/CVD, momentum multi-asset, price level clustering)
2. NO asumir que las reglas SMC de manuales funcionan — tratarlas como hipótesis a falsear
3. Especificar fuentes de datos: APIs funcionales verificadas (Binance, yfinance, CoinGecko)
4. Definir validación: walk-forward, multi-instrumento, corrección BH-FDR
5. Especificar formato de alertas: movimiento, dirección, consolidación/acumulación
6. **Incluir una sección de auto-auditoría en el informe final**: desafiar cada afirmación (¿de dónde viene este número? ¿quién lo validó? ¿es replicable?), documentar puntos ciegos, y reconocer limitaciones abiertamente.

**Fase TDD (Test-Driven Development):**
1. Implementar backtesting automatizado de cada señal ANTES de la lógica de producción
2. Usar datos históricos con separación IS/OOS estricta
3. Medir: Sharpe ratio, win rate, profit factor, max drawdown
4. Comparar contra random-entry baseline
5. Solo pasar a producción señales que sobreviven validación estadística

## Estrategia de Investigación: Framework de Señales Integradas (5 Capas)

Al sintetizar hallazgos de múltiples dimensiones, usar este framework para organizar el análisis (adaptado de material profesional en Conceptos/term3.txt):

``` 1. MACRO: Yield curve + Credit Impulse + Leading Indicators → régimen de mercado
2. FLUJOS: Flow of Funds + 13F positioning + rotaciones sectoriales → dónde va el capital
3. MICROESTRUCTURA: Order Flow + Gamma Exposure + Volume Profile → timing de entrada/salida
4. SENTIMIENTO: VIX + Put/Call Ratio + Breadth → temperatura del mercado
5. FUNDAMENTAL: Earnings Revision + FCF Yield + Insider Activity → convicción en el activo
```

## Conexión LegalTech: Oportunidades de la Investigación

El hallazgo de que SMC está falsificado y que las herramientas gratuitas existen abre oportunidades para construir aplicaciones LegalTech:

1. **Auditoría forense de MEV** — detectar manipulación de mercado en DEXs, probar front-running en smart contracts
2. **Validación estadística de estrategias** — ofrecer como servicio lo que los manuales SMC no hacen: backtesting riguroso con corrección BH-FDR
3. **Alertas basadas en señales validadas** — solo implementar señales con respaldo académico (OFI, momentum, price clustering, alternative data) en vez de reglas SMC no validadas

## Common Pitfalls

1. **No asumir que SMC es académicamente validado** — ICT/Michael Huddleston NO tiene respaldo académico. Los conceptos SMC son interpretaciones cualitativas de fenómenos reales de microestructura. Usar papers como `arXiv:2510.27334` para explicar el "por qué", no como validación ICT.

2. **Datos IIF cambian mensualmente** — El IIF Capital Flows Tracker se publica a fin de mes. Los datos del mes en curso NO están disponibles hasta el mes siguiente. Verificar la fecha de publicación.

3. **CoinGecko tiene rate limits** — Después de ~4 consultas API, devuelve 429. Espaciar las consultas.

4. **ssrn.com y Google Scholar bloquean** — Cloudflare/JS challenges. Usar arXiv como fallback principal (no bloquea). **Nota**: arXiv API requiere HTTPS — `curl -sL https://export.arxiv.org/api/query?search_query=...` El puerto HTTP (80) redirige 301 a HTTPS. Siempre usar `-L` (follow redirects) en curl.

5. **Reddit bloquea new.reddit.com** — Usar `old.reddit.com` con curl y User-Agent header.

6. **Regulación 13F cambia** — SEC propuso aumentar umbral de $100M a $3.5B. Verificar estado actual antes de citar umbrales.

7. **SEC.gov tiene CAPTCHA** — Usar sec.gov/cgi-bin/browse-edgar?action=getcompany para consultas directas sin CAPTCHA. Para filings específicos, usar la API EDGAR: `https://efts.sec.gov/LATEST/search-index?q=...`

8. **GitHub sin login tiene vistas limitadas** — Se ve README y estructura de archivos, pero no Issues ni Discussions completos.

9. **Los subagentes pueden mentir sobre archivos creados** — Siempre verificar con `ls -la` después de que reporten haber escrito algo.

10. **Datos de stablecoins cambian diariamente** — Los $310.3B (Jul 2026) son un snapshot. No tratarlos como fijos.

11. **Cerrar el QUÉ→CÓMO gap** — Es fácil describir qué es Smart Money. Más difícil es decir cómo actuar. El informe debe incluir workflows ejecutables (código, setup de herramientas, criterios de entrada/salida), no solo descripciones.

12. **No forzar conexiones academia-SMC** — Mapear "Order Blocks → Kyle (1985)" es una conexión débil. Kyle modela informed trading general, no bloques de órdenes específicos. Cuando un concepto SMC no tiene equivalente académico directo, decirlo explícitamente en vez de forzar la conexión.

13. **Incluir alternativas gratuitas** — Las herramientas recomendadas (ATAS $70/mes, Sierra Chart $125/mes, Nansen $$$) son caras para retail. Mencionar Dune Analytics, TensorCharts, CoinGecko API, TradingView free, NinjaTrader simulación como opciones accesibles.

14. **No ignorar DeFi microstructure** — MEV (Maximal Extractable Value), flash loans, validator dynamics y liquidity pool dynamics son el "order flow" de blockchain. Incluirlos en la dimensión crypto.

15. **Reconocer el debate EMH** — La tesis del "Smart Money como entidad identificable" es debatible. Fama y la Efficient Market Hypothesis argumentan que no hay Smart Money, que los retornos anómalos son suerte. El informe debe reconocer esta controversia, no elegir un lado silenciosamente.

16. **Backtesting ausente** — Ninguna estrategia SMC o de tracking 13F debería presentarse sin datos de backtesting. Si no hay datos públicos, decirlo explícitamente: "No hay validación estadística pública de esta estrategia".

17. **DuckDuckGo browser snapshots no muestran resultados** — El snapshot de accesibilidad de DuckDuckGo solo contiene la interfaz (menús, botones, temas de privacidad). Los resultados de búsqueda reales NO aparecen en el árbol de accesibilidad. No uses `browser_navigate` a DuckDuckGo para buscar información — usa `terminal(curl)` a sitios directamente, o navega a URLs específicas.

19. **No todos los arXiv IDs listados en skills son válidos** — Verificar cada arXiv ID con la API: `curl -sL 'https://export.arxiv.org/api/query?id_list=XXXX.YYYYY'`. IDs que retornan "no element found" fueron retractados, son incorrectos o no existen. El skill `smart-money-research` tenía `arXiv:2605.11423` que resultó ser inválido (Jul 2026). Siempre verificar antes de citar.

20. **yfinance API cambia entre versiones** — El codigo GEX (sm11.txt) usaba `ticker.expirations` que fue deprecado. Usar `ticker.options`. La tupla no soporta slicing directo: convertir a `list(ticker.options)[:n]`.

21. **Gamma Flip con GEX sesgado a calls** — Cuando Net GEX es todo positivo, la deteccion por cruce de cero falla. Usar GEX acumulado (cumsum) como alternativa. Ver `references/gex-backtest-kpis.md`.

22. **Validar en vivo antes de integrar** — Todo código de subagentes, PDFs o GitHub debe ejecutarse contra datos reales antes de incorporarlo. El GEX Calculator de sm11.txt se probó con SPY ($1.59B Net GEX) y AAPL ($563M) — ambos dieron resultados consistentes, pero revelaron un bug en la detección de Gamma Flip cuando Net GEX es todo positivo (calls dominan). **Corrección:** usar GEX_Cumulative (cumsum) en vez de Net_GEX directo.

23. **Gamma Flip con GEX sesgado a calls** — Cuando Net GEX es todo positivo (situación común en SPY, índices), el método de interpolación por cruce de cero falla porque nunca hay cambio de signo. Solución: (a) usar GEX acumulado (cumsum) para detectar cambio de pendiente, o (b) marcar el flip en el strike donde el cumsum cruza un umbral personalizado. Documentar el método usado para que el usuario pueda juzgar su validez.

24. **Auto-auditoría de afirmaciones** — Al producir informes finales, incluir una sección explícita de auto-auditoría donde CADA afirmación clave sea desafiada: "¿De dónde viene este número? ¿Quién lo validó? ¿Es replicable? ¿Qué evidencia contraria existe?". Esto evita confirmación bias y da credibilidad al informe. El INFORME_FINAL_APP.md incluye un modelo de esta auditoría con 5 afirmaciones desafiadas.

## Verification Checklist

- [ ] 6 archivos locales leídos y catalogados (si existen)
- [ ] 13+ papers de arXiv identificados y analizados
- [ ] 3+ GitHub repos evaluados con stars
- [ ] Datos IIF más recientes incluidos
- [ ] Panorama crypto en vivo (CoinGecko + DefiLlama)
- [ ] Regulación actualizada (GENIUS Act, MiCA, BEPS, SEC 13F)
- [ ] Herramientas de order flow comparadas con precios
- [ ] 3 subagentes lanzados en paralelo (si aplica)
- [ ] Informe guardado en .md + .txt
- [ ] Referencias numeradas correctamente
- [ ] **Dimensión 7 (Alternative Data)** cubierta
- [ ] **Dimensión 8 (Behavioral Finance)** cubierta — 8 sesgos con datos duros, papers (Barber & Odean, Kahneman & Tversky, Thaler), mecanismos de explotación, Y evidencia contraria
- [ ] **Dimensión 14 (Tríada GEX+Flow+Revisions)** cubierta — convergencia de las 3 señales como alerta de alta convicción
- [ ] **Dimensión 15 (Backtesting Architecture)** incluida — KPIs quant (Sharpe >1.8, Sortino >2.5, Max DD <12%), Walk-Forward, Monte Carlo
- [ ] **GEX Python code** en `scripts/gex-calculator.py` — funcional, usar como base para motor de app
- [ ] **6 estrategias GEX** en `references/gex-strategies-six.md` — condiciones de entrada explicitas
- [ ] **Seccion de Zonas Grises / Controversias** incluida (EMH debate, detectabilidad del order flow, contraevidencia a Behavioral Finance)
- [ ] **Alternativas gratuitas** a herramientas caras mencionadas (ver `references/free-tools-apis.md`)
- [ ] **Gap QUE→COMO** revisado: el informe describe COMO actuar, no solo QUE es
- [ ] **Backtesting**: si hay estrategias, tienen datos de backtesting o se declara su ausencia
- [ ] **Validacion en vivo**: el codigo se ejecuto contra datos reales antes de integrarse
- [ ] **Gamma Flip detection**: verificar que funciona con GEX acumulado (cumsum), no solo Net_GEX directo
- [ ] **API changes**: verificar que las APIs usadas (yfinance, etc.) no hayan deprecado endpoints
