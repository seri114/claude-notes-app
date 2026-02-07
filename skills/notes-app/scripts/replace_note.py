#!/usr/bin/env python3
"""Replace an existing note in Notes.app with Markdown from STDIN.

Usage:
    replace_note.py "Title" < file.md
    echo "Content" | replace_note.py "Title"

Environment variables:
    NOTES_ACCOUNT: Account name (default: "iCloud")
    NOTES_FOLDER: Folder name (default: "Notes")
    LIMIT: Maximum notes to search (default: 100)
"""

import os
import subprocess
import sys

from utils import _escape_applescript


def main() -> int:
    from converter import markdown_to_html

    title = sys.argv[1] if len(sys.argv) > 1 else ""
    if not title:
        print("Usage: replace_note.py \"Title\" < file.md", file=sys.stderr)
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
    limit = os.environ.get('LIMIT', '100')

    # Build AppleScript
    script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteList to every note in theFolder
    set targetNote to missing value
    set searchLimit to {limit}
    set checkedCount to 0
    repeat with n in noteList
        set checkedCount to checkedCount + 1
        if checkedCount > searchLimit then
            return "ERROR: Note not found (searched first " & searchLimit & " notes)"
        end if
        if name of n is "{_escape_applescript(title)}" then
            set targetNote to n
            exit repeat
        end if
    end repeat

    if targetNote is missing value then
        return "ERROR: Note not found"
    end if

    set originalName to name of targetNote
    set noteBody to "{_escape_applescript(html)}" as Unicode text
    set body of targetNote to noteBody
    set name of targetNote to originalName
    return "SUCCESS"
end tell
'''

    # Execute AppleScript
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()
    print(output)

    if result.returncode == 0 and output == "SUCCESS":
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
