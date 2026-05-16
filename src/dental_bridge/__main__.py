"""CLI entry point."""

from __future__ import annotations


def main() -> None:
    from dental_bridge.cli.app import app

    app()


if __name__ == "__main__":
    main()
