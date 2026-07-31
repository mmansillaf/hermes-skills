#!/usr/bin/env python3
"""
GEX Calculator — Gamma Exposure desde opciones listadas
Basado en: Conceptos_v2/sm11.txt (investigación Smart Money Jul 2026)

Calcula Net GEX por strike, Gamma Flip, Call Wall, Put Wall usando:
- yfinance → option chain
- scipy.stats.norm → Black-Scholes Gamma
- numpy/pandas → agregación
"""
import math, numpy as np, pandas as pd
from scipy.stats import norm
import yfinance as yf
import matplotlib.pyplot as plt

def black_scholes_gamma(S, K, T, r, sigma):
    """Gamma (Γ) teórica Black-Scholes para una opción."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))

def calculate_gex(ticker_symbol: str, risk_free_rate: float = 0.045):
    """Descarga option chain y calcula GEX por strike + Gamma Flip."""
    ticker = yf.Ticker(ticker_symbol)
    spot_price = ticker.fast_info["lastPrice"]
    expirations = ticker.expirations
    if not expirations:
        raise ValueError(f"Sin opciones para {ticker_symbol}")

    gex_by_strike = {}
    today = pd.Timestamp.now()

    for exp_date in expirations[:5]:  # limitar a 5 vencimientos
        opt_chain = ticker.option_chain(exp_date)
        days_to_exp = (pd.to_datetime(exp_date) - today).days
        T = max(days_to_exp, 1) / 365.0

        for opt_type, options_df in [("call", opt_chain.calls), ("put", opt_chain.puts)]:
            if options_df.empty:
                continue
            for _, row in options_df.iterrows():
                strike = row["strike"]
                oi = row["openInterest"]
                iv = row["impliedVolatility"]
                if pd.isna(oi) or oi <= 0 or pd.isna(iv) or iv <= 0:
                    continue
                gamma = black_scholes_gamma(spot_price, strike, T, risk_free_rate, iv)
                gex = gamma * oi * 100 * (spot_price**2) * 0.01
                if opt_type == "put":
                    gex = -gex
                gex_by_strike[strike] = gex_by_strike.get(strike, 0.0) + gex

    df = pd.DataFrame(list(gex_by_strike.items()), columns=["Strike", "Net_GEX"]
                      ).sort_values("Strike").reset_index(drop=True)
    df = df[(df["Strike"] >= spot_price * 0.8) & (df["Strike"] <= spot_price * 1.2)]

    # Gamma Flip: interpolación donde Net_GEX cruza cero
    gamma_flip = spot_price
    for i in range(1, len(df)):
        if (df.loc[i-1, "Net_GEX"] < 0 and df.loc[i, "Net_GEX"] >= 0) or \
           (df.loc[i-1, "Net_GEX"] > 0 and df.loc[i, "Net_GEX"] <= 0):
            s1, g1 = df.loc[i-1, "Strike"], df.loc[i-1, "Net_GEX"]
            s2, g2 = df.loc[i, "Strike"], df.loc[i, "Net_GEX"]
            gamma_flip = s1 - g1 * (s2 - s1) / (g2 - g1)
            break

    return df, spot_price, gamma_flip

def plot_gex(df, spot, flip, ticker):
    """Gráfico de barras: GEX por strike."""
    colors = ["#2ecc71" if x >= 0 else "#e74c3c" for x in df["Net_GEX"]]
    plt.figure(figsize=(12, 6))
    plt.bar(df["Strike"], df["Net_GEX"] / 1e6, color=colors, width=1.5, alpha=0.8)
    plt.axvline(x=spot, color="blue", linestyle="--", linewidth=2, label=f"Spot: ${spot:.2f}")
    plt.axvline(x=flip, color="purple", linestyle="-.", linewidth=2, label=f"Gamma Flip: ${flip:.2f}")
    call_wall = df.loc[df["Net_GEX"].idxmax(), "Strike"]
    put_wall = df.loc[df["Net_GEX"].idxmin(), "Strike"]
    plt.axvline(x=call_wall, color="green", linestyle=":", label=f"Call Wall: ${call_wall:.2f}")
    plt.axvline(x=put_wall, color="red", linestyle=":", label=f"Put Wall: ${put_wall:.2f}")
    plt.title(f"Perfil GEX - {ticker}", fontsize=14)
    plt.xlabel("Strike ($)"); plt.ylabel("Net GEX (Millones $ / 1%)")
    plt.grid(True, linestyle=":", alpha=0.6); plt.legend(); plt.tight_layout()
    plt.savefig(f"gex_{ticker}.png"); print(f"📊 Gráfico: gex_{ticker}.png")

if __name__ == "__main__":
    SYMBOL = "SPY"
    df, spot, flip = calculate_gex(SYMBOL)
    print(f"\n{SYMBOL} | Spot: ${spot:.2f} | Gamma Flip: ${flip:.2f}")
    print(f"Régimen: {'LONG GAMMA (amortiguado)' if spot > flip else 'SHORT GAMMA (acelerado)'}")
    plot_gex(df, spot, flip, SYMBOL)
