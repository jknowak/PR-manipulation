"""
OpenRouter API client for generating press releases and judgments.
"""

import os
import time
import requests
from typing import Optional


class OpenRouterClient:
    """Client for calling OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable."
            )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def call(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> str:
        """
        Call OpenRouter API with retry logic.

        Args:
            model_id: Model identifier (e.g., 'anthropic/claude-sonnet-4.5')
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_retries: Maximum number of retry attempts
            retry_delay: Seconds to wait between retries

        Returns:
            Response content as string

        Raises:
            Exception: If all retry attempts fail
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 2

        raise Exception(f"API call failed after {max_retries} attempts: {last_error}")
