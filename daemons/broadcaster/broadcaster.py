#!/usr/bin/env python3
"""Legacy compatibility wrapper - imports from src/daemons/"""
import sys
import os
from pathlib import Path

# Add src/daemons to path
src_daemons = Path(__file__).parent.parent.parent / 'src' / 'daemons'
sys.path.insert(0, str(src_daemons))

# Run the canonical broadcaster
from infra.broadcaster import Broadcaster, acquire_lock

if __name__ == '__main__':
    if acquire_lock():
        Broadcaster().run()
