"""
Async OpenRouter API client with concurrent request support and rate limiting.
"""

import os
import time
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, List


class AsyncOpenRouterClient:
    """Async client for calling OpenRouter API with concurrency control."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        log_file: str = "data/api_calls.log",
        max_concurrent: int = 10,
        max_rpm: int = 60
    ):
        """
        Initialize async OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            log_file: Path to log file for API calls
            max_concurrent: Maximum concurrent requests
            max_rpm: Maximum requests per minute (0 for no limit)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable."
            )
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.call_count = 0
        self.max_concurrent = max_concurrent
        self.max_rpm = max_rpm

        # Track request times for rate limiting
        self.request_times = []

        # Set up logging
        self.logger = logging.getLogger("AsyncOpenRouterClient")
        self.logger.setLevel(logging.INFO)

        # Create file handler
        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setLevel(logging.INFO)

        # Create formatter with Warsaw timezone
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        formatter.converter = lambda *args: datetime.now(ZoneInfo('Europe/Warsaw')).timetuple()
        fh.setFormatter(formatter)

        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(fh)

    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        if self.max_rpm <= 0:
            return

        now = time.time()
        # Remove timestamps older than 60 seconds
        self.request_times = [t for t in self.request_times if now - t < 60]

        # If we're at the limit, wait until oldest request expires
        if len(self.request_times) >= self.max_rpm:
            sleep_time = 60 - (now - self.request_times[0]) + 0.1
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

        # Record this request time
        self.request_times.append(time.time())

    async def call_async(
        self,
        session: aiohttp.ClientSession,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> str:
        """
        Call OpenRouter API asynchronously with retry logic.

        Args:
            session: aiohttp ClientSession
            model_id: Model identifier
            messages: List of message dicts
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
            retry_delay: Seconds between retries

        Returns:
            Response content as string
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
                # Wait for rate limit
                await self._wait_for_rate_limit()

                start_time = time.time()
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    elapsed_time = time.time() - start_time

                    # Log rate limit headers
                    rate_limit_info = {}
                    for header in ['x-ratelimit-limit-requests', 'x-ratelimit-remaining-requests',
                                   'x-ratelimit-reset-requests', 'x-ratelimit-limit-tokens',
                                   'x-ratelimit-remaining-tokens']:
                        if header in response.headers:
                            rate_limit_info[header] = response.headers[header]

                    if rate_limit_info:
                        self.logger.info(f"Rate Limit Headers: {json.dumps(rate_limit_info, indent=2)}")

                    response.raise_for_status()
                    data = await response.json()
                    response_content = data["choices"][0]["message"]["content"]

                    # Log successful response
                    self.logger.info(f"API CALL #{call_id} - RESPONSE (SUCCESS)")
                    self.logger.info(f"Time: {elapsed_time:.2f}s")
                    self.logger.info(f"Status: {response.status}")
                    if "usage" in data:
                        self.logger.info(f"Usage: {json.dumps(data['usage'], indent=2)}")
                    self.logger.info(f"Response content ({len(response_content)} chars):")
                    self.logger.info(f"{response_content}")
                    self.logger.info(f"=" * 80)

                    return response_content

            except Exception as e:
                last_error = e
                self.logger.error(f"API CALL #{call_id} - ATTEMPT {attempt + 1}/{max_retries} FAILED")
                self.logger.error(f"Error: {str(e)}")

                print(f"API call #{call_id} failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        # Log final failure
        self.logger.error(f"API CALL #{call_id} - ALL ATTEMPTS FAILED")
        self.logger.error(f"Final error: {str(last_error)}")
        self.logger.info(f"=" * 80)

        raise Exception(f"API call #{call_id} failed after {max_retries} attempts: {last_error}")

    async def call_batch(
        self,
        requests: List[Dict],
        temperature: float = 0.7,
        progress_callback=None
    ) -> List:
        """
        Call OpenRouter API for multiple requests concurrently.

        Args:
            requests: List of dicts with 'model_id' and 'messages'
            temperature: Sampling temperature
            progress_callback: Optional callback function called after each request completes

        Returns:
            List of response strings (or Exception objects for failures)
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = [None] * len(requests)

        async def limited_call(session, idx, req):
            async with semaphore:
                try:
                    result = await self.call_async(
                        session,
                        req['model_id'],
                        req['messages'],
                        temperature=temperature
                    )
                    results[idx] = result
                except Exception as e:
                    results[idx] = e
                finally:
                    if progress_callback:
                        progress_callback()

        async with aiohttp.ClientSession() as session:
            tasks = [limited_call(session, i, req) for i, req in enumerate(requests)]
            await asyncio.gather(*tasks)
            return results
