# Contributing to Alter/Ego

Thank you for helping shape Alter/Ego! We're grateful for your interest in making this project better. This document describes how to set up your environment, follow the project's coding style, and run tests.

## Getting Started

### Prerequisites

- **Python 3.9+** installed on your system
- Git for version control

### Setup (Clone to Running in 60 Seconds)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/emre2821/Alter_Ego.git
   cd Alter_Ego
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run linting and tests to verify your setup:**
   ```bash
   flake8 src/ tests/
   pytest tests/
   ```

You're ready to contribute!

## Development Workflow

### Running the Application

```bash
# CLI usage
alter-ego speak "Hello, world!"

# For development with GUI (requires additional dependencies)
python src/alter_ego/alter_ego_gui.py
```

### Environment Configuration

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```

## Coding Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use four spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Write clear, descriptive names for variables and functions
- Include docstrings for new modules, classes, and functions
- Keep functions focused; prefer readability over cleverness

### Linting

We use `flake8` for code quality checks:
```bash
flake8 src/ tests/
```

## Tests

Run the test suite:
```bash
pytest tests/ -v
```

### Writing Tests

- Add tests for any new features or bug fixes
- Place test files in the `tests/` directory
- Follow the existing naming convention: `test_<module>.py`
- Ensure all tests pass before opening a pull request

## Pull Request Process

1. Fork the repository and create a new branch from `develop`
2. Make your changes following the coding style guidelines
3. Write or update tests as needed
4. Ensure all tests pass locally
5. Submit a pull request with a clear description

## Issues

Use the templates under `.github/ISSUE_TEMPLATE` when:
- **Reporting bugs**: Include steps to reproduce and expected behavior
- **Requesting features**: Describe the problem and proposed solution

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

---

We appreciate your contributions—big or small. Thank you for helping make Alter/Ego better! 🙏
