#!/usr/bin/env python3
"""
SPECIMEN DNA SNAPSHOTS — Tamper-proof daily archival
Captures complete state of every specimen: brain.md, soul.md, baselines, config.
Generates SHA-256 hash manifest for chain of custody.

Usage:
    python3 scripts/snapshot_specimens.py                 # Snapshot all tanks
    python3 scripts/snapshot_specimens.py tank-01-adam     # Snapshot specific tank
"""
import os
import sys
import json
import hashlib
import tarfile
import subprocess
from datetime import datetime
from pathlib import Path

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
SNAPSHOT_DIR = DIGIQUARIUM_DIR / 'snapshots'
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def snapshot_tank(tank_name):
    tank_dir = LOGS_DIR / tank_name
    if not tank_dir.exists():
        print(f"  {tank_name}: no log directory, skipping")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_name = f"{tank_name}_{timestamp}"
    tarpath = SNAPSHOT_DIR / f"{snapshot_name}.tar.gz"
    manifest = {'tank': tank_name, 'timestamp': datetime.now().isoformat(), 'files': {}}

    with tarfile.open(tarpath, 'w:gz') as tar:
        for root, dirs, files in os.walk(tank_dir):
            for fn in files:
                filepath = Path(root) / fn
                relpath = filepath.relative_to(tank_dir)
                tar.add(filepath, arcname=str(relpath))
                manifest['files'][str(relpath)] = {
                    'sha256': sha256_file(filepath),
                    'size': filepath.stat().st_size,
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                }

    # Hash the tarball itself
    manifest['archive_sha256'] = sha256_file(tarpath)
    manifest['archive_size'] = tarpath.stat().st_size

    # Write manifest
    manifest_path = SNAPSHOT_DIR / f"{snapshot_name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  {tank_name}: {len(manifest['files'])} files, {manifest['archive_size']} bytes, SHA-256: {manifest['archive_sha256'][:16]}...")
    return manifest

def main():
    tanks = sys.argv[1:] if len(sys.argv) > 1 else sorted([
        d.name for d in LOGS_DIR.iterdir()
        if d.is_dir() and d.name.startswith('tank-')
    ])

    print(f"=== SPECIMEN DNA SNAPSHOT — {datetime.now().isoformat()} ===")
    print(f"Archiving {len(tanks)} tanks to {SNAPSHOT_DIR}/\n")

    results = []
    for tank in tanks:
        m = snapshot_tank(tank)
        if m:
            results.append(m)

    # Write master manifest
    master = {
        'timestamp': datetime.now().isoformat(),
        'tanks_archived': len(results),
        'total_files': sum(len(r['files']) for r in results),
        'total_size': sum(r['archive_size'] for r in results),
        'manifests': [r['tank'] for r in results]
    }
    master_path = SNAPSHOT_DIR / f"master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    master_path.write_text(json.dumps(master, indent=2))

    print(f"\n=== COMPLETE: {master['tanks_archived']} tanks, {master['total_files']} files, {master['total_size']} bytes ===")
    print(f"Master manifest: {master_path}")

if __name__ == '__main__':
    main()
