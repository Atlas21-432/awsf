# Contributing to AWSF

First off, thanks for taking the time to contribute! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible using our bug report template.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Create an issue using the feature request template and provide the following information:

- Use a clear and descriptive title
- Provide a detailed description of the suggested enhancement
- Explain why this enhancement would be useful

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure your code follows the existing style
4. Make sure your code lints (use `pylint` or `flake8`)
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/awsf.git
cd awsf

# Install dependencies
pip install -r requirements.txt

# Make your changes
# Test your changes
./awsf

# Run linter (optional but recommended)
pylint src/awsf.py
```

## Code Style

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Add docstrings to functions
- Keep functions focused and modular

## Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Adding New AWS Services

To add support for a new AWS service:

1. Update `SERVICE_CONFIG` in `src/awsf.py` with service metadata
2. Add service fetching logic in `scripts/populate_resources.py`
3. Test with real AWS resources
4. Update README.md to list the new service
5. Submit a pull request!

## Questions?

Feel free to open a discussion or reach out via issues!
