# Google Translate Proxy — Authwall Bypass

> General-purpose technique to bypass login/signup walls on sites that
> serve content to crawler IPs (Google, Bing) but block residential/datacenter
> IPs. Confirmed working with LinkedIn Jobs in Jun 2026.

## How It Works

Google Translate loads the target URL from Google's own servers (crawler IPs)
to render it for translation. If the target site allows Googlebot but blocks
anonymous visitors, the translated version bypasses the wall because the
request originates from Google's infrastructure.

The URL shape is:

```
https://translate.google.com/translate?hl=<lang>&sl=auto&tl=<lang>&u=<target_url>
```

The target URL must be URL-encoded. The result loads via
`<target-domain>.translate.goog` — Google's translated proxy domain.

## When to Try This

| Signal | Try Translate Proxy? |
|---|---|
| Site shows login wall for anonymous visitors | ✅ Yes, likely works if Google-indexed |
| Site blocks datacenter IPs (CAPTCHA, Cloudflare) | ⚠️ Possibly — request comes from Google IPs |
| Site requires JS to render (SPA) | ⚠️ Maybe — proxy may not execute JS |
| Site requires cookies/session | ❌ No — proxy doesn't carry session |
| Site is behind Cloudflare (general) | ⚠️ Depends — some CF configs block translate.goog |
| API endpoint (JSON/XML) | ❌ No — proxy expects HTML pages |

## Test Results (LinkedIn, Jun 2026)

| LinkedIn Feature | Direct Access | Via Translate Proxy |
|---|---|---|
| Jobs search | Count only ("2 jobs") + login wall | Full listings with titles, companies, locations |
| Pulse articles | Login wall (if URL exists) | Loads via translate.goog (if URL is valid) |
| Company pages | Login wall or page-not-found | Redirects to feed (not reliable) |
| Profiles | Login wall | Not tested |

## Procedure

1. **Get the exact URL** of the content you want. Use Google dorking
   (`site:target.com/path keywords`) from a residential IP to find URLs.

2. **Build the translate URL**:

   ```
   https://translate.google.com/translate?hl=es&sl=auto&tl=es&u=https%3A%2F%2Fsite.com%2Fpath
   ```

3. **Open in browser**. If the page loads via `site-com.translate.goog`,
   the bypass worked. If it redirects to the login page, the method failed
   for that particular page type.

4. **Navigate within the proxied session** — links inside the translated
   page also go through translate.goog, so you may be able to browse deeper
   without hitting the authwall again.

## Limitations

- **Not all pages work**: Login-protected pages that aren't in Google's index
  won't be cached by Translate. Company pages on LinkedIn redirect to feed.
- **No session persistence**: You can't perform logged-in actions.
- **Translation artifacts**: Google Translate modifies the HTML (adds
  `_x_tr_...` params, wraps in translate frame). Page structure may change.
- **Rate limits**: Google may throttle aggressive use.
- **SPA content**: Single-page apps that load data via JS XHR after page load
  won't work — the proxy only captures the initial HTML.

## Related

- `references/tc-jurisprudencia-api-discovery.md` — More robust API discovery
  for SPAs (complementary approach when Translate proxy fails)
- Yandex Translate is an alternative with slightly different tolerance —
  `https://translate.yandex.com/?lang=es&url=<target_url>`
