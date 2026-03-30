"""
Inference chain for the Digiquarium.
Cerebras (fastest) → Together.ai → Groq → Ollama (sovereign failsafe).
All cloud providers use OpenAI-compatible API format.
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error
import fcntl

logger = logging.getLogger('Inference')

# Provider configs — each has URL, key env var, model, and rate limit (seconds between calls)
PROVIDERS = [
    {
        'name': 'Cerebras',
        'url': 'https://api.cerebras.ai/v1/chat/completions',
        'key_env': 'CEREBRAS_API_KEY',
        'model_env': 'CEREBRAS_MODEL',
        'default_model': 'llama-3.3-70b',
        'rate_limit': 2,  # 30 RPM = 2s between calls
    },
    {
        'name': 'Together',
        'url': 'https://api.together.xyz/v1/chat/completions',
        'key_env': 'TOGETHER_API_KEY',
        'model_env': 'TOGETHER_MODEL',
        'default_model': 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
        'rate_limit': 2,
    },
    {
        'name': 'Groq',
        'url': 'https://api.groq.com/openai/v1/chat/completions',
        'key_env': 'GROQ_API_KEY',
        'model_env': 'GROQ_MODEL',
        'default_model': 'llama-3.1-8b-instant',
        'rate_limit': 20,  # 6000 TPM limit = need 20s spacing
    },
]

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')


def generate(system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
    """Generate via the inference chain. First available provider wins."""

    # Try each cloud provider in order
    for provider in PROVIDERS:
        key = os.getenv(provider['key_env'], '')
        if not key:
            continue

        model = os.getenv(provider['model_env'], provider['default_model'])

        try:
            result = _call_provider(
                name=provider['name'],
                url=provider['url'],
                key=key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout=timeout,
                rate_limit=provider['rate_limit'],
            )
            if result:
                return result
        except Exception as e:
            logger.warning(f"{provider['name']} failed: {e}")
            continue

    # Final fallback: local Ollama
    try:
        return _call_ollama(system_prompt, user_prompt, timeout)
    except Exception as e:
        logger.error(f"All providers failed. Ollama: {e}")
        return ''


def _call_provider(name: str, url: str, key: str, model: str,
                   system_prompt: str, user_prompt: str,
                   timeout: int, rate_limit: int) -> str:
    """Call an OpenAI-compatible provider with shared rate limiting."""

    # Shared rate limiter per provider
    lock_path = f'/shared/.{name.lower()}_rate_lock'
    ts_path = f'/shared/.{name.lower()}_last_call'

    try:
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError, PermissionError):
        # Can't get lock — another tank is using this provider, skip to next
        raise Exception(f"{name} lock busy, trying next provider")

    try:
        # Rate limit: wait if needed
        try:
            last = float(open(ts_path).read().strip())
            elapsed = time.time() - last
            if elapsed < rate_limit:
                time.sleep(rate_limit - elapsed)
        except (FileNotFoundError, ValueError):
            pass

        # Make the request
        data = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.8,
            'top_p': 0.9,
            'max_tokens': 1024
        }).encode()

        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
            'User-Agent': 'Digiquarium/1.0'
        })

        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode())

        # Record timestamp
        try:
            with open(ts_path, 'w') as f:
                f.write(str(time.time()))
        except PermissionError:
            pass

        return result['choices'][0]['message']['content']

    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except:
            pass


def _call_ollama(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Local Ollama fallback. Uses shared lock since CPU can only serve one at a time."""
    lock_path = '/shared/.ollama_lock'
    lock_fd = None

    try:
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError, PermissionError):
        # Can't get Ollama lock — return empty rather than block
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
