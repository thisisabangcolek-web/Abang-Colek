# ABANGCOLEK Intelligence & Business Discovery Engine

ABANGCOLEK is currently an **evidence-first business discovery system**, not the final Business OS application.

Its job is to reconstruct how the real ABANGCOLEK / STYLOAIRPOOL / LIURLELEH / JERUX business operates from verifiable social, public, owner-provided and internal evidence before software requirements are finalized.

## Current stage

Status as of 2026-09-29:

- Forensic recovery: **PASS**
- Evidence integrity: **PASS**
- Tests: **33/33 PASS**
- Raw capture snapshots retained: **167**
- Repeated snapshots suppressed from classification: **39**
- Unique evidence classified: **128**
- Authoritative live-JEV decisions: **304**
- JEV resolved model: **jev-1.13.0**
- Synthetic authoritative records: **0**
- Digital Twin: **BLOCKED pending broader coverage and internal discovery**
- Final PRD: **BLOCKED pending validated Digital Twin and workflows**

## Governing pipeline

```text
SOCIAL / PUBLIC / OWNER / LOCAL-PC DISCOVERY
                    ↓
             RAW CAPTURE PROOF
                    ↓
        PROVENANCE + SHA-256 VALIDATION
                    ↓
               NORMALIZATION
                    ↓
               LIVE TYPESAFE JEV
                    ↓
      FACT / CLASSIFICATION / INFERENCE
                    ↓
          KNOWLEDGE GRAPH + ANALYTICS
                    ↓
         BUSINESS DIGITAL TWIN DRAFT
                    ↓
           INTERNAL BUSINESS DISCOVERY
                    ↓
             VALIDATED WORKFLOWS
                    ↓
                 PRD / APP
```

Missing evidence is represented as `UNKNOWN`, `NOT_OBSERVED`, `NOT_ACCESSIBLE` or `INSUFFICIENT_EVIDENCE`. It must never be replaced by generated evidence.

## Documentation map

- `docs/RECOVERY-STATUS.md` — current verified project state and counts.
- `docs/ARCHITECTURE.md` — current runtime/data architecture.
- `docs/EVIDENCE-JEV-GOVERNANCE.md` — provenance, epistemology and JEV rules.
- `docs/NO-KEY-SOCIAL-COLLECTION.md` — no-platform-API-key collection design.
- `docs/SOCIAL-AUTH-SETUP.md` — optional owner-authorized API/export enrichment.
- `docs/IMPLEMENTATION-IMPROVEMENTS.md` — what was fixed and why.
- `docs/ROADMAP.md` — current execution plan and gates.
- `reports/SOCIAL-BACKFILL-REPORT.md` — current source coverage.
- `reports/ABANGCOLEK-BUSINESS-DIGITAL-TWIN.md` — gated Digital Twin status.
- `reports/ABANGCOLEK-OS-PRD.md` — gated final PRD status.

Anything under `docs/legacy/`, `reports/legacy/`, `forensic_archive/` or `data/quarantine/` is historical/forensic material and is **not** a current source of truth.

## Core commands

```powershell
cd D:\ABANGCOLEK
python -m src.scripts.run_backfill
python -m src.scripts.verify_integrity
pytest -q
```

`run_backfill` performs local-PC discovery, no-key public collection, optional authorized enrichment and then the mandatory live JEV gate.
