"""Comprehensive tests for Supabase PostgreSQL sync, Evidence Review Server, and CLI."""
from __future__ import annotations

import json
import socket
import threading
import time
import urllib.request
from pathlib import Path
import pytest

from src.config import DATA_DIR, PROJECT_ROOT
from src.db.supabase_sync import SupabaseSynchronizer
from src.workspace.server import ReviewWorkspaceHandler, socketserver


def test_supabase_synchronizer_dataset_integrity():
    """Verify that SupabaseSynchronizer correctly compiles all 128 evidence, 389 decisions, and graph entities."""
    sync = SupabaseSynchronizer()
    dataset = sync.load_active_dataset()

    assert dataset["run_id"].startswith("run_")
    assert len(dataset["evidence_records"]) == 128
    assert len(dataset["decisions"]) == 389
    assert len(dataset["entities"]) == 131
    assert len(dataset["relationships"]) == 128
    assert len(dataset["epistemology"]) == 389
    assert len(dataset["timeline"]) == 124
    assert len(dataset["questions"]) == 8
    counts = dataset["bi_metrics"].get("total_counts") or dataset["bi_metrics"].get("counts", {})
    assert counts.get("total_posts") == 123


def test_supabase_sql_dump_generation(tmp_path):
    """Verify that generate_sql_dump produces valid, non-empty PostgreSQL / Supabase seed script."""
    sync = SupabaseSynchronizer()
    out_file = tmp_path / "test_supabase_seed.sql"
    res_path = sync.generate_sql_dump(output_path=out_file)

    assert res_path.exists()
    assert res_path.stat().st_size > 500_000  # Over 500 KB of SQL statements

    content = res_path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.evidence_records" in content
    assert "CREATE TABLE IF NOT EXISTS public.jev_decisions" in content
    assert "ALTER TABLE public.evidence_records ENABLE ROW LEVEL SECURITY" in content
    assert "INSERT INTO public.processing_runs" in content
    assert "INSERT INTO public.evidence_records" in content
    assert "INSERT INTO public.jev_decisions" in content
    assert "BEGIN;" in content
    assert "COMMIT;" in content


@pytest.fixture(scope="module")
def review_server():
    """Spins up an in-memory background instance of ReviewWorkspaceHandler for HTTP testing."""
    # Find an open port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), ReviewWorkspaceHandler)
    server.allow_reuse_address = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()


def test_review_server_endpoints(review_server):
    """Test all GET and POST endpoints of the Evidence Review server."""
    base_url = review_server

    # 1. UI Root
    with urllib.request.urlopen(f"{base_url}/") as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "ABANGCOLEK" in html
        assert "Source Library" in html

    # 2. Status API
    with urllib.request.urlopen(f"{base_url}/api/status") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["ok"] is True
        assert data["total_evidence"] == 128
        assert data["total_decisions"] == 389

    # 3. Evidence API
    with urllib.request.urlopen(f"{base_url}/api/evidence") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["total"] == 128
        assert len(data["evidence"]) == 128

    # 4. Evidence Filter by Platform
    with urllib.request.urlopen(f"{base_url}/api/evidence?platform=tiktok") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["total"] == 82

    # 5. Decisions API
    with urllib.request.urlopen(f"{base_url}/api/decisions") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["total"] == 389

    # 6. Graph API
    with urllib.request.urlopen(f"{base_url}/api/graph") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data["nodes"]) == 131
        assert len(data["edges"]) == 128
        assert len(data["timeline"]) == 124

    # 7. Questions API
    with urllib.request.urlopen(f"{base_url}/api/questions") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data["questions"]) == 8

    # 8. Export Supabase SQL Trigger
    req = urllib.request.Request(f"{base_url}/api/export-supabase", data=b"{}", method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["ok"] is True
        assert data["size_kb"] > 500


def test_cli_commands():
    """Test CLI commands execution."""
    from src.cli import cmd_status
    import argparse

    args = argparse.Namespace()
    assert cmd_status(args) == 0
