# Implementation Improvements

## Why this recovery was necessary

The earlier implementation could generate or hard-code representative social records, media descriptions and business assumptions, then allow those outputs to flow into JEV, BI, the Knowledge Graph, Digital Twin and PRD.

That created an epistemic failure: generated information could look like observed business evidence.

The recovery changed the project from **output-first** to **evidence-first**.

## Improvement 1 — Evidence decontamination

Completed changes:

- synthetic/mock production evidence quarantined
- legacy normalized records removed from active production inputs
- manually authored “verified real data” path disabled
- legacy reports archived/provisionally gated
- current production Evidence Lake accepts only provenance-valid records

Result: `synthetic authoritative records = 0`.

## Improvement 2 — Provenance enforcement

`src/evidence/integrity.py` now blocks authoritative records without capture proof.

Setting `synthetic=false` or `authoritative=true` is not sufficient to bypass provenance validation.

## Improvement 3 — Live JEV is authoritative and fail-closed

The old production path could silently fall back to deterministic rules when TypeSafe failed.

Current production behavior:

- discover/use live TypeSafe JEV
- record actual resolved model
- one bundled System One call per unique evidence item
- split one JEV result into compatible decision views
- reject silent fallback for authoritative discovery
- retain `root_cause_status=UNDETERMINED` without operational proof

Current verified model: `jev-1.13.0`.

## Improvement 4 — No-key social collection

Official social APIs are no longer a hard dependency for public discovery.

Working lanes include:

- Playwright public JS-rendered capture
- TikTok URL discovery
- `yt-dlp` stable TikTok metadata
- `gallery-dl` TikTok photo fallback
- owner exports when available
- optional official API enrichment
- planned archive/search recovery

This approach preserves legitimate source provenance while avoiding generated replacement data.

## Improvement 5 — Local-PC discovery with JEV

A bounded local discovery lane now uses relevant browser-history URLs and selected project folders to find research leads.

Important boundary:

```text
LOCAL LEAD → LIVE JEV DISCOVERY → RECAPTURE ORIGINAL SOURCE → AUTHORITATIVE EVIDENCE
```

Local discovery is never promoted directly into business truth. Legacy/provisional ABANGCOLEK reports are excluded to prevent circular reasoning.

This lane found:

- one previously missing TikTok URL
- Instagram candidate `@abangcolek`
- Instagram candidate/reseller `@jeruxsliurlelehterengganu`

Those public sources were subsequently recaptured by normal collectors.

## Improvement 6 — Media hallucination removed

The media pipeline no longer invents transcripts, OCR, packaging details or visual descriptions when media bytes are unavailable.

Missing media stays explicitly unavailable/pending.

## Improvement 7 — Snapshot dedupe

Repeated public captures are retained for forensic history but no longer inflate JEV/BI counts.

Current deduplicated state:

- 167 raw capture snapshots retained
- 39 repeat snapshots suppressed from classification
- 128 unique evidence items classified
- 304 authoritative live-JEV decisions

## Improvement 8 — Tests now protect truth, not fake richness

Old expectations that required minimum comments, fixed business eras or fabricated media outputs were removed.

Current tests validate:

- provenance requirements
- synthetic isolation
- no-media/no-transcript behavior
- JEV fail-closed behavior
- evidence-linked graph relationships
- zero-evidence state as valid
- repeated snapshot deduplication

Current suite: **33/33 PASS**.

## Recovery commits

- `3f21bb2` — forensic recovery: enforce real evidence and live JEV
- `7fc8241` — no-key social backfill with mandatory live JEV
- `0de5bda` — integrate local-PC discovery with live JEV and dedupe

These commits form the current recovery lineage.
