"""
Console Output Formatting Utilities

Provides consistent, terminal-width-aware formatting for console output.
Uses tqdm.write() for compatibility with progress bars.
"""

import shutil
from tqdm import tqdm
from typing import Optional


def get_terminal_width() -> int:
    """
    Get current terminal width, with fallback to 80.

    Returns:
        Terminal width in characters
    """
    try:
        width = shutil.get_terminal_size().columns
        return max(60, min(width, 120))  # Clamp between 60-120
    except (AttributeError, ValueError):
        return 80


def write_separator(char: str = "=", width: Optional[int] = None):
    """
    Write a separator line using tqdm.write().

    Args:
        char: Character to repeat (default: "=")
        width: Line width (auto-detects if None)
    """
    if width is None:
        width = get_terminal_width()
    tqdm.write(char * width)


def write_header(title: str, width: Optional[int] = None):
    """
    Write a centered header with separator lines.

    Args:
        title: Header text
        width: Line width (auto-detects if None)
    """
    if width is None:
        width = get_terminal_width()
    tqdm.write("")
    write_separator("=", width)
    tqdm.write(title.center(width))
    write_separator("=", width)


def write_section(title: str, prefix: str = "", width: Optional[int] = None):
    """
    Write a section header with optional prefix.

    Args:
        title: Section title
        prefix: Optional prefix (e.g., "Step 1:")
        width: Line width (auto-detects if None)
    """
    if width is None:
        width = get_terminal_width()
    tqdm.write("")
    write_separator("-", width)
    full_title = f"{prefix} {title}".strip()
    tqdm.write(full_title.center(width))
    write_separator("-", width)


def write_info(message: str, indent: int = 0):
    """
    Write an info message with optional indentation.

    Args:
        message: Message to write
        indent: Indentation level (spaces)
    """
    tqdm.write(" " * indent + message)


def write_box(title: str, content: list[str], width: Optional[int] = None):
    """
    Write a boxed section with title and content.

    Args:
        title: Box title
        content: List of content lines
        width: Box width (auto-detects if None)
    """
    if width is None:
        width = get_terminal_width()

    tqdm.write("")
    write_separator("=", width)
    tqdm.write(title.center(width))
    write_separator("=", width)
    for line in content:
        tqdm.write(line)
    write_separator("=", width)
