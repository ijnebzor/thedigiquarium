"""
Ollama API client with exponential backoff retry logic.
"""
import os
import time
import logging
import requests
from typing import Optional

# Setup logging
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama API client with exponential backoff retry logic.

    Features:
    - 3 retries with delays: 2s -> 4s -> 8s
    - Only retries on connection errors, timeouts, and 5xx status codes
    - Does not retry on 4xx errors
    - Logs all retry attempts
    """

    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.2:latest"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_retries = 3
        self.base_delay = 2  # seconds

    def _should_retry(self, exception: Exception, status_code: Optional[int] = None) -> bool:
        """
        Determine if we should retry based on exception type or status code.

        Retries on:
        - Connection errors (ConnectionError)
        - Timeouts (Timeout, ReadTimeout, ConnectTimeout)
        - 5xx server errors

        Does NOT retry on:
        - 4xx client errors
        """
        # Check status code if provided
        if status_code is not None:
            if 500 <= status_code < 600:
                return True
            if 400 <= status_code < 500:
                return False

        # Check exception type
        if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
            return True
        if isinstance(exception, requests.RequestException):
            return False

        return False

    def _retry_with_backoff(self, method, url, **kwargs):
        """
        Execute a request with exponential backoff retry logic.

        Args:
            method: requests method (get, post, etc.)
            url: request URL
            **kwargs: additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            RequestException: if all retries fail
        """
        attempt = 0
        last_exception = None

        while attempt <= self.max_retries:
            try:
                response = method(url, **kwargs)

                # Check for 5xx errors
                if 500 <= response.status_code < 600:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(
                            f"5xx error {response.status_code} from {url}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(delay)
                        attempt += 1
                        continue

                # For 4xx errors or successful responses, return immediately
                response.raise_for_status()
                return response

            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Connection error from {url}: {e}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    raise

            except requests.HTTPError as e:
                # 4xx errors should not be retried
                raise

        # If we've exhausted retries
        if last_exception:
            logger.error(f"All {self.max_retries} retries failed for {url}")
            raise last_exception

    def generate(self, prompt: str, system: str = None, timeout: int = 60) -> str:
        """
        Generate a response from the model with retry logic.

        Args:
            prompt: The prompt to send to the model
            system: Optional system message
            timeout: Request timeout in seconds

        Returns:
            Generated response text
        """
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

        url = f"{self.base_url}/api/generate"

        response = self._retry_with_backoff(
            requests.post,
            url,
            json=payload,
            timeout=timeout
        )

        return response.json().get('response', '')

    def health_check(self) -> bool:
        """
        Check if Ollama is responding with retry logic.

        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = self._retry_with_backoff(
                requests.get,
                url,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
