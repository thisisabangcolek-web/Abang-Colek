# Social Data Access Setup

Do not paste tokens into chat, source code, reports or logs.

## Environment variables
Copy `.env.example` to `C:\Users\megat\.env` or add the same keys to the environment.

Required for owner-authorized API collection:
- Threads: `THREADS_ACCESS_TOKEN` (or `META_THREADS_ACCESS_TOKEN`)
- TikTok: `TIKTOK_ACCESS_TOKEN` (or `TIKTOK_DISPLAY_ACCESS_TOKEN`)
- Instagram Professional: `INSTAGRAM_ACCESS_TOKEN` plus optional `INSTAGRAM_USER_ID`
- Facebook Pages: `FACEBOOK_USER_ACCESS_TOKEN` (or `META_USER_ACCESS_TOKEN`)
- TypeSafe JEV: `TYPESAFE_API_KEY`

## Owner exports
Put owner-downloaded ZIP/JSON exports in:
`D:\ABANGCOLEK\data\owner_exports\inbox\`

Filename should contain the platform name where possible (`tiktok`, `threads`, `instagram`, `facebook`) so the importer can classify it.

## Safety rule
Never use CAPTCHA bypass, stolen cookies, login circumvention, IP/rate-limit evasion, or private data without owner authorization. A blocked source stays blocked and appears in `data\coverage\collection_manifest.json`.
