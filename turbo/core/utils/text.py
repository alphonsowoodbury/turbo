"""Text processing utilities."""

import re


def strip_emojis(text: str) -> str:
    """
    Remove all emoji characters from text.

    Args:
        text: Input text that may contain emojis

    Returns:
        Text with all emojis removed
    """
    if not text:
        return text

    # Emoji regex pattern - covers most emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # extended symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "]+",
        flags=re.UNICODE
    )

    # Remove emojis and clean up extra whitespace
    text = emoji_pattern.sub('', text)

    # Clean up multiple spaces (but preserve newlines for markdown)
    # Only collapse consecutive spaces/tabs, not newlines
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove trailing whitespace from each line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    return text


def clean_text(text: str) -> str:
    """
    Clean text by removing emojis and normalizing whitespace.

    Args:
        text: Input text to clean

    Returns:
        Cleaned text
    """
    return strip_emojis(text)
