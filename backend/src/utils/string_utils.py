"""
String utility functions for text processing and sanitization.

This module provides common string operations used throughout the application,
particularly for creating filesystem-safe names and cleaning user input.
"""

import re


def to_safe_filename(name: str, replace_char: str = '_') -> str:
    """
    Convert a name to a filesystem-safe string.

    Converts to lowercase, replaces spaces and forward slashes with
    the specified replacement character (default: underscore).

    Args:
        name: The string to convert (e.g., product name, campaign name)
        replace_char: Character to use for replacing unsafe characters (default: '_')

    Returns:
        Filesystem-safe string suitable for use in file/directory names

    Examples:
        >>> to_safe_filename("Summer T-Shirt")
        'summer_t-shirt'
        >>> to_safe_filename("Product A/B Test")
        'product_a_b_test'
        >>> to_safe_filename("Test Product", replace_char='-')
        'test-product'
    """
    # Convert to lowercase
    safe_name = name.lower()

    # Replace spaces and slashes
    safe_name = safe_name.replace(' ', replace_char)
    safe_name = safe_name.replace('/', replace_char)

    return safe_name


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing or replacing unsafe characters.

    Removes characters that are problematic across different filesystems
    (Windows, macOS, Linux) and optionally truncates to maximum length.

    Args:
        filename: The filename to sanitize
        max_length: Maximum filename length (default: 255, typical filesystem limit)

    Returns:
        Sanitized filename safe for all major filesystems

    Examples:
        >>> sanitize_filename('my file: test?.txt')
        'my_file_test.txt'
        >>> sanitize_filename('a' * 300, max_length=10)
        'aaaaaaaaaa'
    """
    # Remove or replace unsafe characters
    # Unsafe: < > : " / \ | ? *
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing dots and spaces (Windows issue)
    filename = filename.strip('. ')

    # Truncate to max length
    if len(filename) > max_length:
        # Try to preserve extension if present
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            # Reserve space for extension + dot
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]

    return filename


def truncate_text(text: str, max_words: int = 10, suffix: str = '...') -> str:
    """
    Truncate text to a maximum number of words.

    Args:
        text: Text to truncate
        max_words: Maximum number of words to keep
        suffix: String to append if text was truncated (default: '...')

    Returns:
        Truncated text

    Examples:
        >>> truncate_text("This is a very long message that needs truncating", max_words=5)
        'This is a very long...'
        >>> truncate_text("Short text", max_words=10)
        'Short text'
    """
    words = text.split()

    if len(words) <= max_words:
        return text

    truncated = ' '.join(words[:max_words])
    return truncated + suffix
