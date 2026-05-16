"""Root Typer application — wires the four operating modes."""

from __future__ import annotations

import typer

from dental_bridge import __version__
from dental_bridge.cli import analyze as analyze_module
from dental_bridge.cli import extract as extract_module
from dental_bridge.cli import plan_mode
from dental_bridge.cli import verify as verify_module

app = typer.Typer(
    name="dental-bridge",
    help="Open source migration toolkit for dental practice management systems.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    if version:
        typer.echo(f"dental-bridge {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


analyze_module.register(app)
plan_mode.register(app)
extract_module.register(app)
verify_module.register(app)
