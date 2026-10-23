"""Abstract base class for LLM clients."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients supporting different providers."""

    def __init__(self, model: str, temperature: float = 0.7):
        """
        Initialize the LLM client.

        Args:
            model: Model identifier (e.g., 'gpt-4o-mini', 'claude-3-sonnet')
            temperature: Sampling temperature for generation
        """
        self.model = model
        self.temperature = temperature

    @abstractmethod
    def call_with_json_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
        max_tokens: int = 100
    ) -> Dict[str, Any]:
        """
        Call the LLM with a JSON schema for structured output.

        Args:
            system_prompt: System message defining the agent's role and context
            user_prompt: User message with the specific task/question
            json_schema: JSON schema defining the expected output structure
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response matching the schema
        """
        pass

    @abstractmethod
    def call_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 150
    ) -> str:
        """
        Call the LLM for simple text generation without structured output.

        Args:
            system_prompt: System message defining the agent's role and context
            user_prompt: User message with the specific task/question
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass
