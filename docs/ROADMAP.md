# ABANGCOLEK Evidence-First Roadmap

## Current objective

Do not build the final Business OS yet.

The current objective is to recover enough real historical and operational evidence to understand how the business actually works across products, customers, agents/resellers, locations, events, production, stock movement and complaints.

## Completed foundation

- forensic snapshot/recovery
- contaminated evidence quarantine
- provenance enforcement
- synthetic production paths disabled
- live TypeSafe JEV fail-closed
- no-key public collectors
- local-PC discovery lane
- snapshot dedupe
- Digital Twin/PRD gates
- integrity tests

## Phase N1 — Expand social history

Priority:

1. deeper Threads history
2. deeper Instagram history
3. old Jerux/LiurLeleh public accounts and reseller traces
4. Facebook historical pages/posts
5. public search/index/archive recovery
6. bound every source with coverage status

## Phase N2 — Structured comments and replies

Current public captures expose some visible comments, but comments/replies are not yet normalized as first-class conversation records across platforms.

Target:

```text
POST
  └─ COMMENT
       └─ CREATOR REPLY
            └─ SUB-REPLY
```

This phase is critical for customer intent, complaint history, location demand, stock questions, price questions, agent interest and resolution tracking.

## Phase N3 — Real media intelligence

For legitimately obtainable media:

- retain/download permitted media bytes
- SHA-256 media hash
- audio extraction
- real ASR transcription
- frame sampling
- real OCR
- vision observations with provenance

No generated transcript/OCR may substitute for unavailable media.

## Phase N4 — Historical corroboration

Use archive/search evidence to recover older public traces and cross-check brand/product/distribution evolution. Archived material must retain its historical timestamp and must not be presented as current state.

## Phase N5 — Evidence-grounded business reconstruction

After broader coverage:

- rebuild Knowledge Graph from current clean evidence
- run deterministic analytics
- identify candidate business eras from data, not hard-coded dates
- separate facts, supported inferences and open hypotheses
- produce Business Digital Twin draft

## Phase N6 — Internal discovery

Public social data cannot prove internal workflows such as supplier receiving, recipes/BOM, batch handling, actual transport routes, agent stock terms, accounting or staff operations.

Use the Digital Twin gaps to ask management targeted questions and validate the real operating model.

## Final gates before PRD

Final PRD remains blocked until:

- historical coverage is explicitly bounded
- comments/replies are substantially recovered or gaps documented
- actual media pipeline is running where media is available
- critical identity/brand relationships are resolved or marked uncertain
- Digital Twin is evidence-supported
- internal operating workflows are validated
- software requirements have evidence/internal-confirmation traceability

Unknown remains a valid answer. Coverage quality is more important than producing a premature complete-looking system.
