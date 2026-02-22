"""Ollama API client."""
import requests
from typing import Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.2:latest"):
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def generate(self, prompt: str, system: str = None, timeout: int = 60) -> str:
        """Generate a response from the model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9
            }
        }
        if system:
            payload["system"] = system
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json().get('response', '')
    
    def health_check(self) -> bool:
        """Check if Ollama is responding."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
