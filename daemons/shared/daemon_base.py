#!/usr/bin/env python3
"""
Shared Daemon Base Class
========================
Provides single-instance locking and common functionality for all daemons.
"""

import os
import sys
import fcntl
import signal
from pathlib import Path
from datetime import datetime

DAEMONS_DIR = Path('/home/ijneb/digiquarium/daemons')


class DaemonBase:
    """Base class for all daemons with single-instance locking."""
    
    def __init__(self, name: str):
        self.name = name
        self.running = True
        self.lock_file = DAEMONS_DIR / name / f'{name}.lock'
        self.pid_file = DAEMONS_DIR / name / f'{name}.pid'
        self.lock_fd = None
        
        # Ensure directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    def acquire_lock(self) -> bool:
        """Acquire exclusive lock - prevents multiple instances."""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write PID
            self.pid_file.write_text(str(os.getpid()))
            
            return True
        except IOError:
            print(f"[{self.name}] ERROR: Another instance is already running")
            return False
    
    def release_lock(self):
        """Release lock on shutdown."""
        try:
            if self.lock_fd:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
            self.pid_file.unlink(missing_ok=True)
            self.lock_file.unlink(missing_ok=True)
        except:
            pass
    
    def setup_signals(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"[{self.name}] Received signal {signum}, shutting down gracefully")
        self.running = False
        self.release_lock()
        sys.exit(0)
    
    def start(self):
        """Start the daemon with locking."""
        if not self.acquire_lock():
            sys.exit(1)
        
        self.setup_signals()
        
        try:
            self.run()
        finally:
            self.release_lock()
    
    def run(self):
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")
