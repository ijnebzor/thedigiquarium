"""
Inference chain for the Digiquarium.
v3.0 (2026-04-01): Security-first architecture.

Tanks call the inference proxy on the isolated network.
The proxy handles cloud API routing and key management.
Tanks NEVER have direct internet access or API keys.

Fallback: local Ollama on isolated-net (blocking lock, fair queue).
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error
import fcntl

logger = logging.getLogger('Inference')

INFERENCE_PROXY_URL = os.getenv('INFERENCE_PROXY_URL', 'http://digiquarium-inference-proxy:8100')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')


def generate(system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
    """Generate via inference proxy (cloud providers) with Ollama fallback.
    The proxy handles Cerebras/Groq key rotation and rate limiting.
    Tanks never see API keys or touch the internet."""

    # Try the inference proxy first (routes to cloud providers)
    try:
        result = _call_proxy(system_prompt, user_prompt, timeout)
        if result:
            return result
    except Exception as e:
        logger.warning(f"Proxy failed: {e}")

    # Fallback: local Ollama with blocking lock (fair queue)
    try:
        return _call_ollama(system_prompt, user_prompt, timeout)
    except Exception as e:
        logger.error(f"All inference failed (proxy + Ollama): {e}")
        return ''


def _call_proxy(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Call the inference proxy on the isolated network."""
    data = json.dumps({
        'system': system_prompt,
        'prompt': user_prompt,
        'timeout': timeout
    }).encode()

    req = urllib.request.Request(
        f"{INFERENCE_PROXY_URL}/v1/generate",
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=timeout + 30) as r:
        result = json.loads(r.read().decode())

    response = result.get('response', '')
    if response:
        provider = result.get('provider', 'unknown')
        logger.debug(f"Got response from {provider}")
    return response


def _call_ollama(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Local Ollama fallback. Uses OS-level blocking lock (LOCK_EX).
    The kernel fairly queues all waiters. Every tank gets its turn."""
    lock_path = '/shared/.ollama_lock'
    lock_fd = None

    try:
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
    except (IOError, OSError, PermissionError) as e:
        logger.warning(f"Ollama lock failed: {e}")
        if lock_fd:
            lock_fd.close()
        return ''

    try:
        data = json.dumps({
            'model': OLLAMA_MODEL,
            'prompt': user_prompt,
            'system': system_prompt,
            'stream': False,
            'options': {'temperature': 0.8, 'top_p': 0.9}
        }).encode()

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode())

        return result.get('response', '')
    finally:
        if lock_fd:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except:
                pass
