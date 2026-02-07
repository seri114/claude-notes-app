# claude-notes-app

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/seri114/claude-notes-app?style=social)](https://github.com/seri114/claude-notes-app/stargazers)

A Claude Code plugin for reading and writing macOS Notes.app using Python. Create, read, update, and delete notes with full Markdown support.

![Demo](images/demo.gif)

## Features

- **Create notes** from Markdown content
- **Read notes** and convert to Markdown
- **Update notes** by replacing content
- **Rename notes** while preserving content
- **Delete notes** by title
- **List notes** with optional pattern filtering
- **Markdown ↔ HTML conversion** for Notes.app compatibility
- **No external dependencies** - Uses Python standard library only

## Installation

### Recommended: via Marketplace

```bash
# Add the marketplace
claude plugin marketplace add seri114/claude-code

# Install the plugin
claude plugin install claude-notes-app
```

### Alternative: Manual Installation

```bash
# Clone the repository
git clone https://github.com/seri114/claude-notes-app.git ~/.claude/plugins/claude-notes-app

# Or add to your project-local plugins
git clone https://github.com/seri114/claude-notes-app.git .claude/plugins/claude-notes-app
```

## Requirements

- **macOS** with Notes.app
- **Python 3** (standard library only, no pip dependencies)
- **Claude Code** with plugin support

## Usage

The plugin provides a `/notes-app` skill that you can use directly in Claude Code.

### Examples

```
# Create a new note
/notes-app Create a note titled "Meeting Notes" with agenda items

# Read an existing note
/notes-app Show me the content of "Meeting Notes"

# Update a note
/notes-app Replace "Meeting Notes" with the updated agenda

# List all notes
/notes-app List all my notes

# List notes matching a pattern
/notes-app List notes containing "Project"

# Rename a note
/notes-app Rename "Old Title" to "New Title"

# Delete a note
/notes-app Delete "Old Notes"
```

## Development

### Testing

Install pytest and run tests:

```bash
pip install pytest
cd skills/notes-app
pytest scripts/test_all.py -v
```

See `scripts/test_all.py` for more test options.

### Project Structure

```
claude-notes-app/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/
│   └── notes-app/
│       ├── SKILL.md         # Skill documentation
│       └── scripts/
│           ├── converter.py      # Markdown ↔ HTML converter
│           ├── utils.py          # AppleScript utilities
│           ├── create_note.py
│           ├── replace_note.py
│           ├── rename_note.py
│           ├── show_note.py
│           ├── delete_note.py
│           ├── list_notes.py
│           └── test_all.py       # Test suite
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Author

Created by [seri114](https://github.com/seri114)

---

**Keywords**: claude-code, claude-plugin, macos, notes-app, apple-notes, markdown, productivity, python, メモ, ノート
