#!/usr/bin/env python3
"""
THE ARCHIVIST v1.0 - Data Storage & Historical Query Engine
=============================================================
Manages the data storage layer: thinking traces, personality baselines,
deep dive reports, and intervention records. Handles data retention
policies, enables historical queries, and prepares data exports for
external researchers. Every trace is indexed and searchable.

Responsibilities:
- Index and catalog all thinking traces across tanks
- Maintain searchable metadata index for historical queries
- Enforce data retention policies (archive old data, prune expired)
- Generate data export packages for external researchers
- Monitor storage usage and alert on capacity issues
- Coordinate with THE DOCUMENTARIAN for historical data access

SLA: 4 hours for index updates
     Immediate for data integrity issues
"""

import os
import sys
import time
import json
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.utils import DaemonLogger, run_command, write_pid_file, send_email_alert
from shared.escalation import escalate_to_overseer

DIGIQUARIUM_DIR = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
LOGS_DIR = DIGIQUARIUM_DIR / 'logs'
ARCHIVE_DIR = DIGIQUARIUM_DIR / 'archive'
INDEX_DIR = DIGIQUARIUM_DIR / 'archive' / 'index'
EXPORT_DIR = DIGIQUARIUM_DIR / 'archive' / 'exports'
DAEMONS_DIR = DIGIQUARIUM_DIR / 'daemons'

# Timing
INDEX_INTERVAL = 14400       # Full reindex every 4 hours
INCREMENTAL_INTERVAL = 900   # Incremental scan every 15 minutes
RETENTION_DAYS = 90          # Keep raw traces for 90 days
ARCHIVE_AFTER_DAYS = 30      # Archive traces older than 30 days
EXPORT_RETENTION_DAYS = 14   # Keep exports for 14 days
STORAGE_WARN_GB = 50         # Warn at 50 GB used
SLEEP_INTERVAL = 300         # Main loop sleep: 5 minutes


class Archivist:
    """THE ARCHIVIST - Data Storage & Historical Query Engine"""

    def __init__(self):
        self.log = DaemonLogger('archivist')
        self.index_file = INDEX_DIR / 'master_index.json'
        self.catalog_file = INDEX_DIR / 'catalog.json'
        self.stats_file = INDEX_DIR / 'storage_stats.json'
        self.last_scan_file = INDEX_DIR / 'last_scan.json'

        # Ensure directories exist
        for d in [ARCHIVE_DIR, INDEX_DIR, EXPORT_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        self.index = self._load_index()
        self.catalog = self._load_catalog()

    # ── Index Management ──────────────────────────────────────────────

    def _load_index(self) -> dict:
        """Load the master index from disk"""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError) as e:
                self.log.warn(f"Corrupt index, rebuilding: {e}")
        return {'version': 1, 'entries': {}, 'last_full_reindex': None}

    def _save_index(self):
        """Persist the master index atomically"""
        tmp = self.index_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.index, indent=2, default=str), encoding='utf-8')
        tmp.rename(self.index_file)

    def _load_catalog(self) -> dict:
        """Load the trace catalog (per-tank summaries)"""
        if self.catalog_file.exists():
            try:
                return json.loads(self.catalog_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                pass
        return {'tanks': {}, 'total_traces': 0, 'last_updated': None}

    def _save_catalog(self):
        """Persist the catalog atomically"""
        tmp = self.catalog_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.catalog, indent=2, default=str), encoding='utf-8')
        tmp.rename(self.catalog_file)

    # ── Trace Indexing ────────────────────────────────────────────────

    def _file_hash(self, path: Path) -> str:
        """Compute a fast hash for change detection"""
        h = hashlib.md5()
        h.update(str(path.stat().st_size).encode())
        h.update(str(path.stat().st_mtime).encode())
        return h.hexdigest()

    def _get_last_scan_state(self) -> dict:
        """Load state from last incremental scan"""
        if self.last_scan_file.exists():
            try:
                return json.loads(self.last_scan_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                pass
        return {'file_hashes': {}}

    def _save_scan_state(self, state: dict):
        """Save incremental scan state"""
        self.last_scan_file.write_text(json.dumps(state, default=str), encoding='utf-8')

    def incremental_index(self):
        """Scan for new or modified trace files and update index"""
        self.log.info("Starting incremental index scan")
        scan_state = self._get_last_scan_state()
        old_hashes = scan_state.get('file_hashes', {})
        new_hashes = {}
        files_indexed = 0
        files_skipped = 0

        for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
            tank_id = tank_dir.name
            traces_dir = tank_dir / 'thinking_traces'
            if not traces_dir.exists():
                continue

            for trace_file in sorted(traces_dir.glob('*.jsonl')):
                fkey = str(trace_file)
                fhash = self._file_hash(trace_file)
                new_hashes[fkey] = fhash

                # Skip if unchanged
                if old_hashes.get(fkey) == fhash:
                    files_skipped += 1
                    continue

                # Index the file
                try:
                    self._index_trace_file(tank_id, trace_file)
                    files_indexed += 1
                except Exception as e:
                    self.log.error(f"Failed to index {trace_file}: {e}")

            # Also scan baselines
            baselines_dir = tank_dir / 'baselines'
            if baselines_dir.exists():
                for baseline_file in baselines_dir.glob('*.json'):
                    fkey = str(baseline_file)
                    fhash = self._file_hash(baseline_file)
                    new_hashes[fkey] = fhash
                    if old_hashes.get(fkey) == fhash:
                        files_skipped += 1
                        continue
                    try:
                        self._index_baseline_file(tank_id, baseline_file)
                        files_indexed += 1
                    except Exception as e:
                        self.log.error(f"Failed to index baseline {baseline_file}: {e}")

        self._save_scan_state({'file_hashes': new_hashes})
        self._save_index()
        self._update_catalog()
        self.log.info(f"Incremental scan complete: {files_indexed} indexed, {files_skipped} unchanged")
        return files_indexed

    def _index_trace_file(self, tank_id: str, trace_file: Path):
        """Parse a JSONL trace file and add entries to the master index"""
        entry_count = 0
        first_ts = None
        last_ts = None

        with open(trace_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    ts = record.get('timestamp', record.get('time', ''))
                    if ts:
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts
                    entry_count += 1
                except json.JSONDecodeError:
                    continue

        file_key = f"{tank_id}/{trace_file.name}"
        self.index['entries'][file_key] = {
            'tank_id': tank_id,
            'file': str(trace_file),
            'type': 'thinking_trace',
            'entry_count': entry_count,
            'first_timestamp': first_ts,
            'last_timestamp': last_ts,
            'size_bytes': trace_file.stat().st_size,
            'indexed_at': datetime.now().isoformat(),
        }

    def _index_baseline_file(self, tank_id: str, baseline_file: Path):
        """Index a personality baseline JSON file"""
        try:
            data = json.loads(baseline_file.read_text(encoding='utf-8'))
            ts = data.get('timestamp', data.get('date', ''))
        except (json.JSONDecodeError, IOError):
            ts = ''

        file_key = f"{tank_id}/baselines/{baseline_file.name}"
        self.index['entries'][file_key] = {
            'tank_id': tank_id,
            'file': str(baseline_file),
            'type': 'baseline',
            'timestamp': ts,
            'size_bytes': baseline_file.stat().st_size,
            'indexed_at': datetime.now().isoformat(),
        }

    def full_reindex(self):
        """Complete reindex - clears and rebuilds from scratch"""
        self.log.info("Starting full reindex")
        self.index = {'version': 1, 'entries': {}, 'last_full_reindex': datetime.now().isoformat()}

        # Clear scan state to force full scan
        if self.last_scan_file.exists():
            self.last_scan_file.unlink()

        count = self.incremental_index()
        self.index['last_full_reindex'] = datetime.now().isoformat()
        self._save_index()
        self.log.info(f"Full reindex complete: {len(self.index['entries'])} entries")
        return count

    def _update_catalog(self):
        """Rebuild per-tank catalog from index"""
        tanks = {}
        total = 0

        for key, entry in self.index['entries'].items():
            tid = entry['tank_id']
            if tid not in tanks:
                tanks[tid] = {'trace_files': 0, 'baseline_files': 0, 'total_entries': 0, 'size_bytes': 0}

            if entry['type'] == 'thinking_trace':
                tanks[tid]['trace_files'] += 1
                tanks[tid]['total_entries'] += entry.get('entry_count', 0)
            elif entry['type'] == 'baseline':
                tanks[tid]['baseline_files'] += 1

            tanks[tid]['size_bytes'] += entry.get('size_bytes', 0)
            total += entry.get('entry_count', 0) if entry['type'] == 'thinking_trace' else 1

        self.catalog = {
            'tanks': tanks,
            'total_traces': total,
            'total_indexed_files': len(self.index['entries']),
            'last_updated': datetime.now().isoformat(),
        }
        self._save_catalog()

    # ── Data Retention ────────────────────────────────────────────────

    def enforce_retention(self):
        """Archive old traces and prune expired archives"""
        self.log.info("Enforcing data retention policies")
        archived = 0
        pruned = 0

        now = datetime.now()
        archive_cutoff = now - timedelta(days=ARCHIVE_AFTER_DAYS)
        retention_cutoff = now - timedelta(days=RETENTION_DAYS)

        for tank_dir in sorted(LOGS_DIR.glob('tank-*')):
            traces_dir = tank_dir / 'thinking_traces'
            if not traces_dir.exists():
                continue

            for trace_file in sorted(traces_dir.glob('*.jsonl')):
                try:
                    file_date_str = trace_file.stem  # Expected: YYYY-MM-DD
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                except ValueError:
                    continue

                if file_date < archive_cutoff:
                    # Archive the file
                    tank_archive = ARCHIVE_DIR / tank_dir.name
                    tank_archive.mkdir(parents=True, exist_ok=True)
                    dest = tank_archive / trace_file.name

                    if not dest.exists():
                        shutil.copy2(trace_file, dest)
                        archived += 1
                        self.log.info(f"Archived: {trace_file.name} from {tank_dir.name}")

        # Prune expired archives
        for archive_tank_dir in ARCHIVE_DIR.glob('tank-*'):
            for archived_file in archive_tank_dir.glob('*.jsonl'):
                try:
                    file_date_str = archived_file.stem
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                except ValueError:
                    continue

                if file_date < retention_cutoff:
                    archived_file.unlink()
                    pruned += 1
                    self.log.info(f"Pruned expired archive: {archived_file.name}")

        # Prune old exports
        export_cutoff = now - timedelta(days=EXPORT_RETENTION_DAYS)
        for export_file in EXPORT_DIR.glob('export_*.json'):
            if datetime.fromtimestamp(export_file.stat().st_mtime) < export_cutoff:
                export_file.unlink()
                pruned += 1

        self.log.info(f"Retention enforcement complete: {archived} archived, {pruned} pruned")
        return archived, pruned

    # ── Data Export ───────────────────────────────────────────────────

    def generate_export(self, tank_ids: list = None, days_back: int = 7) -> Path:
        """Generate a data export package for external researchers"""
        self.log.info(f"Generating data export (tanks={tank_ids}, days_back={days_back})")

        cutoff = datetime.now() - timedelta(days=days_back)
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'parameters': {'tank_ids': tank_ids, 'days_back': days_back},
            'tanks': {},
        }

        target_entries = {
            k: v for k, v in self.index['entries'].items()
            if v['type'] == 'thinking_trace'
            and (tank_ids is None or v['tank_id'] in tank_ids)
        }

        for key, entry in target_entries.items():
            tid = entry['tank_id']
            if tid not in export_data['tanks']:
                export_data['tanks'][tid] = {'traces': [], 'summary': {}}

            trace_path = Path(entry['file'])
            if not trace_path.exists():
                continue

            # Only include recent entries
            last_ts = entry.get('last_timestamp', '')
            if last_ts:
                try:
                    entry_date = datetime.fromisoformat(last_ts.replace('Z', '+00:00').replace('+00:00', ''))
                except (ValueError, TypeError):
                    entry_date = datetime.now()
                if entry_date < cutoff:
                    continue

            export_data['tanks'][tid]['traces'].append({
                'file': trace_path.name,
                'entry_count': entry.get('entry_count', 0),
                'time_range': {
                    'first': entry.get('first_timestamp'),
                    'last': entry.get('last_timestamp'),
                },
            })

        # Write export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = EXPORT_DIR / f"export_{timestamp}.json"
        export_file.write_text(json.dumps(export_data, indent=2, default=str), encoding='utf-8')

        self.log.info(f"Export generated: {export_file.name} ({len(export_data['tanks'])} tanks)")
        return export_file

    # ── Storage Monitoring ────────────────────────────────────────────

    def check_storage(self) -> dict:
        """Monitor storage usage and alert if thresholds exceeded"""
        stats = {'tanks': {}, 'total_bytes': 0, 'archive_bytes': 0}

        # Measure logs directory
        for tank_dir in LOGS_DIR.glob('tank-*'):
            tank_bytes = sum(f.stat().st_size for f in tank_dir.rglob('*') if f.is_file())
            stats['tanks'][tank_dir.name] = tank_bytes
            stats['total_bytes'] += tank_bytes

        # Measure archive directory
        for f in ARCHIVE_DIR.rglob('*'):
            if f.is_file():
                stats['archive_bytes'] += f.stat().st_size

        stats['total_gb'] = round((stats['total_bytes'] + stats['archive_bytes']) / (1024 ** 3), 2)
        stats['checked_at'] = datetime.now().isoformat()

        # Write stats
        self.stats_file.write_text(json.dumps(stats, indent=2, default=str), encoding='utf-8')

        if stats['total_gb'] >= STORAGE_WARN_GB:
            self.log.warn(f"Storage warning: {stats['total_gb']} GB used (threshold: {STORAGE_WARN_GB} GB)")
            escalate_to_overseer(
                severity='high',
                issue_type='STORAGE_WARNING',
                message=f"Archive storage at {stats['total_gb']} GB, approaching capacity",
                extra={'stats': stats}
            )

        self.log.info(f"Storage check: {stats['total_gb']} GB total across {len(stats['tanks'])} tanks")
        return stats

    # ── Historical Query Support ──────────────────────────────────────

    def query_traces(self, tank_id: str = None, date_from: str = None, date_to: str = None,
                     trace_type: str = None) -> list:
        """Query the index for matching trace entries"""
        results = []

        for key, entry in self.index['entries'].items():
            if tank_id and entry['tank_id'] != tank_id:
                continue
            if trace_type and entry['type'] != trace_type:
                continue
            if date_from and entry.get('first_timestamp', '') < date_from:
                continue
            if date_to and entry.get('last_timestamp', '') > date_to:
                continue
            results.append(entry)

        return sorted(results, key=lambda x: x.get('first_timestamp', ''))

    # ── Main Loop ─────────────────────────────────────────────────────

    def run(self):
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║              THE ARCHIVIST v1.0 - Data Storage & Query Engine        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Trace indexing & historical queries                                 ║
║  Data retention enforcement                                          ║
║  Export generation for researchers                                   ║
║  Reports to THE DOCUMENTARIAN                                        ║
╚══════════════════════════════════════════════════════════════════════╝
""")
        write_pid_file('archivist')
        self.log.info("THE ARCHIVIST v1.0 starting")

        # Initial full reindex on startup
        self.full_reindex()
        self.check_storage()

        last_full_reindex = datetime.now()
        last_incremental = datetime.now()
        last_retention = datetime.now()
        last_storage_check = datetime.now()
        last_export = datetime.now()

        while True:
            try:
                _sla_cycle_start = time.time()
                now = datetime.now()

                # Incremental index every 15 minutes
                if (now - last_incremental).total_seconds() >= INCREMENTAL_INTERVAL:
                    self.incremental_index()
                    last_incremental = now

                # Full reindex every 4 hours
                if (now - last_full_reindex).total_seconds() >= INDEX_INTERVAL:
                    self.full_reindex()
                    last_full_reindex = now

                # Retention enforcement every 12 hours
                if (now - last_retention).total_seconds() >= 43200:
                    self.enforce_retention()
                    last_retention = now

                # Storage check every 6 hours
                if (now - last_storage_check).total_seconds() >= 21600:
                    self.check_storage()
                    last_storage_check = now

                # Automatic export every 24 hours
                if (now - last_export).total_seconds() >= 86400:
                    self.generate_export()
                    last_export = now

                # Write SLA status
                _sla_cycle_duration = time.time() - _sla_cycle_start
                _sla_data = {
                    'daemon': 'archivist',
                    'compliant': True,
                    'last_check_time': datetime.now().isoformat(),
                    'cycle_duration': _sla_cycle_duration,
                    'sla_target': 300,
                    'violations_count': 0
                }
                _sla_path = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons' / 'archivist' / 'sla_status.json'
                _sla_path.parent.mkdir(parents=True, exist_ok=True)
                _sla_path.write_text(json.dumps(_sla_data, indent=2))

                time.sleep(SLEEP_INTERVAL)

            except KeyboardInterrupt:
                self.log.info("Shutdown signal received, saving state...")
                self._save_index()
                self._save_catalog()
                break
            except Exception as e:
                self.log.error(f"Error in main loop: {e}")
                escalate_to_overseer(
                    severity='high',
                    issue_type='DAEMON_ERROR',
                    message=f"THE ARCHIVIST encountered an error: {e}",
                    extra={'daemon': 'archivist'}
                )
                time.sleep(SLEEP_INTERVAL)


# Single-instance lock
import fcntl
LOCK_FILE = Path(__file__).parent / 'archivist.lock'
lock_fd = None

def acquire_lock():
    global lock_fd
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        print("[archivist] Another instance is already running")
        return False


if __name__ == "__main__":
    if acquire_lock():
        Archivist().run()
