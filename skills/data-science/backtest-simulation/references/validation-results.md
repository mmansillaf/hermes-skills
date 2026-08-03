# Protocolo "Una Variable a la Vez" — Aplicado a Backtesting

> **Fuente:** Lewis Jackson, Self-Improving AI Trading Agent (video 2026)
> **Validado:** Junio 2026 — backtest de momentum RSI+EMA con 20 configuraciones

---

## Resultados de la Validación

Se probó la estrategia Momentum RSI+EMA contra datos sintéticos multi-régimen
(2000 velas por régimen, 4 regímenes = 8000 velas total).

### Variables evaluadas

| # | Variable | Valores probados | Ganador | Δ Sharpe vs default |
|---|----------|-----------------|---------|-------------------|
| 1 | EMA rápida | 5, 7, 9, **12, 15** | **15** | +42% |
| 2 | EMA lenta | 14, **21**, 30, 50, 100 | **21 o 30** | −4% (depende régimen) |
| 3 | RSI periodo | 7, 10, **14**, 20, 25 | **14** o **20** | +41% |
| 4 | RSI umbral compra | 40, 45, **50**, 55, 60 | **50** | <5% (mínimo impacto) |

### Lecciones Aprendidas

1. **No hay óptimo universal** — EMA 15/21 es mejor en sideways (+82% Sharpe) y bullish (+12%), pero EMA 9/21 es mejor en bearish (−14% Sharpe). La optimización debe considerar el régimen.

2. **El orden de optimización importa** — Optimizar EMA primero (mayor impacto) produce resultados distintos que optimizar RSI primero. Priorizar: (a) variables con mayor impacto teórico, (b) variables con rango más amplio.

3. **Variables con impacto mínimo** — RSI umbral de compra (40-60) no cambia resultados porque el filtro real es el cruce de EMA, no el RSI. Identificar y saltar estas variables ahorra tiempo.

4. **Validar en todos los regímenes** — Una configuración que gana en un régimen puede perder en otro. Siempre probar en bullish, bearish, sideways y mixed.

### Métricas por Configuración

| Config | Bullish | Bearish | Sideways | Mixed | Global |
|--------|---------|---------|----------|-------|--------|
| Default (9/21/14) | Ret −13%, DD 15% | Ret +156%, DD 12% | Ret −18%, DD 19% | Ret −5%, DD 14% | Sharpe −0.43 |
| Optimizada (15/21/14) | Ret −8%, DD 9% | Ret +108%, DD 13% | Ret −4%, DD 11% | Ret −5%, DD 13% | Sharpe −0.55 |
