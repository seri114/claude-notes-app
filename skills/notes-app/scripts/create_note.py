#!/usr/bin/env python3
"""Create a new note in Notes.app from Markdown via STDIN.

Usage:
    create_note.py "Title" < file.md
    echo "Content" | create_note.py "Title"

Environment variables:
    NOTES_ACCOUNT: Account name (default: "iCloud")
    NOTES_FOLDER: Folder name (default: "Notes")
"""

import os
import subprocess
import sys

from utils import _escape_applescript


def main() -> int:
    from converter import markdown_to_html

    title = sys.argv[1] if len(sys.argv) > 1 else ""
    if not title:
        print("Usage: create_note.py \"Title\" < file.md", file=sys.stderr)
        return 1

    # Read Markdown from STDIN
    markdown = sys.stdin.read()

    # Ensure first line is the title (Notes.app uses first line as title)
    # Accept "Title", "# Title", "## Title", "### Title", etc.
    import re
    lines = markdown.strip().split('\n')
    if lines:
        first_line = lines[0].strip()
        # Check if first line matches title (with 0+ # prefix)
        title_pattern = rf'^#+\s+{re.escape(title)}$|^{re.escape(title)}$'
        if not re.match(title_pattern, first_line):
            markdown = f"# {title}\n\n{markdown.strip()}"

    # Convert to HTML
    html = markdown_to_html(markdown)

    # Get environment variables
    account = os.environ.get('NOTES_ACCOUNT', 'iCloud')
    folder = os.environ.get('NOTES_FOLDER', 'Notes')

    # Build AppleScript - create note, then set name explicitly
    script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteBody to "{_escape_applescript(html)}" as Unicode text
    set newNote to make new note at theFolder with properties {{body:noteBody}}
    set name of newNote to "{_escape_applescript(title)}"
    return "Created note"
end tell
'''

    # Execute AppleScript
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Created note")
        return 0
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
