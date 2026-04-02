#!/usr/bin/env python3
"""
Digiquarium Inference Proxy — security boundary between tanks and cloud APIs.

Tanks on the isolated network call this proxy. The proxy forwards to cloud APIs
on the default network. This way tanks never have direct internet access, and
API keys are only stored in this container's environment.

Supports multi-key rotation per provider with per-key rate limiting.
"""
import os
import json
import time
import fcntl
import logging
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger('InferenceProxy')

LISTEN_PORT = int(os.getenv('PROXY_PORT', '8100'))
LOCK_DIR = Path('/tmp/proxy_locks')
LOCK_DIR.mkdir(exist_ok=True)

# Load keys from environment
def load_keys(env_var):
    val = os.getenv(env_var, '')
    return [k.strip() for k in val.split(',') if k.strip()]

PROVIDERS = {
    'cerebras': {
        'url': 'https://api.cerebras.ai/v1/chat/completions',
        'keys': load_keys('CEREBRAS_API_KEYS'),
        'model': os.getenv('CEREBRAS_MODEL', 'llama3.1-8b'),
        'rate_limit': 2,
    },
    # Together.ai removed — requires payment to activate (402)
    'groq': {
        'url': 'https://api.groq.com/openai/v1/chat/completions',
        'keys': load_keys('GROQ_API_KEYS'),
        'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
        'rate_limit': 20,
    },
}

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')


def try_provider(name, config, system_prompt, user_prompt, timeout):
    """Try each key for a provider. Returns response text or None."""
    for idx, key in enumerate(config['keys']):
        lock_path = LOCK_DIR / f'.{name}_{idx}_lock'
        ts_path = LOCK_DIR / f'.{name}_{idx}_ts'

        try:
            lock_fd = open(lock_path, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            continue  # Key busy, try next

        try:
            # Rate limit
            try:
                last = float(open(ts_path).read().strip())
                elapsed = time.time() - last
                if elapsed < config['rate_limit']:
                    time.sleep(config['rate_limit'] - elapsed)
            except (FileNotFoundError, ValueError):
                pass

            data = json.dumps({
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.8,
                'top_p': 0.9,
                'max_tokens': 2048
            }).encode()

            req = urllib.request.Request(config['url'], data=data, headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {key}',
                'User-Agent': 'Digiquarium/1.0'
            })

            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read().decode())

            with open(ts_path, 'w') as f:
                f.write(str(time.time()))

            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"{name}[{idx}]: {e}")
        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except:
                pass
    return None


def try_ollama(system_prompt, user_prompt, timeout):
    """Ollama fallback with blocking lock."""
    lock_path = LOCK_DIR / '.ollama_lock'
    lock_fd = open(lock_path, 'w')
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Non-blocking — skip if busy

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
    except Exception as e:
        logger.error(f"Ollama: {e}")
        return ''
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/v1/generate':
            self.send_error(404)
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))

        system_prompt = body.get('system', '')
        user_prompt = body.get('prompt', '')
        timeout = body.get('timeout', 60)

        # Try cloud providers in order
        result = None
        for name in ['cerebras', 'groq']:
            config = PROVIDERS[name]
            if not config['keys']:
                continue
            result = try_provider(name, config, system_prompt, user_prompt, timeout)
            if result:
                break

        # Fallback to Ollama
        if not result:
            result = try_ollama(system_prompt, user_prompt, timeout)

        response = json.dumps({'response': result or '', 'provider': name if result else 'ollama'})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        pass  # Suppress per-request logging


if __name__ == '__main__':
    logger.info(f"Inference Proxy starting on port {LISTEN_PORT}")
    logger.info(f"Cerebras keys: {len(PROVIDERS['cerebras']['keys'])}")
    logger.info(f"Groq keys: {len(PROVIDERS['groq']['keys'])}")
    logger.info(f"Ollama: {OLLAMA_URL}")

    server = ThreadingHTTPServer(('0.0.0.0', LISTEN_PORT), ProxyHandler)
    server.serve_forever()
