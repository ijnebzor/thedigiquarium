#!/usr/bin/env python3
"""
Budget Tracker — Tracks inference API usage per tank per provider.
Reads inference proxy logs to calculate usage. Outputs JSON report.

Usage:
    python3 scripts/budget_tracker.py              # Full report
    python3 scripts/budget_tracker.py --summary    # Summary only
"""
import os, sys, json, re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DIGIQUARIUM = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium'))
PROXY_LOG = DIGIQUARIUM / 'logs' / 'inference-proxy'
OUTPUT = DIGIQUARIUM / 'logs' / 'budget'
OUTPUT.mkdir(parents=True, exist_ok=True)

# Approximate token costs (free tier, but tracking for when we scale)
COSTS = {
    'cerebras': 0.0,  # Free tier
    'groq': 0.0,      # Free tier
    'ollama': 0.0,    # Local
}


def scan_proxy_logs():
    """Scan inference proxy container logs for usage data."""
    import subprocess
    result = subprocess.run(
        ['docker', 'logs', 'digiquarium-inference-proxy', '--since', '24h'],
        capture_output=True, text=True, timeout=30
    )
    
    usage = defaultdict(lambda: defaultdict(int))
    provider_totals = defaultdict(int)
    
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        # Look for provider usage patterns
        # Typical log: "2026-04-05 22:00:00 [cerebras-key3] tank-01-adam 200 OK"
        m = re.search(r'\[(\w+?)(?:-key\d+)?\].*?(tank-\d+-\w+)', line)
        if m:
            provider = m.group(1).lower()
            tank = m.group(2)
            usage[tank][provider] += 1
            provider_totals[provider] += 1
        
        # Also match simpler patterns
        for provider in ['cerebras', 'groq', 'ollama']:
            if provider in line.lower():
                provider_totals[provider] += 1
                break
    
    return dict(usage), dict(provider_totals)


def scan_tank_activity():
    """Count brain entries per tank in last 24h as a proxy for inference usage."""
    activity = {}
    cutoff = datetime.now() - timedelta(hours=24)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    logs_dir = DIGIQUARIUM / 'logs'
    for d in sorted(logs_dir.iterdir()):
        if not d.name.startswith('tank-'):
            continue
        brain = d / 'brain.md'
        if not brain.exists():
            continue
        
        today_entries = 0
        total_entries = 0
        for line in brain.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.startswith('['):
                total_entries += 1
                if cutoff_str in line:
                    today_entries += 1
        
        if total_entries > 0:
            activity[d.name] = {
                'entries_24h': today_entries,
                'entries_total': total_entries,
            }
    
    return activity


def generate_report():
    """Generate a comprehensive budget/usage report."""
    print("Scanning proxy logs...")
    proxy_usage, provider_totals = scan_proxy_logs()
    
    print("Scanning tank activity...")
    tank_activity = scan_tank_activity()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'period': 'last_24h',
        'provider_totals': provider_totals,
        'tank_activity': tank_activity,
        'proxy_usage_by_tank': proxy_usage,
        'costs': COSTS,
        'summary': {
            'total_tanks_active': len([t for t in tank_activity.values() if t['entries_24h'] > 0]),
            'total_entries_24h': sum(t['entries_24h'] for t in tank_activity.values()),
            'total_entries_all_time': sum(t['entries_total'] for t in tank_activity.values()),
            'total_inference_calls': sum(provider_totals.values()),
        }
    }
    
    # Save report
    report_path = OUTPUT / f"budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"Report saved: {report_path}")
    
    return report


def print_summary(report):
    """Print a human-readable summary."""
    s = report['summary']
    print(f"\n{'='*50}")
    print(f"BUDGET REPORT — {report['timestamp'][:19]}")
    print(f"{'='*50}")
    print(f"Active tanks (24h):     {s['total_tanks_active']}")
    print(f"Brain entries (24h):    {s['total_entries_24h']}")
    print(f"Brain entries (total):  {s['total_entries_all_time']}")
    print(f"Inference calls (24h):  {s['total_inference_calls']}")
    print(f"\nProvider breakdown:")
    for provider, count in sorted(report['provider_totals'].items()):
        cost = COSTS.get(provider, 0) * count
        print(f"  {provider}: {count} calls (${cost:.2f})")
    print(f"\nTop tanks by 24h activity:")
    sorted_tanks = sorted(
        report['tank_activity'].items(),
        key=lambda x: -x[1]['entries_24h']
    )
    for tank, data in sorted_tanks[:10]:
        if data['entries_24h'] > 0:
            print(f"  {tank}: {data['entries_24h']} entries today / {data['entries_total']} total")
    print(f"{'='*50}")


if __name__ == '__main__':
    report = generate_report()
    if '--summary' in sys.argv or True:  # Always show summary
        print_summary(report)
