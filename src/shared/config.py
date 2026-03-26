"""Configuration utilities."""
import os
import yaml
import json
from pathlib import Path

def load_config(path: str) -> dict:
    """Load YAML or JSON config file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    
    with open(path) as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        return json.load(f)

def get_env(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)

def get_digiquarium_home() -> str:
    """Get DIGIQUARIUM_HOME from environment or use default."""
    return os.environ.get('DIGIQUARIUM_HOME', '/home/ijneb/digiquarium')

def get_ollama_host() -> str:
    """Get OLLAMA_HOST from environment or use default."""
    return os.environ.get('OLLAMA_HOST', 'digiquarium-ollama')

def get_ollama_port() -> int:
    """Get OLLAMA_PORT from environment or use default."""
    return int(os.environ.get('OLLAMA_PORT', '11434'))

def get_ollama_local_port() -> int:
    """Get OLLAMA_LOCAL_PORT from environment or use default."""
    return int(os.environ.get('OLLAMA_LOCAL_PORT', '11435'))

def get_ollama_url() -> str:
    """Construct Ollama URL from host and port environment variables."""
    host = get_ollama_host()
    port = get_ollama_port()
    return f'http://{host}:{port}'

def get_ollama_local_url() -> str:
    """Construct local Ollama URL from port environment variable."""
    port = get_ollama_local_port()
    return f'http://localhost:{port}'
