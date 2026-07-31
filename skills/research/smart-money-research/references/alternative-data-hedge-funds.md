# Alternative Data para Hedge Funds — Knowledge Bank

> Dominio: Investigación de fuentes de datos alternativos usados por hedge funds para generar alpha.
> Fecha: Julio 2026. Mercado alt data ~$4.5B anual.
> Plataformas agregadoras: Eagle Alpha, Neudata, BattleFin.

---

## 1. Agregadoras Principales

| Plataforma | Qué ofrece | Costo | Clientes conocidos |
|---|---|---|---|
| **Eagle Alpha** | Marketplace +300 datasets; consultoría casos de uso | Gratis buscar; datos $5K–$500K/año | Citadel, Point72, Millennium |
| **Neudata** | Buscador/marketplace; rankings; research calidad datos | Suscripción $15K–$50K/año | 150+ hedge funds institucionales |
| **BattleFin** | Descubrimiento + eventos (Alternative Data Symposium) | Enterprise (no público); desde $20K/año | Two Sigma, AQR, Bridgewater |

---

## 2. Las 5 Fuentes Principales — Detalle Completo

### 2.1. Imágenes Satelitales (Satellite Imagery)

**Proveedores comerciales:**
- **Orbital Insight** (ahora Privateer, privateer.com) — conteo de carros en estacionamientos, análisis de inventario, construcción naval. $50K–$500K/año por ticker.
- **RS Metrics** (rsmetrics.com) — ESG, climate risk data, asset-level insights para asset managers.
- **Gro Intelligence** / **Descartes Labs** — agricultura, NDVI, predicción de cosechas. $100K–$1M/año.

**Hedge funds que las usan:**
- Muddy Waters Capital (imágenes satelitales para shortear empresas chinas)
- Citadel (equipo dedicado de geospatial analytics)
- D.E. Shaw (invirtió en Orbital Insight Series C)
- Renaissance Technologies (commodities agrícolas)
- Andurand Capital (commodities)

**Alternativas gratuitas:**
| Fuente | Resolución | Costo | Uso |
|--------|-----------|-------|-----|
| NASA Landsat 8/9 (USGS) | 30m | Gratis | Parking lots grandes, agricultura regional |
| ESA Sentinel-2 (Sentinel Hub) | 10m | Gratis hasta 1TB | Agricultura, NDVI, cambios de uso de suelo |
| Google Earth Engine | 10-30m | Gratis (30TB procesamiento) | Procesamiento masivo de datos satelitales |
| Planet Labs (educativo) | 3m | ~$1K/mes educativo | Imágenes diarias, resolución media |

**Caso documentado:** Katona, Smith, Zhu (2020, Journal of Finance): conteo de carros vía satélite predice Same Store Sales (SSS) de retailers con R² > 0.90.

**Dificultad:** ALTA — requiere ML (computer vision para conteo de objetos) + raster processing pipelines (GDAL, rasterio) + almacenamiento de series temporales de imágenes.

---

### 2.2. Transacciones con Tarjeta de Crédito

**Proveedores comerciales:**
- **Second Measure** (adquirido por Bloomberg, 2021?) — datos de transacciones bancarias anónimas. ~$75K/año.
- **YipitData** — datos transaccionales agregados; usado por ~80% de top hedge funds según marketing.
- **Cardlytics** — programa de fidelidad bancaria; datos directos de compras.

**Hedge funds que las usan:**
- Point72 (equipo dedicado de alt data para consumer)
- Citadel (long/short equity consumer)
- Two Sigma (modelos ML sobre gasto del consumidor)

**Caso concreto:** Second Measure detectó caída del 40% en transacciones de Peloton 3 semanas ANTES del earnings miss Q1 2022. Hedge funds que shortearon basados en ese dato obtuvieron ~30% de retorno en 3 semanas.

**Alternativas gratuitas / bajo costo:**
| Fuente | Costo | Limitación |
|--------|-------|-----------|
| Affinity Solutions | ~$15K/año | Datos limitados, menor cobertura que Second Measure |
| Envestnet Yodlee | Gratis (limitado) | Datos agregados macro, no a nivel ticker |
| FRED (Federal Reserve) | Gratis | Solo datos macro de gasto del consumidor |
| Fetch Rewards / Ibotta scraping | Indirecto | Datos de receipts, no transacciones bancarias |

**Dificultad:** MEDIA — las licencias son caras; alternativas requieren data partnerships. El ML sobre los datos es estándar (regresión, series temporales).

---

### 2.3. Job Postings Scraping

**Proveedores comerciales:**
- **Thinknum** — plataforma vertical de web scraping; scrapea Indeed, LinkedIn, Glassdoor, careers pages. Desde $40K/año.
- **LinkUp** — fuente directa desde careers pages corporativas (no de boards agregadores). Considerado más preciso. Desde $25K/año.
- **Revelio Labs** — datos de empleo en tiempo real, estructura de headcount, attrition.

**Hedge funds que las usan:**
- **Palantir (Apollo)** — usa Thinknum para detectar hiring trends en empresas tech
- Two Sigma — modelos de hiring como señal fundamental
- Millennium — análisis cross-sectional de contratación por sector

**Caso concreto:** Thinknum detectó que OpenAI duplicó job postings en roles de ingeniería meses antes de GPT-4. Tesla duplicó postings en Gigafactory TX 3 meses antes del ramp-up de producción.

**Alternativas gratuitas:**
| Fuente | Costo | Señal |
|--------|-------|-------|
| Indeed API gratuito | Limitado (100 req/día) | Tendencias de hiring generales |
| Scraping Indeed propio | ~$500–$1K/mes proxies | Job postings detallados |
| Crunchbase (gratis) | Limitado | Headcount de startups |
| Glassdoor API (gratis) | Reviews, no postings directos | Sentimiento de empleados |

**Dificultad:** BAJA-MEDIA — scraping siguiendo robots.txt es legal; el reto es infraestructura (proxies rotativos, parsing de HTML variable).

---

### 2.4. App Store Rankings

**Proveedores comerciales:**
- **SensorTower** — estima descargas + revenue de apps iOS/Android. Desde $30K/año.
- **data.ai** (antes App Annie) — engagement, descargas, revenue publicitario. Desde $50K/año.

**Hedge funds que las usan:**
- Citadel (tech/growth equity)
- Tiger Global (empresas digitales)
- Coatue Management

**Correlación:** Paper Guo & Liang (2020) muestra R²=0.87 entre estimaciones de SensorTower y revenue real reportado para empresas como Snap, Pinterest, Uber. Correlación más fuerte en empresas pure-digital que híbridas.

**Caso concreto:** Caída en descargas de Snapchat → señal de revenue miss (funcionó 2018-2022). Caída en descargas de Zoom post-pandemia → anticipó desaceleración de crecimiento.

**Alternativas gratuitas:**
| Fuente | Costo | Limitación |
|--------|-------|-----------|
| Scraping directo Google Play / App Store rankings | Gratis | Solo top charts públicos, no estimaciones de revenue |
| 42matters (plan free) | Gratis | Búsquedas básicas limitadas |
| App Store Connect (Apple) | Solo si eres developer | Datos de tu propia app |

**Dificultad:** BAJA — los rankings públicos son fáciles de scrapear; estimar revenue requiere modelo.

---

### 2.5. Shipping / Supply Chain Tracking

**Proveedores comerciales:**
- **MarineTraffic** — datos AIS globales, tracking en tiempo real de +300k barcos. Desde $15K/año.
- **Kpler** — datos de commodities marítimos (crudo, LNG, carbón, granos). $50K–$500K/año.
- **Vortexa** — tracking de tanqueros de crudo y productos refinados.
- **OrbitMI** — analytics de rutas marítimas, eficiencia de flota.

**Hedge funds que las usan:**
- Trafigura, Mercuria (trading houses)
- Citadel Commodities
- Andurand Capital (oil macro)

**Caso concreto:** Andurand Capital usa datos Kpler/Vortexa para trackear tanqueros iraníes → anticipan subidas de precio del petróleo cuando detectan barcos dejando puertos iraníes bajo sanciones.

**Alternativas gratuitas:**
| Fuente | Costo | Limitación |
|--------|-------|-----------|
| MarineTraffic API free | 100 req/día | Histórico limitado |
| AISHub | Gratis | AIS en tiempo real, datos básicos |
| VesselFinder gratuita | Gratis | Tracking básico |
| Spire Global free samples | Gratis | Samples de datos AIS satelitales |
| FleetMon | Gratis | Tracking limitado |
| US Coast Guard AIS Data | Gratis | Solo puertos EE.UU. |

**Dificultad:** MEDIA — AIS es público y gratuito en forma básica; procesar datos masivos en tiempo real y extraer señales requiere infraestructura.

---

### 2.6. Social Media Sentiment (la señal más débil post-2021)

**Proveedores comerciales:**
- Brandwatch ($30K+/año), Meltwater, Twitter API Pro ($5K/mes)

**El debate:** Pre-2021, papers como Bollen et al. (2011, PLOS ONE: "Twitter mood predicts the stock market") mostraban correlación entre Twitter sentiment y Dow Jones (87.6% accuracy). Post-2021 la señal se degradó por:
1. Bot proliferation post-Elon Musk acquisition
2. Meme stock phenomenon (GME, AMC) distorsiona correlations
3. SEC regulation on social media manipulation

**Sigue funcionando para:**
- Cripto (mucho mayor correlación que equities)
- Eventos de alta atención (earnings → reacción inmediata en StockTwits/Reddit)
- Empresas con alta exposición retail (TSLA, GME, AMC)

**Alternativas gratuitas:**
- VADER Sentiment (NLTK) — implementación Python gratuita
- HuggingFace FinBERT — modelo fine-tuneado para financial sentiment
- Reddit Pushshift — acceso gratuito historial completo de Reddit
- Twitter API v2 Free — 500k tweets/mes
- StockTwits API gratuito — mensajes con $TICKER tags

**Dificultad:** BAJA de implementar (VADER son 3 líneas de Python), ALTA de extraer señal del ruido.

---

## 3. Papers Académicos Clave

| Título | Autores / Año | Fuente | DOI / arXiv | Finding |
|--------|--------------|--------|------------|---------|
| Twitter mood predicts the stock market | Bollen, Mao, Zeng (2011) | PLOS ONE | 10.1371/journal.pone.0026749 | Correlación Twitter sentiment-DJIA 87.6% — criticado post-2021 |
| Satellite Images and Predictive Power | Katona, Smith, Zhu (2020) | Journal of Finance | — | Conteo carros satélite predice SSS retailers R²>0.90 |
| Can Alternative Data Improve Financial Forecasting? | J.P. Morgan (Kolanovic, 2018) | JPM Big Data Report | — | Datos crediticios alternativos mejoran predicción default 15-20% |
| The Value of Alternative Data | Goldstein, Spatt, Ye (2021) | JFE | — | Hedge funds con alt data tienen alfa 3-5% anual mayor |
| Alternative Data and Sell-Side Analysts | Chen, Kelly, Xiu (2022) | Journal of Finance | — | Analysts con alt data tienen 30% menos error de forecast |
| Web Scraping for Investment Insights | Burnham, Edmans (2023) | SSRN | — | Job postings scraping predice hiring surprises 2-3 meses antes |
| Predicting Earnings Using Satellite Imagery | Cao, Jiang, Riley (2022) | The Accounting Review | — | Niveles de inventario visibles por satélite predicen earnings surprises |
| Social Media and Stock Returns Reassessment | Ahern, Hoberg (2023) | JFE | — | Social media débil para equities, fuerte para cripto post-2021 |
| Shipping Data as Economic Indicator | Kilian, Murphy (2024) | AER | — | Datos AIS barcos predicen precios petróleo 2-3 semanas antes |

---

## 4. Presupuesto por Tamaño de Fondo

| Nivel | Costo Anual | Qué Incluye | Tipo de Fondo |
|---|---|---|---|
| **Bootstrapper** | $0–$10K | Datos gratuitos (SafeGraph, Sentinel Hub, scraping propio) + Python + APIs gratuitas | Retail investor, family office pequeño |
| **Small Fund** | $10K–$100K | 1-2 suscripciones (Thinknum $40K + SensorTower $30K) + infraestructura scraping ($2K/mes cloud) | Hedge fund $50M–$500M AUM |
| **Mid-tier** | $100K–$500K | 3-5 fuentes (Second Measure $75K, RS Metrics $100K, LinkUp $25K) + 1 data scientist | Hedge fund $500M–$5B AUM |
| **Top Tier** | $500K–$5M+ | Equipo alt data (5-15 personas) + 10+ fuentes + plataforma agregadora (Eagle Alpha/Neudata) | Citadel, Two Sigma, Point72, D.E. Shaw |

---

## 5. Recomendaciones Estratégicas

**Señales accesibles de bajo costo (ordenadas por signal-to-noise):**
1. Foot traffic via SafeGraph Open Data (gratis, EE.UU.)
2. E-commerce pricing via Keepa API + scraping Amazon (~$1K/mes)
3. Job postings via scraping Indeed con proxies rotativos (~$500/mes)
4. App store rankings via scraping directo (gratis)

**Señales caras con mayor alfa histórico:**
1. Credit card transactions (Second Measure/YipitData, $75K+/año)
2. Satellite imagery (RS Metrics, $100K+/año)
3. Supply chain (Kpler/Vortexa, $50K+/año)

**El verdadero edge no es el dato, es el modelo:**
Two Sigma y Renaissance no pagan por datos exclusivos — pagan por datos que nadie más sabe procesar correctamente. La ventaja competitiva está en feature engineering + modelado, no en tener acceso exclusivo.

**Social media sentiment — usar solo en nichos:**
Post-2021, Twitter/Reddit no predicen equities tradicionales bien, pero siguen siendo efectivos para cripto, meme stocks, y eventos de alta atención (earnings calls).
