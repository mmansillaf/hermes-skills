# API Evaluation Methodology & Results
## For Smart Money Detection App

### Methodology (Verified Jul 2026)

When user provides API keys or service URLs:

1. **Test basic endpoint**: `curl -s "URL_BASE/v3/status?apiKey=..."` or health check
2. **Reference data**: `/reference/tickers`, `/reference/dividends`
3. **Options data**: test with SPY + near-term expiration
4. **Earnings/fundamentals**: test with AAPL (high coverage)
5. **Streaming/MCP**: check for MCP Server or WebSocket support
6. **Document** what works, what gives 404, what needs JS

### Results Table (Keep Updated)

| API | Works | Cost | Verdict |
|-----|-------|------|---------|
| Unusual Whales | 100+ endpoints (GEX, Flow, Dark Pool, Congress, Crypto, Earnings, Alerts). MCP Server + skill.md | $150+/mo | **Best option** — covers 70% of needs |
| Massive API | Only `/v3/reference/tickers` and `/v3/reference/dividends` | Free (key: vME3VzHxYaiUDGU6LI6BI9_V2yG1v5Zg) | Low value — reference data only |
| mcp-capitol-trades | Installed via npm. Blocked by Vercel Cloudflare (429) | Free | Use Unusual Whales `/api/congress/recent-trades` instead |
| CryptoQuant | Insight link expired (404) | $79-199/mo | Phase 3 expansion |
| Apify | Scraping-as-a-service platform | Pay-per-use | Alternative data Phase 3 |
| Market Chameleon | Not accessible via curl (needs JS) | Unknown | Grey zone |

### Free/Open-Source Alternatives Found

| Need | Resource | Stars | Cost | Status |
|------|----------|-------|------|--------|
| GEX indices | Matteo-Ferrara/gex-tracker (CBOE scrape) | 205⭐ | Free | ✅ Verified |
| GEX + VEX + CHEX | aaguiar10/gflows (Dash UI) | 106⭐ | Free | ✅ Verified |
| GEX theory + code | FlashAlpha-lab/gex-explained | 7⭐ | Free | ✅ Updated today |
| GEX stocks | Our yfinance-based code (sm11.txt adapted) | — | Free | ✅ Tested SPY+AAPL |
| Options Flow | No free real-time alternative | — | Free | ❌ Requires paid API |
| Congress | Capitol Trades website | — | Free | 🟡 Cloudflare blocked |
| Crypto | Binance WS + CoinGecko + Deribit API | — | Free | ✅ Best in class |

### Recommended Stack (Budget-Conscious)

```
GEX:      gex-tracker (gratis) + yfinance code (gratis)       → $0/mes
Options:  Polygon.io Basic ($29/mes) or Unusual Whales ($150+) → $29-150/mes
Crypto:   Binance WS + CoinGecko (gratis)                      → $0/mes
Congress: Unusual Whales endpoint or Capitol Trades scraping   → $0-150/mes
Earnings: yfinance + Finnhub free                              → $0/mes

Total: $29-150/mes vs $150+ for Unusual Whales alone
```

### Validation Tests Performed

| Test | Result | Bug Found |
|------|--------|-----------|
| GEX on SPY | $1,590.96M Net GEX, 730 contracts, ~15s | Gamma Flip ($504) unrealistic vs spot ($742) — fix: use cumsum |
| GEX on AAPL | $563.04M Net GEX, 291 contracts | Same Gamma Flip issue |
| yfinance API | `ticker.expirations` deprecated → use `ticker.options` | API change documented |
