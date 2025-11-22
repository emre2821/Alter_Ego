# Alter/Ego

> Lightweight text-to-speech / voice automation assistant

[![Build Status](#)](#) [![PyPI](#)](#) [![License](#)](#)

Alter/Ego is a compact voice companion for desktop workflows. It ships with a simple Python API and CLI so you can script speech in seconds.

## Installation

```bash
pip install alter-ego
```

To enable the optional RAG/CLI features that rely on larger libraries such as ChromaDB and the Transformers stack, install the
`rag` extra:

```bash
pip install "alter-ego[rag]"
```

## CLI Quickstart

```bash
alter-ego speak "Hello"
```

## Python Quickstart

```python
from alter_ego import AlterEgo

bot = AlterEgo()
bot.speak("Hello")
```

## Features

- Minimal setup for local text-to-speech.
- Click-powered CLI with a `speak` command.
- Extensible Python API for integrating speech into automations.
- Ships with scaffolding for CI, docs, and releases.
- Ready for packaging and PyPI distribution.

## Demo

![Demo GIF Placeholder](docs/img/demo.gif)

## Documentation

- [Overview](docs/index.md)
- [Quickstart](docs/quickstart.md)
- [TTS Engines](docs/tts-engines.md)
- [Configuration](docs/config.md)

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` for guidelines.

### Branch naming for CI

The GitHub Actions workflow runs on pushes and pull requests to `develop`, `release/**`, `main`, and `master`. When cutting a
release branch, use the `release/<name>` pattern (for example, `release/1.2.0`) so CI builds are triggered automatically.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
