"""OpenRouter LLM client implementation."""
from __future__ import annotations
import json
import requests
import time
from typing import Dict, Any
from src.llm.base import BaseLLMClient
from src.llm.capabilities import supports_structured_output


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client with structured output support."""

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini", temperature: float = 0.7,
                 timeout: int = 120, max_retries: int = 3,
                 base_url: str = "https://openrouter.ai/api/v1/chat/completions"):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (e.g., 'openai/gpt-4o-mini', 'anthropic/claude-3.5-sonnet')
            temperature: Sampling temperature
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        super().__init__(model, temperature)
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Check if model supports structured outputs
        self.supports_structured_output = supports_structured_output(model)

    def _make_request(
        self,
        messages: list,
        response_format: Dict[str, Any] = None,
        max_tokens: int = 100
    ) -> Dict[str, Any]:
        """
        Make a request to OpenRouter API with retry logic.

        Args:
            messages: List of message dicts with role and content
            response_format: Optional JSON schema for structured output
            max_tokens: Max tokens to generate

        Returns:
            API response as dict

        Raises:
            Exception: If API request fails after all retries
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens
        }

        # Add structured output if supported
        if response_format and self.supports_structured_output:
            data["response_format"] = response_format

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    print(f"Retryable error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)

            except requests.exceptions.HTTPError as e:
                last_exception = e
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if status_code in [429, 500, 502, 503, 504] and attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) + (time.time() % 1)
                        print(f"HTTP {status_code} error (attempt {attempt + 1}/{self.max_retries})")
                        print(f"Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"OpenRouter API request failed: {e}")
                else:
                    raise Exception(f"OpenRouter API request failed: {e}")

            except requests.exceptions.RequestException as e:
                last_exception = e
                raise Exception(f"OpenRouter API request failed: {e}")

        raise Exception(f"OpenRouter API request failed after {self.max_retries} attempts: {last_exception}")

    def call_with_json_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        max_tokens: int = 100
    ) -> Dict[str, Any]:
        """
        Call OpenRouter with structured JSON output.

        Args:
            system_prompt: System message
            user_prompt: User message
            json_schema: JSON schema for structured output
            max_tokens: Max tokens to generate

        Returns:
            Parsed JSON response
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # For models with structured output support
            if self.supports_structured_output:
                response_format = {
                    "type": "json_schema",
                    "json_schema": json_schema
                }
                response = self._make_request(messages, response_format, max_tokens)
                raw = response["choices"][0]["message"]["content"].strip()
                return json.loads(raw)

            # For models without structured output, enhance prompt
            else:
                enhanced_user_prompt = (
                    user_prompt +
                    "\n\nIMPORTANT: You must respond with ONLY valid JSON matching this schema. "
                    "No explanation, no markdown, just the JSON object.\n\n"
                    f"Required JSON schema:\n{json.dumps(json_schema.get('schema', {}), indent=2)}"
                )

                messages[1]["content"] = enhanced_user_prompt

                response = self._make_request(messages, None, max_tokens)
                raw = response["choices"][0]["message"]["content"].strip()

                # Try to extract JSON if wrapped in markdown code blocks
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()

                return json.loads(raw)

        except Exception as e:
            # Report the failure instead of fabricating the schema's fields with empty
            # values -- an empty field is indistinguishable from a real decision once
            # it reaches the game logic. Callers treat "_error" as a parse failure.
            print(f"Warning: OpenRouter call failed with error: {e}")
            return {"_error": str(e)}

    def call_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 150
    ) -> str:
        """
        Call OpenRouter for simple text generation.

        Args:
            system_prompt: System message
            user_prompt: User message
            max_tokens: Max tokens to generate

        Returns:
            Generated text
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self._make_request(messages, None, max_tokens)
            return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"Warning: OpenRouter call failed with error: {e}")
            return ""
