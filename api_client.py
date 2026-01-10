"""
OpenRouter API client for generating press releases and judgments.
"""

import os
import time
import json
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional


class OpenRouterClient:
    """Client for calling OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None, log_file: str = "data/api_calls.log"):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            log_file: Path to log file for API calls
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable."
            )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.call_count = 0

        # Set up logging
        self.logger = logging.getLogger("OpenRouterClient")
        self.logger.setLevel(logging.INFO)

        # Create file handler
        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setLevel(logging.INFO)

        # Create formatter with Warsaw timezone (GMT+1)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        # Set formatter to use Warsaw timezone
        formatter.converter = lambda *args: datetime.now(ZoneInfo('Europe/Warsaw')).timetuple()
        fh.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(fh)

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
        self.call_count += 1
        call_id = self.call_count

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature
        }

        # Log request
        self.logger.info(f"=" * 80)
        self.logger.info(f"API CALL #{call_id} - REQUEST")
        self.logger.info(f"Model: {model_id}")
        self.logger.info(f"Temperature: {temperature}")
        self.logger.info(f"Messages: {json.dumps(messages, indent=2, ensure_ascii=False)}")

        last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                elapsed_time = time.time() - start_time

                response.raise_for_status()
                data = response.json()
                response_content = data["choices"][0]["message"]["content"]

                # Log successful response
                self.logger.info(f"API CALL #{call_id} - RESPONSE (SUCCESS)")
                self.logger.info(f"Time: {elapsed_time:.2f}s")
                self.logger.info(f"Status: {response.status_code}")
                if "usage" in data:
                    self.logger.info(f"Usage: {json.dumps(data['usage'], indent=2)}")
                self.logger.info(f"Response content ({len(response_content)} chars):")
                self.logger.info(f"{response_content}")
                self.logger.info(f"=" * 80)

                return response_content

            except requests.exceptions.RequestException as e:
                last_error = e
                self.logger.error(f"API CALL #{call_id} - ATTEMPT {attempt + 1}/{max_retries} FAILED")
                self.logger.error(f"Error: {str(e)}")

                print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 2

        # Log final failure
        self.logger.error(f"API CALL #{call_id} - ALL ATTEMPTS FAILED")
        self.logger.error(f"Final error: {str(last_error)}")
        self.logger.info(f"=" * 80)

        raise Exception(f"API call failed after {max_retries} attempts: {last_error}")
