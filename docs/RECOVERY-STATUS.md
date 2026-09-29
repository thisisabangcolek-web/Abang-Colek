# ABANGCOLEK Forensic Recovery Status

## Current gate
- Code integrity: PASS
- Tests: 29/29 PASS
- TypeSafe JEV connectivity: PASS (`jev-1.13.0` resolved during live check)
- Production raw evidence: 0 authoritative records
- Social backfill: BLOCKED_AUTH on Threads, TikTok, Instagram, Facebook
- Digital Twin: BLOCKED
- PRD: BLOCKED

## What was repaired
1. Synthetic/manual evidence can no longer self-mark as authoritative.
2. Old fake/manual records and derived outputs were quarantined.
3. JEV authoritative path is fail-closed; deterministic fallback is test/dev only.
4. BI reads only clean raw/normalized/live-JEV paths and invents no minimum counts/eras/variants.
5. Media analysis cannot emit transcript/OCR/vision claims without actual media bytes.
6. Knowledge Graph is rebuilt from evidence only; hard-coded business facts are disabled.
7. Threads, TikTok, Instagram and Facebook official collectors now have pagination/coverage handling.
8. Owner-export importer hashes the source archive/member and records provenance.
9. Legacy PRD/Digital Twin/specifications are archived and current paths are gated.

## Remaining external blockers
The app cannot lawfully recover owner-account history until account authorization or owner exports are provided. Missing access is recorded as a coverage gap and is never replaced with generated data.

## Run order after access is available
```powershell
cd D:\ABANGCOLEK
python -m src.scripts.run_backfill
python -m src.jev.batch_runner
python -c "from src.media.pipeline import MediaProcessor; MediaProcessor().process_all_sources()"
python -m src.knowledge.graph
python -m src.analytics.bi_engine
python -m src.scripts.verify_integrity
pytest -q
```
