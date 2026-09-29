# Social Data Access Setup

## Position in the current architecture

Owner-authorized APIs are **optional enrichment**, not a hard dependency for ABANGCOLEK public discovery.

The project can already collect public evidence through no-key lanes. Authorization/export data is still valuable for scopes the public lane cannot prove, especially deleted/private history, full comments/replies, insights and account-native historical completeness.

Do not paste tokens into chat, source code, reports or logs.

## Environment variables

Use `C:\Users\megat\.env` or equivalent environment variables.

Optional platform enrichment:

- Threads: `THREADS_ACCESS_TOKEN` or `META_THREADS_ACCESS_TOKEN`
- TikTok: `TIKTOK_ACCESS_TOKEN` or `TIKTOK_DISPLAY_ACCESS_TOKEN`
- Instagram Professional: `INSTAGRAM_ACCESS_TOKEN` and optional `INSTAGRAM_USER_ID`
- Facebook Pages: `FACEBOOK_USER_ACCESS_TOKEN` or `META_USER_ACCESS_TOKEN`

Required for authoritative structured interpretation:

- TypeSafe JEV: `TYPESAFE_API_KEY`

## Owner exports

Place owner-downloaded ZIP/JSON exports in:

`D:\ABANGCOLEK\data\owner_exports\inbox\`

Where possible, include the platform name in the filename (`tiktok`, `threads`, `instagram`, `facebook`) so the importer can route it correctly.

Owner-export files are hashed and preserved as first-party evidence. They must not be merged invisibly with public data; their origin remains explicit.

## Access safety

Never use:

- CAPTCHA bypass
- stolen/decrypted cookies
- login circumvention
- IP/rate-limit evasion
- private data without owner authorization

A blocked source stays blocked and must appear as a coverage gap in `data\coverage\collection_manifest.json`.

See `NO-KEY-SOCIAL-COLLECTION.md` for the public collection architecture.
