# ABANGCOLEK Social Backfill Report

Sources tracked: **9**

| Platform | Account/source | Status | Records | Posts | Replies | Oldest | Newest | Exhausted | Gaps |
|---|---|---|---:|---:|---:|---|---|---|---|
| threads | @airpoolstylo | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | All owner-authorized Threads history; Replies and insights |
| tiktok | @styloairpool | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Authorized video history; Profile metadata; Comments are not exposed by Display API; Owner export required for lifetime/deleted data |
| instagram | instagram professional account | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Professional account media; Comments/replies; Profile metadata |
| facebook | managed pages | BLOCKED_AUTH | 0 | 0 | 0 |  |  | False | Managed Pages; Page posts; Comments/replies |
| threads | @airpoolstylo:public-browser | PARTIAL_UNKNOWN | 16 | 15 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| instagram | @airpoolstylo:public-browser | PARTIAL_UNKNOWN | 12 | 11 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| tiktok | @styloairpool:public-browser | PARTIAL_UNKNOWN | 1 | 0 | 0 |  |  | False | Public browser collection cannot prove deleted/private history completeness; Owner export/browser session may expose additional history |
| tiktok | @styloairpool:yt-dlp | PARTIAL_UNKNOWN | 78 | 78 | 0 | 2026-01-17T08:28:55+00:00 | 2026-09-26T04:47:18+00:00 | False | URL discovery derives from public profile scrolling and cannot prove deleted/private history completeness; Comments/replies require a separate browser/session collection lane; 2 discovered URLs failed metadata extraction |
| tiktok | @styloairpool:gallery-dl-photo | PARTIAL_PLATFORM_LIMIT | 2 | 2 | 0 |  |  | False | Only browser-discovered public photo posts are covered |

## Rule

A source is never described as complete beyond the scope actually exhausted. Missing OAuth/export data remains a coverage gap; it is never replaced with generated evidence.
