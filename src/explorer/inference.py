"""
Inference abstraction layer for the Digiquarium.
Primary: Groq API (fast cloud inference)
Fallback: Local Ollama (slow but sovereign)
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error

logger = logging.getLogger('Inference')

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://digiquarium-ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')


def generate(system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
    """Generate a response using Groq (primary) with Ollama fallback.
    
    Returns the generated text, or empty string on failure.
    """
    # Try Groq first if API key is available
    if GROQ_API_KEY:
        try:
            result = _call_groq(system_prompt, user_prompt, timeout)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Groq failed: {e}, falling back to Ollama")
    
    # Fallback to local Ollama
    try:
        return _call_ollama(system_prompt, user_prompt, timeout)
    except Exception as e:
        logger.error(f"Ollama also failed: {e}")
        return ''


def _call_groq(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Call Groq's OpenAI-compatible API."""
    data = json.dumps({
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 1024
    }).encode()
    
    req = urllib.request.Request(
        GROQ_URL,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GROQ_API_KEY}'
        }
    )
    
    with urllib.request.urlopen(req, timeout=timeout) as r:
        result = json.loads(r.read().decode())
    
    return result['choices'][0]['message']['content']


def _call_ollama(system_prompt: str, user_prompt: str, timeout: int) -> str:
    """Call local Ollama API."""
    # Acquire lock for Ollama (single-threaded CPU inference)
    import fcntl
    lock_path = '/shared/.ollama_lock'
    lock_fd = None
    
    wait_start = time.time()
    while time.time() - wait_start < 300:
        try:
            lock_fd = open(lock_path, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except (IOError, OSError):
            if lock_fd:
                lock_fd.close()
                lock_fd = None
            time.sleep(5)
    
    if lock_fd is None:
        return ''
    
    try:
        data = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.8, "top_p": 0.9}
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
