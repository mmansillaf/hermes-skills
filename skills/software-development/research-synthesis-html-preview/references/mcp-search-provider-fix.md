# MCP Search Provider Fix: Serper→Tavily Priority Swap

When kindly-web-search returns 403 Forbidden, it's because:
1. `SERPER_API_KEY` exists but has 0 credits (Serper)
2. `TAVILY_API_KEY` exists and has free credits (Tavily)
3. The MCP wrapper only exports `SERPER_API_KEY`
4. The server code checks Serper first and never reaches Tavily

## Fix 1: Wrapper — Export Both Keys

File: `mcp-wrapper.sh`

Replace the single-key export with:

```bash
if [ -f "$ENV_FILE" ]; then
    SERPER_API_KEY=$(grep -E '^SERPER_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    TAVILY_API_KEY=$(grep -E '^TAVILY_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    export SERPER_API_KEY
    export TAVILY_API_KEY
fi
```

## Fix 2: Server Code — Swap Provider Priority

File: `src/kindly_web_search_mcp_server/search/__init__.py`

Change the provider selection block from:

```python
if has_serper:
    provider = search_serper
    provider_name = "serper"
elif has_tavily:
    provider = search_tavily
    provider_name = "tavily"
```

To:

```python
if has_tavily:
    provider = search_tavily
    provider_name = "tavily"
elif has_serper:
    provider = search_serper
    provider_name = "serper"
```

Also update the docstring: change "If SERPER_API_KEY is set: use Serper. Else if TAVILY_API_KEY..." to "If TAVILY_API_KEY is set: use Tavily (preferred — has credits). Else if SERPER_API_KEY..."

## Fix 3: Restart MCP Server

Kill old MCP processes so the watchdog respawns them with the new keys:

```bash
pkill -f "kindly-web-search"
# The gateway watchdog respawns automatically.
# Alternatively, start a new Hermes session.
```

## Verification

After fixes:
```bash
hermes mcp test kindly-web-search
# Expected: ✓ Connected, ✓ Tools discovered: 2

# Then try a real search:
mcp__kindly_web_search__web_search(query="test query", num_results=2)
# Expected: actual results, not 403
```

## Root Cause

The `settings.py` file only reads `SERPER_API_KEY` from the environment. The `search/__init__.py` has strict ordering: Serper first, then Tavily, then SearXNG. No cross-provider fallback — if Serper responds with 403 (no credits), the entire search call fails rather than falling through to Tavily.
