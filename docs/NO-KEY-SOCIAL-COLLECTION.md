# ABANGCOLEK No-Key Social Collection Architecture

## Principle

Official platform APIs are optional enrichment. Public business discovery must be able to recover legitimate public history without requiring paid/platform API keys and without fabricating replacement data.

“No-key” does not mean bypassing access controls. CAPTCHA bypass, stolen/decrypted cookies, login circumvention, IP/rate-limit evasion and unauthorized private-data access are not part of this architecture.

## Lane A — Public JS browser

`src/collectors/browser_public_adapter.py`

Uses Chromium + Playwright to capture public JS-rendered profile/post pages. Each authoritative capture preserves source URL, final URL, HTTP status, visible text, page metadata, capture timestamp and HTML SHA-256.

Current proven targets:

- Threads `@airpoolstylo`
- Instagram `@airpoolstylo`
- TikTok `@styloairpool`
- Instagram candidate `@abangcolek`
- Instagram candidate/reseller `@jeruxsliurlelehterengganu`

The collector does not export cookies, local storage or browser authorization secrets into the Evidence Lake.

## Lane B — Public extractor tools

TikTok URL discovery and metadata extraction are separated.

- Browser discovery accumulates public video/photo URLs.
- `tiktok_ytdlp_adapter.py` extracts stable metadata with `yt-dlp`.
- `tiktok_gallery_adapter.py` handles public photo posts not covered by the video extractor.
- Signed CDN URLs, request headers and volatile download formats are excluded from authoritative metadata.

Current verified TikTok checkpoint:

- 81 public URLs accumulated
- 79/81 successfully extracted by `yt-dlp`
- 2 URLs remain failed
- 2 photo posts handled by `gallery-dl`
- earliest recovered TikTok metadata currently reaches 2025-11-02

## Lane C — Local-PC discovery

`src/scripts/local_pc_discovery.py` searches a bounded set of relevant local signals: sanitized browser-history URLs and selected project folders.

The output is `DISCOVERY_ONLY`. Live JEV may classify these leads, but they remain `authoritative_for_business_truth=false` until an original public source is recaptured by a normal collector.

## Lane D — Owner data and optional APIs

Owner exports and official APIs remain useful for scopes public collection cannot prove: deleted/private history, insights, full replies, profile metadata and platform-native historical completeness.

See `SOCIAL-AUTH-SETUP.md`. These integrations are optional enrichment, not a requirement for the no-key public lane to operate.

## Lane E — Archive/search recovery

Planned recovery for older/deleted public traces includes search indexes and public web archives. Archive evidence must retain archived URL and snapshot date and must be described as historical evidence, not current state.

## Mandatory live JEV gate

Every provenance-valid unique evidence item is classified through TypeSafe JEV before contributing to authoritative BI.

Current invariant:

```text
decision_engine = TYPESAFE_JEV
authoritative = true
fallback = rejected for authoritative discovery
root cause = UNDETERMINED without operational proof
```

Current verified state: 167 raw capture snapshots retained; 39 repeat snapshots suppressed; 128 unique evidence items processed; 304 authoritative decisions resolved with `jev-1.13.0`.

## Completion rule

A source is only “complete” within the scope actually exhausted. Public crawling cannot prove deleted/private lifetime history. Coverage gaps remain explicit until a stronger source legitimately closes them.
