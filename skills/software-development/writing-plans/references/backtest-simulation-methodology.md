# Backtest / Simulation Methodology

## When to use this reference

Any plan involving a **quantitative strategy** (trading algorithm, ranking system, scoring function, portfolio optimizer, or anything with measurable performance). Use the methodology below to validate the plan before implementation.

---

## 1. Multi-Scenario Data Generation

Never test against a single scenario. Generate data for at least 3 contrasting regimes:

| Regime | Data characteristics | What it tests |
|--------|---------------------|---------------|
| **Bullish** | Upward drift with pullbacks | Can the strategy capture trends? |
| **Bearish** | Downward drift with bounces | Does it cut losses or hold? |
| **Sideways** | Mean-reverting noise | Does it whipsaw on false signals? |
| **Mixed** | Cycles: bullish → bearish → sideways | Real-world robustness |

For synthetic data generation:
```python
import numpy as np

def generate_regime(regime: str, n: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    if regime == "bullish":
        drift = np.linspace(0, 0.30, n)  # +30%
        noise = rng.normal(0, 0.005, n)
        corrections = -0.03 * rng.binomial(1, 0.08, n)
        returns = np.diff(np.insert(drift, 0, 0)) + noise + corrections
    elif regime == "bearish":
        drift = np.linspace(0, -0.25, n)  # -25%
        noise = rng.normal(0, 0.006, n)
        bounces = 0.04 * rng.binomial(1, 0.06, n)
        returns = np.diff(np.insert(drift, 0, 0)) + noise + bounces
    elif regime == "sideways":
        returns = rng.normal(0, 0.008, n)
    else:  # mixed
        segments = [0.12, -0.10, 0.0, 0.08]
        ...  # concatenate segment drifts
    # Build price series from returns
    price = 100000.0
    closes = [price]
    for ret in returns:
        price *= math.exp(ret)
        closes.append(price)
    return closes[:n]
```

---

## 2. Simulation Engine Requirements

The backtest simulator must track, at minimum:

| Component | What to model | Why |
|-----------|--------------|-----|
| **Entry logic** | Exact condition + price + timestamp | Reproducibility |
| **Exit logic** | Exact condition + price + timestamp | Auditability |
| **Position sizing** | % of capital, max positions, cooldown | Realism |
| **Fees** | Maker/taker, per-trade | Fee blindness kills strategies at small scale |
| **Slippage** | % added to entry, subtracted from exit | Market impact in low-liquidity conditions |
| **Equity curve** | Time series of portfolio value | Drawdown calculation |
| **Trade log** | Per-trade: entry/exit prices, P&L, hold time, reason | Honest review |

```python
class Simulator:
    def __init__(self, capital: float, fee: float, slippage: float):
        self.capital = capital
        self.trades = []
        self.equity = []

    def run(self, prices: pd.Series, entry_condition, exit_condition):
        for i in range(...):
            if not in_position and entry_condition(i):
                # Buy
                pass
            elif in_position and exit_condition(i):
                # Sell, record P&L, log trade
                pass
        return self.metrics()
```

---

## 3. "One Variable at a Time" (OVAT) Optimization

The core insight from Lewis Jackson's self-improving agent methodology:

> **"Modify one variable, measure impact, repeat. If you don't know which change caused the result, you don't know what to improve."**

OVAT procedure:

```python
def one_variable_at_a_time(base_config, df):
    results = []
    for dimension, values in [
        ("ema_fast", [5, 7, 9, 12, 15]),
        ("ema_slow",  [14, 21, 30, 50, 100]),
        ("rsi_period", [7, 10, 14, 20, 25]),
        ("entry_threshold", [40, 45, 50, 55, 60]),
    ]:
        for val in values:
            config = base_config.copy()
            config[dimension] = val
            metrics = simulate(config, df)
            results.append({**config, **metrics})
            print(f"{dimension}={val:3d} → Sharpe {metrics['sharpe']:.3f}")
    results.sort(key=lambda r: r['sharpe'], reverse=True)
    return results
```

### What OVAT reveals that multi-variable optimization hides

| Finding | Interpretation | Action |
|---------|---------------|--------|
| `ema_fast=15` beats `ema_fast=9` in 3 of 4 regimes | The parameter has regime-dependent impact | Add regime detection |
| `rsi_threshold` 40-60 gives same results | The parameter is negligible | Remove it (YAGNI) |
| `rsi_period=20` slightly better than 14 | Worth changing default | Update config |
| All configs lose money in sideways | The strategy class is wrong for this regime | Add alternative strategy, not parameter search |

---

## 4. Honest Evaluation Framework

### Required metrics table

```markdown
| Metric | Value | Interpretation |
|--------|-------|---------------|
| Total return | +12.4% | Positive, but... |
| Sharpe ratio | 0.34 | Below 0.5 = unacceptable risk-adjusted |
| Max drawdown | -18.2% | High for the return level |
| Win rate | 32% | Low — needs high avg win to compensate |
| Avg win / avg loss | +4.2% / -2.1% | Ratio 2:1 is adequate |
| Profit factor | 1.12 | Marginal (needs >1.5 for confidence) |
| Trades | 47 | Low for statistical significance (<200) |
```

### Confusion matrix approach

| | Predicted Win | Predicted Loss |
|---|---|---|
| **Actual Win** | True Positive | False Negative |
| **Actual Loss** | False Positive | True Negative |

Report the false positive rate (losses you took) and false negative rate (wins you missed).

### Trade-by-trade audit format

```markdown
| Date | Action | Price | P&L | Hold | Reason |
|------|--------|-------|-----|------|--------|
| 2025-09-14 | BUY  | $115,971 | —    | —    | EMA crossed up, RSI 71 |
| 2025-09-23 | SELL | $112,697 | -$3.89 | 9d | RSI dropped to 34 |
```

Always show the losing trades. The pattern of *why* they lost (premature exit, false entry, fee-drain) reveals design flaws that aggregate metrics hide.

---

## 5. Fee / Capital Sensitivity Analysis

```python
def fee_sensitivity(strategy_fn, capital_levels, fee_rates):
    for capital in [200, 500, 1000, 5000, 25000]:
        for fee in [0.0005, 0.001, 0.002]:
            result = strategy_fn(capital=capital, fee=fee)
            print(f"${capital:>5} | fee {fee:.1%} | Return {result['return']:+.1f}% | Viable: {result['return'] > 0}")
```

Expected output pattern:

```
Capital | Fee  | Return | Viable
$200    | 0.1% | -6.0% | ❌  (fees consume 15% of capital)
$1,000  | 0.1% | -1.2% | ⚠️  (marginal)
$5,000  | 0.1% | +3.8% | ✅  (fees are 0.3% of capital)
```

### Rule of thumb

```
Minimum viable capital = (cost per trade × 200) + (expected max drawdown × 1.5)
```

For a strategy with $0.50/trade cost and 15% expected DD:
```
Minimum = ($0.50 × 200) + (15% × 1.5) = $100 + $22.50 = ~$125
```
But for statistical significance (>200 trades), multiply by 5-10x.

---

## 6. Synthetic vs Real Data Gap

From empirical observation across multiple domains:

| Metric | Synthetic overestimate | Typical real gap |
|--------|----------------------|-----------------|
| Win rate | +10-20pp | Expect 15-30% lower in real data |
| Trade frequency | +50-100% | Real markets generate fewer clean signals |
| Sharpe ratio | +0.3-0.8 | Real data has heavier tails |
| Max drawdown | -5-15pp understated | Real markets have black swans |

**Mitigation:** always validate against at least one real data source (CoinGecko, Yahoo Finance, exchange public API) before committing to a design based on synthetic data alone.
