"""``dental-bridge analyze`` — read-only inspection of a source DB."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from dental_bridge import __version__
from dental_bridge.adapters.gesden.adapter import GesdenAdapter
from dental_bridge.cli.utils.inventory import SourceInventory, collect
from dental_bridge.cli.utils.reports import render_analyze_report

console = Console()


def run(
    source: str,
    *,
    user: str | None,
    password: str | None,
    trusted_connection: bool,
    trust_server_certificate: bool,
    encrypt: bool,
    tenant_label: str | None,
    output: Path,
) -> int:
    adapter = GesdenAdapter()
    try:
        adapter.connect(
            source,
            user=user,
            password=password,
            trusted_connection=trusted_connection,
            trust_server_certificate=trust_server_certificate,
            encrypt=encrypt,
        )
        fingerprint = adapter.fingerprint()
        conn = adapter._require_conn()
        inventory = collect(conn, fingerprint=fingerprint)
    finally:
        adapter.close()

    label = tenant_label or _guess_tenant_label(source)
    _render_summary(inventory, label, fingerprint)
    render_analyze_report(inventory, tenant_label=label, version=__version__, output_path=output)
    console.print(f"\n[bold green]HTML report:[/bold green] {output}")
    return 0


def _guess_tenant_label(source: str) -> str:
    return source.rsplit("/", 1)[-1] or "unknown"


def _render_summary(inventory: SourceInventory, label: str, fingerprint: str) -> None:
    console.print(f"\n[bold]Source:[/bold] {label}")
    console.print(f"[bold]Fingerprint:[/bold] {fingerprint}")
    console.print(f"[bold]Distinct tenants:[/bold] {len(inventory.tenant_labels)}")
    console.print(f"[bold]Total source rows:[/bold] {inventory.total_rows:,}")
    if inventory.risks:
        console.print(f"[yellow]{len(inventory.risks)} risk(s) detected:[/yellow]")
        for r in inventory.risks:
            colour = {"info": "blue", "warn": "yellow", "error": "red"}.get(r.severity, "white")
            console.print(f"  [{colour}]{r.severity}[/]: {r.code} — {r.message}")
    table = Table(title="Source counts per entity", show_lines=False)
    table.add_column("Entity")
    table.add_column("Source table")
    table.add_column("Rows", justify="right")
    for e in inventory.entities:
        count = f"{e.row_count:,}" if e.row_count >= 0 else "—"
        table.add_row(e.entity_type, e.source_table, count)
    console.print(table)


def register(app: typer.Typer) -> None:
    @app.command(name="analyze")
    def analyze_cmd(
        source: str = typer.Option(..., "--source"),
        user: str | None = typer.Option(None, "--user"),
        password: str | None = typer.Option(None, "--password", envvar="DENTAL_BRIDGE_PWD"),
        trusted_connection: bool = typer.Option(False, "--trusted-connection"),
        trust_server_certificate: bool = typer.Option(False, "--trust-server-certificate"),
        no_encrypt: bool = typer.Option(False, "--no-encrypt"),
        tenant_label: str | None = typer.Option(None, "--tenant-label"),
        output: Path = typer.Option(
            Path("analyze-report.html"), "--output", "-o", help="HTML report path"
        ),
    ) -> None:
        """Read-only inspection. Produces an HTML report, writes no DPMF."""
        rc = run(
            source,
            user=user,
            password=password,
            trusted_connection=trusted_connection,
            trust_server_certificate=trust_server_certificate,
            encrypt=not no_encrypt,
            tenant_label=tenant_label,
            output=output,
        )
        raise typer.Exit(code=rc)
