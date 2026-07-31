# KPIs y Arquitectura de Backtesting para App Smart Money

## KPIs Cuantitativos (de sm9.txt — validado contra Conceptos_v2)

| Categoría | Métrica | Objetivo | Método de Validación |
|-----------|---------|----------|---------------------|
| Rendimiento | Sharpe Ratio (anualizado) | > 1.8 | Walk-Forward Analysis |
| Rendimiento | Sortino Ratio | > 2.5 | Solo penaliza downside vol |
| Riesgo | Maximum Drawdown | < 12% | Pico a valle máximo |
| Riesgo | Calmar Ratio | > 2.0 | CAGR / Max DD |
| Ejecución | Win Rate | > 52% (con RR ≥ 1:2.5) | % de trades ganadores |
| Ejecución | Profit Factor | > 1.85 | Bruto ganado / Bruto perdido |
| Robustez | Expectancy/trade | > +0.45 × ATR(14) | Valor esperado por trade |
| Robustez | p-value (Monte Carlo) | < 0.01 | Permutación de retornos |
| Sesgos | Walk-forward OOS gap | < 0.2 Sharpe | IS vs OOS |
| Sesgos | Multi-instrumento | > 60% positivos | % de activos rentables |

## Control de Sesgos (punto crítico)

| Sesgo | Problema | Solución |
|-------|----------|----------|
| **Survivorship Bias** | Probar solo con empresas actuales sobreestima Sharpe | Universo dinámico reconstructivo: tickers que existían en cada fecha t |
| **Look-Ahead Bias** | Usar OI del día t para trades del día t | OI se publica al cierre — usar t+1 para decisiones; revisions con lag de 1h |
| **GEX Inference Bias** | Asumir que calls compradas = dealers short gamma | Algoritmo Lee-Ready sobre el tick de la opción para determinar agresión real |
| **Slippage** | Ejecución perfecta infla resultados | Market orders: slippage = 25% del Bid-Ask spread. Options: 50% del spread |

## Arquitectura de Datos (Point-in-Time Schema)

```
┌─────────────────────────────────────────────────────┐
│  1. FUNDAMENTALES (Point-in-Time)                   │
│     - EPS Revisions históricas (IBES/Zacks)          │
│     - Companies delistadas incluidas                 │
│     - Event dates (earnings, FOMC, expirations)      │
├─────────────────────────────────────────────────────┤
│  2. OPCIONES / OPRA (Tick-Level)                     │
│     - Time & Sales, Open Interest, Implied Vol       │
│     - Condition codes para ISO/Block identification  │
├─────────────────────────────────────────────────────┤
│  3. SPOT / GEX                                      │
│     - OHLCV ajustado por splits/dividendos           │
│     - Gamma Exposure histórico (recalculable)        │
│     - IV Surface histórica                           │
└─────────────────────────────────────────────────────┘
```

## Validación Robusta

1. **Walk-Forward Analysis**: Entrenar IS 2 años → Probar OOS 6 meses → Desplazar → Repetir 10 años
2. **Monte Carlo Permutations**: Aleatorizar secuencia de retornos de trades para verificar que la curva de equity no depende del orden temporal
3. **Parametric Sweep**: Variar umbrales clave y verificar rentabilidad en el nodo central del mapa de calor (no en un punto aislado)

## Nota: Gamma Flip Detection Bug (Corregido)

El código original (sm11.txt) usa `Net_GEX` directo para detectar el Gamma Flip. Esto **falla** cuando la distribución de GEX está fuertemente sesgada hacia calls (todo positivo) — el Net GEX nunca cruza cero.

**Corrección:** Usar `GEX_Cumulative` (cumsum) o detectar el punto donde cambia la pendiente. Alternativamente, calcular el Gamma Flip como el strike donde el GEX marginal cambia de signo (no el acumulado).

```python
# CORRECCIÓN: Usar cumsum en vez de Net_GEX directo
df_gex["GEX_Cumulative"] = df_gex["Net_GEX"].cumsum()
# Buscar cruce por cero en el acumulado
for i in range(1, len(df_gex)):
    if df_gex.loc[i-1, "GEX_Cumulative"] < 0 and df_gex.loc[i, "GEX_Cumulative"] >= 0:
        # Interpolar
        ...
```
