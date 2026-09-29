"""Build one internally consistent derived-data run and activate it atomically."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from src.analytics.bi_engine import BusinessIntelligenceEngine
from src.config import COVERAGE_FILE, DATA_DIR
from src.jev.batch_runner import JevBatchRunner
from src.knowledge.graph import KnowledgeGraph
from src.media.pipeline import MediaProcessor
from src.runs.manager import ProcessingRun
from src.validation.workflow import ensure_validation_templates
from src.workspace.builder import DiscoveryWorkspaceBuilder


def _read_json(path:Path,default):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception: return default

def _normalized_docs(directory:Path):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]

def validate_run(run:ProcessingRun,selected,jev,media,bi,graph,workspace)->dict:
    normalized=_normalized_docs(run.normalized_dir); norm_ids={x.get("normalized_id") for x in normalized}; capture_ids={x.get("capture_id") for x in normalized}
    decision_norm={d.get("normalized_id") for d in jev.get("decisions",[])}; decision_caps={d.get("capture_id") for d in jev.get("decisions",[])}
    checks={
        "jev_complete":jev.get("status")=="COMPLETE" and jev.get("decision_engine")=="TYPESAFE_JEV",
        "normalized_count_matches":jev.get("total_normalized_processed")==len(normalized)==jev.get("normalized_file_count"),
        "normalized_ids_unique":len(norm_ids)==len(normalized),
        "decision_lineage":decision_norm.issubset(norm_ids) and decision_caps.issubset(capture_ids),
        "normalized_run_matches":all(x.get("run_id")==run.run_id and x.get("input_fingerprint")==jev.get("input_fingerprint") for x in normalized),
        "media_run_matches":all(x.get("run_id")==run.run_id and x.get("input_fingerprint")==jev.get("input_fingerprint") for x in media),
        "bi_run_matches":bi.get("run_id")==run.run_id and bi.get("input_fingerprint")==jev.get("input_fingerprint"),
        "bi_lineage":bi.get("total_counts",{}).get("lineage_errors")==0,
        "graph_evidence_matches":graph.get("total_evidence")==len(selected),
        "graph_run_matches":graph.get("run_id")==run.run_id and graph.get("input_fingerprint")==jev.get("input_fingerprint"),
        "workspace_matches":workspace.get("sources")==len(normalized),
        "media_has_one_per_selected":len(media)==len(selected),
    }
    return {"valid":all(checks.values()),"checks":checks,"counts":{"selected":len(selected),"normalized":len(normalized),"decisions":jev.get("total_decisions",0),"media":len(media),"graph_evidence":graph.get("total_evidence",0)}}
def publish_compatibility(run:ProcessingRun)->dict:
    targets={
        "normalized":DATA_DIR/"normalized_v4",
        "decisions":DATA_DIR/"jev"/"live_decisions_v4.json",
        "media":DATA_DIR/"media_processed_v4.json",
        "bi":DATA_DIR/"analytics"/"bi_metrics_v4.json",
        "graph":DATA_DIR/"knowledge"/"abangcolek_v4.db",
        "workspace":DATA_DIR/"workspace_active",
    }
    tmp_norm=targets["normalized"].with_name(targets["normalized"].name+".tmp")
    if tmp_norm.exists(): shutil.rmtree(tmp_norm)
    shutil.copytree(run.normalized_dir,tmp_norm)
    if targets["normalized"].exists(): shutil.rmtree(targets["normalized"])
    tmp_norm.replace(targets["normalized"])
    for key,src in (("decisions",run.decisions_file),("media",run.media_file),("bi",run.bi_file),("graph",run.graph_file)):
        dst=targets[key]; dst.parent.mkdir(parents=True,exist_ok=True); tmp=dst.with_suffix(dst.suffix+".tmp"); shutil.copy2(src,tmp); tmp.replace(dst)
    for extra_dst in (DATA_DIR/"knowledge"/"abangcolek_v3.db",):
        extra_dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(run.graph_file, extra_dst)
    for extra_bi in (DATA_DIR/"analytics"/"bi_metrics_v2.json", DATA_DIR/"analytics"/"bi_metrics_v3.json"):
        extra_bi.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(run.bi_file, extra_bi)
    for extra_med in (DATA_DIR/"media_processed_v3.json",):
        extra_med.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(run.media_file, extra_med)
    tmp_ws=targets["workspace"].with_name(targets["workspace"].name+".tmp")
    if tmp_ws.exists(): shutil.rmtree(tmp_ws)
    shutil.copytree(run.workspace_dir,tmp_ws)
    if targets["workspace"].exists(): shutil.rmtree(targets["workspace"])
    tmp_ws.replace(targets["workspace"])
    return {k:str(v) for k,v in targets.items()}


def rebuild(*,publish:bool=True)->dict:
    ensure_validation_templates(); run=ProcessingRun()
    try:
        runner=JevBatchRunner(normalized_dir=run.normalized_dir,output_file=run.decisions_file,force_fallback=False)
        selected=runner.load_raw_sources(); hashes=[r["raw_hash"] for r in selected]
        fingerprint=ProcessingRun.fingerprint_hashes(hashes); run.set_input(fingerprint=fingerprint,selected_records=len(selected),total_captures=runner.total_raw_captures_loaded,raw_hashes=hashes)
        run.stage("select_evidence","PASS",selected=len(selected),total_captures=runner.total_raw_captures_loaded,duplicates=runner.duplicate_snapshots_suppressed,unusable=runner.unusable_captures_suppressed)
        jev=runner.run_all(run_id=run.run_id,raw_records=selected); run.stage("jev","PASS",decisions=jev.get("total_decisions"),normalized=jev.get("total_normalized_processed"),model_engine=jev.get("decision_engine")); run.artifact("jev_decisions",run.decisions_file)
        norm_manifest=run.root/"normalized_manifest.json"
        norm_entries=[]
        for nf in sorted(run.normalized_dir.glob("*.json")):
            norm_entries.append({"file":nf.name,"sha256":ProcessingRun._sha(nf),"size":nf.stat().st_size})
        norm_manifest.write_text(json.dumps({"run_id":run.run_id,"input_fingerprint":fingerprint,"count":len(norm_entries),"files":norm_entries},indent=2),encoding="utf-8")
        run.artifact("normalized_manifest",norm_manifest)
        media=MediaProcessor(output_file=run.media_file).process_records(selected,output_file=run.media_file,run_id=run.run_id,input_fingerprint=fingerprint); run.stage("media","PASS",assets=len(media),bytes_verified=sum(1 for x in media if x.get("media_status")=="BYTES_VERIFIED")); run.artifact("media",run.media_file)
        bi=BusinessIntelligenceEngine(normalized_dir=run.normalized_dir,decisions_file=run.decisions_file,metrics_file=run.bi_file,coverage_file=COVERAGE_FILE).run_all(); run.stage("bi","PASS",bi_status=bi.get("status"),counts=bi.get("total_counts")); run.artifact("bi",run.bi_file)
        kg=KnowledgeGraph(run.graph_file)
        try: graph=kg.build_from_verified_evidence(raw_records=selected,decisions_file=run.decisions_file,run_id=run.run_id,input_fingerprint=fingerprint)
        finally: kg.close()
        run.stage("knowledge_graph","PASS",**graph); run.artifact("knowledge_graph",run.graph_file)
        coverage=_read_json(COVERAGE_FILE,{"sources":[]}); normalized=_normalized_docs(run.normalized_dir)
        workspace=DiscoveryWorkspaceBuilder(run.workspace_dir).build(selected,normalized,jev,coverage,run.run_id); run.stage("workspace","PASS",**workspace)
        for name in ("source_library.json","claim_ledger.json","coverage_matrix.json","entity_review.json","interview_board.json","index.html","summary.json"):
            run.artifact(f"workspace_{name}",run.workspace_dir/name)
        validation=validate_run(run,selected,jev,media,bi,graph,workspace); run.stage("validation","PASS" if validation["valid"] else "FAIL",**validation)
        if not validation["valid"]: raise RuntimeError(f"Run validation failed: {validation}")
        compatibility={}
        if publish:
            try:
                compatibility=publish_compatibility(run); run.stage("compatibility_publish","PASS",targets=compatibility)
            except Exception as compat_exc:
                run.stage("compatibility_publish","WARNING",error=str(compat_exc)[:1000])
        pointer=run.activate(validation)
        return {"status":"ACTIVE","run_id":run.run_id,"pointer":pointer,"validation":validation,"bi":bi,"graph":graph,"workspace":workspace,"compatibility":compatibility}
    except Exception as exc:
        run.fail(exc); raise


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--no-publish",action="store_true",help="Activate run without compatibility mirrors"); args=ap.parse_args()
    result=rebuild(publish=not args.no_publish); print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
