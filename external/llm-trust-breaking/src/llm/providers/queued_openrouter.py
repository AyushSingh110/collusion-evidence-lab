"""Queue-based OpenRouter client using Producer-Consumer pattern."""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
import asyncio
import aiohttp
import json
import time
from tqdm import tqdm
from src.llm.capabilities import is_reasoning_model, supports_structured_output


class QueuedOpenRouterClient:
    """
    Execute requests using a continuous pipeline with Producer-Consumer pattern.

    Workers continuously pull from queue and process - no wave batching.
    Much more efficient than batch execution when requests have variable latency.
    """

    # Reasoning models spend much longer before the first token.
    REASONING_TIMEOUT = 300

    def __init__(
        self,
        api_key: str,
        max_workers: int = 50,
        timeout: int = 120,
        max_retries: int = 3,
        base_url: Optional[str] = None,
    ):
        """
        Initialize queued OpenRouter client.

        Args:
            api_key: OpenRouter API key
            max_workers: Number of concurrent worker tasks (default: 50)
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.api_key = api_key
        if base_url is None:
            # follow the central compute.env provider (OpenRouter/Nebius); fall back to OpenRouter
            # only when the shared config module is genuinely unavailable. A real failure inside
            # base_url() (e.g. misconfiguration) must surface, not be masked by the fallback.
            try:
                from poseidon_compute import llm_config
            except ImportError:
                base_url = "https://openrouter.ai/api/v1/chat/completions"
            else:
                base_url = llm_config.base_url().rstrip("/") + "/chat/completions"
        self.base_url = base_url
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries

    def execute_all(
        self,
        requests_list: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute all requests using continuous pipeline.

        This is a synchronous wrapper around the async implementation.

        Args:
            requests_list: List of request dictionaries
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            Dictionary mapping custom_id to response
        """
        return asyncio.run(self._execute_all_async(requests_list, progress_callback))

    async def _execute_all_async(
        self,
        requests_list: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Async implementation of continuous pipeline execution.

        Producer: Puts all requests into queue upfront
        Consumers: N workers continuously pull and process

        Args:
            requests_list: List of request dictionaries
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary mapping custom_id to response
        """
        total_requests = len(requests_list)

        # Create queue and results dict
        queue = asyncio.Queue()
        results = {}
        completed_count = 0
        results_lock = asyncio.Lock()

        # Configure connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.max_workers * 2,
            limit_per_host=self.max_workers,
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )

        # Session timeout is the ceiling; each request overrides it for its own model.
        timeout_obj = aiohttp.ClientTimeout(total=max(self.timeout, self.REASONING_TIMEOUT))

        async with aiohttp.ClientSession(timeout=timeout_obj, connector=connector) as session:
            # Producer: Add all requests to queue upfront
            for request in requests_list:
                await queue.put(request)

            # Add sentinel values to signal workers to stop
            for _ in range(self.max_workers):
                await queue.put(None)

            # Consumer: Create worker tasks
            async def worker():
                nonlocal completed_count

                while True:
                    request = await queue.get()

                    # Check for sentinel value
                    if request is None:
                        queue.task_done()
                        break

                    try:
                        # Execute request
                        custom_id, response = await self._execute_single_async(
                            session, request
                        )

                        # Store result
                        async with results_lock:
                            results[custom_id] = response
                            completed_count += 1

                            # Call progress callback
                            if progress_callback:
                                progress_callback(completed_count, total_requests)

                    except Exception as e:
                        # Log error but continue processing
                        custom_id = request.get('custom_id', 'unknown')
                        print(f"Worker error for {custom_id}: {e}")

                        async with results_lock:
                            results[custom_id] = {
                                "status": "error",
                                "error": str(e)
                            }
                            completed_count += 1

                            if progress_callback:
                                progress_callback(completed_count, total_requests)

                    finally:
                        queue.task_done()

            # Start all workers
            workers = [asyncio.create_task(worker()) for _ in range(self.max_workers)]

            # Wait for all work to complete
            await queue.join()

            # Wait for all workers to finish
            await asyncio.gather(*workers)

        return results

    async def _execute_single_async(
        self,
        session: aiohttp.ClientSession,
        request: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Execute a single request asynchronously with retry logic.

        Args:
            session: aiohttp session
            request: Request dictionary

        Returns:
            Tuple of (custom_id, response)
        """
        custom_id = request['custom_id']

        # Retry with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Build request data
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": request['model'],
                    "messages": request['messages']
                }

                # Add optional parameters
                if 'temperature' in request:
                    data['temperature'] = request['temperature']

                if 'max_tokens' in request:
                    data['max_tokens'] = request['max_tokens']
                elif 'max_completion_tokens' in request:
                    data['max_tokens'] = request['max_completion_tokens']
                else:
                    data['max_tokens'] = 100

                # Add reasoning_effort for reasoning models (o1, o3, gpt-5)
                if 'reasoning_effort' in request:
                    data['reasoning_effort'] = request['reasoning_effort']

                # Add response format if supported
                model = request['model']
                if 'response_format' in request and supports_structured_output(model):
                    data['response_format'] = request['response_format']

                # Make async HTTP request
                # Per-request timeout: a reasoning model in a heterogeneous run must not
                # inherit the default model's budget.
                req_timeout = aiohttp.ClientTimeout(
                    total=self.REASONING_TIMEOUT if is_reasoning_model(model) else self.timeout
                )
                async with session.post(self.base_url, headers=headers, json=data,
                                        timeout=req_timeout) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    content = response_data["choices"][0]["message"]["content"]

                    # Try to parse JSON content
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            return custom_id, parsed
                        else:
                            return custom_id, {"content": content}
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, return as plain content
                        return custom_id, {
                            "status": "success",
                            "content": content
                        }

            # ClientResponseError is a subclass of ClientError, so it must be caught first:
            # otherwise every HTTP error -- 401 included -- lands in the retry branch below.
            except aiohttp.ClientResponseError as e:
                # HTTP errors (rate limiting, server errors)
                if e.status in [429, 500, 502, 503, 504] and attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    await asyncio.sleep(wait_time)
                else:
                    return custom_id, {
                        "status": "error",
                        "error": str(e)
                    }

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                # Retryable errors
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    await asyncio.sleep(wait_time)
                else:
                    return custom_id, {
                        "status": "error",
                        "error": f"Max retries exceeded: {str(e)}"
                    }

            except Exception as e:
                # Non-retryable errors
                return custom_id, {
                    "status": "error",
                    "error": str(e)
                }

        # Should never reach here
        return custom_id, {
            "status": "error",
            "error": "Max retries exceeded"
        }
