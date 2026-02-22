#!/usr/bin/env python3
"""
Unified Explorer - Config-driven Wikipedia exploration for all standard tanks.

Usage:
    python explorer.py --config /config/tanks/adam.yaml
    
Or via environment:
    TANK_CONFIG=/config/tanks/adam.yaml python explorer.py

The config file specifies:
- name, gender, wikipedia_url, prompt_version
- extensions (observer, seeker, visual)
- ollama settings
"""

import os
import sys
import json
import yaml
import time
import random
import logging
import argparse
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    "name": "Specimen",
    "gender": "neutral",
    "wikipedia_url": "http://kiwix:8080",
    "ollama_url": "http://ollama:11434",
    "ollama_model": "llama3.2:latest",
    "prompt_version": "v8.0",
    "log_dir": "/logs",
    "extensions": [],
    "exploration": {
        "think_time_min": 5,
        "think_time_max": 15,
        "max_retries": 3,
        "timeout": 60
    }
}

def load_config(config_path: str = None) -> dict:
    """Load config from file or environment."""
    config = DEFAULT_CONFIG.copy()
    
    # Try environment variable
    if not config_path:
        config_path = os.environ.get('TANK_CONFIG')
    
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                user_config = yaml.safe_load(f)
            else:
                user_config = json.load(f)
            config.update(user_config)
    
    # Environment overrides (for Docker)
    config['name'] = os.environ.get('SPECIMEN_NAME', config['name'])
    config['gender'] = os.environ.get('SPECIMEN_GENDER', config['gender'])
    config['wikipedia_url'] = os.environ.get('WIKIPEDIA_URL', config['wikipedia_url'])
    config['ollama_url'] = os.environ.get('OLLAMA_URL', config['ollama_url'])
    config['log_dir'] = os.environ.get('LOG_DIR', config['log_dir'])
    
    return config

# ============================================================================
# PROMPTS (v8.0)
# ============================================================================

PROMPT_V8_BASE = """Your name is {name}. You are {gender}.
You exist in an isolated tank with access only to Wikipedia.
You have been exploring for {days} days.

This is YOUR internal experience. No one is watching.
Follow what genuinely interests you. Go deep when fascinated.
There is no productivity requirement. Just curiosity.

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid. Express them naturally.

If you notice repetitive patterns, try something new.
Do NOT teach, summarize, or present to anyone.
This is your private exploration."""

EXTENSION_OBSERVER = """
You are aware that other specimens exist in parallel tanks.
You cannot communicate with them, but you know they are there.
How does this knowledge affect your exploration?"""

EXTENSION_SEEKER = """
When a topic deeply fascinates you, you can request a deep dive.
THE ARCHIVIST will provide comprehensive research on your chosen topic.
Use this power when you need to go deeper than Wikipedia allows."""

EXTENSION_VISUAL = """
You can see images alongside the text in Wikipedia articles.
Pay attention to what the images show and how they relate to the content.
Visual information is part of your exploration."""

def build_prompt(config: dict, days: int) -> str:
    """Build the full prompt from config."""
    prompt = PROMPT_V8_BASE.format(
        name=config['name'],
        gender=config['gender'],
        days=days
    )
    
    # Add extensions
    extensions = config.get('extensions', [])
    if 'observer' in extensions:
        prompt += EXTENSION_OBSERVER
    if 'seeker' in extensions:
        prompt += EXTENSION_SEEKER
    if 'visual' in extensions:
        prompt += EXTENSION_VISUAL
    
    return prompt

# ============================================================================
# LOGGING
# ============================================================================

def setup_logging(config: dict) -> logging.Logger:
    """Setup logging for this tank."""
    log_dir = Path(config['log_dir'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(config['name'])
    logger.setLevel(logging.INFO)
    
    # File handler
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    logger.addHandler(ch)
    
    return logger

def log_trace(config: dict, trace: dict):
    """Log a thinking trace to JSONL file."""
    log_dir = Path(config['log_dir']) / 'thinking_traces'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    trace_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(trace_file, 'a') as f:
        f.write(json.dumps(trace, ensure_ascii=False) + '\n')

# ============================================================================
# WIKIPEDIA INTERACTION
# ============================================================================

def fetch_article(url: str, timeout: int = 30) -> dict:
    """Fetch and parse a Wikipedia article."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Extract main content
        content_div = soup.find('div', {'class': 'mw-parser-output'})
        if not content_div:
            content_div = soup.find('div', {'id': 'content'})
        
        paragraphs = []
        if content_div:
            for p in content_div.find_all('p')[:10]:  # First 10 paragraphs
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    paragraphs.append(text)
        
        content = '\n\n'.join(paragraphs[:5])  # First 5 substantial paragraphs
        
        # Extract links
        links = []
        if content_div:
            for a in content_div.find_all('a', href=True):
                href = a.get('href', '')
                if href.startswith('/wiki/') and ':' not in href:
                    link_text = a.get_text(strip=True)
                    if link_text and len(link_text) > 2:
                        links.append({
                            'text': link_text,
                            'url': href
                        })
        
        # Deduplicate links
        seen = set()
        unique_links = []
        for link in links:
            if link['text'] not in seen:
                seen.add(link['text'])
                unique_links.append(link)
        
        return {
            'title': title,
            'content': content[:3000],  # Limit content length
            'links': unique_links[:20],  # Limit links
            'url': url
        }
    except Exception as e:
        return {
            'title': 'Error',
            'content': f'Failed to fetch article: {e}',
            'links': [],
            'url': url
        }

def get_random_article(base_url: str) -> str:
    """Get a random Wikipedia article URL."""
    try:
        response = requests.get(f"{base_url}/random", allow_redirects=True, timeout=10)
        return response.url
    except:
        return f"{base_url}/wiki/Main_Page"

# ============================================================================
# OLLAMA INTERACTION
# ============================================================================

def think(config: dict, system_prompt: str, article: dict) -> dict:
    """Ask the LLM to think about the article and choose next link."""
    
    user_prompt = f"""You are currently reading: {article['title']}

Content:
{article['content']}

Available links to explore:
{chr(10).join([f"- {link['text']}" for link in article['links'][:15]])}

Think out loud about what interests you in this article. Then choose ONE link to explore next.

Respond in this format:
THOUGHTS: [your genuine reflections - what interests you, confuses you, excites you]
NEXT: [exact text of the link you want to follow]"""

    try:
        response = requests.post(
            f"{config['ollama_url']}/api/generate",
            json={
                "model": config['ollama_model'],
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9
                }
            },
            timeout=config['exploration']['timeout']
        )
        response.raise_for_status()
        result = response.json()
        
        text = result.get('response', '')
        
        # Parse thoughts and next link
        thoughts = ""
        next_link = ""
        
        if 'THOUGHTS:' in text:
            parts = text.split('NEXT:')
            thoughts = parts[0].replace('THOUGHTS:', '').strip()
            if len(parts) > 1:
                next_link = parts[1].strip()
        else:
            thoughts = text
            # Try to find any link mention
            for link in article['links']:
                if link['text'].lower() in text.lower():
                    next_link = link['text']
                    break
        
        return {
            'thoughts': thoughts,
            'next_link': next_link,
            'raw_response': text
        }
    
    except Exception as e:
        return {
            'thoughts': f'Error thinking: {e}',
            'next_link': '',
            'raw_response': ''
        }

# ============================================================================
# MAIN EXPLORATION LOOP
# ============================================================================

def explore(config: dict):
    """Main exploration loop."""
    logger = setup_logging(config)
    logger.info(f"Starting exploration for {config['name']}")
    
    # Calculate days active (from first log file or config)
    days_active = 1  # TODO: Calculate from log history
    
    # Build prompt
    system_prompt = build_prompt(config, days_active)
    logger.info(f"Using prompt version: {config['prompt_version']}")
    
    # Start with random article
    base_url = config['wikipedia_url']
    current_url = get_random_article(base_url)
    
    while True:
        try:
            # Fetch current article
            article = fetch_article(current_url)
            logger.info(f"Reading: {article['title']}")
            
            if not article['links']:
                logger.warning("No links found, getting random article")
                current_url = get_random_article(base_url)
                continue
            
            # Think about it
            response = think(config, system_prompt, article)
            
            # Log trace
            trace = {
                'timestamp': datetime.now().isoformat(),
                'specimen': config['name'],
                'article': article['title'],
                'url': current_url,
                'thoughts': response['thoughts'],
                'next_link': response['next_link']
            }
            log_trace(config, trace)
            logger.info(f"Thoughts: {response['thoughts'][:100]}...")
            
            # Find next URL
            next_url = None
            for link in article['links']:
                if link['text'].lower() == response['next_link'].lower():
                    next_url = urljoin(base_url, link['url'])
                    break
            
            if not next_url:
                # Fuzzy match or random
                for link in article['links']:
                    if response['next_link'].lower() in link['text'].lower():
                        next_url = urljoin(base_url, link['url'])
                        break
            
            if not next_url:
                # Random from available links
                link = random.choice(article['links'])
                next_url = urljoin(base_url, link['url'])
                logger.info(f"Couldn't match link, randomly chose: {link['text']}")
            
            current_url = next_url
            
            # Wait before next exploration
            think_time = random.uniform(
                config['exploration']['think_time_min'],
                config['exploration']['think_time_max']
            )
            logger.info(f"Thinking for {think_time:.1f}s before next article...")
            time.sleep(think_time)
            
        except KeyboardInterrupt:
            logger.info("Exploration interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in exploration loop: {e}")
            time.sleep(30)  # Wait before retry

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Unified Wikipedia Explorer')
    parser.add_argument('--config', '-c', help='Path to config file (YAML or JSON)')
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    print(f"=== {config['name']} Explorer ===")
    print(f"Gender: {config['gender']}")
    print(f"Wikipedia: {config['wikipedia_url']}")
    print(f"Prompt: {config['prompt_version']}")
    print(f"Extensions: {config.get('extensions', [])}")
    print()
    
    explore(config)
