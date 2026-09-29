---
title: "ABANGCOLEK Evidence-First Strategic Roadmap"
document_id: "DOC-AC-ROADMAP-001"
version: "4.2.0"
last_updated: "2026-09-30 04:18:00"
maintainer: "Antigravity Sovereign Conductor"
classification: "INTERNAL_CORE"
lifecycle_status: "ACTIVE"
---

# ABANGCOLEK Evidence-First Strategic Roadmap

## 1. Executive Objective

Do not build a bloated, premature "Business OS" based on social media assumptions.

The operational objective is to use the **Discovery Workspace** to validate real operational transactions with the business owner across order handling, stock ownership, agent reconciliation, and customer complaints, before committing to software architecture.

---

## 2. Completed Milestones

* [x] **M1: Forensic Decontamination** — Synthetic and mock records quarantined; provenance gates enforced.
* [x] **M2: No-Key Social Ingestion** — Headless browser and CLI extractors for TikTok, Instagram, and Threads.
* [x] **M3: Identity & Integrity Hardening (AC-01 to AC-06)** — Platform-segmented hashes eliminate collisions; canonical record kinds fix BI post aggregation (123 posts).
* [x] **M4: Deterministic JEV Classification (AC-11, AC-12)** — Pinned to `jev-1.13.0` with 100% cache replay rate and neutral criteria.
* [x] **M5: Knowledge Graph Ingestion (AC-13)** — 131 entities, 128 relationships, 389 epistemology items, and 124 timeline events.
* [x] **M6: Enterprise Supabase PostgreSQL Integration** — 11-table schema with RLS (`src/db/schema.sql`) and 1.18 MB idempotent SQL seed dump (`supabase_seed.sql`).
* [x] **M7: Discovery Workspace & Review UI (AC-16)** — Interactive Dark OLED web dashboard and REST server active at `http://127.0.0.1:8765`.
* [x] **M8: Unified CLI** — Single-command management via `python -m src.cli`.

---

## 3. Active & Upcoming Phases

### Phase O1 — Owner Walkthrough & Internal Operational Discovery (CURRENT FOCUS)
* **Tool**: The 8 Foundational Business Questions board on the Evidence Review UI (`http://127.0.0.1:8765`).
* **Objective**: Walk through one real end-to-end transaction with the business owner:
  1. `ORDER_FLOW`: How is a real customer order received, recorded, and fulfilled?
  2. `STOCK_OWNERSHIP`: Who owns inventory at HQ vs. mobile pop-up stalls vs. agents?
  3. `AGENT_RESTOCK`: What are the real terms, prices, and replenishment rules for agents?
  4. `COMPLAINT_TRACE`: How are packaging/taste issues mapped to batches and suppliers?
  5. `PRODUCTION_TRACE`: What paperwork or digital logs exist for food prep and QC?
  6. `TRANSPORT_TRACE`: How are parcels dispatched and tracked?
  7. `EVENT_CREW`: How are mobile teams rostered and reconciled?
  8. `PAYMENT_CLOSE`: How are cash, QR, and COD funds banked and verified?

### Phase O2 — Targeted Operational MVP Scoping
* Rather than building an all-in-one suite, select **one single verified workflow** that produces immediate operational value:
  * *Candidate A*: Order Intake & Status Register (eliminating WhatsApp slip loss).
  * *Candidate B*: Agent Stock & Restock Tracker.
  * *Candidate C*: Complaint Case Management & Lot Tracing.
* Document traceability from verified evidence directly to user stories.

### Phase O3 — Deeper Social & Conversation Recovery (As Needed)
* **Structured Comments & Creator Replies**: Parse nested comment hierarchies to capture customer demand and recurring questions.
* **Real Media Intelligence**: Process audio and video bytes for ASR/OCR only when media files are legitimately downloaded.

---

## 4. Gates Before PRD Sign-Off

Final PRD remains gated until:
1. At least one core business workflow is validated with physical or digital transaction proof.
2. The 8 Foundational Questions board has recorded answers and owner sign-off.
3. Identified gaps are accepted with documented mitigations.

---

## 5. Audit & Revision Ledger

| Version | Timestamp (MYT) | Author | Why | How | Validation |
|---|---|---|---|---|---|
| `4.2.0` | `2026-09-30 04:18:00` | Antigravity Sovereign Conductor | Alignment with Supabase, Review UI, and post-audit status | Marked Milestones M1-M8 complete; defined Phase O1/O2 operational focus | Server running on port 8765; 53/53 tests pass |
| `4.0.0` | `2026-09-29 12:10:00` | Recovery Team | Initial roadmap post-decontamination | Formulated phases N1 through N6 | Initial planning baseline |
