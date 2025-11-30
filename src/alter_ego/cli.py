import click
from alter_ego import AlterEgo


@click.group()
def cli() -> None:
    """Alter/Ego command-line interface."""
    pass


@cli.command()
@click.argument("text", nargs=-1)
def speak(text: tuple[str, ...]) -> None:
    """Speak text using the Alter/Ego engine."""

    ae = AlterEgo()
    ae.speak(" ".join(text))


def main() -> None:
    cli(prog_name="alter-ego")


if __name__ == "__main__":
    main()
