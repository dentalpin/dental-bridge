"""``dental-bridge verify`` — reconcile a DPMF against its source DB."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from dental_bridge import __version__
from dental_bridge.adapters.gesden.adapter import GesdenAdapter
from dental_bridge.cli.utils.inventory import ENTITY_SOURCE_TABLE, collect
from dental_bridge.cli.utils.reports import render_verify_report
from dental_bridge.core.dpmf.reader import open_dpmf

console = Console()


@dataclass(slots=True)
class CountRow:
    entity_type: str
    source_count: int
    dpmf_count: int

    @property
    def delta(self) -> int:
        return self.dpmf_count - self.source_count


def run(
    source: str,
    file: Path,
    *,
    user: str | None,
    password: str | None,
    trusted_connection: bool,
    trust_server_certificate: bool,
    encrypt: bool,
    tenant_label: str | None,
    output: Path,
    dpmf_passphrase: str | None,
) -> int:
    if not file.exists():
        console.print(f"[red]DPMF file not found:[/red] {file}")
        return 2

    with open_dpmf(file, passphrase=dpmf_passphrase) as dpmf_conn:
        dpmf_meta = _read_meta(dpmf_conn)
        dpmf_counts = _read_counts(dpmf_conn)
        financial_for_dpmf_fn = lambda totals: _reconcile_financial(dpmf_conn, totals)  # noqa: E731

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

        rows: list[CountRow] = []
        for e in inventory.entities:
            rows.append(
                CountRow(
                    entity_type=e.entity_type,
                    source_count=e.row_count,
                    dpmf_count=dpmf_counts.get(e.entity_type, 0),
                )
            )

        financial = financial_for_dpmf_fn(inventory.financial_totals)

        label = tenant_label or dpmf_meta.get("tenant_label", "unknown")
        render_verify_report(
            rows=rows,
            financial=financial,
            dpmf_path=file,
            dpmf_size_bytes=file.stat().st_size,
            dpmf_integrity_hash=dpmf_meta.get("integrity_hash", "?"),
            source_fingerprint=fingerprint,
            tenant_label=label,
            version=__version__,
            output_path=output,
        )

    _render_summary(rows, financial)
    discrepancies = [r for r in rows if r.delta != 0]
    if discrepancies:
        console.print(f"[red]FAIL[/red]: {len(discrepancies)} entity row-count mismatch.")
        console.print(f"[bold green]Report:[/bold green] {output}")
        return 1
    console.print("[bold green]PASS[/bold green]: all counts match.")
    console.print(f"[bold green]Report:[/bold green] {output}")
    return 0


def _read_meta(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT key, value FROM _meta"))


def _read_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entity_type, row_count, _schema in conn.execute(
        "SELECT entity_type, row_count, schema_version FROM _entities"
    ):
        counts[entity_type] = row_count
    return counts


def _reconcile_financial(
    conn: sqlite3.Connection, source_totals: dict[str, str]
) -> list[dict[str, object]]:
    queries: dict[str, tuple[str, str]] = {
        "applied_treatment.amount (StaTto=5)": (
            "applied_treatment",
            "SELECT SUM(CAST(json_extract(payload,'$.amount') AS REAL)) "
            "FROM applied_treatment "
            "WHERE CAST(json_extract(payload,'$.status_code') AS INT) = 5",
        ),
        "payment.amount": (
            "payment",
            "SELECT SUM(CAST(json_extract(payload,'$.amount') AS REAL)) FROM payment",
        ),
        "debt.owed_amount": (
            "debt",
            "SELECT SUM(CAST(json_extract(payload,'$.owed_amount') AS REAL)) FROM debt",
        ),
        "debt.pending_amount": (
            "debt",
            "SELECT SUM(CAST(json_extract(payload,'$.pending_amount') AS REAL)) FROM debt",
        ),
        "fiscal_document_line.amount": (
            "fiscal_document_line",
            "SELECT SUM(CAST(json_extract(payload,'$.amount') AS REAL)) FROM fiscal_document_line",
        ),
        "budget_line.base_amount": (
            "budget_line",
            "SELECT SUM(CAST(json_extract(payload,'$.base_amount') AS REAL)) FROM budget_line",
        ),
    }
    out: list[dict[str, object]] = []
    existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for label, (table, sql) in queries.items():
        if table not in existing:
            continue
        dpmf_value = conn.execute(sql).fetchone()[0] or 0
        source_value = source_totals.get(label, "—")
        out.append(
            {
                "label": label,
                "source": _format(source_value),
                "dpmf": f"{dpmf_value:,.2f}",
                "match": _matches(source_value, dpmf_value),
            }
        )
    return out


def _format(value: str) -> str:
    try:
        return f"{Decimal(value):,.2f}"
    except (InvalidOperation, TypeError):
        return value


def _matches(source: str, dpmf: float) -> bool:
    try:
        return abs(Decimal(source) - Decimal(str(dpmf))) < Decimal("0.5")
    except (InvalidOperation, TypeError):
        return False


def _render_summary(rows: list[CountRow], financial: list[dict[str, object]]) -> None:
    table = Table(title="Row-count reconciliation", show_lines=False)
    table.add_column("Entity")
    table.add_column("Source", justify="right")
    table.add_column("DPMF", justify="right")
    table.add_column("Δ", justify="right")
    for r in rows:
        delta = "[green]0[/]" if r.delta == 0 else f"[red]{r.delta:+,}[/]"
        source = f"{r.source_count:,}" if r.source_count >= 0 else "—"
        table.add_row(r.entity_type, source, f"{r.dpmf_count:,}", delta)
    console.print(table)
    if financial:
        ft = Table(title="Financial totals", show_lines=False)
        ft.add_column("Metric")
        ft.add_column("Source", justify="right")
        ft.add_column("DPMF", justify="right")
        ft.add_column("Status")
        for m in financial:
            ft.add_row(
                m["label"],
                m["source"],
                m["dpmf"],
                "[green]match[/]" if m["match"] else "[red]diff[/]",
            )
        console.print(ft)


def register(app: typer.Typer) -> None:
    @app.command(name="verify")
    def verify_cmd(
        source: str = typer.Option(..., "--source"),
        file: Path = typer.Option(..., "--file", "-f", help="Path to the DPMF file"),
        user: str | None = typer.Option(None, "--user"),
        password: str | None = typer.Option(None, "--password", envvar="DENTAL_BRIDGE_PWD"),
        trusted_connection: bool = typer.Option(False, "--trusted-connection"),
        trust_server_certificate: bool = typer.Option(False, "--trust-server-certificate"),
        no_encrypt: bool = typer.Option(False, "--no-encrypt"),
        tenant_label: str | None = typer.Option(None, "--tenant-label"),
        output: Path = typer.Option(Path("verify-report.html"), "--output", "-o"),
        dpmf_passphrase: str | None = typer.Option(
            None,
            "--dpmf-passphrase",
            envvar="DENTAL_BRIDGE_DPMF_PASSPHRASE",
            help="Passphrase needed for encrypted DPMF files.",
        ),
    ) -> None:
        """Reconcile a DPMF file against its source database."""
        rc = run(
            source,
            file,
            user=user,
            password=password,
            trusted_connection=trusted_connection,
            trust_server_certificate=trust_server_certificate,
            encrypt=not no_encrypt,
            tenant_label=tenant_label,
            output=output,
            dpmf_passphrase=dpmf_passphrase,
        )
        raise typer.Exit(code=rc)


# Silence unused imports kept for future expansion
_ = ENTITY_SOURCE_TABLE
