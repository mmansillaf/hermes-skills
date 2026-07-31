# Free Tools & APIs for Smart Money Research

> Verified working July 2026 — all tested via terminal(curl) and/or Python from WSL.

## Free Alternatives to Paid Trading Platforms

| Paid Tool | Cost | Free Alternative | What It Provides |
|-----------|------|------------------|-----------------|
| **ATAS** | $30-70/mo | `smartmoneyconcepts` (pip) + TradingView Free + NinjaTrader Sim | Order blocks, FVG, liquidity sweeps, BOS/CHoCH. Volume profile basics. |
| **Sierra Chart** | $25-125/mo | TradingView Free + Quantower Free | Charting, indicators, DOM, CVD, footprint (Quantower free tier limited) |
| **Bookmap** | $50-150/mo | **OrderFlow-Analysis-Pro** (GitHub) + **TapeFlow** (GitHub) | Heatmap-style visualizations, footprint charts, delta analysis, real-time orderbook |
| **Nansen** | $$$$ | **Dune Analytics** (free tier) + **DeBank** + **Zapper** + Etherscan | On-chain wallet tracking, token flows, TVL. SQL queries on Dune. |
| **Arkham** | $$$$ | **Etherscan** + **Solscan** + **DefiLlama** | Entity tracking, whale alerts (manual). All free with rate limits. |
| **Glassnode** | $$$$ | **CoinGecko API** + **DefiLlama** + **Solana RPC** | Macro on-chain metrics: exchange flows, stablecoin TVL, whale distribution |
| **FlowAlgo** | $30-100/mo | **Barchart free** + **MarketBeat** + **AlphaQuery (13F)** | Options flow basics, institutional holdings via SEC EDGAR |

## Key GitHub Repositories (Verified)

| Repo | Stars | Language | Install | What It Detects |
|------|-------|----------|---------|-----------------|
| [joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) | 1.9k⭐ | Python | `pip install smartmoneyconcepts` | FVG, Order Blocks, Liquidity Sweep, BOS/CHoCH, Swing Highs/Lows, Retracements, Sessions |
| [mahmoud20138/OrderFlow-Analysis-Pro](https://github.com/mahmoud20138/OrderFlow-Analysis-Pro) | 24⭐ | Python (Dash) | `pip install -r requirements.txt` | Footprint charts, delta analytics, volume profile, absorption/initiative/divergence/sweep detection, state machine trade lifecycle. ~12K LOC |
| [python-telegramBot/crypto-liquidity-ai-trading-bot](https://github.com/python-telegramBot/crypto-liquidity-ai-trading-bot) | 84⭐ | Python + Node.js | `npm install && pip install` | Order book gaps, hidden liquidity walls, sweep events. Backtest: 58.2% win rate, 1.42 profit factor. |
| [ianfigueroa/TapeFlow](https://github.com/ianfigueroa/TapeFlow) | 13⭐ | C++ + React | Docker | Production-grade trading terminal: Time & Sales, footprint charts, DOM ladder, CVD overlays, paper trading engine. MIT license. |
| [elicat001/btc_quant_industrial-](https://github.com/elicat001/btc_quant_industrial-) | 11⭐ | Python | Clone & run | BTC real-time signal system: order flow + multi-factor resonance + ML models |

## Free Market Data APIs — Tested & Working

### 1. yfinance (Yahoo Finance)
```python
import yfinance as yf
# Stocks, ETFs, crypto, forex — unlimited historical data
spy = yf.download("SPY", period="1mo", interval="1d")
btc = yf.download("BTC-USD", period="7d", interval="1h")
# Institutional holders
msft = yf.Ticker("MSFT")
print(msft.institutional_holders)  # Top holders from 13F
```
- **Rate limit**: None documented (practical: ~10 queries/min)
- **Data**: OHLCV, dividends, splits, institutional holders, options chains

### 2. Binance REST API (No key needed for public endpoints)
```python
import requests
r = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT")
data = r.json()
print(f"Price: ${data['lastPrice']}, 24h Vol: {data['volume']}")
# Also: depth, klines (OHLCV), trades, aggTrades
```
- **Rate limit**: 1200 weight/min (even without API key)
- **Data**: Spot + futures, tick-level to 1w candles

### 3. CoinGecko API
```python
import requests
# Price
r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
# OHLC (7d, 30d)
r = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=7")
```
- **Rate limit**: ~30 calls/min (free tier without key)
- **Data**: Prices, market cap, OHLC, trending, categories

### 4. Bybit REST API (No key needed)
```python
import requests
r = requests.get("https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT")
print(r.json()["result"]["list"][0]["lastPrice"])
```
- **Data**: Spot + derivatives tickers, klines, orderbook, funding rate

### 5. Kraken REST API (No key needed)
```python
import requests
r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD")
print(r.json()["result"]["XXBTZUSD"]["c"][0])
```
- **Data**: Ticker, OHLC, depth, trades, spread, volume

## Free On-Chain APIs (No Key Needed)

| API | Endpoint | Example | Data |
|-----|----------|---------|------|
| **DefiLlama** | `stablecoins.llama.fi/stablecoins` | GET w/ `?includePrices=true` | 412 tracked stablecoins, TVL, market cap |
| **DeBank** | `api.debank.com/chain/list` | GET | Chain list, wallet portfolio (open api) |
| **Solana RPC** | `api.mainnet-beta.solana.com` | POST `{"jsonrpc":"2.0","method":"getLatestBlockhash"}` | Solana blockchain data (free public) |
| **Etherscan** | `api.etherscan.io/api` | GET w/ free API key | Ethereum data, transactions, token transfers |

## Research Workflow Tip

When investigating Smart Money, use `terminal(curl)` for these sources — the browser tool is 5-10x slower and triggers bot detection:

1. **arXiv papers**: `curl -sL "https://export.arxiv.org/api/query?id_list=XXXX.YYYYY"` (parses XML)
2. **GitHub READMEs**: `curl -sL "https://raw.githubusercontent.com/owner/repo/branch/README.md"`
3. **Crypto exchange data**: Direct REST endpoints listed above
4. **SEC EDGAR filings**: `curl -sL "https://efts.sec.gov/LATEST/search-index?q=..."`

Use `python3 -c "import sys, json; data=json.load(sys.stdin); ..."` or `grep -oP` for one-liner parsing of API responses.
