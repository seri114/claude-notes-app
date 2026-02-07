# Contributing to claude-notes-app

Thank you for your interest in contributing to claude-notes-app!

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Your macOS version
- Your Python version (`python3 --version`)
- Any relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- Use a clear and descriptive title
- Provide a detailed explanation of the suggested enhancement
- Explain why this enhancement would be useful

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-notes-app.git
   cd claude-notes-app
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Running Tests

Test the scripts directly:

```bash
cd skills/notes-app/scripts
python test_all.py
```

### Code Style

- Use Python 3 type hints where appropriate
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Keep functions focused and modular

### Submitting Changes

1. Commit your changes with a clear message
2. Push to your fork
3. Create a pull request with:
   - A clear title describing the change
   - A description of what you changed and why
   - Reference any related issues

### Pull Request Guidelines

- Keep PRs focused on a single issue or feature
- Ensure all tests pass
- Update documentation as needed
- Be responsive to feedback

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
