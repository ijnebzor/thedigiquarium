"""Logging utilities."""
import logging
import json
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """Setup a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    
    # File handler (if log_dir provided)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path / f"{datetime.now().strftime('%Y-%m-%d')}.log")
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    return logger

def log_jsonl(filepath: str, data: dict):
    """Append JSON line to file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
