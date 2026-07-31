# Auditoría julio 2026 — Hallazgos de 5 Subagentes para Smart Money V2

## Contexto
El 23 de julio de 2026 se lanzaron 5 subagentes de investigación paralelos para fortalecer el informe Smart Money V1 (993 líneas, 51 KB). Se identificaron 5 brechas críticas, 5 debilidades significativas y 4 perspectivas no cubiertas.

## Subagente 1: Behavioral Finance
- **Documentó 8 sesgos** con papers Barber & Odean (2000, 2001, 2014), Kahneman & Tversky (1979), Shefrin & Statman (1985), Tversky & Kahneman (1974)
- **Datos duros:** 99% de day traders pierden dinero; transferencia retail→SM de $50-100B/año solo en EEUU; -3.8% anual de underperformance del retail activo
- **Fórmula de transferencia:** Ganancia SM ≈ (Volumen retail) × (Overtrading) × (Spread + Costos) + (Liquidaciones) + (Distribución en tops)
- **Evidencia contraria:** EMH (Fama 1970), Coval/Hirshleifer/Shumway (2005), O'Hara (2015), Pompian (2006)

## Subagente 2: Alternative Data
- **6+ fuentes** documentadas con costos comerciales y alternativas gratuitas
- Casos concretos: Peloton caída CC data, Tesla job postings, Andurand ship tracking
- Hedge funds que gastan $5M-$50M+ anuales (60%+ de fondos)
- Papers: Goldstein/Spatt/Ye (2021) — alfa 3-5% anual; Katona/Smith/Zhu (2020) — R²>0.90 satellite

## Subagente 3: DeFi MEV
- $800M-$1,300M/año en MEV extraído (2025-2026)
- Sandwich attacks: 0.1-5% pérdida retail por swap
- PBS institucionalizó (no eliminó) el MEV
- Herramientas gratuitas: Flashbots Protect, Dune, EigenPhi, Etherscan

## Subagente 4: Free Tools + Retail Advantages
- Stack gratuito funcional: yfinance + smartmoneyconcepts + Binance WS
- 3 estrategias retail-advantage: small-cap value (Fama-French), event-driven special sits, buy & hold sin fees (SPIVA)

## Subagente 5: SMC Backtesting
- **HALLAZGO CRÍTICO:** SMC FALSIFICADO. Estudio AaroNLaU0307: 0/210 configs sobreviven corrección BH-FDR, walk-forward negativo (-0.339 R)
- Mismos mappings academia-SMC del V1 eran INCORRECTOS (Kyle 1985 ≠ Order Blocks, Cont 2010 ≠ FVGs)
- Único concepto respaldado: OFI/CVD (en tick-data, no OHLC)
- El mismo autor confirmó edge en momentum multi-asset (Sharpe ~0.75)

## Material de Conceptos analizado
- 7 archivos .txt (glosarios profesionales de trading): aportan framework de 5 capas (macro→flujos→microestructura→sentimiento→fundamental)
- 1 PDF de 110 páginas (manual SMC de @chart.wzrd): reglas codificables pero CERO backtesting; contradicción interna 8/10 continuation trades
- El framework de 5 capas se incorporó al skill como metodología de síntesis
