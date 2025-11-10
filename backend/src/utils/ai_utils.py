"""
AI/LLM utility functions for working with OpenAI API responses.

This module provides helper functions for parsing and processing responses
from OpenAI's GPT models, particularly for extracting structured data.
"""

import json
from typing import Any, Dict


def extract_json_from_markdown(content: str) -> str:
    """
    Extract JSON content from markdown code blocks.

    OpenAI models often wrap JSON responses in markdown code fences.
    This function extracts the raw JSON string from these blocks.

    Args:
        content: String content that may contain markdown code blocks

    Returns:
        Cleaned JSON string (or original content if no code blocks found)

    Examples:
        >>> content = '```json\\n{"key": "value"}\\n```'
        >>> extract_json_from_markdown(content)
        '{"key": "value"}'

        >>> content = '```\\n{"key": "value"}\\n```'
        >>> extract_json_from_markdown(content)
        '{"key": "value"}'

        >>> content = '{"key": "value"}'  # No code blocks
        >>> extract_json_from_markdown(content)
        '{"key": "value"}'
    """
    content = content.strip()

    # Check for json code block
    if "```json" in content:
        # Extract content between ```json and ```
        parts = content.split("```json", 1)
        if len(parts) > 1:
            json_part = parts[1].split("```", 1)
            return json_part[0].strip()

    # Check for generic code block
    elif "```" in content:
        # Extract content between ``` and ```
        parts = content.split("```", 1)
        if len(parts) > 1:
            code_part = parts[1].split("```", 1)
            return code_part[0].strip()

    # No code blocks found, return as-is
    return content


def parse_json_response(content: str) -> Dict[str, Any]:
    """
    Parse JSON from OpenAI response, handling markdown code blocks.

    Combines markdown extraction and JSON parsing in one convenient function.

    Args:
        content: String content from OpenAI API response

    Returns:
        Parsed JSON as dictionary

    Raises:
        json.JSONDecodeError: If content is not valid JSON after extraction

    Examples:
        >>> content = '```json\\n{"result": "success"}\\n```'
        >>> parse_json_response(content)
        {'result': 'success'}
    """
    cleaned = extract_json_from_markdown(content)
    return json.loads(cleaned)


def count_tokens_estimate(text: str, model: str = "gpt-4") -> int:
    """
    Estimate token count for a given text.

    This is a rough estimation. For exact counts, use tiktoken library.
    Rule of thumb: ~4 characters per token for English text.

    Args:
        text: Text to estimate token count for
        model: Model name (for future tiktoken integration)

    Returns:
        Estimated token count

    Examples:
        >>> count_tokens_estimate("Hello, world!")
        4
        >>> count_tokens_estimate("A" * 100)
        25
    """
    # Rough estimation: 4 characters per token
    # This is conservative and works for English text
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text to approximately fit within token limit.

    Uses rough estimation. For production, consider using tiktoken library.

    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        model: Model name (for future tiktoken integration)

    Returns:
        Truncated text that fits within token limit

    Examples:
        >>> truncate_to_tokens("Hello " * 100, max_tokens=10)
        'Hello Hello Hello Hello Hello Hello Hello Hello Hello Hello ...'
    """
    estimated_tokens = count_tokens_estimate(text, model)

    if estimated_tokens <= max_tokens:
        return text

    # Calculate approximate character limit
    # Using 4 chars per token, subtract some for safety and "..."
    char_limit = (max_tokens * 4) - 10

    truncated = text[:char_limit]
    return truncated + "..."
