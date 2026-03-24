"""
DaemonBase - Base class for all Digiquarium daemons
Provides single-instance locking, signal handling, PID management, graceful shutdown
"""

import os
import sys
import signal
import fcntl
from pathlib import Path
from abc import ABC, abstractmethod


class DaemonBase(ABC):
    """Abstract base class for all Digiquarium daemons"""

    def __init__(self, daemon_name: str):
        self.daemon_name = daemon_name
        self.daemons_dir = Path(os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')) / 'daemons'
        self.pid_file = self.daemons_dir / f"{daemon_name}.pid"
        self.lock_file = self.daemons_dir / f"{daemon_name}.lock"
        self.should_exit = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup graceful shutdown on signals"""
        def signal_handler(signum, frame):
            self.should_exit = True
            print(f"\n[{self.daemon_name}] Received signal {signum}, shutting down gracefully...")

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def _acquire_lock(self):
        """Acquire exclusive lock to ensure single instance"""
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            fd = open(self.lock_file, 'w')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except IOError:
            print(f"[{self.daemon_name}] Another instance already running")
            sys.exit(1)

    def _write_pid(self):
        """Write PID file for process management"""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))

    def _cleanup(self):
        """Cleanup PID and lock files"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            if self.lock_file.exists():
                self.lock_file.unlink()
        except:
            pass

    @abstractmethod
    def run(self):
        """Main daemon loop - must be implemented by subclass"""
        pass

    def start(self):
        """Start the daemon with locking and PID management"""
        lock_fd = self._acquire_lock()
        self._write_pid()
        try:
            self.run()
        except Exception as e:
            print(f"[{self.daemon_name}] Fatal error: {e}")
            sys.exit(1)
        finally:
            self._cleanup()
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
