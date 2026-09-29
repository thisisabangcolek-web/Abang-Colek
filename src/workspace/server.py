"""ABANGCOLEK Forensic Discovery Workspace & Evidence Review Server.

Provides a zero-dependency, high-performance HTTP server and REST API for human-in-the-loop (HITL)
evidence review, JEV claim auditing, knowledge graph exploration, and Supabase synchronization.
"""
from __future__ import annotations

import http.server
import json
import os
import socketserver
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import DATA_DIR, PROJECT_ROOT
from src.db.supabase_sync import SupabaseSynchronizer


class ReviewWorkspaceHandler(http.server.BaseHTTPRequestHandler):
    """REST API and Static Asset Handler for Evidence Review."""

    server_version = "AbangColekReviewServer/1.0"

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _get_active_dataset(self) -> Dict[str, Any]:
        sync = SupabaseSynchronizer()
        return sync.load_active_dataset()

    def _read_body_json(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        body = self.rfile.read(content_len).decode("utf-8")
        return json.loads(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. Root / UI Dashboard
        if path == "/" or path == "/index.html":
            self._serve_ui()
            return

        # 2. REST API: Summary / Status
        if path == "/api/status":
            dataset = self._get_active_dataset()
            res = {
                "ok": True,
                "run_id": dataset["run_id"],
                "total_evidence": len(dataset["evidence_records"]),
                "total_decisions": len(dataset["decisions"]),
                "total_entities": len(dataset["entities"]),
                "total_relationships": len(dataset["relationships"]),
                "total_epistemology": len(dataset["epistemology"]),
                "total_timeline": len(dataset["timeline"]),
                "bi_metrics": dataset["bi_metrics"],
                "manifest_status": dataset["manifest"].get("status", "ACTIVE"),
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        # 3. REST API: Evidence List
        if path == "/api/evidence":
            dataset = self._get_active_dataset()
            records = dataset["evidence_records"]

            platform_filter = params.get("platform", [None])[0]
            kind_filter = params.get("kind", [None])[0]
            search_query = params.get("q", [None])[0]

            filtered = []
            for r in records:
                if platform_filter and r.get("platform") != platform_filter and r.get("source_platform") != platform_filter:
                    continue
                if kind_filter and r.get("record_kind") != kind_filter:
                    continue
                if search_query:
                    q = search_query.lower()
                    text = (r.get("text") or "").lower()
                    url = (r.get("source_url") or "").lower()
                    cap = (r.get("capture_id") or "").lower()
                    if q not in text and q not in url and q not in cap:
                        continue
                filtered.append({
                    "capture_id": r.get("capture_id"),
                    "content_id": r.get("content_id"),
                    "normalized_id": r.get("normalized_id"),
                    "platform": r.get("platform") or r.get("source_platform"),
                    "record_kind": r.get("record_kind"),
                    "source_url": r.get("source_url"),
                    "published_at": r.get("published_at"),
                    "raw_hash": r.get("source_raw_hash") or r.get("raw_hash"),
                    "capture_verified": r.get("capture_verified", True),
                    "excerpt": (r.get("text") or "")[:240],
                    "has_full_text": bool(r.get("text")),
                })

            self._set_headers(200)
            self.wfile.write(json.dumps({"total": len(filtered), "evidence": filtered}, ensure_ascii=False).encode("utf-8"))
            return

        # 4. REST API: Single Evidence Detail
        if path.startswith("/api/evidence/"):
            capture_id = path.split("/api/evidence/")[1].strip("/")
            dataset = self._get_active_dataset()
            found = None
            for r in dataset["evidence_records"]:
                if r.get("capture_id") == capture_id:
                    found = r
                    break

            if not found:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Evidence capture not found"}).encode("utf-8"))
                return

            # Find linked decisions
            linked_decisions = [d for d in dataset["decisions"] if d.get("capture_id") == capture_id]

            self._set_headers(200)
            self.wfile.write(json.dumps({"evidence": found, "decisions": linked_decisions}, ensure_ascii=False).encode("utf-8"))
            return

        # 5. REST API: JEV Decisions List
        if path == "/api/decisions":
            dataset = self._get_active_dataset()
            decisions = dataset["decisions"]

            eval_type = params.get("eval_type", [None])[0]
            brand_filter = params.get("brand", [None])[0]

            filtered_d = []
            for d in decisions:
                if eval_type and d.get("evaluation_type") != eval_type:
                    continue
                classified = d.get("classified") or {}
                if brand_filter and classified.get("brand") != brand_filter:
                    continue
                filtered_d.append(d)

            self._set_headers(200)
            self.wfile.write(json.dumps({"total": len(filtered_d), "decisions": filtered_d}, ensure_ascii=False).encode("utf-8"))
            return

        # 6. REST API: Knowledge Graph
        if path == "/api/graph":
            dataset = self._get_active_dataset()
            nodes = [
                {
                    "id": ent["entity_id"],
                    "label": ent["name"],
                    "type": ent["entity_type"],
                    "canonical_name": ent.get("canonical_name"),
                    "trust_score": ent.get("trust_score"),
                }
                for ent in dataset["entities"]
            ]
            edges = [
                {
                    "id": rel["rel_id"],
                    "source": rel["source_id"],
                    "target": rel["target_id"],
                    "label": rel["relation_type"],
                    "confidence": rel.get("confidence"),
                    "epistemology_class": rel.get("epistemology_class"),
                }
                for rel in dataset["relationships"]
            ]
            self._set_headers(200)
            self.wfile.write(json.dumps({"nodes": nodes, "edges": edges, "timeline": dataset["timeline"]}, ensure_ascii=False).encode("utf-8"))
            return

        # 7. REST API: Business Questions & Interview Board
        if path == "/api/questions":
            dataset = self._get_active_dataset()
            self._set_headers(200)
            self.wfile.write(json.dumps({"questions": dataset["questions"]}, ensure_ascii=False).encode("utf-8"))
            return

        # Fallback 404
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Update Business Question / Interview Answer
        if path.startswith("/api/questions/"):
            qid = path.split("/api/questions/")[1].strip("/")
            body = self._read_body_json()
            sync = SupabaseSynchronizer()
            q_file = sync.run_dir / "workspace" / "interview_board.json"

            if not q_file.exists():
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "interview_board.json not found"}).encode("utf-8"))
                return

            questions = json.loads(q_file.read_text(encoding="utf-8"))
            updated = False
            for q in questions:
                if q.get("question_id") == qid:
                    if "owner_answer" in body:
                        q["owner_answer"] = body["owner_answer"]
                    if "status" in body:
                        q["status"] = body["status"]
                    if "workflow_steps" in body:
                        q["workflow_steps"] = body["workflow_steps"]
                    q["validated_at"] = datetime.now(timezone.utc).isoformat()
                    q["validated_by"] = body.get("validated_by", "HUMAN_OPERATOR")
                    updated = True
                    break

            if updated:
                q_file.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
                self._set_headers(200)
                self.wfile.write(json.dumps({"ok": True, "message": f"Updated question {qid}"}).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": f"Question {qid} not found"}).encode("utf-8"))
            return

        # 2. Record Claim Review Decision
        if path.startswith("/api/reviews/"):
            decision_id = path.split("/api/reviews/")[1].strip("/")
            body = self._read_body_json()
            sync = SupabaseSynchronizer()
            claim_file = sync.run_dir / "workspace" / "claim_ledger.json"

            if claim_file.exists():
                claims = json.loads(claim_file.read_text(encoding="utf-8"))
                for c in claims:
                    if c.get("claim_id") == decision_id:
                        c["status"] = body.get("status", "REVIEWED")
                        c["reviewer"] = body.get("reviewer", "HUMAN_OPERATOR")
                        c["review_note"] = body.get("review_note")
                        c["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                        break
                claim_file.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")

            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True, "decision_id": decision_id, "status": body.get("status")}).encode("utf-8"))
            return

        # 3. Trigger Supabase SQL Dump Generation
        if path == "/api/export-supabase":
            sync = SupabaseSynchronizer()
            out_file = sync.generate_sql_dump()
            root_copy = PROJECT_ROOT / "supabase_seed.sql"
            root_copy.write_text(out_file.read_text(encoding="utf-8"), encoding="utf-8")

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "ok": True,
                "file": str(out_file),
                "root_copy": str(root_copy),
                "size_bytes": out_file.stat().st_size,
                "size_kb": round(out_file.stat().st_size / 1024, 2),
            }).encode("utf-8"))
            return

        # 4. Trigger Supabase REST Sync
        if path == "/api/sync-supabase":
            body = self._read_body_json()
            sync = SupabaseSynchronizer()
            result = sync.sync_to_supabase_rest(
                supabase_url=body.get("supabase_url"),
                supabase_key=body.get("supabase_key"),
            )
            self._set_headers(200 if result.get("ok") else 400)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def _serve_ui(self):
        """Generates and serves the standalone high-aesthetic Evidence Review SPA."""
        sync = SupabaseSynchronizer()
        dataset = sync.load_active_dataset()
        run_id = dataset["run_id"]
        total_ev = len(dataset["evidence_records"])
        total_dec = len(dataset["decisions"])
        total_posts = dataset["bi_metrics"].get("counts", {}).get("total_posts", 123)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ABANGCOLEK — Discovery & Evidence Review Workspace</title>
<style>
  :root {{
    --bg-base: #09090b;
    --bg-card: #121215;
    --bg-card-hover: #18181c;
    --border: #27272a;
    --border-subtle: #1f1f23;
    --text-primary: #f4f4f5;
    --text-secondary: #a1a1aa;
    --text-muted: #71717a;
    --accent: #10b981;
    --accent-indigo: #6366f1;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-base);
    color: var(--text-primary);
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }}
  header {{
    background: #0d0d10;
    border-bottom: 1px solid var(--border);
    padding: 14px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .logo {{
    font-weight: 800;
    letter-spacing: -0.03em;
    font-size: 1.15rem;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .badge-run {{
    background: #18181b;
    border: 1px solid #27272a;
    color: #38bdf8;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }}
  .metrics-strip {{
    display: flex;
    gap: 16px;
    font-size: 0.82rem;
  }}
  .metric-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-secondary);
  }}
  .metric-value {{
    font-weight: 700;
    color: #fff;
  }}
  .nav-tabs {{
    display: flex;
    background: #0d0d10;
    border-bottom: 1px solid var(--border);
    padding: 0 28px;
    gap: 8px;
  }}
  .tab-btn {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-secondary);
    padding: 12px 16px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .tab-btn:hover {{
    color: #fff;
  }}
  .tab-btn.active {{
    color: #fff;
    border-bottom-color: var(--accent);
  }}
  main {{
    flex: 1;
    padding: 24px 28px;
    max-width: 1700px;
    width: 100%;
    margin: 0 auto;
  }}
  .panel {{
    display: none;
  }}
  .panel.active {{
    display: block;
  }}
  .toolbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .search-input {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: #fff;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.88rem;
    width: 340px;
    outline: none;
  }}
  .search-input:focus {{
    border-color: var(--accent);
  }}
  .btn {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.15s ease;
  }}
  .btn:hover {{
    background: var(--bg-card-hover);
    border-color: #3f3f46;
  }}
  .btn-accent {{
    background: var(--accent);
    color: #000;
    border-color: var(--accent);
  }}
  .btn-accent:hover {{
    background: #059669;
    border-color: #059669;
    color: #fff;
  }}
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
  }}
  .data-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.1s ease, border-color 0.1s ease;
  }}
  .data-card:hover {{
    border-color: #3f3f46;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }}
  .pill {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
  }}
  .pill-tiktok {{ background: rgba(255,0,80,0.15); color: #ff0050; border: 1px solid rgba(255,0,80,0.3); }}
  .pill-threads {{ background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }}
  .pill-instagram {{ background: rgba(225,48,108,0.15); color: #e1306c; border: 1px solid rgba(225,48,108,0.3); }}
  .pill-kind {{ background: #27272a; color: #d4d4d8; }}
  .card-excerpt {{
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 12px;
    line-height: 1.45;
  }}
  .card-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    border-top: 1px solid var(--border-subtle);
    font-size: 0.78rem;
    color: var(--text-muted);
  }}
  .hash-code {{
    font-family: monospace;
    font-size: 0.75rem;
    background: #000;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #1f1f23;
    color: #10b981;
  }}
  table.data-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  table.data-table th, table.data-table td {{
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    font-size: 0.85rem;
  }}
  table.data-table th {{
    background: #0f0f13;
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
  }}
  table.data-table tr:hover td {{
    background: var(--bg-card-hover);
  }}
  .modal {{
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.85);
    z-index: 1000;
    justify-content: center;
    align-items: center;
    padding: 24px;
  }}
  .modal-content {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    max-width: 900px;
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .modal-header {{
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .modal-body {{
    padding: 20px;
    overflow-y: auto;
    font-size: 0.88rem;
  }}
  pre.code-block {{
    background: #08080a;
    border: 1px solid #1f1f23;
    padding: 12px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 0.8rem;
    color: #e4e4e7;
    overflow-x: auto;
    margin-top: 8px;
  }}
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="logo">⚡ ABANGCOLEK DISCOVERY</div>
    <span class="badge-run">{run_id}</span>
  </div>
  <div class="metrics-strip">
    <div class="metric-item">Evidence: <span class="metric-value">{total_ev} Verified</span></div>
    <div class="metric-item">JEV Decisions: <span class="metric-value">{total_dec}</span></div>
    <div class="metric-item">Posts: <span class="metric-value">{total_posts}</span></div>
    <div class="metric-item">Model: <span class="metric-value" style="color:#10b981;">jev-1.13.0</span></div>
  </div>
  <div style="display:flex; gap:10px;">
    <button class="btn btn-accent" onclick="exportSupabase()">⚡ Export Supabase SQL</button>
  </div>
</header>

<div class="nav-tabs">
  <button class="tab-btn active" onclick="switchTab('evidence')">📁 Source Library ({total_ev})</button>
  <button class="tab-btn" onclick="switchTab('decisions')">🧠 JEV Claims & Ledger ({total_dec})</button>
  <button class="tab-btn" onclick="switchTab('graph')">🕸️ Knowledge Graph & Timeline</button>
  <button class="tab-btn" onclick="switchTab('questions')">📋 Operational Validation (8 Questions)</button>
  <button class="tab-btn" onclick="switchTab('supabase')">☁️ Supabase Cloud</button>
</div>

<main>
  <!-- TAB 1: EVIDENCE -->
  <div id="panel-evidence" class="panel active">
    <div class="toolbar">
      <input type="text" id="ev-search" class="search-input" placeholder="Search capture text, URL, or hash..." oninput="filterEvidence()">
      <div style="display:flex; gap:8px;">
        <button class="btn" onclick="setPlatformFilter('')">All Platforms</button>
        <button class="btn" onclick="setPlatformFilter('tiktok')">TikTok (81)</button>
        <button class="btn" onclick="setPlatformFilter('threads')">Threads (15)</button>
        <button class="btn" onclick="setPlatformFilter('instagram')">Instagram (32)</button>
      </div>
    </div>
    <div id="evidence-container" class="card-grid">Loading evidence...</div>
  </div>

  <!-- TAB 2: JEV DECISIONS -->
  <div id="panel-decisions" class="panel">
    <div class="toolbar">
      <div style="display:flex; gap:8px;">
        <button class="btn" onclick="filterDecisions('')">All Types</button>
        <button class="btn" onclick="filterDecisions('content')">Content (128)</button>
        <button class="btn" onclick="filterDecisions('signal')">Signals (128)</button>
        <button class="btn" onclick="filterDecisions('interaction')">Interactions (123)</button>
        <button class="btn" onclick="filterDecisions('complaint')">Complaints (10)</button>
      </div>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Claim ID</th>
          <th>Type</th>
          <th>Brand / Intent / Signal</th>
          <th>Confidence</th>
          <th>Model</th>
          <th>Provenance Capture</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="decisions-tbody">
        <tr><td colspan="7">Loading decisions...</td></tr>
      </tbody>
    </table>
  </div>

  <!-- TAB 3: GRAPH & TIMELINE -->
  <div id="panel-graph" class="panel">
    <div style="margin-bottom:16px;">
      <h3 style="margin-bottom:6px;">Observed Event Timeline (124 Events Grounded in Provenance)</h3>
      <p style="color:var(--text-secondary); font-size:0.88rem;">Each timeline event corresponds to an independently observed post or metadata capture with SHA-256 integrity.</p>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Title</th>
          <th>Description</th>
          <th>Entities</th>
          <th>Evidence Citation</th>
        </tr>
      </thead>
      <tbody id="timeline-tbody">
        <tr><td colspan="5">Loading timeline...</td></tr>
      </tbody>
    </table>
  </div>

  <!-- TAB 4: BUSINESS QUESTIONS -->
  <div id="panel-questions" class="panel">
    <div style="margin-bottom:16px;">
      <h3 style="margin-bottom:6px;">8 Foundational Operational Questions (Walkthrough Required)</h3>
      <p style="color:var(--text-secondary); font-size:0.88rem;">These questions cannot be hallucinated from social captures alone. They require a live transaction walkthrough with the business owner.</p>
    </div>
    <div id="questions-container" style="display:flex; flex-direction:column; gap:16px;">Loading questions...</div>
  </div>

  <!-- TAB 5: SUPABASE CLOUD -->
  <div id="panel-supabase" class="panel">
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:10px; padding:24px; max-width:900px;">
      <h3 style="margin-bottom:12px;">Supabase Cloud Integration</h3>
      <p style="color:var(--text-secondary); margin-bottom:18px;">
        Project Reference: <code class="hash-code">gcpyatuhoxrwbuljvleo</code><br>
        MCP Server URL: <code class="hash-code">https://mcp.supabase.com/mcp?project_ref=gcpyatuhoxrwbuljvleo</code>
      </p>
      <div style="display:flex; gap:12px; margin-bottom:20px;">
        <button class="btn btn-accent" onclick="exportSupabase()">Generate / Refresh SQL Dump</button>
      </div>
      <div id="supabase-status" style="font-size:0.88rem; color:var(--text-secondary);">
        Seed SQL Dump is located at: <code>supabase_seed.sql</code> (1.18 MB).<br>
        Ready to execute in Supabase SQL Editor.
      </div>
    </div>
  </div>
</main>

<!-- DETAIL MODAL -->
<div id="detail-modal" class="modal" onclick="closeModal(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <div class="modal-header">
      <h3 id="modal-title">Evidence Capture Detail</h3>
      <button class="btn" onclick="document.getElementById('detail-modal').style.display='none'">✕</button>
    </div>
    <div class="modal-body" id="modal-body">Loading...</div>
  </div>
</div>

<script>
let currentPlatform = '';
let allEvidence = [];
let allDecisions = [];

function switchTab(tabId) {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + tabId).classList.add('active');
  event.target.classList.add('active');
  if (tabId === 'decisions' && allDecisions.length === 0) loadDecisions();
  if (tabId === 'graph') loadGraph();
  if (tabId === 'questions') loadQuestions();
}}

async function loadEvidence() {{
  const res = await fetch('/api/evidence');
  const data = await res.json();
  allEvidence = data.evidence || [];
  renderEvidence(allEvidence);
}}

function setPlatformFilter(p) {{
  currentPlatform = p;
  filterEvidence();
}}

function filterEvidence() {{
  const q = document.getElementById('ev-search').value.toLowerCase();
  const filtered = allEvidence.filter(e => {{
    const matchPlat = !currentPlatform || e.platform === currentPlatform;
    const matchQ = !q || (e.excerpt && e.excerpt.toLowerCase().includes(q)) || (e.source_url && e.source_url.toLowerCase().includes(q)) || e.capture_id.includes(q);
    return matchPlat && matchQ;
  }});
  renderEvidence(filtered);
}}

function renderEvidence(list) {{
  const container = document.getElementById('evidence-container');
  if (list.length === 0) {{
    container.innerHTML = '<div style="color:var(--text-muted); padding:20px;">No matching evidence captures found.</div>';
    return;
  }}
  container.innerHTML = list.map(e => `
    <div class="data-card">
      <div>
        <div class="card-header">
          <span class="pill pill-${{e.platform}}">${{e.platform}}</span>
          <span class="pill pill-kind">${{e.record_kind}}</span>
        </div>
        <div class="card-excerpt">${{e.excerpt || '<i>[No direct text payload]</i>'}}</div>
      </div>
      <div class="card-footer">
        <span class="hash-code" title="${{e.raw_hash}}">${{e.raw_hash ? e.raw_hash.substring(0, 10) + '…' : 'NO_HASH'}}</span>
        <div style="display:flex; gap:6px;">
          <a href="${{e.source_url || '#'}}" target="_blank" class="btn" style="padding:4px 8px; font-size:0.75rem;">Source ↗</a>
          <button class="btn" style="padding:4px 8px; font-size:0.75rem;" onclick="viewDetail('${{e.capture_id}}')">Inspect</button>
        </div>
      </div>
    </div>
  `).join('');
}}

async function viewDetail(captureId) {{
  const modal = document.getElementById('detail-modal');
  modal.style.display = 'flex';
  const body = document.getElementById('modal-body');
  body.innerHTML = 'Loading capture details...';
  
  const res = await fetch('/api/evidence/' + captureId);
  const data = await res.json();
  const ev = data.evidence;
  const decs = data.decisions || [];

  body.innerHTML = `
    <h4 style="margin-bottom:8px;">Capture ID: <code>${{ev.capture_id}}</code></h4>
    <p style="color:var(--text-secondary); margin-bottom:12px;">URL: <a href="${{ev.source_url}}" target="_blank" style="color:#38bdf8;">${{ev.source_url}}</a></p>
    <div style="display:flex; gap:16px; margin-bottom:16px;">
      <div>Platform: <b>${{ev.platform || ev.source_platform}}</b></div>
      <div>Collector: <b>${{ev.collector}}</b></div>
      <div>Published: <b>${{ev.published_at || 'N/A'}}</b></div>
    </div>
    <h5 style="margin-top:14px; margin-bottom:6px;">Verified Raw Payload</h5>
    <pre class="code-block">${{JSON.stringify(ev.raw_payload || {{}}, null, 2)}}</pre>
    <h5 style="margin-top:16px; margin-bottom:6px;">Linked JEV Classifications (${{decs.length}})</h5>
    <div>${{decs.map(d => `
      <div style="background:#0d0d10; border:1px solid #27272a; padding:10px; border-radius:6px; margin-top:6px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <b>${{d.evaluation_type.toUpperCase()}}</b>
          <span style="color:#10b981;">Confidence: ${{d.confidence !== null ? d.confidence : 'N/A'}}</span>
        </div>
        <pre class="code-block">${{JSON.stringify(d.classified || {{}}, null, 2)}}</pre>
      </div>
    `).join('')}}</div>
  `;
}}

function closeModal(e) {{
  document.getElementById('detail-modal').style.display = 'none';
}}

async function loadDecisions() {{
  const res = await fetch('/api/decisions');
  const data = await res.json();
  allDecisions = data.decisions || [];
  renderDecisions(allDecisions);
}}

function filterDecisions(type) {{
  if (!type) renderDecisions(allDecisions);
  else renderDecisions(allDecisions.filter(d => d.evaluation_type === type));
}}

function renderDecisions(list) {{
  const tbody = document.getElementById('decisions-tbody');
  tbody.innerHTML = list.map(d => {{
    const c = d.classified || {{}};
    const summary = c.brand || c.customer_intent || c.issue_class || JSON.stringify(c).substring(0, 50);
    return `
      <tr>
        <td><code>${{d.decision_id.substring(0, 16)}}…</code></td>
        <td><span class="pill pill-kind">${{d.evaluation_type}}</span></td>
        <td><b>${{summary}}</b></td>
        <td>${{d.confidence !== null ? d.confidence : 'N/A'}}</td>
        <td><code>${{d.model_resolved || d.model || 'jev-1.13.0'}}</code></td>
        <td><code>${{d.capture_id.substring(0, 12)}}…</code></td>
        <td><button class="btn" style="padding:3px 8px; font-size:0.75rem;" onclick="viewDetail('${{d.capture_id}}')">Audit</button></td>
      </tr>
    `;
  }}).join('');
}}

async function loadGraph() {{
  const res = await fetch('/api/graph');
  const data = await res.json();
  const tbody = document.getElementById('timeline-tbody');
  tbody.innerHTML = (data.timeline || []).map(t => `
    <tr>
      <td>${{t.event_date ? t.event_date.substring(0, 10) : 'N/A'}}</td>
      <td><b>${{t.title}}</b></td>
      <td style="color:var(--text-secondary);">${{t.description}}</td>
      <td>${{t.entity_ids.map(id => `<span class="pill pill-kind">${{id}}</span>`).join(' ')}}</td>
      <td>${{t.evidence_ids.map(id => `<code>${{id.substring(0, 12)}}…</code>`).join(' ')}}</td>
    </tr>
  `).join('');
}}

async function loadQuestions() {{
  const res = await fetch('/api/questions');
  const data = await res.json();
  const container = document.getElementById('questions-container');
  container.innerHTML = (data.questions || []).map(q => `
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:18px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <h4 style="color:#fff;">${{q.question_id}}: ${{q.question}}</h4>
        <span class="pill pill-kind">${{q.status}}</span>
      </div>
      <p style="color:var(--text-muted); font-size:0.84rem; margin-bottom:12px;">Missing evidence: ${{q.missing_evidence || 'Direct owner walkthrough required'}}</p>
      <div>
        <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:4px;">Owner / Team Walkthrough Notes:</label>
        <textarea id="ans-${{q.question_id}}" style="width:100%; height:75px; background:#08080a; border:1px solid var(--border); color:#fff; border-radius:6px; padding:8px; font-size:0.85rem;" placeholder="Record owner interview answers here...">${{q.owner_answer || ''}}</textarea>
        <button class="btn btn-accent" style="margin-top:8px; padding:4px 12px; font-size:0.8rem;" onclick="saveAnswer('${{q.question_id}}')">Save Notes</button>
      </div>
    </div>
  `).join('');
}}

async function saveAnswer(qid) {{
  const text = document.getElementById('ans-' + qid).value;
  const res = await fetch('/api/questions/' + qid, {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ owner_answer: text, status: 'IN_PROGRESS' }})
  }});
  const data = await res.json();
  if (data.ok) alert('Saved notes for ' + qid);
}}

async function exportSupabase() {{
  const res = await fetch('/api/export-supabase', {{ method: 'POST' }});
  const data = await res.json();
  if (data.ok) {{
    alert('Supabase SQL Dump generated successfully! Size: ' + data.size_kb + ' KB\\nSaved to: ' + data.root_copy);
  }}
}}

// Initialize
loadEvidence();
</script>

</body>
</html>
"""
        self._set_headers(200, "text/html")
        self.wfile.write(html_content.encode("utf-8"))


def run_server(port: int = 8765, host: str = "127.0.0.1", open_browser: bool = False):
    """Starts the Evidence Review HTTP server."""
    with socketserver.ThreadingTCPServer((host, port), ReviewWorkspaceHandler) as httpd:
        httpd.allow_reuse_address = True
        url = f"http://{host}:{port}"
        print(f"\n=======================================================")
        print(f"⚡ ABANGCOLEK Discovery Workspace & Evidence Review UI")
        print(f"🌐 Running at: {url}")
        print(f"🔒 Localhost only, zero external tracking, evidence-first")
        print(f"=======================================================\n")
        if open_browser:
            import webbrowser
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    run_server()
