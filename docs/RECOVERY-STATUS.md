# ABANGCOLEK Forensic Recovery Status

## Current gate — 2026-09-29
- Code integrity: PASS
- Tests: 33/33 PASS
- TypeSafe JEV connectivity: PASS (`jev-1.13.0`)
- Raw capture snapshots retained: 167 authoritative records
- Repeated capture snapshots suppressed from classification: 39
- Unique evidence classified by JEV: 128
- Authoritative live-JEV decisions: 304
- Synthetic contamination: 0 production records
- Digital Twin: BLOCKED pending broader historical coverage/internal discovery
- PRD: BLOCKED pending Digital Twin/internal validation

## No-key collection now working
- Threads `@airpoolstylo`: profile + 15 public post pages captured.
- Instagram `@airpoolstylo`: profile + 11 public post/reel pages captured.
- TikTok `@styloairpool`: 81 public post URLs accumulated from public-browser + local-history discovery.
- TikTok metadata: 79/81 URLs extracted by yt-dlp without platform API key; 2 URLs remain failed.
- TikTok photo fallback: 2 photo posts extracted by gallery-dl.
- Candidate Instagram `@abangcolek`: profile + 4 public posts captured; relationship remains evidence-led, not assumed official.
- Candidate Jerux reseller `@jeruxsliurlelehterengganu`: profile + 12 public posts captured.
- Official OAuth/API collectors remain optional enrichment, not a hard dependency.

## Local-PC discovery lane
- Current clean discovery set: 15 leads (9 sanitized browser-history URLs + 6 current project artifacts).
- Legacy/provisional ABANGCOLEK documents are excluded from future local discovery.
- All 15 leads were evaluated by live JEV `jev-1.13.0` as `DISCOVERY_ONLY`.
- Local-PC leads are never promoted directly to business facts; public URLs must be recaptured with provenance first.
- This lane surfaced one previously missing TikTok URL and two additional Instagram account/profile leads.

## Current JEV signal summary (deduplicated)
- Brands: ABANGCOLEK 21, JERUX 18, LIURLELEH 10, MULTI_BRAND 2, UNKNOWN 77.
- Business functions: DIRECT_SALES 46, MARKETING 43, EVENT 18, CUSTOMER_SERVICE 6, PRODUCTION 6, TRANSPORT 4, AGENT_MANAGEMENT 4, FINANCE 1.
- Complaint records flagged: 6; issue classes = LEAKAGE 2, TASTE 1, UNKNOWN 3.
- Signals: new variant 5, new territory 21, mobile team/pop-up 46, recruitment 12.

## Root-cause rule
A real captured complaint may be classified as `LEAKAGE`, but JEV must keep root cause `UNDETERMINED` until operational evidence links the incident to production, packaging, transport, storage, agent handling, or another stage.

## Current source-of-truth documents

Start with `README.md`.

- `ARCHITECTURE.md` — runtime/data architecture
- `EVIDENCE-JEV-GOVERNANCE.md` — truth/provenance/JEV rules
- `NO-KEY-SOCIAL-COLLECTION.md` — public no-key collection lanes
- `IMPLEMENTATION-IMPROVEMENTS.md` — recovery and improvements completed
- `ROADMAP.md` — next execution phases and product gates
- `../reports/SOCIAL-BACKFILL-REPORT.md` — source-by-source coverage

Recovery implementation lineage: `3f21bb2` → `7fc8241` → `0de5bda`.
Legacy/quarantine/forensic material is retained for audit but is not current business truth.
