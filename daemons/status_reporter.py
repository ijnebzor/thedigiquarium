#!/usr/bin/env python3
"""
Standard Status Reporter for All Daemons

Usage:
    from status_reporter import StatusReporter
    
    reporter = StatusReporter('daemon_name')
    reporter.report(status='running', metrics={'checks': 100})
    reporter.error('Something failed')
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DAEMONS_DIR = Path('/home/ijneb/digiquarium/daemons')


class StatusReporter:
    def __init__(self, daemon_name: str):
        self.daemon_name = daemon_name
        self.daemon_dir = DAEMONS_DIR / daemon_name
        self.status_file = self.daemon_dir / 'status.json'
        self.errors: List[Dict] = []
        
        # Ensure directory exists
        self.daemon_dir.mkdir(parents=True, exist_ok=True)
    
    def report(self, 
               status: str = 'running',
               metrics: Optional[Dict] = None,
               message: Optional[str] = None):
        """Write status report."""
        
        data = {
            'daemon': self.daemon_name,
            'status': status,
            'last_check': datetime.now().isoformat(),
            'message': message,
            'metrics': metrics or {},
            'recent_errors': self.errors[-10:],  # Last 10 errors
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def error(self, message: str):
        """Log an error."""
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        
        # Keep only last 100 errors in memory
        self.errors = self.errors[-100:]
    
    def heartbeat(self, metrics: Optional[Dict] = None):
        """Quick heartbeat - just update timestamp."""
        self.report(status='running', metrics=metrics)


# Standalone function for simple scripts
def quick_status(daemon_name: str, status: str = 'running', metrics: Optional[Dict] = None):
    """Quick status update without instantiating class."""
    reporter = StatusReporter(daemon_name)
    reporter.report(status=status, metrics=metrics)
