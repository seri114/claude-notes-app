#!/usr/bin/env python3
"""Delete a note from Notes.app by title.

Usage:
    delete_note.py "Title"

Environment variables:
    NOTES_ACCOUNT: Account name (default: "iCloud")
    NOTES_FOLDER: Folder name (default: "Notes")
    LIMIT: Maximum notes to search (default: 100)

Note: Deletes the first matching note found (most recently modified).
"""

import os
import subprocess
import sys

from utils import _escape_applescript


def main() -> int:
    title = sys.argv[1] if len(sys.argv) > 1 else ""
    if not title:
        print("Usage: delete_note.py \"Title\"", file=sys.stderr)
        return 1

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

    set noteName to name of targetNote
    delete targetNote
    return "Deleted note: " & noteName
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

    if result.returncode == 0 and not output.startswith("ERROR:"):
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
