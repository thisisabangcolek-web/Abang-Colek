# ABANGCOLEK No-Key Social Collection Architecture

## Principle
Official platform APIs are optional enrichment. The primary discovery system must recover the maximum legitimate public/owner-controlled history without requiring paid API access or fabricated data.

## Lane A — Public JS Browser
`src/collectors/browser_public_adapter.py`

Uses real Chromium + Playwright to render public profiles and posts exactly as a normal anonymous browser receives them.

Current proven targets:
- Threads `@airpoolstylo`
- Instagram `@airpoolstylo`
- TikTok `@styloairpool`

It records source URL, final URL, HTTP status, timestamp, visible text, page metadata, HTML SHA-256 and a local HTML snapshot. It never exports cookies, local storage, authorization tokens or browser credentials.

## Lane B — Public Extractor Tools
TikTok URL discovery is separated from metadata extraction.

- Browser discovers public TikTok video/photo URLs.
- `tiktok_ytdlp_adapter.py` extracts stable video metadata with yt-dlp.
- `tiktok_gallery_adapter.py` handles photo posts unsupported by yt-dlp.
- Signed CDN URLs, request headers and volatile download formats are excluded from authoritative metadata.

## Lane C — Owner-Controlled Browser Session
Hermes-WebApp already contains browser automation patterns and Agent-Reach integration. OpenCLI 1.8.8 is installed locally and is designed to operate a logged-in Chrome session without requiring platform API keys.

Use this lane only when public browsing cannot expose enough history. The browser remains under the owner's control. Do not export/decrypt cookies or copy session tokens into ABANGCOLEK.

Current state:
- OpenCLI installed.
- OpenCLI Browser Bridge extension is not connected yet.
- GangNiaga WebBridge port 10087 is currently offline.
- CDP ports checked during recovery were not active.

## Lane D — Public Archive / Search Recovery
For older/deleted public traces, use public search indexes, Jina Reader, Wayback/Common Crawl or equivalent archives where available. Archive evidence must retain archived URL/snapshot date and must never be presented as current state without temporal qualification.

## Evidence rule
Every authoritative record needs actual capture proof. No collector may replace inaccessible content with generated captions, representative comments, guessed metrics or synthetic transcripts.

## Completion rule
"Complete" means complete within a clearly stated source scope. Deleted/private/unexposed history remains a documented coverage gap until owner exports or an owner-controlled session legitimately closes it.

## Mandatory Live JEV Gate
Every provenance-valid raw record is normalized and classified by TypeSafe JEV before it can contribute to authoritative BI or the Business Digital Twin.

Current implementation:
- `src/jev/batch_runner.py` reads only authoritative production evidence.
- One bundled System One call evaluates each evidence item across content, customer intent, complaint, issue, channel and business-signal dimensions.
- The response is split into compatible `content`, `business_signal`, `interaction` and `complaint` decision views without additional JEV calls.
- Live model/fallback invariant: `decision_engine=TYPESAFE_JEV`, `authoritative=true`; deterministic fallback is rejected for authoritative discovery.
- Root cause remains `UNDETERMINED` unless separate operational evidence proves it.

Verified 2026-09-29: 113 authoritative raw records produced 258 decisions, all resolved by `jev-1.13.0`.

