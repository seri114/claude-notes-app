#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive test suite for notes-app Python scripts.

Usage:
    # Run all tests
    pytest test_all.py

    # Run specific test class
    pytest test_all.py::TestConverter
    pytest test_all.py::TestEndToEndRoundtrip

    # Run single test function
    pytest test_all.py::TestConverter::test_markdown_to_html_h1
    pytest test_all.py::TestEndToEndRoundtrip::test_e2e_h1_only

    # Filter by keyword
    pytest test_all.py -k checkbox
    pytest test_all.py -k table
    pytest test_all.py -k "e2e"

    # Verbose output
    pytest test_all.py -v

    # Stop on first failure
    pytest test_all.py -x

Test Classes:
    TestConverter           - Unit tests for Markdown↔HTML conversion
    TestEndToEndRoundtrip  - E2E tests: create note → show note → verify
    TestCreateNote         - Test create_note.py
    TestReplaceNote        - Test replace_note.py
    TestDeleteNote         - Test delete_note.py
    TestShowNote           - Test show_note.py
    TestListNotes          - Test list_notes.py
    TestLimit              - Test LIMIT environment variable
    TestTable              - Table-specific tests
    TestNoteRewrite        - Scenarios for updating existing notes
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str, stdin: str = "", args: list = None, env: dict = None) -> tuple:
    """Run a Python script and return stdout, stderr, returncode."""
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def _escape_applescript(text: str) -> str:
    """Escape text for AppleScript string literal."""
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return text


def cleanup_test_notes():
    """Delete all test notes from Notes.app."""
    script = '''
tell application "Notes"
    set theAccount to account "iCloud"
    set theFolder to folder "Notes" of theAccount
    set noteList to every note in theFolder
    set testNotes to {}
    set searchLimit to 100
    set checkedCount to 0
    repeat with n in noteList
        set checkedCount to checkedCount + 1
        if checkedCount > searchLimit then
            exit repeat
        end if
        if name of n starts with "【notes-appテスト専用】" then
            set end of testNotes to contents of n
        end if
    end repeat
    repeat with n in testNotes
        delete n
    end repeat
end tell
'''
    subprocess.run(['osascript', '-e', script], capture_output=True)


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """Cleanup once at the start and once at the end of the session.

    Skip cleanup by setting NO_CLEANUP=1:
        NO_CLEANUP=1 pytest test_all.py
    """
    if os.environ.get('NO_CLEANUP'):
        print("[INFO] Cleanup disabled (NO_CLEANUP=1)", file=sys.stderr)
        yield
    else:
        cleanup_test_notes()
        yield
        cleanup_test_notes()


# ========== Converter Tests ==========
class TestConverter:
    """Test converter.py"""

    def test_markdown_to_html_h1(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("# Title")
        assert '<div><h1>Title</h1></div>' in result

    def test_markdown_to_html_h2(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("## Section")
        assert '<div><h2>Section</h2></div>' in result

    def test_markdown_to_html_h3(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("### Sub")
        assert '<div><h3>Sub</h3></div>' in result

    def test_markdown_to_html_bold(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("**bold**")
        assert '<b>bold</b>' in result

    def test_markdown_to_html_italic(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("*italic*")
        assert '<i>italic</i>' in result

    def test_markdown_to_html_ulist(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("- item")
        assert '<div><ul><li>item</li></ul></div>' in result

    def test_markdown_to_html_olist(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("1. item")
        assert '<div><ol><li>item</li></ol></div>' in result

    def test_markdown_to_html_code(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("`code`")
        assert '<font face="monospace">code</font>' in result

    def test_markdown_to_html_link(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("[text](url)")
        # Links are stored as Markdown in HTML comments to preserve format
        assert '<!--MD_LINK-->' in result
        assert '[text](url)' in result
        assert '<!--/MD_LINK-->' in result

    def test_html_to_markdown_h1(self):
        from scripts.converter import html_to_markdown
        result = html_to_markdown('<div><h1>Title</h1></div>')
        assert "# Title" in result

    def test_html_to_markdown_h2(self):
        from scripts.converter import html_to_markdown
        result = html_to_markdown('<div><h2>Section</h2></div>')
        assert "## Section" in result

    def test_html_to_markdown_h3(self):
        from scripts.converter import html_to_markdown
        result = html_to_markdown('<div><h3>Sub</h3></div>')
        assert "### Sub" in result

    def test_html_to_markdown_bold(self):
        from scripts.converter import html_to_markdown
        result = html_to_markdown('<div><b>bold</b></div>')
        assert "**bold**" in result

    def test_html_to_markdown_h3_single_word(self):
        """Note: Single-word H3 headers look identical to bold in Notes.app HTML."""
        from scripts.converter import markdown_to_html, html_to_markdown
        # Single-word H3 becomes indistinguishable from bold after roundtrip
        md = "### 見出し"  # Single word, won't have multiple <b> tags
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        # Will be **見出し** not ### 見出し - this is a Notes.app limitation
        assert "**見出し**" in back or "### 見出し" in back  # Accept either

    def test_html_to_markdown_italic(self):
        from scripts.converter import html_to_markdown
        result = html_to_markdown('<div><i>italic</i></div>')
        assert "*italic*" in result

    def test_roundtrip_conversion(self):
        from scripts.converter import markdown_to_html, html_to_markdown
        original = "# Title\n\n**bold** text\n- item1\n- item2"
        html = markdown_to_html(original)
        back = html_to_markdown(html)
        assert "# Title" in back
        assert "**bold**" in back
        assert "- item1" in back
        assert "- item2" in back

    def test_roundtrip_no_extra_hashes(self):
        """Test that headers don't gain extra # characters after roundtrip."""
        from scripts.converter import markdown_to_html, html_to_markdown
        original = "# Title"
        html = markdown_to_html(original)
        back = html_to_markdown(html).strip()
        # Should be exactly "# Title", not "# Title#" or "## Title" etc.
        assert back == "# Title", f"Expected '# Title', got '{back}'"

    def test_roundtrip_header_with_table(self):
        """Test header + table roundtrip (regression for # appearing at end)."""
        from scripts.converter import markdown_to_html, html_to_markdown
        original = "# Title\n\n| Col1 | Col2 |\n| --- | --- |\n| A | B |"
        html = markdown_to_html(original)
        back = html_to_markdown(html).strip()
        lines = back.split('\n')
        # First line should be exactly "# Title"
        assert lines[0] == "# Title", f"Expected '# Title', got '{lines[0]}'"
        # Should not contain "# Title#" or similar artifacts
        assert not lines[0].endswith('#') or lines[0] == "#", \
            f"Header should not end with #: '{lines[0]}'"

    def test_notesapp_h1_with_br_span(self):
        """Test Notes.app specific format: <span style='font-size: 24px'>title</span><span><br></span>"""
        from scripts.converter import html_to_markdown
        # This is the actual format Notes.app uses for headers
        html = '<div><b><span style="font-size: 24px">テーブルテスト</span></b><b><span style="font-size: 24px"><br></span></b></div>'
        result = html_to_markdown(html).strip()
        # Should be "# テーブルテスト" not "# テーブルテスト#"
        assert result == "# テーブルテスト", f"Expected '# テーブルテスト', got '{result}'"
        # Count the # symbols - there should be exactly 1
        hash_count = result.count('#')
        assert hash_count == 1, f"Expected 1 '#', got {hash_count} in '{result}'"

    def test_notesapp_empty_span_cleanup(self):
        """Test that empty spans with <br> are properly cleaned up."""
        from scripts.converter import html_to_markdown
        # After br removal, we get empty spans that should be removed
        html = '<div><span style="font-size: 24px">Title</span></div><span style="font-size: 24px"></span>'
        result = html_to_markdown(html).strip()
        assert result == "# Title", f"Expected '# Title', got '{result}'"

    def test_checkbox_unchecked(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("- [ ] 未完了")
        assert '<div><ul><li>[ ] 未完了</li></ul></div>' in result

    def test_checkbox_checked(self):
        from scripts.converter import markdown_to_html
        result = markdown_to_html("- [x] 完了")
        assert '<div><ul><li>[x] 完了</li></ul></div>' in result

    def test_checkbox_with_font_tags(self):
        from scripts.converter import html_to_markdown
        html = '<ul>\n<li><font face="test">[</font> ] 項目1</li>\n<li><font face="test">[</font>x] 項目2</li>\n</ul>'
        result = html_to_markdown(html)
        assert "- [ ] 項目1" in result
        assert "- [x] 項目2" in result

    def test_list_multiple_items(self):
        from scripts.converter import markdown_to_html, html_to_markdown
        md = "- 項目1\n- 項目2\n- 項目3"
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        assert "- 項目1" in back
        assert "- 項目2" in back
        assert "- 項目3" in back

    def test_ordered_list_roundtrip(self):
        """Test ordered list roundtrip (numbering is lost)."""
        from scripts.converter import markdown_to_html, html_to_markdown
        md = "1. 最初\n2. 次へ\n3. 最後"
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        # All items become 1. after roundtrip (Notes.app limitation)
        assert "1. 最初" in back
        assert "1. 次へ" in back
        assert "1. 最後" in back

    def test_table_markdown_to_html(self):
        from scripts.converter import markdown_to_html
        md = "| ヘッダ1 | ヘッダ2 |\n| --- | --- |\n| データ1 | データ2 |"
        result = markdown_to_html(md)
        assert '<object><table' in result
        assert '</table></object>' in result

    def test_table_html_to_markdown(self):
        from scripts.converter import html_to_markdown
        html = '<object><table><tbody><tr><td><div>A</div></td><td><div>B</div></td></tr></tbody></table></object>'
        result = html_to_markdown(html)
        assert '| A | B |' in result

    def test_code_block_markdown_to_html(self):
        """Test code block conversion to HTML."""
        from scripts.converter import markdown_to_html
        md = '```python\ndef hello():\n    print("hi")\n```'
        result = markdown_to_html(md)
        # Current implementation uses <pre><code> format
        assert '<pre><code>' in result
        assert '</code></pre></div>' in result
        assert 'def hello():' in result
        assert '    print("hi")' in result

    def test_code_block_html_to_markdown(self):
        """Test code block conversion from Notes.app HTML to Markdown."""
        from scripts.converter import html_to_markdown
        # Notes.app format: individual div lines with Courier font
        html = '''<div><font face="Courier"><tt>def hello():</tt></font></div>
<div><font face="Courier"><tt>    print("hi")</tt></font></div>'''
        result = html_to_markdown(html)
        assert '```' in result
        assert 'def hello():' in result
        assert '    print("hi")' in result

    def test_code_block_roundtrip(self):
        """Test code block roundtrip preserves indentation."""
        from scripts.converter import html_to_markdown
        # Simulate Notes.app HTML format (individual div lines with Courier font)
        # This is what Notes.app actually returns after we send our HTML
        notes_html = '''<div><font face="Courier"><tt>def hello():</tt></font></div>
<div><font face="Courier"><tt>    print("hi")</tt></font></div>
<div><font face="Courier"><tt>    return True</tt></font></div>'''
        back = html_to_markdown(notes_html)
        assert '```' in back
        assert 'def hello():' in back
        assert '    print("hi")' in back
        assert '    return True' in back

    def test_inline_code_roundtrip(self):
        """Test inline code roundtrip."""
        from scripts.converter import markdown_to_html, html_to_markdown
        md = 'This is `inline code` test'
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        assert '`inline code`' in back

    def test_special_characters_roundtrip(self):
        """Test special characters (<, >, &, ", ') are preserved through roundtrip."""
        from scripts.converter import markdown_to_html, html_to_markdown
        md = """## Special Characters

Less than: <
Greater than: >
Ampersand: &
Quote: \"""
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        # All special characters should be preserved
        assert "Less than: <" in back, f"< not preserved in: {back}"
        assert "Greater than: >" in back, f"> not preserved in: {back}"
        assert "Ampersand: &" in back, f"& not preserved in: {back}"
        assert 'Quote: "\'" in back, f'"\'' not preserved in: {back}'
"""
    def test_code_block_indentation_roundtrip(self):
        """Test code block indentation is preserved through roundtrip."""
        from scripts.converter import markdown_to_html, html_to_markdown
        md = '''```python
def hello():
    print("Hello")
    return True
```'''
        html = markdown_to_html(md)
        back = html_to_markdown(html)
        # Indentation should be preserved
        assert '    print("Hello")' in back, f"Indentation not preserved in: {back}"
        assert '    return True' in back, f"Indentation not preserved in: {back}"


# ========== End-to-End Roundtrip Tests ==========
class TestEndToEndRoundtrip:
    """Test that input MD matches output MD after create + show cycle.

    Notes are cleaned up once at the end of the test session by session_cleanup.
    """

    def _verify_roundtrip(self, title: str, input_md: str, expected_md: str = None):
        """Create note from input_md, show it, and verify output matches expected_md."""
        import time
        if expected_md is None:
            expected_md = input_md  # For simplicity, default to expecting same as input

        # Create
        stdout, stderr, retcode = run_script("create_note.py", stdin=input_md, args=[title])
        assert retcode == 0, f"Create failed: {stderr}"
        time.sleep(0.3)

        # Show and verify
        show_stdout, show_stderr, show_retcode = run_script("show_note.py", args=[title])
        assert show_retcode == 0, f"Show failed: {show_stderr}"

        expected_lines = [l.strip() for l in expected_md.strip().split('\n') if l.strip()]
        result_lines = [l.strip() for l in show_stdout.strip().split('\n') if l.strip()]

        for i, (exp, res) in enumerate(zip(expected_lines, result_lines)):
            assert exp == res, f"Line {i+1} mismatch:\n  Expected: {exp}\n  Got:      {res}"

        assert len(expected_lines) == len(result_lines), \
            f"Line count mismatch: expected {len(expected_lines)}, got {len(result_lines)}"

    def test_e2e_h1_only(self):
        title = "【notes-appテスト専用】E2E H1"
        markdown = "# 【notes-appテスト専用】E2E H1"
        self._verify_roundtrip(title, markdown)

    def test_e2e_h1_with_paragraph(self):
        title = "【notes-appテスト専用】E2E H1+段落"
        markdown = "# 【notes-appテスト専用】E2E H1+段落\n\n本文です"
        self._verify_roundtrip(title, markdown)

    def test_e2e_headers(self):
        title = "【notes-appテスト専用】E2E 見出し"
        markdown = "# 【notes-appテスト専用】E2E 見出し\n\n## H2セクション\n\n### H3サブセクション\n\n本文"
        self._verify_roundtrip(title, markdown)

    def test_e2e_formatting(self):
        title = "【notes-appテスト専用】E2E 書体"
        markdown = "# 【notes-appテスト専用】E2E 書体\n\n**太字**と*イタリック*と**太字と*イタリック*混在**"
        self._verify_roundtrip(title, markdown)

    def test_e2e_unordered_list(self):
        title = "【notes-appテスト専用】E2E 箇条書き"
        markdown = "# 【notes-appテスト専用】E2E 箇条書き\n\n- 項目1\n- 項目2\n- 項目3"
        self._verify_roundtrip(title, markdown)

    def test_e2e_ordered_list(self):
        title = "【notes-appテスト専用】E2E 番号付き"
        # User input: numbered list
        input_md = "# 【notes-appテスト専用】E2E 番号付き\n\n1. 最初\n2. 次へ\n3. 最後"
        # Expected output: all items become 1. (Notes.app limitation)
        expected_md = "# 【notes-appテスト専用】E2E 番号付き\n\n1. 最初\n1. 次へ\n1. 最後"
        self._verify_roundtrip(title, input_md, expected_md)

    def test_e2e_checkboxes(self):
        title = "【notes-appテスト専用】E2E チェックボックス"
        markdown = "# 【notes-appテスト専用】E2E チェックボックス\n\n- [ ] 未完了\n- [x] 完了済み\n- [ ] もうひとつ"
        self._verify_roundtrip(title, markdown)

    def test_e2e_table(self):
        title = "【notes-appテスト専用】E2E テーブル"
        # User input: with separator row (standard Markdown)
        input_md = "# 【notes-appテスト専用】E2E テーブル\n\n| 列1 | 列2 |\n| --- | --- |\n| A | B |\n| C | D |"
        # Expected output: separator row is not stored
        expected_md = "# 【notes-appテスト専用】E2E テーブル\n\n| 列1 | 列2 |\n| A | B |\n| C | D |"
        self._verify_roundtrip(title, input_md, expected_md)

    def test_e2e_code(self):
        title = "【notes-appテスト専用】E2E コード"
        markdown = "# 【notes-appテスト専用】E2E コード\n\nこれは`コード`です\n\n`monospace`フォント"
        self._verify_roundtrip(title, markdown)

    # Note: Links don't roundtrip through Notes.app - URLs are lost
    # Notes.app converts <a href="..."> to <u> (underline) and drops the URL

    def test_e2e_complex(self):
        title = "【notes-appテスト専用】E2E 複合"
        # User input: ALL Markdown elements
        input_md = '''# 【notes-appテスト専用】E2E 複合

## 段落

本文です。**太字**と*イタリック*と___下線___と~~取り消し線~~。

### H3見出し

- 箇条書き項目1
- 箇条書き項目2
  - 入れ子の項目

## リスト

1. 番号付き1
2. 番号付き2
3. 番号付き3

## チェックボックス

- [ ] 未完了タスク
- [x] 完了済みタスク

## テーブル

| 列A | 列B | 列C |
| --- | --- | --- |
| A1 | B1 | C1 |
| A2 | B2 | C2 |

## コードブロック

```python
def hello():
    print("Hello, World!")
    return True
```

インラインコードは `code` のように。
'''
        # Expected output: ordered list numbering lost, separator row lost
        expected_md = """# 【notes-appテスト専用】E2E 複合

## 段落

本文です。**太字**と*イタリック*と___下線___と~~取り消し線~~。

### H3見出し

- 箇条書き項目1
- 箇条書き項目2
  - 入れ子の項目

## リスト

1. 番号付き1
1. 番号付き2
1. 番号付き3

## チェックボックス

- [ ] 未完了タスク
- [x] 完了済みタスク

## テーブル

| 列A | 列B | 列C |
| A1 | B1 | C1 |
| A2 | B2 | C2 |

## コードブロック

```
def hello():
    print("Hello, World!")
    return True
```

インラインコードは `code` のように。
"""
        self._verify_roundtrip(title, input_md, expected_md)

    def test_e2e_lenient_markdown_patterns(self):
        """Test various lenient markdown patterns - creates note for manual verification."""
        title = "【notes-appテスト専用】寛容Markdownパターン"
        # Various lenient markdown patterns
        input_md = """#NoSpaceHeader
##TrailingHash##

###NoSpaceH3

#### H4 Header
##### H5 Header
###### H6 Header

- Dash bullet
* Asterisk bullet
+ Plus bullet

1) Parenthesis number
2. Period number

**Bold** and *Italic* and ___Underline___ and ~~Strikethrough~~.

`inline code` test

```
Code block without language
```

```python
def hello():
    print("Hello")
```

| A | B |
| --- | --- |
| 1 | 2 |

- [ ] Checkbox unchecked
- [x] Checkbox checked
"""
        # For this test, we just verify the note is created successfully
        # Manual verification will check the visual output
        stdout, stderr, retcode = run_script("create_note.py", stdin=input_md, args=[title])
        assert retcode == 0, f"Create failed: {stderr}"
        # Don't verify roundtrip since we're just checking if parsing works


# ========== Create Note Tests ==========
class TestCreateNote:
    """Test create_note.py"""

    def test_create_with_h1(self):
        title = "【notes-appテスト専用】パターン1 H1あり"
        markdown = f"# {title}\n\n## 要項\n\n- 項目1"
        stdout, stderr, retcode = run_script("create_note.py", stdin=markdown, args=[title])
        assert retcode == 0
        assert "Created note" in stdout

    def test_create_with_h2_only(self):
        title = "【notes-appテスト専用】パターン2 H2のみ"
        markdown = f"## {title}\n\n- 項目1"
        stdout, stderr, retcode = run_script("create_note.py", stdin=markdown, args=[title])
        assert retcode == 0
        assert "Created note" in stdout

    def test_create_plain_text(self):
        title = "【notes-appテスト専用】パターン3 プレーンテキスト"
        markdown = f"{title}\n\n## 要項\n\n- 項目1"
        stdout, stderr, retcode = run_script("create_note.py", stdin=markdown, args=[title])
        assert retcode == 0
        assert "Created note" in stdout


# ========== Replace Note Tests ==========
class TestReplaceNote:
    """Test replace_note.py"""

    def test_replace_single_note(self):
        title = "【notes-appテスト専用】更新テスト"
        original = f"# {title}\n\n元の内容"
        run_script("create_note.py", stdin=original, args=[title])
        import time
        time.sleep(0.5)

        updated = f"# {title}\n\n## 更新後の内容\n\n- 新項目"
        stdout, stderr, retcode = run_script("replace_note.py", stdin=updated, args=[title])
        assert retcode == 0
        assert "SUCCESS" in stdout

    def test_replace_multiple_notes_first_only(self):
        title = "【notes-appテスト専用】複数更新テスト"

        # Create 3 notes with same title
        for i in range(3):
            markdown = f"# {title}\n\n## ノート {i+1}"
            run_script("create_note.py", stdin=markdown, args=[title])
            import time
            time.sleep(0.3)

        updated = f"# {title}\n\n## 更新済み"
        stdout, stderr, retcode = run_script("replace_note.py", stdin=updated, args=[title])
        assert retcode == 0
        assert "SUCCESS" in stdout


# ========== Note Rewrite Scenarios Tests ==========
class TestNoteRewrite:
    """Test various note rewrite scenarios"""

    def test_add_to_existing_list(self):
        title = "【notes-appテスト専用】書き換えテスト1"
        original = f"# {title}\n\n- 既存項目1\n- 既存項目2"
        run_script("create_note.py", stdin=original, args=[title])
        import time
        time.sleep(0.5)

        updated = f"# {title}\n\n- 既存項目1\n- 既存項目2\n- 新規項目3"
        run_script("replace_note.py", stdin=updated, args=[title])

        show_stdout, _, _ = run_script("show_note.py", args=[title])
        assert "新規項目3" in show_stdout

    def test_toggle_checkbox(self):
        title = "【notes-appテスト専用】書き換えテスト2"
        original = f"# {title}\n\n- [ ] タスクA\n- [ ] タスクB"
        run_script("create_note.py", stdin=original, args=[title])
        import time
        time.sleep(0.5)

        updated = f"# {title}\n\n- [x] タスクA\n- [ ] タスクB"
        run_script("replace_note.py", stdin=updated, args=[title])

        show_stdout, _, _ = run_script("show_note.py", args=[title])
        assert "- [x] タスクA" in show_stdout
        assert "- [ ] タスクB" in show_stdout

    def test_add_section_keep_content(self):
        title = "【notes-appテスト専用】書き換えテスト3"
        original = f"# {title}\n\n本文内容"
        run_script("create_note.py", stdin=original, args=[title])
        import time
        time.sleep(0.5)

        updated = f"# {title}\n\n## 追加したセクション\n\n本文内容"
        run_script("replace_note.py", stdin=updated, args=[title])

        show_stdout, _, _ = run_script("show_note.py", args=[title])
        assert "追加したセクション" in show_stdout
        assert "本文内容" in show_stdout


# ========== Delete Note Tests ==========
class TestDeleteNote:
    """Test delete_note.py"""

    def test_delete_single_note(self):
        title = "【notes-appテスト専用】削除テスト"
        markdown = f"# {title}\n\n削除用ノート"
        run_script("create_note.py", stdin=markdown, args=[title])
        import time
        time.sleep(0.5)

        stdout, stderr, retcode = run_script("delete_note.py", args=[title])
        assert retcode == 0
        assert "Deleted note" in stdout

    def test_delete_multiple_notes_first_only(self):
        title = "【notes-appテスト専用】複数削除テスト"

        for i in range(3):
            markdown = f"# {title}\n\n## ノート {i+1}"
            run_script("create_note.py", stdin=markdown, args=[title])
            import time
            time.sleep(0.3)

        stdout, stderr, retcode = run_script("delete_note.py", args=[title])
        assert retcode == 0
        assert "Deleted note" in stdout


# ========== Show Note Tests ==========
class TestShowNote:
    """Test show_note.py"""

    def test_show_note_content(self):
        title = "【notes-appテスト専用】表示テスト"
        markdown = f"# {title}\n\n## セクション1\n\n**太字**と*イタリック*\n\n- 項目1\n- 項目2"
        run_script("create_note.py", stdin=markdown, args=[title])
        import time
        time.sleep(0.5)

        stdout, stderr, retcode = run_script("show_note.py", args=[title])
        assert retcode == 0
        assert title in stdout
        assert "セクション1" in stdout
        assert "**太字**" in stdout
        assert "*イタリック*" in stdout
        assert "項目1" in stdout


# ========== List Notes Tests ==========
class TestListNotes:
    """Test list_notes.py"""

    def test_list_notes_with_pattern(self):
        title = "【notes-appテスト専用】一覧テスト"
        markdown = f"# {title}\n\n一覧テスト用"
        run_script("create_note.py", stdin=markdown, args=[title])
        import time
        time.sleep(0.5)

        stdout, stderr, retcode = run_script("list_notes.py", args=["【notes-appテスト専用】"])
        assert retcode == 0
        assert title in stdout


# ========== LIMIT Tests ==========
class TestLimit:
    """Test LIMIT environment variable"""

    def test_limit_variable(self):
        # Create 3 test notes
        for i in range(1, 4):
            title = f"【notes-appテスト専用】LIMITテスト{i}"
            markdown = f"# {title}\n\nテスト{i}"
            run_script("create_note.py", stdin=markdown, args=[title])
            import time
            time.sleep(0.3)

        # List with LIMIT=2 should only return 2 notes
        env = os.environ.copy()
        env['LIMIT'] = '2'
        script_path = SCRIPT_DIR / "list_notes.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "【notes-appテスト専用】LIMITテスト"],
            capture_output=True,
            text=True,
            env=env
        )

        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert result.returncode == 0
        assert len(lines) == 2


# ========== Table Tests ==========
class TestTable:
    """Test table functionality"""

    def test_create_note_with_table(self):
        title = "【notes-appテスト専用】テーブルテスト"
        markdown = f"# {title}\n\n| 列1 | 列2 |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |"
        stdout, stderr, retcode = run_script("create_note.py", stdin=markdown, args=[title])
        assert retcode == 0
        assert "Created note" in stdout

    def test_show_note_with_table(self):
        title = "【notes-appテスト専用】テーブル表示テスト"
        markdown = f"# {title}\n\n| A | B |\n| --- | --- |\n| X | Y |"
        run_script("create_note.py", stdin=markdown, args=[title])
        import time
        time.sleep(0.5)

        stdout, stderr, retcode = run_script("show_note.py", args=[title])
        assert retcode == 0
        assert "| A | B |" in stdout
        assert "| X | Y |" in stdout

    def test_table_roundtrip(self):
        from scripts.converter import markdown_to_html, html_to_markdown

        md = "| ヘッダ1 | ヘッダ2 |\n| --- | --- |\n| データ1 | データ2 |"
        html = markdown_to_html(md)
        back = html_to_markdown(html)

        assert "| ヘッダ1 | ヘッダ2 |" in back
        assert "| データ1 | データ2 |" in back
