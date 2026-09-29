"""Central ABANGCOLEK runtime settings.

All paths are derived from ABANGCOLEK_ROOT or the repository location.  No
production module should hard-code a user profile or drive letter.
"""
from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.getenv("ABANGCOLEK_ROOT", PACKAGE_ROOT.parent)).resolve()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RUNS_DIR = DATA_DIR / "runs"
ACTIVE_RUN_FILE = DATA_DIR / "active_run.json"
COVERAGE_FILE = DATA_DIR / "coverage" / "collection_manifest.json"
OWNER_EXPORT_INBOX = DATA_DIR / "owner_exports" / "inbox"
REPORTS_DIR = PROJECT_ROOT / "reports"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"

LOCAL_DISCOVERY_ENABLED = os.getenv("ABANGCOLEK_LOCAL_DISCOVERY", "0").lower() in {"1", "true", "yes"}
LOCAL_DISCOVERY_ROOTS = [
    Path(x).expanduser().resolve()
    for x in os.getenv("ABANGCOLEK_LOCAL_DISCOVERY_ROOTS", "").split(os.pathsep)
    if x.strip()
]

NORMALIZER_VERSION = "4.0.0"
RUN_SCHEMA_VERSION = "4.0.0"
JEV_PROMPT_VERSION = "3.0.0"
