---
title: "ABANGCOLEK Enterprise Forensic Architecture"
document_id: "DOC-AC-ARCH-001"
version: "4.2.0"
last_updated: "2026-09-30 04:12:00"
maintainer: "Antigravity Sovereign Conductor"
classification: "INTERNAL_CORE"
lifecycle_status: "ACTIVE"
---

# ABANGCOLEK Enterprise Forensic Architecture

## 1. Purpose & Core Philosophy

The ABANGCOLEK architecture is an **evidence-driven forensic intelligence pipeline**. Its primary architectural constraint is **epistemic integrity**: it prohibits hallucinating, interpolating, or promoting machine assumptions into business facts without strict, verifiable provenance chains.

---

## 2. End-to-End Runtime Pipeline

```text
DISCOVERY & INGESTION LANES
  ├─ Lane A: Public Browser (Playwright headless captures)
  ├─ Lane B: Public Extractors (yt-dlp metadata + gallery-dl photo fallback)
  ├─ Lane C: Local-PC Discovery Leads (JEV-evaluated DISCOVERY_ONLY)
  └─ Lane D: Owner Data & Official Exports (JSON payloads)
          ↓
RAW EVIDENCE LAKE (data/raw/*.json)
  └─ Enforces SHA-256 payload matching, HTTP status, and capture receipts
          ↓
IDENTITY & PROVENANCE SEGMENTATION (src/evidence/identity.py)
  └─ Computes platform-segmented SHA-256 hashes (eliminates cross-platform ID collisions)
          ↓
NORMALIZATION LAYER (data/runs/<run_id>/normalized/)
  └─ Maps source payloads to canonical record kinds (src/models/record_kind.py)
          ↓
DETERMINISTIC JEV INTERPRETATION (src/jev/engine.py & typesafe_client.py)
  └─ System-1 bundled evaluations pinned to model jev-1.13.0 with deterministic cache
          ↓
ANALYTICS & KNOWLEDGE GRAPH (src/analytics/bi_engine.py & src/knowledge/graph.py)
  ├─ BI Analytics: Computes canonical metrics (123 posts, channel distributions)
  └─ Knowledge Graph: SQLite (131 entities, 128 relationships, 389 epistemology, 124 timeline events)
          ↓
ATOMIC RUN STAGING & PUBLICATION (src/runs/manager.py & src/scripts/rebuild_pipeline.py)
  └─ Validates 12/12 integrity gates before activating run pointer (active_run.json)
          ↓
DOWNSTREAM CONSUMPTION & DISCOVERY
  ├─ Evidence Review UI & REST Server: Zero-dependency local SPA on port 8765 (src/workspace/server.py)
  ├─ Supabase Cloud Integration: PostgreSQL 15+ schema with RLS & 1.18 MB seed dump (src/db/)
  └─ Operational Validation Board: 8 Foundational Business Questions for owner walkthrough
```

---

## 3. Core Architectural Modules

### A. Identification & Anti-Collision Engine (`src/evidence/identity.py`)
To prevent ID collisions across social platforms sharing handles (such as `@airpoolstylo` on Threads vs. Instagram):
* `make_content_id(platform, native_id, record_kind)`: Generates platform-prefixed SHA-256 hashes (`cnt_<hash>`).
* `make_capture_id(content_id, collector, raw_hash)`: Generates capture-specific identifiers (`cap_<hash>`).
* `make_normalized_id(capture_id, normalizer_version)`: Generates file-safe normalized identifiers (`norm_<hash>`).

### B. Canonical Record Kind Layer (`src/models/record_kind.py`)
Standardizes diverse collector payloads into unambiguous operational categories:
* `POST`: Aggregates `public_post_snapshot`, `public_video_metadata`, and `public_photo_metadata` (currently **123 posts**).
* `PROFILE`: Public profile captures.
* `COMMENT` / `REPLY`: Structured conversation entries.

### C. Deterministic JEV Classification (`src/jev/`)
* **Pinned Model**: Pinned strictly to `jev-1.13.0` via `DEFAULT_MODEL` in [typesafe_client.py](file:///D:/ABANGCOLEK/src/jev/typesafe_client.py), eliminating cache misses caused by dynamic aliases (`jev-latest`).
* **Deterministic Cache Keys**: Computes hash across state, taxonomy version, question schema, and resolved model.
* **Abstention Support**: Neutral taxonomy criteria ensuring `UNKNOWN` is a valid, non-penalized evaluation state.

### D. Knowledge Graph with Provenance Foreign Keys (`src/knowledge/graph.py`)
Backed by SQLite (`abangcolek_v4.db`):
* `evidence_registry`: 128 verified captures.
* `entities`: 131 distinct nodes categorized by `EVIDENCE`, `PLATFORM`, `BRAND`, etc.
* `relationships` & `relationship_evidence`: 128 links requiring evidence citations.
* `epistemology` & `epistemology_evidence`: 389 assertions (Classification / Inference / Hypothesis).
* `timeline_events` & `timeline_evidence`: 124 chronological events.

### E. Supabase Cloud PostgreSQL Layer (`src/db/`)
* **Schema**: [schema.sql](file:///D:/ABANGCOLEK/src/db/schema.sql) defines 11 relational tables with native `TIMESTAMPTZ`, `JSONB`, foreign keys with cascading deletions, and full Row Level Security (RLS).
* **Dump Generator**: [supabase_sync.py](file:///D:/ABANGCOLEK/src/db/supabase_sync.py) extracts active run data and produces an idempotent, transaction-wrapped [supabase_seed.sql](file:///D:/ABANGCOLEK/supabase_seed.sql) (1.18 MB).

### F. Discovery Workspace & Review Server (`src/workspace/server.py`)
* Zero-dependency HTTP server running on `127.0.0.1:8765`.
* Serves responsive Dark OLED Single-Page Application (SPA) and REST API endpoints:
  * `/api/status`, `/api/evidence`, `/api/decisions`, `/api/graph`, `/api/questions`, `/api/export-supabase`.

### G. Unified CLI Entrypoint (`src/cli.py`)
Provides single-command operations for operators:
* `doctor`, `rebuild`, `review`, `export-sql`, `sync-supabase`, `status`.

---

## 4. Current Verified State

* **Raw Capture Snapshots**: 167 records (100% SHA-256 verified).
* **Deduplicated Records**: 128 normalized records (0 ID collisions).
* **JEV Decisions**: 389 decisions evaluated with `jev-1.13.0` (100% cache hit rate).
* **BI Metrics**: 123 posts, 10 complaint signals, 123 intent signals, 0 lineage errors.
* **Knowledge Graph**: 131 entities, 128 relationships, 389 epistemology items, 124 timeline events.
* **Test Suite**: 53/53 tests passed in 4.58 seconds.

---

## 5. Audit & Revision Ledger

| Version | Timestamp (MYT) | Author | Why | How | Validation |
|---|---|---|---|---|---|
| `4.2.0` | `2026-09-30 04:12:00` | Antigravity Sovereign Conductor | Architectural alignment with Supabase, Review Server, Identity module, and CLI | Documented new modular components, identity engine, and active state counts | 53/53 Pytest Passed; HTTP 200 verified |
| `4.0.0` | `2026-09-29 12:10:00` | Recovery Team | Forensic decontamination baseline | Segregated raw lake from downstream consumers | Doctor checks passed |
