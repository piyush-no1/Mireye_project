import asyncio
import time
import httpx
from typing import Any, Dict, Optional
from app.config import settings
from app.core.logging import logger, log_tool_call

class ResilientHTTPClient:
    """Async httpx client wrapper with timeout and exponential backoff retry logic."""

    def __init__(
        self,
        timeout: float = float(settings.http_timeout_seconds),
        max_retries: int = settings.http_max_retries,
        backoff_base: float = settings.http_retry_backoff_base_seconds,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_override: Optional[float] = None,
    ) -> httpx.Response:
        effective_timeout = timeout_override or self.timeout
        start_time = time.time()
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=effective_timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    if response.status_code >= 500:
                        response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
                last_exception = e
                # Check if it's a 4xx error (non-retry eligible)
                if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                    logger.warning(f"HTTP 4xx non-retryable error for {url}: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    sleep_time = self.backoff_base * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {url} ({e}). Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed for {url}.")
                    raise e
            except Exception as e:
                raise e

        if last_exception:
            raise last_exception
        raise httpx.RequestError(f"Request failed for {url}")

    async def post(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_override: Optional[float] = None,
    ) -> httpx.Response:
        effective_timeout = timeout_override or float(settings.http_timeout_seconds_long)
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=effective_timeout) as client:
                    response = await client.post(url, json=json_data, headers=headers)
                    if response.status_code >= 500:
                        response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
                last_exception = e
                if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                    logger.warning(f"HTTP 4xx non-retryable error for {url}: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    sleep_time = self.backoff_base * (2 ** attempt)
                    logger.warning(f"POST attempt {attempt + 1} failed for {url} ({e}). Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"All {self.max_retries + 1} POST attempts failed for {url}.")
                    raise e
            except Exception as e:
                raise e

        if last_exception:
            raise last_exception
        raise httpx.RequestError(f"POST Request failed for {url}")

http_client = ResilientHTTPClient()
