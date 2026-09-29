---
title: "ABANGCOLEK Evidence & JEV Governance Policy"
document_id: "DOC-AC-GOV-001"
version: "4.2.0"
last_updated: "2026-09-30 04:22:00"
maintainer: "Antigravity Sovereign Conductor"
classification: "INTERNAL_CORE"
lifecycle_status: "ACTIVE"
---

# Evidence & JEV Governance

## 1. Non-Negotiable Epistemic Hierarchy

Every statement or data point within the ABANGCOLEK system must occupy an explicit epistemic layer:

```text
RAW EVIDENCE (SHA-256 Verified Captures)
  ↓
OBSERVED FACT (Empirical, Grounded Occurrence)
  ↓
STRUCTURED CLASSIFICATION (Deterministic JEV System-1 Evaluation)
  ↓
INFERENCE (Corroborated Multi-Source Connection)
  ↓
HYPOTHESIS (Provisional Working Assumption; Cannot Auto-Verify)
  ↓
BUSINESS CONCLUSION (Gated by Human Owner Walkthrough & Real Transactions)
```

Downstream systems (Knowledge Graph, BI, and PRD) are strictly forbidden from flattening this hierarchy or promoting classifications into observed facts without verifiable provenance chains.

---

## 2. Authoritative Evidence Requirements

A record cannot become authoritative merely because metadata flags declare `authoritative=true`.

Ingestion into production requires empirical verification:
* **Public Web Captures**: URL, HTTP response status (200), final URL, and HTML/text SHA-256 receipt.
* **Extractor Metadata**: Extractor version receipt (`yt-dlp` / `gallery-dl`), native media IDs, and payload hash.
* **Owner Exports**: File hashes, platform export receipts, and sanitized non-synthetic payloads.

`src/evidence/integrity.py` validates these boundaries at the gate. Manual representative comments, guessed follower metrics, or hallucinated transcripts are unconditionally rejected.

---

## 3. JEV System-1 Operational Contract

TypeSafe JEV serves as the mandatory, neutral interpretation engine:
* **Deterministic Version Pinning**: Pinned to `jev-1.13.0` via `src/jev/typesafe_client.py`.
* **Zero Silent Fallback**: Rule-based fallbacks are strictly non-authoritative. Live API connectivity or deterministic cache replay is required.
* **Abstention Integrity**: `UNKNOWN` is an explicit, supported, and neutral outcome.
* **Root Cause Invariant**: Complaints (e.g. `LEAKAGE` or `TASTE`) are recorded as observed customer signals, while the operational root cause must remain **`UNDETERMINED`** until linked to manufacturing, transport, or storage batch records.

---

## 4. Media Provenance Constraints

* Zero transcripts without verified audio/video bytes.
* Zero OCR observations without real pixels and frames.
* Unprocessed media assets remain explicitly `PENDING` rather than generating placeholder text.

---

## 5. Snapshot Deduplication & Identity Integrity

Raw captures are immutable forensic records. Deduplication is performed dynamically during normalization:
* Deduplication Key: `(platform, source_native_id, collector)`.
* Platform-Segmented IDs: SHA-256 hashes generated via `src/evidence/identity.py` prevent handle collisions across social platforms.

---

## 6. Current Verified Operational Counters

* **Raw Capture Snapshots Retained**: 167 records
* **Duplicate Snapshots Suppressed**: 39 records
* **Unique Evidence Records Normalized**: 128 records (0 collisions)
* **Live Authoritative JEV Decisions**: 389 decisions
* **Total Posts Counted in BI**: 123 posts/videos/photos
* **Resolved JEV Model**: `jev-1.13.0` (100% cache hit rate on replay)
* **Synthetic Production Records**: 0

---

## 7. Audit & Revision Ledger

| Version | Timestamp (MYT) | Author | Why | How | Validation |
|---|---|---|---|---|---|
| `4.2.0` | `2026-09-30 04:22:00` | Antigravity Sovereign Conductor | Post-audit alignment and SMS-v1.0 standardization | Updated counters (389 decisions, 128 normalized, 123 posts) and documented identity segmentation | Pytest 53/53 passed; clean build run |
| `4.0.0` | `2026-09-29 12:10:00` | Recovery Team | Decontamination governance baseline | Established epistemic hierarchy and root cause invariants | Integrity gate passed |
