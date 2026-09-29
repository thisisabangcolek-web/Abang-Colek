# ABANGCOLEK Social Backfill Report

Sources tracked: **11**

| Platform | Account/source | Status | Records | Posts | Replies | Oldest | Newest | Exhausted | Gaps |
|---|---|---|---:|---:|---:|---|---|---|---|
| threads | @airpoolstylo:public-browser | PARTIAL_UNKNOWN | 16 | 15 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| instagram | @airpoolstylo:public-browser | PARTIAL_UNKNOWN | 12 | 11 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| tiktok | @styloairpool:public-browser | PARTIAL_AUTH_LIMIT | 1 | 0 | 0 |  |  | False | Collection encountered platform challenge/block: SOMETHING_WENT_WRONG; Owner-controlled browser session may expose additional public/history content |
| instagram | @abangcolek:public-browser | PARTIAL_UNKNOWN | 5 | 4 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| instagram | @jeruxsliurlelehterengganu:public-browser | PARTIAL_UNKNOWN | 13 | 12 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| tiktok | @styloairpool:yt-dlp | PARTIAL_UNKNOWN | 79 | 79 | 0 | 2025-11-02T08:00:28+00:00 | 2026-09-26T04:47:18+00:00 | False | URL discovery derives from public profile scrolling and cannot prove deleted/private history completeness; Comments/replies require a separate browser/session collection lane; 2 discovered URLs failed metadata extraction |
| tiktok | @styloairpool:gallery-dl-photo | PARTIAL_PLATFORM_LIMIT | 2 | 2 | 0 |  |  | False | Only browser-discovered public photo posts are covered |
| threads | @airpoolstylo | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | All owner-authorized Threads history; Replies and insights |
| tiktok | @styloairpool | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Authorized video history; Profile metadata; Comments are not exposed by Display API; Owner export required for lifetime/deleted data |
| instagram | instagram professional account | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Professional account media; Comments/replies; Profile metadata |
| facebook | managed pages | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Managed Pages; Page posts; Comments/replies |

## Rule

A source is never described as complete beyond the scope actually exhausted. Missing OAuth/export data remains a coverage gap; it is never replaced with generated evidence.

## Local-PC Discovery Lane

- Clean discovery leads: **15** (9 sanitized browser-history URLs + 6 current project artifacts).
- Live discovery model: **jev-1.13.0**.
- Discovery results are **not authoritative business facts**; public URLs must be recaptured with provenance first.
- This lane surfaced additional public TikTok/Instagram leads that were recaptured by the normal collectors.

## Live JEV Gate

- Status: **COMPLETE**
- Decision engine: **TYPESAFE_JEV**
- Raw capture snapshots retained: **167**
- Repeat snapshots suppressed from classification: **39**
- Unique evidence processed: **128**
- Decisions: **304**
- Resolved model: **jev-1.13.0**
- Rule: authoritative interpretation requires live TypeSafe JEV; fallback decisions are rejected.
