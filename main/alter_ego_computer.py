#!/usr/bin/env python3
"""Compatibility entrypoint for the Alter/Ego CLI.

This wrapper preserves the legacy `main/alter_ego_computer.py` path while
delegating behavior to the canonical package module.
"""

from alter_ego.alter_ego_computer import app, console


def main() -> None:
    if app is None:
        console.print("[red]Typer is not installed; the CLI is unavailable.[/red]")
        return
    app()


if __name__ == "__main__":
    main()
