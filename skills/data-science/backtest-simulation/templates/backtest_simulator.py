#!/usr/bin/env python3
"""
Template: BacktestSimulator — reusable base class for multi-regime simulation.

Copy this file to your project, import BacktestSimulator and
generar_velas_sinteticas, configure your strategy logic inside simular(),
and run.

Usage:
    from backtest_simulator import BacktestSimulator, generar_velas_sinteticas

    df = generar_velas_sinteticas(2000, regimen="mixed", seed=42)
    sim = BacktestSimulator(param1=value1, param2=value2)
    results = sim.simular(df)
    print(results["metrics"])
"""

import math, random
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Synthetic Data Generator
# ═══════════════════════════════════════════════════════════════════════════════

def generar_velas_sinteticas(
    n_velas: int = 2000,
    timeframe: str = "1h",
    regimen: str = "mixed",
    seed: int = 42,
    precio_inicial: float = 100000.0,
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for backtesting.

    Regimenes: bullish, bearish, sideways, mixed
    Returns DataFrame with: timestamp, open, high, low, close, volume
    """
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start="2025-01-01", periods=n_velas, freq=timeframe)

    # Build price path
    if regimen == "bullish":
        trend = np.linspace(0, 0.30, n_velas)
        noise = rng.normal(0, 0.005, n_velas)
        corrections = -0.03 * rng.binomial(1, 0.08, n_velas)
        log_returns = np.diff(np.insert(trend, 0, 0)) + noise + corrections
    elif regimen == "bearish":
        trend = np.linspace(0, -0.25, n_velas)
        noise = rng.normal(0, 0.006, n_velas)
        bounces = 0.04 * rng.binomial(1, 0.06, n_velas)
        log_returns = np.diff(np.insert(trend, 0, 0)) + noise + bounces
    elif regimen == "sideways":
        log_returns = rng.normal(0, 0.008, n_velas)
        log_returns += 0.02 * rng.binomial(1, 0.03, n_velas)
        log_returns += -0.02 * rng.binomial(1, 0.03, n_velas)
    else:  # mixed
        seg = n_velas // 4
        t1 = np.linspace(0, 0.12, seg)
        t2 = np.linspace(0, -0.10, seg)
        t3 = np.zeros(seg)
        t4 = np.linspace(0, 0.08, n_velas - 3 * seg)
        trend = np.concatenate([t1, t2, t3, t4])
        log_returns = np.diff(np.insert(trend, 0, 0)) + rng.normal(0, 0.006, n_velas)

    precio = precio_inicial
    closes = [precio]
    for ret in log_returns:
        precio *= math.exp(ret)
        closes.append(precio)
    closes = closes[:n_velas]

    # Build OHLCV
    data = []
    for i in range(n_velas):
        c = closes[i]
        spread = c * rng.uniform(0.002, 0.008)
        vol = rng.uniform(10, 500)
        data.append([
            int(ts[i].timestamp() * 1000),
            c - spread * rng.uniform(0, 0.5),
            c + spread * rng.uniform(0, 0.8),
            c - spread * rng.uniform(0, 0.8),
            c,
            vol,
        ])

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Backtest Simulator Base Class
# ═══════════════════════════════════════════════════════════════════════════════

class BacktestSimulator:
    """
    Base class for strategy backtesting.

    OVERRIDE `generar_senal()` with your strategy logic.
    The base runs: for each bar, check signal, manage position, track P&L.

    Subclasses should set self.params = {...} with the parameters to optimize.
    """

    def __init__(self, costo_comision: float = 0.001, slippage: float = 0.001):
        self.costo_comision = costo_comision
        self.slippage = slippage
        self.params = {}           # Override in subclass
        self.nombre = "strategy"   # Override in subclass

    def generar_senal(self, i: int, df: pd.DataFrame) -> str:
        """
        Override this. Return 'BUY', 'SELL', or 'HOLD' for bar i.

        Access df['close'], df['open'], df['high'], df['low'], df['volume'].
        Use self.params for configurable parameters.
        """
        raise NotImplementedError

    def simular(self, df: pd.DataFrame) -> Dict:
        """Run backtest and return metrics and trades."""
        capital = 10000.0
        capital_inicial = capital
        in_position = False
        entry_price = 0.0
        entry_idx = 0
        cooldown_until = 0
        trades: List[Dict] = []
        equity_curve: List[float] = []

        for i in range(30, len(df)):  # skip warmup
            senal = self.generar_senal(i, df)

            if senal == "BUY" and not in_position and i >= cooldown_until:
                px = df['close'].iloc[i] * (1 + self.slippage) + px * self.costo_comision
                entry_price = px
                in_position = True
                entry_idx = i

            elif senal == "SELL" and in_position:
                px = df['close'].iloc[i] * (1 - self.slippage) - px * self.costo_comision
                pnl_pct = ((px - entry_price) / entry_price) * 100
                pnl_usdt = capital * (pnl_pct / 100)
                capital += pnl_usdt
                trades.append({
                    "entry_idx": entry_idx, "exit_idx": i,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(px, 2),
                    "pnl_pct": round(pnl_pct, 4),
                    "pnl_usdt": round(pnl_usdt, 4),
                    "hold_velas": i - entry_idx,
                })
                in_position = False
                cooldown_until = i + 1

            if in_position:
                val = capital * (1 + (df['close'].iloc[i] - entry_price) / entry_price)
                equity_curve.append(val)
            else:
                equity_curve.append(capital)

        # Close any open position at end
        if in_position:
            px = df['close'].iloc[-1] * (1 - self.slippage)
            cost = px * self.costo_comision
            pnl_pct = ((px - cost - entry_price) / entry_price) * 100
            pnl_usdt = capital * (pnl_pct / 100)
            capital += pnl_usdt
            trades.append({
                "entry_idx": entry_idx, "exit_idx": len(df) - 1,
                "entry_price": round(entry_price, 2),
                "exit_price": round(px - cost, 2),
                "pnl_pct": round(pnl_pct, 4),
                "pnl_usdt": round(pnl_usdt, 4),
                "motivo": "fin_periodo",
                "hold_velas": len(df) - 1 - entry_idx,
            })

        # Metrics
        equity = pd.Series(equity_curve)
        returns = equity.pct_change().dropna()
        total_ret = ((capital - capital_inicial) / capital_inicial) * 100
        n_trades = len([t for t in trades if t.get("motivo") != "fin_periodo"])
        wins = [t for t in trades if t["pnl_pct"] > 0]
        losses = [t for t in trades if t["pnl_pct"] <= 0]
        win_rate = len(wins) / max(len(trades), 1) * 100
        avg_win = np.mean([t["pnl_pct"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["pnl_pct"] for t in losses]) if losses else 0
        profit_factor = abs(sum(t["pnl_usdt"] for t in wins) / max(abs(sum(t["pnl_usdt"] for t in losses)), 0.01))
        sharpe = (returns.mean() / returns.std() * math.sqrt(8760)) if len(returns) > 1 and returns.std() > 0 else 0.0
        wealth = (1 + returns).cumprod()
        running = wealth.cummax()
        drawdown = (wealth - running) / running
        max_dd = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
        calmar = total_ret / max(max_dd, 0.1)

        return {
            "config": dict(self.params),
            "metrics": {
                "total_return_pct": round(total_ret, 2),
                "n_trades": n_trades,
                "win_rate_pct": round(win_rate, 1),
                "avg_win_pct": round(avg_win, 2),
                "avg_loss_pct": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "sharpe_ratio": round(sharpe, 4),
                "max_drawdown_pct": round(max_dd, 2),
                "calmar_ratio": round(calmar, 2),
                "capital_final": round(capital, 2),
            },
            "trades": trades,
        }
