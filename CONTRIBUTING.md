# Contributing to Alter/Ego

Thank you for helping shape Alter/Ego. This document describes how to set up your environment, follow the project's coding style, and run tests.

## Setup

1. Ensure you have **Python 3.8+** installed.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies from the `main` directory:
   ```bash
   pip install -r main/requirements.txt
   ```

## Coding Style

- Adhere to [PEP 8](https://peps.python.org/pep-0008/).
- Use four spaces for indentation.
- Write clear, descriptive names for variables and functions.
- Include docstrings for new modules, classes, and functions.
- Keep functions focused; prefer readability over cleverness.

## Tests

Run the test suite from the `main` directory:
```bash
cd main
PYTHONPATH=. pytest
```
Add tests for any new features or bug fixes. Ensure all tests pass before opening a pull request.

## Issues

Use the templates under `.github/ISSUE_TEMPLATE` when reporting bugs or requesting features.

We appreciate your contributions—big or small.
