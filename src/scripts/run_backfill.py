"""Run maximum legitimate social backfill and emit auditable coverage."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.threads_adapter import ThreadsOfficialApiAdapter
from src.collectors.tiktok_adapter import TikTokOfficialApiAdapter
from src.collectors.owner_export_importer import OwnerExportImporter
from src.collectors.instagram_adapter import InstagramOfficialApiAdapter
from src.collectors.facebook_adapter import FacebookPagesApiAdapter
from src.collectors.browser_public_adapter import PublicBrowserCollector, collect_default_public_profiles
from src.collectors.tiktok_ytdlp_adapter import TikTokYtDlpAdapter
from src.collectors.tiktok_gallery_adapter import TikTokGalleryPhotoAdapter
from src.jev.batch_runner import JevBatchRunner
from src.scripts.local_pc_discovery import main as run_local_pc_discovery
from src.scripts.run_local_discovery_jev import main as run_local_discovery_jev

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


def merge_local_tiktok_seeds():
    seeds_path=ROOT/'data/local_discovery/public_url_seeds.json'
    discovery_path=ROOT/'data/coverage/discovery/tiktok_styloairpool_public_urls.json'
    if not seeds_path.exists(): return 0
    seeds=json.loads(seeds_path.read_text(encoding='utf-8')).get('urls',[])
    eligible=[]
    for url in seeds:
        p=urlsplit(url)
        if p.netloc.lower().endswith('tiktok.com') and p.path.startswith('/@styloairpool/') and ('/video/' in p.path or '/photo/' in p.path):
            eligible.append(f'{p.scheme}://{p.netloc}{p.path}')
    if not eligible: return 0
    discovery_path.parent.mkdir(parents=True,exist_ok=True)
    data=json.loads(discovery_path.read_text(encoding='utf-8')) if discovery_path.exists() else {'urls':[]}
    before=set(data.get('urls',[])); merged=before|set(eligible)
    data['urls']=sorted(merged); data['count']=len(merged)
    data['source_note']='public browser discovery + sanitized local browser-history leads; every URL must be recaptured before business use'
    discovery_path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    return len(merged-before)


async def collect_local_profile_leads(tracker):
    seeds_path=ROOT/'data/local_discovery/public_url_seeds.json'
    if not seeds_path.exists(): return {}
    urls=json.loads(seeds_path.read_text(encoding='utf-8')).get('urls',[])
    handles=set()
    for url in urls:
        p=urlsplit(url)
        if p.netloc.lower().endswith('instagram.com'):
            parts=[x for x in p.path.split('/') if x]
            if parts and parts[0].lower() not in {'p','reel','explore'}:
                handles.add(parts[0])
    handles.discard('airpoolstylo')
    counts={}
    collector=PublicBrowserCollector(coverage=tracker)
    for handle in sorted(handles):
        rows=await collector.collect_profile('instagram',f'@{handle}',f'https://www.instagram.com/{handle}/',max_scrolls=60,stable_cycles=5,collect_post_pages=True,max_post_pages=30)
        counts[handle]=len(rows)
    return counts


def write_report(summary):
    lines=['# ABANGCOLEK Social Backfill Report','',f"Sources tracked: **{summary['total_sources']}**",'', '| Platform | Account/source | Status | Records | Posts | Replies | Oldest | Newest | Exhausted | Gaps |','|---|---|---|---:|---:|---:|---|---|---|---|']
    for s in summary['sources']:
        gaps='; '.join(s.get('known_gaps') or [])
        lines.append(f"| {s.get('platform','')} | {s.get('account') or s.get('source_name','')} | {s.get('status','')} | {s.get('record_count',0)} | {s.get('posts_recovered',0)} | {s.get('replies_recovered',0)} | {s.get('oldest_recovered_at') or ''} | {s.get('newest_recovered_at') or ''} | {s.get('pagination_exhausted',False)} | {gaps} |")
    lines += ['','## Rule','', 'A source is never described as complete beyond the scope actually exhausted. Missing OAuth/export data remains a coverage gap; it is never replaced with generated evidence.','']
    REPORT.write_text('\n'.join(lines),encoding='utf-8')

def main():
    local_discovery=run_local_pc_discovery()
    local_jev=run_local_discovery_jev()
    new_tiktok_seeds=merge_local_tiktok_seeds()
    tracker=CoverageTracker(); tracker.entries=[]; tracker._save()
    public_counts=asyncio.run(collect_default_public_profiles(tracker))
    local_profile_counts=asyncio.run(collect_local_profile_leads(tracker))
    asyncio.run(TikTokYtDlpAdapter(coverage=tracker).collect_all())
    asyncio.run(TikTokGalleryPhotoAdapter(coverage=tracker).collect_all())
    import_exports(tracker)
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
    # JEV is mandatory for authoritative interpretation. It is fail-closed: no silent fallback.
    jev_result = JevBatchRunner(force_fallback=False).run_all()
    summary=tracker.get_summary()
    summary['local_pc_discovery']={
        'candidates': local_discovery.get('count',0),
        'jev_status': local_jev.get('status'),
        'jev_model_counts': local_jev.get('models',{}),
        'new_tiktok_seed_urls': new_tiktok_seeds,
        'public_profile_counts': public_counts,
        'local_profile_lead_counts': local_profile_counts,
        'authoritative_for_business_truth': False,
    }
    summary['jev']={
        'status': jev_result.get('status'),
        'decision_engine': jev_result.get('decision_engine'),
        'total_raw_captures_loaded': jev_result.get('total_raw_captures_loaded',0),
        'duplicate_snapshots_suppressed': jev_result.get('duplicate_snapshots_suppressed',0),
        'total_raw_processed': jev_result.get('total_raw_processed',0),
        'total_decisions': jev_result.get('total_decisions',0),
    }
    write_report(summary)
    with REPORT.open('a',encoding='utf-8') as f:
        f.write('\n## Live JEV Gate\n\n')
        f.write(f"- Status: **{jev_result.get('status')}**\n")
        f.write(f"- Decision engine: **{jev_result.get('decision_engine')}**\n")
        f.write(f"- Raw capture snapshots loaded: **{jev_result.get('total_raw_captures_loaded',0)}**\n")
        f.write(f"- Repeat snapshots suppressed: **{jev_result.get('duplicate_snapshots_suppressed',0)}**\n")
        f.write(f"- Unique evidence processed: **{jev_result.get('total_raw_processed',0)}**\n")
        f.write(f"- Decisions: **{jev_result.get('total_decisions',0)}**\n")
        f.write('- Rule: authoritative interpretation requires live TypeSafe JEV; fallback decisions are rejected.\n')
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    return summary

if __name__=='__main__': main()
