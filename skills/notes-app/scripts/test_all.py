#!/usr/bin/env python3
"""Test script for notes-app functionality.

Run this script to verify all operations work correctly.
"""

import os
import subprocess
import sys
import tempfile

# Get the scripts directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(name: str, *args, input_text: str | None = None) -> tuple[int, str, str]:
    """Run a script and return (returncode, stdout, stderr)."""
    script_path = os.path.join(SCRIPT_DIR, name)
    cmd = ["python3", script_path] + list(args)

    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR
    )
    return result.returncode, result.stdout, result.stderr


def main() -> int:
    """Run all tests."""
    print("Testing notes-app scripts...")
    print(f"Script directory: {SCRIPT_DIR}")
    print()

    # Test 1: List notes (should work even with no notes)
    print("Test 1: List notes")
    code, stdout, stderr = run_script("list_notes.py")
    if code == 0:
        print(f"  ✓ list_notes.py works")
        print(f"  Output: {stdout.strip() if stdout.strip() else '(no notes)'}")
    else:
        print(f"  ✗ list_notes.py failed: {stderr}")

    # Test 2: Create a test note
    test_title = "claude-notes-app-test"
    test_content = "# Test Note\n\nThis is a **test** note with *formatting*.\n\n- Item 1\n- Item 2"

    print(f"\nTest 2: Create note '{test_title}'")
    code, stdout, stderr = run_script("create_note.py", test_title, input_text=test_content)
    if code == 0:
        print(f"  ✓ create_note.py works")
        print(f"  Output: {stdout.strip()}")
    else:
        print(f"  ✗ create_note.py failed: {stderr}")
        return 1

    # Test 3: Show the note
    print(f"\nTest 3: Show note '{test_title}'")
    code, stdout, stderr = run_script("show_note.py", test_title)
    if code == 0:
        print(f"  ✓ show_note.py works")
        print(f"  Content preview: {stdout[:100]}...")
    else:
        print(f"  ✗ show_note.py failed: {stderr}")
        return 1

    # Test 4: Rename the note
    new_title = "claude-notes-app-test-renamed"
    print(f"\nTest 4: Rename note to '{new_title}'")
    code, stdout, stderr = run_script("rename_note.py", test_title, new_title)
    if code == 0:
        print(f"  ✓ rename_note.py works")
        print(f"  Output: {stdout.strip()}")
    else:
        print(f"  ✗ rename_note.py failed: {stderr}")
        return 1

    # Test 5: Replace the note content
    new_content = "# Updated Test\n\nThis has been **updated**."
    print(f"\nTest 5: Replace note content")
    code, stdout, stderr = run_script("replace_note.py", new_title, input_text=new_content)
    if code == 0:
        print(f"  ✓ replace_note.py works")
        print(f"  Output: {stdout.strip()}")
    else:
        print(f"  ✗ replace_note.py failed: {stderr}")
        return 1

    # Test 6: Delete the test note
    print(f"\nTest 6: Delete note '{new_title}'")
    code, stdout, stderr = run_script("delete_note.py", new_title)
    if code == 0:
        print(f"  ✓ delete_note.py works")
        print(f"  Output: {stdout.strip()}")
    else:
        print(f"  ✗ delete_note.py failed: {stderr}")
        return 1

    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
