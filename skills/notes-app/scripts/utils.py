#!/usr/bin/env python3
"""Utility functions for notes-app scripts."""


def _escape_applescript(text: str) -> str:
    """Escape text for AppleScript string literal.

    Handles quotes, backslashes, and newlines.
    """
    # Escape backslashes FIRST (to avoid double-escaping)
    text = text.replace('\\', '\\\\')
    # Escape quotes
    text = text.replace('"', '\\"')
    # Escape newlines for AppleScript string literal
    text = text.replace('\r\n', '\\n')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\n')
    return text
