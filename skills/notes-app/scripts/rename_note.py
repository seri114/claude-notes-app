#!/usr/bin/env python3
"""Rename a note in Notes.app.

Usage:
    rename_note.py "Old Title" "New Title"

Environment variables:
    NOTES_ACCOUNT: Account name (default: "iCloud")
    NOTES_FOLDER: Folder name (default: "Notes")
"""

import os
import subprocess
import sys

from utils import _escape_applescript


def main() -> int:
    old_title = sys.argv[1] if len(sys.argv) > 1 else ""
    new_title = sys.argv[2] if len(sys.argv) > 2 else ""

    if not old_title or not new_title:
        print("Usage: rename_note.py \"Old Title\" \"New Title\"", file=sys.stderr)
        return 1

    # Get environment variables
    account = os.environ.get('NOTES_ACCOUNT', 'iCloud')
    folder = os.environ.get('NOTES_FOLDER', 'Notes')

    # First, get the current body HTML
    get_script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteList to every note in theFolder
    repeat with n in noteList
        if name of n is "{old_title}" then
            return body of n
        end if
    end repeat
    return "ERROR: Note not found"
end tell
'''

    get_result = subprocess.run(['osascript', '-e', get_script], capture_output=True, text=True)

    if get_result.returncode != 0 or "ERROR" in get_result.stdout:
        print("ERROR: Note not found")
        return 1

    html_body = get_result.stdout.strip()

    # Convert HTML to Markdown, replace title, convert back to HTML
    from converter import html_to_markdown, markdown_to_html

    # Convert to Markdown
    markdown_body = html_to_markdown(html_body)

    # Simple string replacement in first line
    lines = markdown_body.split('\n')
    if lines:
        first_line = lines[0]
        # Replace old title with new title (keep header level if present)
        if '#' in first_line:
            # Header format: "# Old Title" -> "# New Title" or "#Old Title" -> "#New Title"
            if f'# {old_title}' in first_line:
                lines[0] = first_line.replace(f'# {old_title}', f'# {new_title}')
            elif f'#{old_title}' in first_line:
                lines[0] = first_line.replace(f'#{old_title}', f'#{new_title}')
            else:
                # Try to replace just the title part
                parts = first_line.split(' ', 1)
                if len(parts) == 2 and parts[1] == old_title:
                    lines[0] = f"{parts[0]} {new_title}"
                else:
                    lines[0] = first_line.replace(old_title, new_title)
        else:
            # Plain text: just replace
            lines[0] = first_line.replace(old_title, new_title)

    updated_markdown = '\n'.join(lines)

    # Convert back to HTML
    new_html_body = markdown_to_html(updated_markdown)

    # Build AppleScript to update both name and body
    script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteList to every note in theFolder
    repeat with n in noteList
        if name of n is "{old_title}" then
            set name of n to "{new_title}"
            set body of n to "{_escape_applescript(new_html_body)}" as Unicode text
            return "SUCCESS"
        end if
    end repeat
    return "ERROR: Note not found"
end tell
'''

    # Execute AppleScript
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True
    )

    print(result.stdout.strip())

    if result.returncode == 0 and result.stdout.strip() == "SUCCESS":
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
