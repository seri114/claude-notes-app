#!/usr/bin/env python3
"""List notes in Notes.app.

Usage:
    list_notes.py [pattern]

Arguments:
    pattern: Optional pattern to filter note titles

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
    pattern = sys.argv[1] if len(sys.argv) > 1 else ""

    # Get environment variables
    account = os.environ.get('NOTES_ACCOUNT', 'iCloud')
    folder = os.environ.get('NOTES_FOLDER', 'Notes')
    limit = os.environ.get('LIMIT', '100')

    # Build AppleScript
    if pattern:
        script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteList to every note in theFolder
    set resultNames to {{}}
    set searchLimit to {limit}
    set checkedCount to 0
    repeat with n in noteList
        set checkedCount to checkedCount + 1
        if checkedCount > searchLimit then
            exit repeat
        end if
        if name of n contains "{_escape_applescript(pattern)}" then
            set end of resultNames to name of n
        end if
    end repeat
    return resultNames
end tell
'''
    else:
        script = f'''
tell application "Notes"
    set theAccount to account "{account}"
    set theFolder to folder "{folder}" of theAccount
    set noteList to every note in theFolder
    set resultNames to {{}}
    set searchLimit to {limit}
    set checkedCount to 0
    repeat with n in noteList
        set checkedCount to checkedCount + 1
        if checkedCount > searchLimit then
            exit repeat
        end if
        set end of resultNames to name of n
    end repeat
    return resultNames
end tell
'''

    # Execute AppleScript
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Parse output (AppleScript returns comma-separated names)
        output = result.stdout.strip()
        if output:
            # Output is comma-separated: "name1, name2, name3"
            # Remove braces if present: "{name1, name2}" -> "name1, name2"
            if output.startswith('{') and output.endswith('}'):
                output = output[1:-1].strip()
            if output:
                names = [name.strip().strip('"') for name in output.split(',')]
                for name in names:
                    print(name)
        return 0
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
