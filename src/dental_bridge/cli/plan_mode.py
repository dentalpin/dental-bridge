"""``dental-bridge plan`` — emit a YAML scope plan from a source inventory.

The plan file is the operator's contract for the next ``extract``:
which entities to include, what tenant label to attach, optional
date-range filters. v0.1 emits a defaulted plan that includes every
supported entity; the operator can comment out lines, adjust filters,
and feed it back to ``extract`` in a future sprint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer
import yaml
from rich.console import Console

from dental_bridge import __version__
from dental_bridge.adapters.gesden.adapter import GesdenAdapter
from dental_bridge.cli.utils.inventory import collect

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
    plan = {
        "spec_version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "exporter_version": __version__,
        "source": {
            "dsn": source,
            "fingerprint": fingerprint,
            "tenant_label": label,
        },
        "tenants_detected": inventory.tenant_labels,
        "entities": [
            {
                "type": e.entity_type,
                "source_table": e.source_table,
                "expected_row_count": e.row_count,
                "include": True,
            }
            for e in inventory.entities
        ],
        "filters": {
            "date_from": None,
            "date_to": None,
            "center_ids": [],
        },
        "risks": [
            {"code": r.code, "severity": r.severity, "message": r.message} for r in inventory.risks
        ],
    }

    output.write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    console.print(f"[bold green]Plan written:[/bold green] {output}")
    console.print(
        "[dim]Edit the YAML to scope down entities or apply filters, "
        "then feed it to `dental-bridge extract` (planned for Sprint 8+).[/dim]"
    )
    return 0


def _guess_tenant_label(source: str) -> str:
    return source.rsplit("/", 1)[-1] or "unknown"


def register(app: typer.Typer) -> None:
    @app.command(name="plan")
    def plan_cmd(
        source: str = typer.Option(..., "--source"),
        user: str | None = typer.Option(None, "--user"),
        password: str | None = typer.Option(None, "--password", envvar="DENTAL_BRIDGE_PWD"),
        trusted_connection: bool = typer.Option(False, "--trusted-connection"),
        trust_server_certificate: bool = typer.Option(False, "--trust-server-certificate"),
        no_encrypt: bool = typer.Option(False, "--no-encrypt"),
        tenant_label: str | None = typer.Option(None, "--tenant-label"),
        output: Path = typer.Option(Path("migration-plan.yaml"), "--output", "-o"),
    ) -> None:
        """Generate a YAML migration plan from the current source state."""
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
