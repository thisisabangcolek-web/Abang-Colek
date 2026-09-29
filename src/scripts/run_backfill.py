"""Run maximum legitimate social backfill and emit auditable coverage."""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit
from src.config import DATA_DIR, OWNER_EXPORT_INBOX, PROJECT_ROOT, REPORTS_DIR
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.threads_adapter import ThreadsOfficialApiAdapter
from src.collectors.tiktok_adapter import TikTokOfficialApiAdapter
from src.collectors.owner_export_importer import OwnerExportImporter
from src.collectors.instagram_adapter import InstagramOfficialApiAdapter
from src.collectors.facebook_adapter import FacebookPagesApiAdapter
from src.collectors.browser_public_adapter import PublicBrowserCollector, collect_default_public_profiles
from src.collectors.tiktok_ytdlp_adapter import TikTokYtDlpAdapter
from src.collectors.tiktok_gallery_adapter import TikTokGalleryPhotoAdapter
from src.scripts.local_pc_discovery import main as run_local_pc_discovery
from src.scripts.run_local_discovery_jev import main as run_local_discovery_jev
from src.scripts.rebuild_pipeline import rebuild as rebuild_pipeline

ROOT=PROJECT_ROOT; INBOX=OWNER_EXPORT_INBOX; REPORT=REPORTS_DIR/'SOCIAL-BACKFILL-REPORT.md'
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

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--local-discovery",action="store_true",help="Explicitly allow redacted local-PC discovery and JEV classification")
    ap.add_argument("--skip-analysis",action="store_true",help="Collect only; do not rebuild authoritative JEV/BI/graph outputs")
    ap.add_argument("--dry-run",action="store_true",help="Show planned lanes without network calls or external JEV calls")
    args=ap.parse_args(argv)
    if args.dry_run:
        from src.collectors.http_utils import load_env_file
        import os
        load_env_file()
        plan={"network_calls":False,"local_discovery":bool(args.local_discovery),"analysis":not args.skip_analysis,
              "public_lanes":["threads_public_browser:@airpoolstylo","instagram_public_browser:@airpoolstylo","tiktok_public_browser:@styloairpool","tiktok_yt-dlp","tiktok_gallery-dl"],
              "owner_export_files":[p.name for p in sorted(INBOX.glob('*')) if p.is_file()],
              "official_auth_present":{"threads":bool(os.getenv('THREADS_ACCESS_TOKEN') or os.getenv('META_THREADS_ACCESS_TOKEN')),
                                      "tiktok":bool(os.getenv('TIKTOK_ACCESS_TOKEN') or os.getenv('TIKTOK_DISPLAY_ACCESS_TOKEN')),
                                      "instagram":bool(os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('META_USER_ACCESS_TOKEN')),
                                      "facebook":bool(os.getenv('FACEBOOK_USER_ACCESS_TOKEN') or os.getenv('META_USER_ACCESS_TOKEN')),
                                      "typesafe_jev":bool(os.getenv('TYPESAFE_API_KEY'))}}
        print(json.dumps(plan,indent=2)); return plan
    local_discovery={"status":"DISABLED","count":0}; local_jev={"status":"DISABLED","models":{}}; new_tiktok_seeds=0; local_profile_counts={}
    if args.local_discovery:
        local_discovery=run_local_pc_discovery(enabled=True); local_jev=run_local_discovery_jev(enabled=True); new_tiktok_seeds=merge_local_tiktok_seeds()
    tracker=CoverageTracker(); tracker.entries=[]; tracker._save()
    public_counts=asyncio.run(collect_default_public_profiles(tracker))
    if args.local_discovery: local_profile_counts=asyncio.run(collect_local_profile_leads(tracker))
    asyncio.run(TikTokYtDlpAdapter(coverage=tracker).collect_all()); asyncio.run(TikTokGalleryPhotoAdapter(coverage=tracker).collect_all())
    import_exports(tracker)
    threads=ThreadsOfficialApiAdapter(coverage=tracker)
    try:
        threads.collect_user_posts("me",limit=50,collect_replies=True)
        if threads.access_token:
            for term in TERMS: threads.keyword_search(term,search_type="RECENT")
    except Exception: pass
    for action in (lambda: TikTokOfficialApiAdapter(coverage=tracker).collect_user_videos("styloairpool",limit=20),
                   lambda: InstagramOfficialApiAdapter(coverage=tracker).collect_all("instagram professional account"),
                   lambda: FacebookPagesApiAdapter(coverage=tracker).collect_all_managed_pages()):
        try: action()
        except Exception: pass
    summary=tracker.get_summary()
    summary["local_pc_discovery"]={"enabled":args.local_discovery,"candidates":local_discovery.get("count",0),"jev_status":local_jev.get("status"),"jev_model_counts":local_jev.get("models",{}),"new_tiktok_seed_urls":new_tiktok_seeds,"public_profile_counts":public_counts,"local_profile_lead_counts":local_profile_counts,"authoritative_for_business_truth":False}
    analysis={"status":"SKIPPED"}
    if not args.skip_analysis:
        try:
            built=rebuild_pipeline(); analysis={"status":"ACTIVE","run_id":built["run_id"],"validation":built["validation"],"bi_status":built["bi"].get("status")}
        except Exception as exc:
            analysis={"status":"BLOCKED","error":str(exc)[:1000],"note":"Collection succeeded; previous active derived run remains unchanged."}
    summary["analysis_run"]=analysis; write_report(summary)
    with REPORT.open("a",encoding="utf-8") as f:
        f.write("\n## Atomic Analysis Run\n\n")
        f.write(f"- Status: **{analysis.get('status')}**\n")
        if analysis.get("run_id"): f.write(f"- Active run: **{analysis['run_id']}**\n")
        if analysis.get("error"): f.write(f"- Blocker: `{analysis['error']}`\n")
        f.write("- Rule: collection is preserved on JEV outage; derived business interpretation changes only after a fully validated atomic run.\n")
    print(json.dumps(summary,indent=2,ensure_ascii=False)); return summary

if __name__=="__main__": main()
