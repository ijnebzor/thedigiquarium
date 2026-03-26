#!/usr/bin/env python3
"""Legacy compatibility wrapper - imports from src/daemons/"""
import sys
import os
from pathlib import Path

# Add src/daemons to path
src_daemons = Path(__file__).parent.parent.parent / 'src' / 'daemons'
sys.path.insert(0, str(src_daemons))

# Run the canonical caretaker
from core.caretaker import acquire_lock, main, run_maintenance_cycle

if __name__ == '__main__':
    if not acquire_lock():
        sys.exit(1)
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        run_maintenance_cycle()
    else:
        main()
