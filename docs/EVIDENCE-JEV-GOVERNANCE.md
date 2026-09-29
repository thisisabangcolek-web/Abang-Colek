# Evidence & JEV Governance

## Non-negotiable truth model

Every important claim must stay in one of these layers:

```text
RAW EVIDENCE
→ OBSERVED FACT
→ STRUCTURED CLASSIFICATION
→ INFERENCE
→ HYPOTHESIS
→ BUSINESS CONCLUSION
```

A downstream stage may reference an upstream stage, but it must not erase the distinction.

## Authoritative evidence requirements

A record cannot become authoritative merely because code sets `authoritative=true`.

It requires real capture proof such as:

- official/authorized API response receipt
- owner export file hash
- public page capture with URL + HTTP/final URL + HTML hash
- archived public snapshot with archive timestamp

`src/evidence/integrity.py` enforces this boundary.

Manual representative comments, generated transcripts, guessed metrics or developer-authored social posts are never authoritative evidence.

## JEV responsibility

JEV is the mandatory structured interpretation layer for provenance-valid evidence.

JEV may classify:

- brand identity signal
- business function
- sales/distribution channel
- customer intent
- complaint probability
- issue class
- possible process stage for investigation
- recruitment, territory, product and mobile-team signals

JEV does **not** prove ownership, revenue, staff counts, production sites, transport methods or root cause by itself.

## Authoritative JEV invariant

For production discovery:

```text
decision_engine = TYPESAFE_JEV
authoritative = true
model_resolved = actual live model
```

If live JEV fails, the authoritative interpretation stage fails closed. Deterministic fallback is test/development only and must remain non-authoritative.

## Discovery-only data

Browser history, project notes and other local-PC clues are useful for finding sources but are not automatically business facts.

Rules:

1. Local discovery result is stored separately.
2. JEV may rank/classify the lead.
3. `authoritative_for_business_truth=false` remains mandatory.
4. Public URLs must be recaptured by an evidence collector.
5. Only the recaptured source may enter authoritative analytics.

Legacy/provisional ABANGCOLEK reports are excluded from future local-PC discovery to avoid circular reasoning.

## Complaint and root-cause rule

A complaint describes an observed symptom, not necessarily its cause.

Example:

```text
Observed: leaking container complaint
JEV issue class: LEAKAGE
Possible process stage: hypothesis only
Root cause: UNDETERMINED
```

Production, packaging, transport, storage, agent handling or customer storage can only be promoted to a root cause when separate operational evidence supports that link.

## Media provenance

No transcript without real media bytes. No OCR without real pixels/frames. No visual description without actual media analysis.

If media is unavailable, the record must stay in a status such as `MEDIA_NOT_AVAILABLE`, `PENDING_ASR`, `PENDING_OCR` or `PENDING_VISION` instead of fabricating content.

## Snapshot deduplication

Forensic raw captures are immutable and all legitimate snapshots are retained. Classification and BI must not count the same source repeatedly simply because it was captured multiple times.

Current dedupe key:

```text
(platform, source_id/source_native_id, collector)
```

The latest snapshot is selected for JEV classification while older snapshots remain available for audit/history.

## Current verified counters

- Raw capture snapshots retained: 167
- Duplicate/repeat snapshots suppressed: 39
- Unique evidence classified: 128
- Live JEV decisions: 304
- Resolved JEV model: `jev-1.13.0`
- Synthetic authoritative records: 0

These values are operational counters, not claims that historical social coverage is complete.
