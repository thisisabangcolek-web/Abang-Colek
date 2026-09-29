"""Run maximum legitimate social backfill and emit auditable coverage."""
from __future__ import annotations
import json
from pathlib import Path
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.threads_adapter import ThreadsOfficialApiAdapter
from src.collectors.tiktok_adapter import TikTokOfficialApiAdapter
from src.collectors.owner_export_importer import OwnerExportImporter
from src.collectors.instagram_adapter import InstagramOfficialApiAdapter
from src.collectors.facebook_adapter import FacebookPagesApiAdapter

ROOT=Path('D:/ABANGCOLEK'); INBOX=ROOT/'data/owner_exports/inbox'; REPORT=ROOT/'reports/SOCIAL-BACKFILL-REPORT.md'
TERMS=['ABANGCOLEK','ABANG COLEK','STYLOAIRPOOL','AIRPOOLSTYLO','LIURLELEH','LIUR LELEH HOUSE','THE FAMOUS JERUX','JERUX']

def import_exports(tracker):
    importer=OwnerExportImporter(coverage=tracker); total=0
    for p in sorted(INBOX.glob('*')):
        if not p.is_file(): continue
        low=p.name.lower(); platform='tiktok' if 'tiktok' in low else 'threads' if 'threads' in low else 'instagram' if 'instagram' in low else 'facebook' if 'facebook' in low else 'unknown'
        try:
            rows=importer.import_zip(p,platform) if p.suffix.lower()=='.zip' else importer.import_json(p,platform) if p.suffix.lower()=='.json' else []
            total+=len(rows)
        except Exception as exc:
            tracker.register_source(platform,f'owner_export:{p.name}',CoverageStatus.ERROR,notes=str(exc)[:500],data_origin='OWNER_EXPORT')
    return total

def write_report(summary):
    lines=['# ABANGCOLEK Social Backfill Report','',f"Sources tracked: **{summary['total_sources']}**",'', '| Platform | Account/source | Status | Records | Posts | Replies | Oldest | Newest | Exhausted | Gaps |','|---|---|---|---:|---:|---:|---|---|---|---|']
    for s in summary['sources']:
        gaps='; '.join(s.get('known_gaps') or [])
        lines.append(f"| {s.get('platform','')} | {s.get('account') or s.get('source_name','')} | {s.get('status','')} | {s.get('record_count',0)} | {s.get('posts_recovered',0)} | {s.get('replies_recovered',0)} | {s.get('oldest_recovered_at') or ''} | {s.get('newest_recovered_at') or ''} | {s.get('pagination_exhausted',False)} | {gaps} |")
    lines += ['','## Rule','', 'A source is never described as complete beyond the scope actually exhausted. Missing OAuth/export data remains a coverage gap; it is never replaced with generated evidence.','']
    REPORT.write_text('\n'.join(lines),encoding='utf-8')

def main():
    tracker=CoverageTracker(); tracker.entries=[]; tracker._save(); import_exports(tracker)
    threads=ThreadsOfficialApiAdapter(coverage=tracker)
    try:
        threads.collect_user_posts('me',limit=50,collect_replies=True)
        if threads.access_token:
            for term in TERMS: threads.keyword_search(term,search_type='RECENT')
    except Exception: pass
    tiktok=TikTokOfficialApiAdapter(coverage=tracker)
    try: tiktok.collect_user_videos('styloairpool',limit=20)
    except Exception: pass
    instagram=InstagramOfficialApiAdapter(coverage=tracker)
    try: instagram.collect_all('instagram professional account')
    except Exception: pass
    facebook=FacebookPagesApiAdapter(coverage=tracker)
    try: facebook.collect_all_managed_pages()
    except Exception: pass
    summary=tracker.get_summary(); write_report(summary); print(json.dumps(summary,indent=2,ensure_ascii=False)); return summary

if __name__=='__main__': main()
