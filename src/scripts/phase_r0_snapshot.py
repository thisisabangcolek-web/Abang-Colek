"""
⚡ Phase R0: Freeze & Forensic Snapshot
D:\\ABANGCOLEK\\forensic_archive\\pre_recovery_20260928_2135
Copies existing reports, data, and database files and creates MANIFEST.json with SHA-256 hashes.
"""

import os
import shutil
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path("D:/ABANGCOLEK")
SNAPSHOT_DIR = BASE_DIR / "forensic_archive" / "pre_recovery_20260928_2135"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def execute_snapshot():
    print(f"Creating snapshot at {SNAPSHOT_DIR}...")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    sources_to_copy = [
        BASE_DIR / "data",
        BASE_DIR / "reports",
        BASE_DIR / "JEV_AUDIT_REPORT.json",
    ]

    manifest_entries = []
    total_bytes = 0

    for source in sources_to_copy:
        if not source.exists():
            print(f"Warning: {source} does not exist, skipping.")
            continue

        if source.is_file():
            rel_path = source.relative_to(BASE_DIR)
            dest_file = SNAPSHOT_DIR / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest_file)
            file_hash = compute_sha256(source)
            dest_hash = compute_sha256(dest_file)
            assert file_hash == dest_hash, f"Hash mismatch for {source}"
            size = source.stat().st_size
            total_bytes += size
            manifest_entries.append({
                "path": str(rel_path).replace("\\", "/"),
                "size_bytes": size,
                "sha256": file_hash,
                "source_path": str(source).replace("\\", "/"),
                "snapshot_path": str(dest_file).replace("\\", "/")
            })
            print(f"Copied file: {rel_path} ({size} bytes, SHA-256: {file_hash[:12]}...)")
        elif source.is_dir():
            for root, dirs, files in os.walk(source):
                for file in files:
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(BASE_DIR)
                    dest_file = SNAPSHOT_DIR / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    file_hash = compute_sha256(src_file)
                    dest_hash = compute_sha256(dest_file)
                    assert file_hash == dest_hash, f"Hash mismatch for {src_file}"
                    size = src_file.stat().st_size
                    total_bytes += size
                    manifest_entries.append({
                        "path": str(rel_path).replace("\\", "/"),
                        "size_bytes": size,
                        "sha256": file_hash,
                        "source_path": str(src_file).replace("\\", "/"),
                        "snapshot_path": str(dest_file).replace("\\", "/")
                    })
                    print(f"Copied: {rel_path} ({size} bytes, SHA-256: {file_hash[:12]}...)")

    manifest = {
        "manifest_version": "1.0.0",
        "snapshot_id": "pre_recovery_20260928_2135",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "PHASE R0 — Freeze & Forensic Snapshot before decontamination and recovery",
        "governing_document": "CHAT6.md",
        "total_files": len(manifest_entries),
        "total_bytes": total_bytes,
        "files": sorted(manifest_entries, key=lambda x: x["path"])
    }

    manifest_path = SNAPSHOT_DIR / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Snapshot completed successfully.")
    print(f"Total files archived: {len(manifest_entries)}")
    print(f"Total bytes archived: {total_bytes}")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    execute_snapshot()
