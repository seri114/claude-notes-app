---
name: notes-app
description: Read and write macOS Notes.app using Python. Create, read, update, and delete notes with Markdown support. Markdown is converted to/from Notes.app HTML format. Use when users ask to "write a memo", "take notes", "save to Notes", "add to reminder", "create a note", "メモする", "メモを書いて", "ノートに保存", "覚え書き", or want to save information to Notes.app.
argument-hint: [title]
---

# Notes.app Python Scripts Skill

**IMPORTANT:** Always use Python scripts - do not directly manipulate Notes.app data.

## How to Use

When users ask to create/modify notes:
1. Generate the Markdown content
2. Pipe it to the appropriate script:
   - Create: `echo "Markdown" | "${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/create_note.py" "Title"`
   - Replace: `echo "Markdown" | "${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/replace_note.py" "Title"`
   - Rename: `"${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/rename_note.py" "Old Title" "New Title"`
   - Show: `"${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/show_note.py" "Title"`
   - Delete: `"${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/delete_note.py" "Title"`
   - List: `"${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/list_notes.py" [pattern]`

## Requirements

- macOS with Notes.app
- Python 3 (standard library only, no pip dependencies)
- Default: Notes stored in iCloud account > "Notes" folder

Customize account/folder:
```bash
NOTES_ACCOUNT="On My Mac" NOTES_FOLDER="Folder" "${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/create_note.py" "Title" < file.md
```

## Performance Options

Use `LIMIT` to control how many notes are searched (default: 100):
```bash
LIMIT=500 "${CLAUDE_PLUGIN_ROOT}/skills/notes-app/scripts/replace_note.py" "Note Title" < file.md
```

## Markdown Formatting

Supported Markdown syntax:
- `# H1`, `## H2`, `### H3` - Headers
- `**bold**`, `*italic*`, `***bolditalic***` - Emphasis
- `~~strikethrough~~` - Strikethrough
- `- item`, `1. item` - Lists
- `[text](url)` - Links (preserved in original format)
- `` `code` `` - Inline code
- ```text``` - Code blocks (language identifier like ```python is optional, not preserved)
- `| A | B |` - Tables
- `- [ ]`, `- [x]` - Checkboxes
- `> quote` - Blockquote (write-only, not detected when reading)

Notes.app converts headers to styled text (h1→24px, h2→18px, h3→bold).

## Limitations (Notes.app HTML Format)

The following are limitations of Notes.app's internal HTML format, not this implementation:

| Feature | Limitation | Workaround |
|---------|-----------|------------|
| **Ordered lists** | Numbering is not preserved; all items become `1.` | N/A - use unordered lists or accept `1.` |
| **Table separators** | `| --- | --- |` is not stored (Markdown-only syntax) | N/A - tables work without separators |
| **Single-word H3** | `### Word` becomes indistinguishable from `**Word**` | Use multi-word H3: `### Header Text` |
| **Links** | URLs in `<a>` tags are lost; use separate format | Put links on their own line: `[text](url)` → `text` then `url` |
| **Multi-line list items** | Continuation lines with indentation are not preserved | Use single-line list items, or use code blocks ``` for multi-line content |
| **Code block indent** | Indentation outside ``` code blocks is not preserved | Always use ``` fences for code blocks |

## Table Support

Tables are supported using Markdown syntax:
```markdown
| Header1 | Header2 |
| A | B |
| C | D |
```
Note: Separator row `| --- | --- |` is optional (not stored by Notes.app).
