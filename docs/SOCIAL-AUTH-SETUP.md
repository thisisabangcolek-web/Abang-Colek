---
title: "ABANGCOLEK Social & Cloud Data Access Configuration"
document_id: "DOC-AC-AUTH-001"
version: "4.2.0"
last_updated: "2026-09-30 04:26:00"
maintainer: "Antigravity Sovereign Conductor"
classification: "INTERNAL_CORE"
lifecycle_status: "ACTIVE"
---

# Social & Cloud Data Access Configuration

## 1. Architectural Position

Owner-authorized social APIs and cloud credentials are **optional enrichment**, not a hard blocker for ABANGCOLEK public discovery.

The system is fully capable of running public ingestion, normalization, JEV evaluation, and Knowledge Graph construction via no-key collectors. Authorized access and owner exports are reserved for private scopes (deleted posts, direct customer messages, internal financial receipts, and platform analytics).

> [!WARNING]
> Never commit, print, or leak raw API keys, bearer tokens, or database passwords into chat, source code, git commits, or reports.

---

## 2. Environment Configuration

Variables are managed securely via `C:\Users\megat\.env` or operating system environment variables:

### Core Required Credentials
* `TYPESAFE_API_KEY`: Required for live System-1 JEV evaluations (`jev-1.13.0`).

### Cloud Database Credentials (Supabase)
* `SUPABASE_URL`: Supabase project endpoint (e.g. `https://gcpyatuhoxrwbuljvleo.supabase.co`).
* `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`: Required for automated PostgREST sync (`python -m src.cli sync-supabase`).
* *Note*: If environment variables are omitted, offline SQL seed export is always available via `python -m src.cli export-sql`.

### Optional Social Platform Enrichment
* **Threads**: `THREADS_ACCESS_TOKEN`
* **TikTok**: `TIKTOK_ACCESS_TOKEN` / `TIKTOK_DISPLAY_ACCESS_TOKEN`
* **Instagram Professional**: `INSTAGRAM_ACCESS_TOKEN` & `INSTAGRAM_USER_ID`
* **Facebook Pages**: `FACEBOOK_USER_ACCESS_TOKEN`

---

## 3. Owner Exports Inbox

Direct owner-exported data (ZIP/JSON archives) should be deposited into:
```text
D:\ABANGCOLEK\data\owner_exports\inbox\
```

The importer routes and hashes these files as immutable first-party evidence, mapping post captions, comments, and replies into canonical records.

---

## 4. Access Safety Rules

* Zero CAPTCHA bypass, stolen cookies, or session hijacking.
* Zero rate-limit evasion or unauthenticated private scraping.
* Any source blocked by platform access limitations is explicitly recorded as a coverage gap in the manifest.

---

## 5. Audit & Revision Ledger

| Version | Timestamp (MYT) | Author | Why | How | Validation |
|---|---|---|---|---|---|
| `4.2.0` | `2026-09-30 04:26:00` | Antigravity Sovereign Conductor | Post-audit alignment and Supabase credential documentation | Added Supabase env section and SMS-v1.0 frontmatter | CLI doctor check; clean env parse |
| `4.0.0` | `2026-09-29 12:10:00` | Recovery Team | Social auth governance baseline | Documented environment variable definitions | Variable check |
