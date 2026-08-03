---
name: backtest-simulation
description: >-
  Multi-regime backtest simulation with "one variable at a time" parameter
  optimization. Covers synthetic data generation (bullish/bearish/sideways/mixed),
  metrics framework (Sharpe, DD, win rate, profit factor), and comparative
  analysis between default and optimized configurations.
version: 1.0.0
author: Hermes Agent
license: MIT
tags:
  - backtesting
  - simulation
  - optimization
  - trading
  - parameter-tuning
related_skills:
  - web-deep-research
  - time-series-forecasting
  - statistical-formula-engine
---

# Backtest Simulation — Multi-Regime + One Variable at a Time

## What it solves

Systematically test a trading strategy (or any parameterized decision system)
across multiple market regimes, identify which parameter values actually improve
results, and prove that the optimization works — not just by chance.

## Core methodology

### 1. Multi-Regime Data Generation

Generate synthetic OHLCV (or any time-series) data for 4 regimes:

| Regime | Trend | Volatility | Best for testing |
|--------|-------|------------|------------------|
| **bullish** | +20-30% over N bars | Normal + corrections | Strategy in uptrends |
| **bearish** | -20-25% over N bars | Normal + bounces | Strategy in downtrends |
| **sideways** | ~0% | Moderate | Strategy whipsaw resistance |
| **mixed** | Alternates (bull→bear→side→bull) | Variable | Realistic multi-regime |

Default: 2000 bars per regime, 1h timeframe (~83 days).

### 2. Metrics Framework

Every simulation MUST report:

| Metric | Formula | Target (trading) | What it tells you |
|--------|---------|------------------|-------------------|
| **Sharpe Ratio** | `mean(returns) / std(returns) * sqrt(periods_per_year)` | > 1.0 | Risk-adjusted return |
| **Max Drawdown** | `min(equity - running_max) / running_max` | < 15% | Worst peak-to-trough loss |
| **Win Rate** | `wins / total_trades * 100` | > 40% | Percentage of profitable trades |
| **Profit Factor** | `sum(gains) / abs(sum(losses))` | > 1.5 | Ratio of gross wins to losses |
| **Calmar Ratio** | `total_return / max_drawdown` | > 1.0 | Return per unit of drawdown risk |
| **Total Return** | `(final_capital - initial) / initial * 100` | Positive | Absolute performance |

### 3. "One Variable at a Time" Optimization

Protocol (derived from Lewis Jackson, 2026):

1. Define base (default) configuration
2. For each variable:
   - Vary ONLY that variable across 4-6 values
   - Keep ALL other variables at base values
   - Run full simulation for each value
   - Record: Sharpe, DD, Win Rate, Profit Factor
3. Select best value for each variable
4. Compare optimized config vs default on ALL regimes

**Order of variables matters** — optimize highest-impact variables first.
In trading: EMA periods > RSI period > RSI threshold.

**Pitfall — no universal optimum:** The best config for bullish may fail in
sideways. Always validate optimized config across ALL regimes. If no single
config wins everywhere, the system needs regime detection (not parameter tuning).

### 4. Comparative Analysis

After optimization, produce:

1. **By-regime table** — how default and optimized perform in each regime
2. **One-variable impact table** — which variables matter (big Δ Sharpe) vs which don't
3. **Winner selection** — best config per regime, or robust config across regimes

### 5. Known Results from Validation

See `references/validation-results.md` for a complete worked example (momentum
RSI+EMA, 4 variables × 5 values = 20 configurations, validated across 4 regimes).

Key findings:
- One-variable optimization improved Sharpe +42% in sideways regimes
- No universal optimum exists — regime detection matters more than parameter tuning
- RSI threshold had minimal impact (<5% Sharpe change) across all values

## Templates and scripts

- `templates/backtest_simulator.py` — reusable BacktestSimulator class with metrics
- `templates/synthetic_data_generator.py` — OHLCV generator for 4 regimes
- `templates/one_variable_optimizer.py` — runs the full optimization protocol

## When to use this skill

- User asks to test/backtest a trading strategy
- User asks to optimize parameters and wants proof it's better
- User asks "which parameters matter most" for a system
- Research task where the output is a parameterized configuration

## When NOT to use

- Real-money live trading (this is for simulation only)
- Backtesting with real historical data from exchanges (use vectorbt/backtrader instead)
- Single-point estimation where parameters don't apply
