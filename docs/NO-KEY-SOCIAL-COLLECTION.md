---
title: "ABANGCOLEK No-Key Social Collection Architecture"
document_id: "DOC-AC-COLLECT-001"
version: "4.2.0"
last_updated: "2026-09-30 04:24:00"
maintainer: "Antigravity Sovereign Conductor"
classification: "INTERNAL_CORE"
lifecycle_status: "ACTIVE"
---

# ABANGCOLEK No-Key Social Collection Architecture

## 1. Core Operating Principle

Official platform APIs are optional enrichment. Public business discovery must be capable of recovering legitimate public history without requiring paid platform API keys and without fabricating synthetic replacement data.

"No-key" collection strictly adheres to legal and ethical research standards:
* Zero CAPTCHA bypass or session cookie theft.
* Zero rate-limit brute forcing or private endpoint compromise.
* Ingestion is limited to publicly accessible, rendered social media pages and metadata.

---

## 2. Ingestion Lanes

### Lane A — Public JS Browser Automation
* Implemented via [src/collectors/browser_public_adapter.py](file:///D:/ABANGCOLEK/src/collectors/browser_public_adapter.py).
* Uses headless Playwright/Chromium to capture public rendered pages.
* Preserves source URL, final redirect URL, HTTP status (200), visible text, and HTML SHA-256 hash.
* Verified active targets:
  * Threads: `@airpoolstylo`
  * Instagram: `@airpoolstylo`
  * TikTok: `@styloairpool`
  * Candidate Instagram: `@abangcolek`
  * Candidate Reseller: `@jeruxsliurlelehterengganu`

### Lane B — Public Extractor Tools
* TikTok URL discovery is decoupled from media extraction.
* [src/collectors/tiktok_ytdlp_adapter.py](file:///D:/ABANGCOLEK/src/collectors/tiktok_ytdlp_adapter.py) uses `yt-dlp` to extract stable video metadata without credentials.
* [src/collectors/tiktok_gallery_adapter.py](file:///D:/ABANGCOLEK/src/collectors/tiktok_gallery_adapter.py) handles photo slides and carousels via `gallery-dl`.
* Volatile signed URLs and auth headers are stripped to ensure deterministic hashing.
* **Coverage**: 81/81 identified TikTok URLs have metadata recovered.

### Lane C — Local-PC Discovery Leads
* [src/scripts/local_pc_discovery.py](file:///D:/ABANGCOLEK/src/scripts/local_pc_discovery.py) explores local research breadcrumbs (browser history URLs and project artifacts).
* Tagged strictly as `DISCOVERY_ONLY`. Public re-capture is mandatory before promotion to evidence.

### Lane D — Owner Exports & Optional APIs
* Platform archives (JSON/ZIP) provided directly by the business owner.
* Captures private/deleted posts, customer conversations, and exact metrics not accessible via public crawl.

---

## 3. Mandatory Live JEV Gate & Current Operational Counters

Every provenance-valid unique evidence item is classified through TypeSafe JEV System-1 before contributing to authoritative analytics.

* **Raw Capture Snapshots Retained**: 167 records (100% SHA-256 verified)
* **Repeated Snapshots Suppressed**: 39 duplicate captures
* **Unique Normalized Evidence Records**: 128 records (0 collisions)
* **Authoritative Live-JEV Decisions**: 389 decisions (Model: `jev-1.13.0`)
* **Total Posts Counted in BI**: 123 posts/videos/photos
* **Coverage Scope**: Public historical footprint bounded; lifetime completeness is not claimed without owner exports.

---

## 4. Audit & Revision Ledger

| Version | Timestamp (MYT) | Author | Why | How | Validation |
|---|---|---|---|---|---|
| `4.2.0` | `2026-09-30 04:24:00` | Antigravity Sovereign Conductor | Post-audit alignment and SMS-v1.0 standardization | Updated JEV counter to 389, post counts to 123, and added audit ledger | Pytest 53/53 passed; clean build run |
| `4.0.0` | `2026-09-29 12:10:00` | Recovery Team | Initial no-key collection architecture | Documented lanes A through E | Ingestion verified |
