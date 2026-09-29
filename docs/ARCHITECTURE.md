# ABANGCOLEK Current Architecture

## Purpose

The current system is an evidence-driven business intelligence pipeline. It must understand the real business before producing final software requirements.

## Runtime flow

```text
DISCOVERY SOURCES
  ├─ public browser (Playwright)
  ├─ yt-dlp / gallery-dl
  ├─ local-PC discovery leads
  ├─ owner exports
  ├─ optional official APIs
  └─ future archive/search recovery
          ↓
RAW EVIDENCE LAKE
          ↓
PROVENANCE / INTEGRITY GATE
          ↓
NORMALIZATION + SNAPSHOT DEDUPE
          ↓
LIVE TYPESAFE JEV
          ↓
KNOWLEDGE / ANALYTICS
          ↓
DIGITAL TWIN → INTERNAL DISCOVERY → PRD
```

The collection layer and the interpretation layer are deliberately separated. A discovery lead can help find a source, but cannot become a business fact until the original source is recaptured with provenance.

## Collection lanes

### Lane A — No-key public browser

`src/collectors/browser_public_adapter.py`

Captures public JS-rendered profiles/posts with URL, final URL, HTTP status, visible text, metadata, HTML hash and capture timestamp.

Current proven public targets include:

- Threads `@airpoolstylo`
- Instagram `@airpoolstylo`
- TikTok `@styloairpool`
- Instagram candidate `@abangcolek`
- Instagram candidate/reseller `@jeruxsliurlelehterengganu`

### Lane B — Public extractor tools

- `tiktok_ytdlp_adapter.py` — stable TikTok metadata.
- `tiktok_gallery_adapter.py` — photo-post fallback.
- Public extraction must not store volatile signed URLs, cookies or authorization headers as authoritative business data.

### Lane C — Local-PC discovery

`src/scripts/local_pc_discovery.py`

Uses only relevant browser-history URLs and approved project folders to discover leads. Legacy reports are excluded. Personal files are not bulk-read for business conclusions.

Local-PC candidates are classified by live JEV as `DISCOVERY_ONLY`. A public URL discovered locally must be fetched again by a normal collector before it can become authoritative evidence.

### Lane D — Owner data / official API

Owner exports and authorized APIs are optional enrichment rather than a hard dependency for public discovery. They are still important for deleted/private history, replies, insights and other scopes not exposed publicly.

## Evidence Lake

Authoritative raw records live under `data/raw/` and require:

- source platform/type/native ID
- source URL or owner-export source
- capture timestamp
- collector + access method
- capture receipt
- SHA-256/raw hash
- `provenance_verified=true`
- `synthetic=false`
- `authoritative=true`

Synthetic fixtures remain test-only and cannot enter authoritative analytics.

## Snapshot semantics

All legitimate raw capture snapshots are retained for forensic audit. Repeated captures of the same source are not deleted.

Before JEV classification, `JevBatchRunner` selects the latest snapshot for each `(platform, source_id, collector)` tuple. This prevents repeated crawling from inflating business counts while preserving historical capture proof.

## JEV interpretation layer

`src/jev/batch_runner.py` and `src/jev/engine.py` enforce live TypeSafe JEV for authoritative interpretation.

Current behavior:

- one bundled System One call per unique evidence item
- structured questions cover brand, business function, channel, intent, complaint, issue class and business signals
- results are exposed as compatible `content`, `business_signal`, `interaction` and `complaint` views
- silent deterministic fallback is forbidden for authoritative runs
- resolved model is recorded on every decision
- root cause stays `UNDETERMINED` unless independent operational evidence proves it

Current verified state: 167 raw snapshots retained, 39 repeat snapshots suppressed, 128 unique evidence items classified, producing 304 authoritative decisions with `jev-1.13.0`.

## Downstream gates

Knowledge Graph, analytics, Digital Twin and PRD are downstream consumers. They must never promote a classification or hypothesis into a verified fact without evidence lineage.

The Digital Twin remains intentionally blocked until historical coverage, comments/replies, media evidence and internal operating facts are sufficiently complete.
