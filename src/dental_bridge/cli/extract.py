"""``dental-bridge extract`` — Sprint 8 implementation.

Writes a DPMF file with optional zstd compression and AES-256-GCM
encryption layers. Encryption requires a passphrase supplied via the
``DENTAL_BRIDGE_DPMF_PASSPHRASE`` environment variable.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from dental_bridge import __version__
from dental_bridge.core.adapters.origin_abc import OriginAdapter
from dental_bridge.core.adapters.registry import discover
from dental_bridge.core.dpmf.compress import compress_file
from dental_bridge.core.dpmf.crypto import encrypt_file
from dental_bridge.core.dpmf.writer import DpmfWriter
from dental_bridge.core.pipeline.checkpoint import (
    SqliteCheckpointStore,
    default_run_id,
)
from dental_bridge.core.pipeline.runner import run_extraction

console = Console()


def run(
    source: str,
    output: Path,
    *,
    user: str | None,
    password: str | None,
    trusted_connection: bool,
    trust_server_certificate: bool,
    encrypt: bool,
    tenant_label: str | None,
    allow_unknown_schema: bool,
    resume: bool,
    compress: bool,
    dpmf_passphrase: str | None,
    adapter_name: str = "gesden",
) -> int:
    """Implement ``dental-bridge extract`` for a registered origin adapter."""
    if output.exists():
        console.print(f"[red]refusing to overwrite existing file:[/red] {output}")
        return 2

    adapters = discover()
    adapter_cls = _resolve_adapter_class(adapter_name, adapters)
    if adapter_cls is None:
        console.print(
            f"[red]unknown adapter:[/red] {adapter_name}. "
            f"Available adapters: {', '.join(sorted(adapters)) or '(none)'}"
        )
        return 2

    if adapter_name == "nemodent" and (
        user or password or trusted_connection or trust_server_certificate or not encrypt
    ):
        console.print(
            "[red]Nemodent uses a local MDB and does not accept SQL Server "
            "credentials or TLS options.[/red]"
        )
        return 2

    adapter = adapter_cls()
    checkpoint: SqliteCheckpointStore | None = None
    workdir = Path(tempfile.mkdtemp(prefix="dental-bridge-"))
    try:
        label = tenant_label or _guess_tenant_label(source, adapter_name=adapter_name)
        if adapter_name == "nemodent":
            adapter.connect(source, tenant_label=label)
        else:
            adapter.connect(
                source,
                user=user,
                password=password,
                trusted_connection=trusted_connection,
                trust_server_certificate=trust_server_certificate,
                encrypt=encrypt,
            )

        fingerprint = adapter.fingerprint()
        lookup = getattr(adapter, "lookup_fingerprint", None)
        known = lookup(fingerprint) if callable(lookup) else None
        if known is None:
            console.print(
                f"[yellow]Schema fingerprint not in registry:[/yellow] [bold]{fingerprint}[/bold]"
            )
            if not allow_unknown_schema:
                console.print(
                    "Pass --allow-unknown-schema to proceed anyway. "
                    "Please also open an issue and attach the fingerprint."
                )
                return 3
            console.print(
                "[yellow]Proceeding with an unregistered schema by explicit operator opt-in.[/yellow]"
            )
            warnings = _adapter_context_value(adapter, "warnings")
            if warnings is not None:
                warnings.add(
                    severity="warn",
                    code="source.schema_unknown_override",
                    message=(
                        "Extraction continued with --allow-unknown-schema; "
                        f"fingerprint={fingerprint}."
                    ),
                )
        else:
            console.print(f"[green]Schema fingerprint recognised:[/green] {known.description}")

        run_id = default_run_id(tenant_label=label, source_fingerprint=fingerprint)

        if resume:
            checkpoint = SqliteCheckpointStore()
            console.print(f"[dim]Resume enabled, run_id={run_id}[/dim]")

        sqlite_path = workdir / "out.sqlite"
        with DpmfWriter(
            sqlite_path,
            source_system=adapter.name,
            source_adapter_version=adapter.version,
            exporter_version=__version__,
            tenant_label=label,
            source_schema_fingerprint=fingerprint,
        ) as writer:
            summary = run_extraction(
                adapter,
                writer,
                entity_order=adapter.default_entity_order(),
                id_mapping=_adapter_context_value(adapter, "id_mapping"),
                warnings=_adapter_context_value(adapter, "warnings"),
                checkpoint=checkpoint,
                run_id=run_id if checkpoint is not None else None,
            )
            digest = writer.finalise()

        _materialise(sqlite_path, output, compress=compress, passphrase=dpmf_passphrase)
        _render_summary(summary, output, digest, compress, dpmf_passphrase is not None)
        return 0
    finally:
        if checkpoint is not None:
            checkpoint.close()
        adapter.close()
        shutil.rmtree(workdir, ignore_errors=True)


def _materialise(
    sqlite_path: Path,
    final_output: Path,
    *,
    compress: bool,
    passphrase: str | None,
) -> None:
    """Apply optional compression + encryption layers to the built SQLite."""
    working = sqlite_path
    inner_layout = "raw"
    if compress:
        compressed = sqlite_path.with_suffix(".sqlite.zst")
        compress_file(working, compressed)
        working = compressed
        inner_layout = "zstd"

    if passphrase:
        encrypt_file(working, final_output, passphrase=passphrase, inner_layout=inner_layout)
    else:
        shutil.move(str(working), str(final_output))


def _guess_tenant_label(source: str, *, adapter_name: str = "gesden") -> str:
    """Default tenant_label to the database name in the DSN.

    The operator can override with --tenant-label when they want a more
    descriptive name (e.g. the clinic's short code).
    """
    if adapter_name == "nemodent":
        return Path(source).stem or "unknown"
    return source.rsplit("/", 1)[-1] or "unknown"


def _adapter_context_value(adapter: object, name: str) -> Any:
    """Read optional shared state from adapters that supply pipeline registries."""
    context = getattr(adapter, "context", None)
    return getattr(context, name, None)


def _resolve_adapter_class(
    adapter_name: str,
    adapters: dict[str, type[OriginAdapter]] | None = None,
) -> type[OriginAdapter] | None:
    """Resolve the selected source through the installed adapter entry points."""
    available = discover() if adapters is None else adapters
    return available.get(adapter_name)


def _render_summary(
    summary,  # type: ignore[no-untyped-def]
    output: Path,
    digest: str,
    compressed: bool,
    encrypted: bool,
) -> None:
    table = Table(title="Extraction summary", show_lines=False)
    table.add_column("Entity")
    table.add_column("Rows", justify="right")
    for entity, count in summary.rows_by_entity.items():
        table.add_row(entity, f"{count:,}")
    console.print(table)
    layers = []
    if compressed:
        layers.append("zstd")
    if encrypted:
        layers.append("AES-256-GCM")
    layers_label = f" ({', '.join(layers)})" if layers else ""
    console.print(f"[bold green]Output:[/bold green] {output}{layers_label}")
    console.print(f"[bold]SHA-256 (logical content):[/bold] {digest}")
    console.print(f"[bold]File size:[/bold] {output.stat().st_size:,} bytes")
    if len(summary.warnings):
        console.print(
            f"[yellow]{len(summary.warnings)} warning(s) recorded inside the file.[/yellow]"
        )


# Typer wiring -----------------------------------------------------------
def register(app: typer.Typer) -> None:
    @app.command(name="extract")
    def extract_cmd(
        adapter_name: str = typer.Option(
            "gesden",
            "--adapter",
            help="Registered origin adapter to use (default: gesden).",
        ),
        source: str = typer.Option(
            ...,
            "--source",
            help="Source DSN or local database path, depending on the adapter.",
        ),
        output: Path = typer.Option(..., "--output", "-o", help="Path of the .dpm file to write"),
        user: str | None = typer.Option(None, "--user", help="SQL Server login"),
        password: str | None = typer.Option(
            None,
            "--password",
            help="SQL Server password. Prefer the DENTAL_BRIDGE_PWD env var.",
            envvar="DENTAL_BRIDGE_PWD",
        ),
        trusted_connection: bool = typer.Option(
            False,
            "--trusted-connection",
            help="Use Windows authentication instead of SQL login.",
        ),
        trust_server_certificate: bool = typer.Option(
            False,
            "--trust-server-certificate",
            help="Accept the SQL Server's self-signed TLS certificate.",
        ),
        no_encrypt: bool = typer.Option(
            False,
            "--no-encrypt",
            help="Disable TLS. Acceptable on private LAN with legacy SQL Server only.",
        ),
        tenant_label: str | None = typer.Option(
            None,
            "--tenant-label",
            help="Human-readable label recorded in the DPMF file's metadata.",
        ),
        allow_unknown_schema: bool = typer.Option(
            False,
            "--allow-unknown-schema",
            help="Proceed even if the source schema fingerprint is not registered.",
        ),
        no_resume: bool = typer.Option(
            False,
            "--no-resume",
            help="Disable the local checkpoint store. Forces a full re-extraction.",
        ),
        compress: bool = typer.Option(
            False,
            "--compress",
            help="Wrap the output in a zstd frame (5-10x smaller for our payloads).",
        ),
        dpmf_passphrase: str | None = typer.Option(
            None,
            "--dpmf-passphrase",
            envvar="DENTAL_BRIDGE_DPMF_PASSPHRASE",
            help=(
                "Encrypt the DPMF file with AES-256-GCM, deriving the key from "
                "this passphrase via scrypt. Prefer the environment variable."
            ),
        ),
    ) -> None:
        """Extract an origin database into a DPMF file."""
        rc = run(
            source,
            output,
            user=user,
            password=password,
            trusted_connection=trusted_connection,
            trust_server_certificate=trust_server_certificate,
            encrypt=not no_encrypt,
            tenant_label=tenant_label,
            allow_unknown_schema=allow_unknown_schema,
            resume=not no_resume,
            compress=compress,
            dpmf_passphrase=dpmf_passphrase,
            adapter_name=adapter_name,
        )
        raise typer.Exit(code=rc)
