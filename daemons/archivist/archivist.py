#!/usr/bin/env python3
"""Legacy compatibility wrapper - imports from src/daemons/"""
import sys
import os
from pathlib import Path

# Add src/daemons to path
src_daemons = Path(__file__).parent.parent.parent / 'src' / 'daemons'
sys.path.insert(0, str(src_daemons))

# Import from the canonical location
from research.archivist import *

if __name__ == '__main__':
    main()
