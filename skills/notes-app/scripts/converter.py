#!/usr/bin/env python3
"""Markdown ↔ HTML converter for Notes.app using html.parser.

This module handles conversion between Markdown and Notes.app's HTML format.
Notes.app uses non-standard HTML for formatting.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Match

# ==============================================================================
# Markdown to HTML (unchanged - works well)
# ==============================================================================

def markdown_to_html(markdown: str) -> str:
    """Convert Markdown to Notes.app HTML format."""
    if not markdown:
        return ""

    # First, extract code blocks (```...```) to protect them from processing
    code_blocks: list[str] = []
    placeholder_counter = [0]

    def extract_code_block(match: Match[str]) -> str:
        """Extract code block and replace with placeholder."""
        code_blocks.append(match.group(0))
        placeholder = f"__CODE_BLOCK_{placeholder_counter[0]}__"
        placeholder_counter[0] += 1
        return placeholder

    def extract_code_block_with_trailing(match: Match[str]) -> str:
        """Extract code block and preserve any trailing text."""
        full_match = match.group(0)
        match.group(1)

        # Find the LAST ``` in the full match (the closing one)
        last_backtick_pos = full_match.rfind('```')

        # Everything after the last ``` is trailing text (if not just whitespace)
        after_backtick = full_match[last_backtick_pos + 3:]
        trailing_text = after_backtick.strip() if after_backtick else ''

        if trailing_text:
            # Add code block without trailing text
            code_block_only = full_match[:last_backtick_pos + 3]
            code_blocks.append(code_block_only)
            placeholder = f"__CODE_BLOCK_{placeholder_counter[0]}__"
            placeholder_counter[0] += 1
            return placeholder + ' ' + trailing_text
        else:
            # No trailing text
            code_blocks.append(full_match)
            placeholder = f"__CODE_BLOCK_{placeholder_counter[0]}__"
            placeholder_counter[0] += 1
            return placeholder

    # Use the flexible pattern that matches ``` to ```
    markdown = re.sub(
        r'```[^\n]*\n([\s\S]*?)```',
        extract_code_block_with_trailing,
        markdown
    )

    # Also extract inline code blocks (single line ```)
    markdown = re.sub(
        r'```([^`\n]+)```',
        extract_code_block,
        markdown
    )

    # Process remaining markdown (tables, lists, etc.)
    lines = markdown.split('\n')
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for code block placeholder (check before strip to preserve exact match)
        stripped_line = line.strip()
        placeholder_match = re.search(r'(__CODE_BLOCK_\d+__)', stripped_line)
        if placeholder_match:
            # Extract index from __CODE_BLOCK_0__
            placeholder = placeholder_match.group(1)
            idx = int(placeholder.replace('__CODE_BLOCK_', '').replace('__', ''))
            original_block = code_blocks[idx]
            # Extract the code content (remove ``` markers)
            code_match = re.match(r'```[^\n]*\n([\s\S]*?)```', original_block)
            if code_match:
                code_content = code_match.group(1)
            else:
                # Single line format: ```code```
                inline_match = re.match(r'```([^`\n]+)```', original_block)
                code_content = inline_match.group(1) if inline_match else original_block
            # Escape HTML entities
            code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Use <pre><code> format - Notes.app will convert to individual Courier+tt divs with preserved indentation
            result_lines.append(f'<div><pre><code>{code_content}</code></pre></div>')

            # Handle any text after the placeholder
            after_placeholder = stripped_line[placeholder_match.end():].strip()
            if after_placeholder:
                # Process the remaining text as a regular line
                result_lines.append(f'<div>{_inline_format(after_placeholder)}</div>')

            i += 1
            continue

        # Check for table start (line starting with |)
        if stripped_line.startswith('|') and stripped_line.endswith('|') and '|' in stripped_line[1:-1]:
            # Collect all consecutive table lines
            table_lines = [stripped_line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('|') and next_line.endswith('|'):
                    table_lines.append(next_line)
                    i += 1
                elif next_line.startswith('|') and '---' in next_line:
                    # Separator line, include it
                    table_lines.append(next_line)
                    i += 1
                else:
                    break

            # Convert table to HTML
            table_html = _markdown_table_to_html(table_lines)
            result_lines.append(table_html)
            continue

        # Empty line -> <div><br></div>
        if not stripped_line:
            result_lines.append('<div><br></div>')
            i += 1
            continue

        # Blockquote: lines starting with >
        # Collect consecutive quote lines
        if stripped_line.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                # Remove the > prefix (and optional space after)
                quote_line = lines[i].strip()[1:].lstrip()
                quote_lines.append(quote_line)
                i += 1
            # Combine quote lines and format
            quote_content = '\n'.join(quote_lines)
            # Apply inline formatting to the content
            quote_formatted = _inline_format(quote_content)
            # Replace newlines with <br> for multi-line quotes
            quote_formatted = quote_formatted.replace('\n', '<br>')
            result_lines.append(f'<div><blockquote>{quote_formatted}</blockquote></div>')
            continue

        # Headers (more lenient: allow ###Header, #Header#, etc.)
        # Match 1-6 # characters at start of line
        header_match = re.match(r'^(#{1,6})\s*(.*?)\s*#*$', stripped_line)
        if header_match:
            level = len(header_match.group(1))
            content = _inline_format(header_match.group(2).strip())
            result_lines.append(f'<div><h{level}>{content}</h{level}></div>')
        # Unordered list (more lenient: allow -, *, +)
        elif re.match(r'^\s*[-*+]\s+', stripped_line):
            match = re.match(r'^\s*[-*+]\s+(.*)$', stripped_line)
            content = _inline_format(match.group(1).strip())
            result_lines.append(f'<div><ul><li>{content}</li></ul></div>')
        # Ordered list (more lenient: allow 1. or 1) or 1) )
        elif re.match(r'^\s*\d+[\.\)]\s', stripped_line):
            match = re.match(r'^\s*(\d+)[\.\)]\s+(.*)$', stripped_line)
            if match:
                content = _inline_format(match.group(2).strip())
                result_lines.append(f'<div><ol><li>{content}</li></ol></div>')
            else:
                content = _inline_format(stripped_line)
                result_lines.append(f'<div>{content}</div>')
        # Plain paragraph
        else:
            content = _inline_format(stripped_line)
            result_lines.append(f'<div>{content}</div>')

        i += 1

    return '\n'.join(result_lines)


def _markdown_table_to_html(table_lines: list[str]) -> str:
    """Convert markdown table to Notes.app HTML table format."""
    if len(table_lines) < 2:
        # Not enough lines for a valid table, treat as plain text
        return '\n'.join([f'<div>{_inline_format(line.strip()[1:-1].strip())}</div>' for line in table_lines])

    # Parse table rows
    rows = []
    for line in table_lines:
        if '---' in line:
            continue  # Skip separator line
        # Remove leading/trailing | and split by |
        cells = [c.strip() for c in line.strip()[1:-1].split('|')]
        # Apply inline formatting to each cell
        cells = [_inline_format(cell) for cell in cells]
        rows.append(cells)

    if not rows:
        return ''

    # Build Notes.app table HTML
    trs = []
    for row in rows:
        tds = []
        for cell in row:
            td = f'<td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>{cell}</div></td>'
            tds.append(td)
        trs.append(f'<tr>{"".join(tds)}</tr>')

    table_html = f'''<object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
{"".join(trs)}
</tbody>
</table></object>'''

    return table_html


def _inline_format(text: str) -> str:
    """Apply inline formatting to text."""
    # Must process in order to avoid conflicts
    result = text

    # Code: `text` -> <font face="monospace">text</font>
    result = re.sub(r'`([^`]+)`', r'<font face="monospace">\1</font>', result)

    # Bold: **text** -> <b>text</b> (don't use .HiraKakuInterface-W6 as it conflicts with H3 header detection)
    result = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', result)

    # Italic: *text* -> <i>text</i>
    # Use negative lookahead to avoid matching **bold**
    result = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', result)

    # Strikethrough: ~~text~~ -> <s>text</s>
    result = re.sub(r'~~([^~]+)~~', r'<s>\1</s>', result)

    # Links: [text](url) - preserve in original format using HTML comments
    # This allows us to restore the original markdown link when reading back
    def preserve_link(m: Match) -> str:
        text = m.group(1)
        url = m.group(2)
        link = f'[{text}]({url})'
        # Wrap in HTML comments to mark as markdown link
        return f'<!--MD_LINK-->{link}<!--/MD_LINK-->'
    result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', preserve_link, result)

    # Escape special characters as HTML entities
    # Protect HTML tags first to avoid escaping them
    import re as re_local

    tag_counter = [0]
    tag_placeholders = {}

    def save_tag(m: Match) -> str:
        placeholder = f'\x01TAG{tag_counter[0]}\x01'
        tag_counter[0] += 1
        tag_placeholders[placeholder] = m.group(0)
        return placeholder

    # Protect all HTML tags
    result = re_local.sub(r'<[^>]+>', save_tag, result)

    # First, protect already-encoded entities
    result = result.replace('&amp;', '\x00AMP\x00')
    result = result.replace('&lt;', '\x00LT\x00')
    result = result.replace('&gt;', '\x00GT\x00')
    result = result.replace('&quot;', '\x00QUOT\x00')

    # Escape special characters
    result = result.replace('&', '&amp;')
    result = result.replace('<', '&lt;')
    result = result.replace('>', '&gt;')
    result = result.replace('"', '&quot;')

    # Restore protected entities
    result = result.replace('\x00AMP\x00', '&amp;')
    result = result.replace('\x00LT\x00', '&lt;')
    result = result.replace('\x00GT\x00', '&gt;')
    result = result.replace('\x00QUOT\x00', '&quot;')

    # Restore HTML tags
    for placeholder, tag in tag_placeholders.items():
        result = result.replace(placeholder, tag)

    return result


# ==============================================================================
# HTML to Markdown using html.parser
# ==============================================================================

class NotesAppHTMLParser(HTMLParser):
    """Parse Notes.app HTML and convert to Markdown."""

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []
        self._current_line_parts: list[str] = []

        # State tracking
        self._in_div: bool = False
        self._in_list: bool = False
        self._list_type: str | None = None  # 'ul' or 'ol'
        self._in_li: bool = False
        self._in_code_block: bool = False
        self._list_counter: int = 0  # For numbering ordered lists

        # Formatting state
        self._is_bold: bool = False
        self._is_italic: bool = False
        self._is_underline: bool = False
        self._is_strike: bool = False
        self._is_courier: bool = False
        self._is_tt: bool = False
        self._span_font_size: int | None = None
        self._in_header: bool = False  # Inside h1/h2/h3 tag

        # Div tracking
        self._div_has_courier: bool = False
        self._div_has_tt: bool = False
        self._div_has_courier_span: bool = False
        self._div_has_hiraku_w6: bool = False  # Notes.app H3 header uses .HiraKakuInterface-W6 font
        self._div_font_size: int | None = None
        self._div_bold_count: int = 0
        self._div_has_italic: bool = False  # Track if div has italic (to avoid false H3 detection)
        self._div_text_parts: list[str] = []
        self._list_prefix: str = ''
        self._div_has_br: bool = False  # Track if div contains only <br> (blank line)

        # Code block detection
        self._pending_code_lines: list[str] = []
        self._last_was_code_line: bool = False

        # Table detection
        self._in_table: bool = False
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._in_cell: bool = False
        self._cell_text: list[str] = []

    def get_result(self) -> str:
        """Get the final Markdown result."""
        # Flush any pending content
        self._flush_div()
        self._flush_code_block()

        # Notes.app preserves multiple blank lines - don't collapse them
        return '\n'.join(self.lines).strip()

    def _flush_div(self):
        """Process accumulated div content and add to lines."""
        # Check for blank line: <div><br></div> with no other content
        if self._div_has_br and not self._div_text_parts:
            self._flush_code_block()
            self.lines.append('')
            self._last_was_code_line = False
            self._div_has_br = False
            self._list_prefix = ''
            return

        if not self._div_text_parts:
            self._list_prefix = ''
            self._div_has_br = False
            return

        text = ''.join(self._div_text_parts)

        # For code lines, preserve leading whitespace (indentation)
        # For other lines, strip trailing whitespace but keep structure
        is_code_line = self._div_has_courier and self._div_has_tt
        if is_code_line:
            # Only strip trailing whitespace for code, keep leading
            text = text.rstrip()
        else:
            # For non-code, strip both sides
            text = text.strip()

        if not text:
            self._div_text_parts = []
            self._list_prefix = ''
            self._div_has_br = False
            return

        # Determine div type and format accordingly
        if is_code_line:
            # This is a code line (Courier+tt)
            self._pending_code_lines.append(text)
            self._last_was_code_line = True
        elif self._div_has_courier_span:
            # Inline code (Courier+span, not tt)
            # Already formatted as `code` in handle_data
            self._flush_code_block()  # Flush any pending code block first
            self.lines.append(text)
            self._last_was_code_line = False
        elif self._div_font_size == 24:
            # H1 header
            self._flush_code_block()
            self.lines.append(f'# {text}')
            self._last_was_code_line = False
        elif self._div_font_size == 18:
            # H2 header
            self._flush_code_block()
            self.lines.append(f'## {text}')
            self._last_was_code_line = False
        elif (self._div_has_hiraku_w6 or
              (self._div_bold_count >= 2 and not self._div_has_italic)):
            # H3 header (.HiraKakuInterface-W6 font or multiple bold tags)
            # Exclude cases where bold is combined with italic (***text***)
            # Remove any bold markers that were added during handle_data
            text = text.replace('**', '')
            self._flush_code_block()
            self.lines.append(f'### {text}')
            self._last_was_code_line = False
        else:
            # Regular text
            if not self._last_was_code_line:
                self._flush_code_block()
            self.lines.append(text)
            self._last_was_code_line = False

        self._div_text_parts = []
        self._div_has_courier = False
        self._div_has_tt = False
        self._div_has_courier_span = False
        self._div_has_hiraku_w6 = False
        self._div_font_size = None
        self._div_bold_count = 0
        self._div_has_italic = False
        self._list_prefix = ''
        self._div_has_br = False

    def _flush_code_block(self):
        """Flush accumulated code lines as a code block."""
        if len(self._pending_code_lines) >= 2:
            newline = '\n'
            content = newline.join(self._pending_code_lines)
            self.lines.append(f'```{newline}{content}{newline}```')
        elif self._pending_code_lines:
            # Single code line - format as inline code
            for line in self._pending_code_lines:
                # Only wrap in backticks if not already wrapped
                stripped = line.strip()
                if not (stripped.startswith('`') and stripped.endswith('`')):
                    self.lines.append(f'`{line}`')
                else:
                    self.lines.append(line)
        self._pending_code_lines = []
        self._last_was_code_line = False

    def handle_starttag(self, tag: str, attrs: list[tuple]):
        attrs_dict = dict(attrs)

        if tag == 'div':
            # Flush previous div
            self._flush_div()
            self._in_div = True
            # Reset div tracking
            self._div_has_courier = False
            self._div_has_tt = False
            self._div_has_courier_span = False
            self._div_has_hiraku_w6 = False
            self._div_font_size = None
            self._div_bold_count = 0
            self._div_has_italic = False
            self._div_text_parts = []
            self._list_prefix = ''  # Reset list prefix for new div
            self._div_has_br = False  # Reset br flag for new div

        elif tag == 'span' and 'style' in attrs_dict:
            style = attrs_dict['style']
            # Extract font-size from style="font-size: 24px"
            match = re.search(r'font-size:\s*(\d+)px', style)
            if match:
                self._span_font_size = int(match.group(1))
                if self._in_div:
                    self._div_font_size = self._span_font_size

        elif tag == 'b' or tag == 'strong':
            self._is_bold = True
            if self._in_div:
                self._div_bold_count += 1

        elif tag == 'i' or tag == 'em':
            self._is_italic = True
            if self._in_div:
                self._div_has_italic = True

        elif tag == 'u':
            self._is_underline = True

        elif tag == 'strike' or tag == 's' or tag == 'del':
            self._is_strike = True

        elif tag == 'font':
            face = attrs_dict.get('face', '')
            # Check for Courier/monospace fonts
            if face == 'Courier' or face == 'monospace' or 'Courier' in face or 'Monaco' in face or 'Consolas' in face:
                self._is_courier = True
                if self._in_div:
                    self._div_has_courier = True
            # Check for Notes.app H3 header font (.HiraKakuInterface-W6)
            elif '.HiraKakuInterface-W6' in face or face == '.HiraKakuInterface-W6':
                if self._in_div:
                    self._div_has_hiraku_w6 = True

        elif tag == 'tt' or tag == 'code':
            self._is_tt = True
            if self._in_div:
                self._div_has_tt = True

        elif tag in ('h1', 'h2', 'h3'):
            # Handle standard HTML header tags
            self._in_header = True
            if self._in_div:
                if tag == 'h1':
                    self._div_font_size = 24
                elif tag == 'h2':
                    self._div_font_size = 18
                elif tag == 'h3':
                    # H3 uses the same trigger as Notes.app's bold format
                    self._div_bold_count = 2

        elif tag == 'ul':
            self._flush_div()
            self._in_list = True
            self._list_type = 'ul'

        elif tag == 'ol':
            self._flush_div()
            self._in_list = True
            self._list_type = 'ol'

        elif tag == 'li':
            self._in_li = True
            # Set list prefix for this li element
            if self._list_type == 'ul':
                self._list_prefix = '- '
            elif self._list_type == 'ol':
                # Notes.app doesn't preserve list numbering, always use "1."
                self._list_prefix = '1. '
            # Treat li content like a div (accumulate text parts)
            # Reset div tracking to capture li content
            self._in_div = True  # Enable div text accumulation
            self._div_has_courier = False
            self._div_has_tt = False
            self._div_has_courier_span = False
            self._div_font_size = None
            self._div_bold_count = 0
            self._div_has_italic = False
            self._div_text_parts = []

        elif tag == 'br':
            if self._in_div:
                self._div_has_br = True

        elif tag == 'pre':
            self._in_code_block = True

        elif tag == 'table':
            self._in_table = True
            self._table_rows = []
            self._current_row = []

        elif tag == 'tr':
            self._current_row = []

        elif tag == 'td' or tag == 'th':
            self._in_cell = True
            self._cell_text = []

    def handle_endtag(self, tag: str):
        if tag == 'div':
            self._in_div = False
            self._flush_div()  # Flush div content when div closes

        elif tag == 'span':
            self._span_font_size = None

        elif tag == 'b' or tag == 'strong':
            self._is_bold = False

        elif tag == 'i' or tag == 'em':
            self._is_italic = False

        elif tag == 'u':
            self._is_underline = False

        elif tag == 'strike' or tag == 's' or tag == 'del':
            self._is_strike = False

        elif tag == 'font':
            self._is_courier = False

        elif tag == 'tt' or tag == 'code':
            self._is_tt = False

        elif tag in ('h1', 'h2', 'h3'):
            # Exit header context
            self._in_header = False

        elif tag == 'ul':
            self._flush_div()
            self._in_list = False
            self._list_type = None

        elif tag == 'ol':
            self._flush_div()
            self._in_list = False
            self._list_type = None
            self._list_counter = 0  # Reset counter

        elif tag == 'li':
            self._flush_div()  # Flush li content as a line
            self._in_li = False
            self._in_div = False  # Restore previous in_div state

        elif tag == 'pre':
            self._in_code_block = False

        elif tag == 'table':
            self._in_table = False
            # Output table as markdown
            if self._table_rows:
                for row in self._table_rows:
                    self.lines.append(f"| {' | '.join(row)} |")
                self.lines.append('')  # Empty line after table

        elif tag == 'td' or tag == 'th':
            self._in_cell = False
            cell_text = ''.join(self._cell_text).strip()
            self._current_row.append(cell_text)

        elif tag == 'tr':
            if self._current_row:
                self._table_rows.append(self._current_row)

    def handle_data(self, data: str):
        if not data:
            return

        if self._in_cell:
            self._cell_text.append(data)
            return

        # Apply formatting based on current state
        formatted = data

        # Apply inline formatting FIRST (before adding list prefix)
        # Skip bold formatting inside:
        # - Standard h1/h2/h3 tags (_in_header)
        # - Notes.app H3 format (.HiraKakuInterface-W6 font)
        # - Notes.app H3 format (multiple bold tags WITHOUT italic indicating header)

        # Check for bold + italic combination (***text***)
        # When italic is present in the div, multiple bold tags don't indicate H3
        is_bold_italic = (self._is_bold and self._is_italic and
                         not self._span_font_size and not self._in_header and
                         not self._div_has_hiraku_w6 and
                         (self._div_bold_count < 2 or self._div_has_italic))

        if is_bold_italic:
            formatted = f'***{formatted}***'
        elif self._is_bold and not self._span_font_size and not self._in_header and not self._div_has_hiraku_w6 and self._div_bold_count < 2:
            formatted = f'**{formatted}**'
        elif self._is_italic:
            formatted = f'*{formatted}*'

        if self._is_underline:
            formatted = f'___{formatted}___'
        if self._is_strike:
            formatted = f'~~{formatted}~~'

        # For list items, add prefix AFTER inline formatting
        # This ensures "- ~~text~~" not "~~- text~~"
        if self._list_prefix:
            formatted = self._list_prefix + formatted
            # Only use prefix once per li, then reset
            self._list_prefix = ''

        # Handle Courier font (inline code)
        # Check if we have Courier WITHOUT tt (using span instead)
        if self._is_courier and not self._is_tt and not self._in_code_block:
            formatted = f'`{formatted}`'
            if self._in_div:
                self._div_has_courier_span = True

        self._div_text_parts.append(formatted)

    def handle_entityref(self, name: str):
        """Handle named character entities like &lt; &gt; &amp; etc."""
        entity_map = {
            'lt': '<',
            'gt': '>',
            'amp': '&',
            'quot': '"',
            'apos': "'"
        }
        char = entity_map.get(name, f'&{name};')
        self.handle_data(char)

    def handle_charref(self, name: str):
        """Handle numeric character entities like &#123;."""
        try:
            char = chr(int(name))
            self.handle_data(char)
        except (ValueError, TypeError):
            self.handle_data(f'&#{name};')


def html_to_markdown(html: str) -> str:
    """Convert Notes.app HTML to Markdown using html.parser."""
    if not html:
        return ""

    # Special character placeholders
    placeholders = {
        '<': '\x00LT\x00',
        '>': '\x00GT\x00',
        '&': '\x00AMP\x00',
    }

    def protect_and_decode(text: str) -> str:
        """Protect HTML tags, decode entities, then protect decoded special chars."""
        import re as re_local

        # Restore markdown links from HTML comments BEFORE protecting tags
        # Markdown links are stored as <!--MD_LINK-->[text](url)<!--/MD_LINK-->
        def restore_markdown_links(m: Match) -> str:
            return m.group(1)
        text = re_local.sub(r'<!--MD_LINK-->(.+?)<!--/MD_LINK-->', restore_markdown_links, text)

        tag_counter = [0]
        tag_placeholders = {}

        def save_tag(m: Match) -> str:
            placeholder = f'\x01TAG{tag_counter[0]}\x01'
            tag_counter[0] += 1
            tag_placeholders[placeholder] = m.group(0)
            return placeholder

        # Protect all HTML tags first
        text = re_local.sub(r'<[^>]+>', save_tag, text)

        # Decode HTML entities (now they're safe from being interpreted as tags)
        # Process entities without semicolon first (Notes.app sometimes omits them)
        text = text.replace('&quot', '"')
        text = text.replace('&apos', "'")
        text = text.replace('&lt', '<')
        text = text.replace('&gt', '>')
        text = text.replace('&amp', '&')
        # Process standard entities with semicolon
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')

        # Protect the decoded special characters
        text = text.replace('<', placeholders['<'])
        text = text.replace('>', placeholders['>'])
        text = text.replace('&', placeholders['&'])

        # Restore HTML tags
        for placeholder, tag in tag_placeholders.items():
            text = text.replace(placeholder, tag)

        return text

    result = protect_and_decode(html)

    # Process <pre><code> format (from markdown_to_html) - convert to individual divs
    # This matches the format: <div><pre><code>content</code></pre></div>
    def process_pre_code(match: Match) -> str:
        """Convert <pre><code> format to individual divs for processing."""
        pre_content = match.group(1)
        # Decode HTML entities (already decoded above, but just in case)
        pre_content = pre_content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        # Split into lines and create individual divs
        lines = pre_content.split('\n')
        result_divs = []
        for line in lines:
            # Separate indentation from code
            indent_match = re.match(r'^(\s+)(.*)', line)
            if indent_match and indent_match.group(1):
                indent = indent_match.group(1)
                code = indent_match.group(2)
                indent_html = f'<font face=".AppleSystemUIFont"><span style="font-size: 13px"><tt>{indent}</tt></span></font>'
                code_html = f'<font face="Courier"><tt>{code}</tt></font>'
                result_divs.append(f'<div>{indent_html}{code_html}<font face=".AppleSystemUIFont"><span style="font-size: 13px"><tt><br></tt></span></font></div>')
            else:
                # No indentation
                result_divs.append(f'<div><font face="Courier"><tt>{line}</tt></font><font face=".AppleSystemUIFont"><span style="font-size: 13px"><tt><br></tt></span></font></div>')
        return '\n'.join(result_divs)

    result = re.sub(r'<div><pre><code>(.*?)</code></pre></div>', process_pre_code, result, flags=re.DOTALL)

    # Parse with html.parser
    parser = NotesAppHTMLParser()
    try:
        parser.feed(result)
    except Exception as e:
        # If parsing fails, return as-is with error indication
        return f"# Parsing Error\n\n{e}\n\n---\n\n{result}"

    markdown = parser.get_result()

    # Restore placeholders
    markdown = markdown.replace('\x00LT\x00', '<')
    markdown = markdown.replace('\x00GT\x00', '>')
    markdown = markdown.replace('\x00AMP\x00', '&')

    return markdown


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Simple self-test
        test_md = """# Test Title
## Section 1
This is **bold** and *italic* text.

- Item 1
- Item 2

1. First
2. Second

| Header1 | Header2 |
| --- | --- |
| Data1 | Data2 |

`code` test
"""
        html = markdown_to_html(test_md)
        print("=== Markdown -> HTML ===")
        print(html)
        print("\n=== HTML -> Markdown ===")
        print(html_to_markdown(html))
