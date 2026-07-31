# Pre-Informe para App SDD+TDD de Alertas Smart Money

## Archivos principales

- `D:\PyCode\hermes-skills\SmartMoney\PRE_INFORME_APP.md` (32 KB, 379 lineas) — Compilacion de toda la investigacion
- `D:\PyCode\hermes-skills\SmartMoney\INFORME_FINAL_APP.md` (9.6 KB, 229 lineas) — Informe final post-auditoria con seccion "Que produce la app?" y auto-critica
- `D:\PyCode\hermes-skills\SmartMoney\INVENTARIO.md` — Inventario completo de ~513 KB de material generado

## Que produce la aplicacion (4 outputs)

1. **Alertas de Convergencia**: Score 0-10 + senales + accion sugerida
2. **Dashboard de Regimen**: Tabla por ticker (Spot, GEX, Call/Put Walls, Regimen)
3. **Senales Estrategicas**: 7 estrategias con estado activa/standby
4. **Reportes de Backtesting**: Sharpe, Sortino, Max DD, WFA gap, p-value

## Triada de Senales

```
CAPA 1: MICROESTRUCTURA (intradia) — GEX + CVD + Price Clustering
CAPA 2: FLUJO TACTICO (horas-dias) — Options Flow + Gamma Squeeze
CAPA 3: FUNDAMENTAL (semanas-meses) — Earnings Revision + Alt Data
```

## Lo que se descarta
- SMC/ICT (Order Blocks, FVGs, BOS/CHoCH) — FALSIFICADO (0/210 configs)

## Validacion en vivo: lecciones
- GEX Calculator probado SPY ($1.59B Net GEX) y AAPL ($563M)
- Bug Gamma Flip: usar cumsum, no Net_GEX directo
- API change: `ticker.expirations` ya no existe. Usar `ticker.options`
- ~15s/ticker procesando 3 vencimientos

## Stack gratuito verificado
yfinance + Binance WS + CoinGecko + DefiLlama + Koyfin + pushshift = $0/mes

## Priorizacion MVP
FASE 1 (~5h): GEX Engine + TSMOM
FASE 2 (~10h): + Options Flow + Gamma Pin + Earnings Revision
FASE 3 (~10h): + Squeeze + Alt Data
