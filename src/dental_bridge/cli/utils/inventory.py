"""Read-only inventory of a connected source database.

Used by ``analyze``, ``plan`` and ``verify``. The inventory holds:

- Per-canonical-entity row counts of the underlying source table(s).
- Financial totals where they make sense (treatment amounts, debt sums,
  payment sums).
- A handful of risk indicators: multi-tenant detection, sentinel-date
  prevalence in date columns, presence of legacy-encoding glyphs.

Counts are pulled with raw SQL because they are much cheaper than
streaming every row through the canonical pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyodbc

# Map canonical entity → (source table, optional WHERE clause).
# Composite-PK entities count their natural source rows.
ENTITY_SOURCE_TABLE: dict[str, tuple[str, str | None]] = {
    "center": ("Centros", "IdCentro >= 0"),
    "professional": ("TColabos", None),
    "user": ("TUsers", None),
    "client": ("Clientes", None),
    "patient": ("Pacientes", None),
    "patient_client_link": ("PacCli", None),
    "work_calendar": ("TCalCa", None),
    "work_calendar_day": ("TCalDias", None),
    "work_calendar_shift": ("TCalHor", None),
    "appointment_recurrence": ("DCitasPeriod", None),
    "appointment": ("DCitas", None),
    "treatment_catalog_item": ("Tratamientos", None),
    "treatment_catalog_variant": ("Tratamientos_Tarifas", None),
    "treatment_phase_template": ("TratamientosFases", None),
    "budget": ("Presu", None),
    "budget_line": ("PresuTto", None),
    "applied_treatment": ("TtosMed", None),
    "applied_treatment_phase": ("TtosMedFases", None),
    "debt": ("DeudaCli", None),
    "payment": ("PagoCli", None),
    "debt_payment_application": ("DeudaPago", None),
    "fiscal_document": ("DocAdmin", None),
    "fiscal_document_line": ("LinAdmin", None),
    "pharmacological_history": ("TTratamientos", None),
    "prescription": ("RecetasCab", None),
    "prescription_item": ("RecetasDet", None),
    "consent": ("TConsinCab", None),
    "patient_document": ("TDocumentosPac", None),
    "recall": ("Recalls", None),
    "patient_alert": ("AlertPac", None),
    "communication": ("EdMail", None),
}


@dataclass(slots=True)
class EntityInventory:
    entity_type: str
    source_table: str
    row_count: int


@dataclass(slots=True)
class Risk:
    code: str
    severity: str  # info | warn | error
    message: str


@dataclass(slots=True)
class SourceInventory:
    """Aggregate inventory snapshot."""

    fingerprint: str
    tenant_labels: list[str] = field(default_factory=list)
    entities: list[EntityInventory] = field(default_factory=list)
    financial_totals: dict[str, str] = field(default_factory=dict)
    risks: list[Risk] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(e.row_count for e in self.entities)


def collect(conn: pyodbc.Connection, fingerprint: str) -> SourceInventory:
    """Run all inventory queries and return a populated snapshot."""
    inv = SourceInventory(fingerprint=fingerprint)
    inv.tenant_labels = _distinct_tenants(conn)
    inv.entities = _entity_counts(conn)
    inv.financial_totals = _financial_totals(conn)
    inv.risks = list(_detect_risks(conn, inv))
    return inv


def _distinct_tenants(conn: pyodbc.Connection) -> list[str]:
    cursor = conn.cursor()
    try:
        rows = cursor.execute(
            "SELECT DISTINCT CAST(Guid_Tenant AS varchar(64)) FROM Pacientes"
        ).fetchall()
    except Exception:
        return []
    return sorted(str(r[0]) for r in rows if r[0] is not None)


def _entity_counts(conn: pyodbc.Connection) -> list[EntityInventory]:
    out: list[EntityInventory] = []
    cursor = conn.cursor()
    for entity_type, (table, where) in ENTITY_SOURCE_TABLE.items():
        query = f"SELECT COUNT(*) FROM {table}"
        if where:
            query += f" WHERE {where}"
        try:
            count = cursor.execute(query).fetchone()[0]
        except Exception:
            count = -1  # table missing — treat as not applicable
        out.append(EntityInventory(entity_type=entity_type, source_table=table, row_count=count))
    return out


def _financial_totals(conn: pyodbc.Connection) -> dict[str, str]:
    """Return key money sums as formatted strings (avoids float precision games)."""
    queries: dict[str, str] = {
        "applied_treatment.amount (StaTto=5)": (
            "SELECT CAST(SUM(CAST(Importe AS DECIMAL(18,2))) AS VARCHAR) "
            "FROM TtosMed WHERE StaTto=5"
        ),
        "payment.amount": (
            "SELECT CAST(SUM(CAST(Pagado AS DECIMAL(18,2))) AS VARCHAR) FROM PagoCli"
        ),
        "debt.owed_amount": (
            "SELECT CAST(SUM(CAST(Adeudo AS DECIMAL(18,2))) AS VARCHAR) FROM DeudaCli"
        ),
        "debt.pending_amount": (
            "SELECT CAST(SUM(CAST(Pendiente AS DECIMAL(18,2))) AS VARCHAR) FROM DeudaCli"
        ),
        "fiscal_document_line.amount": (
            "SELECT CAST(SUM(CAST(Importe AS DECIMAL(18,2))) AS VARCHAR) FROM LinAdmin"
        ),
        "budget_line.base_amount": (
            "SELECT CAST(SUM(CAST(BaseImponible AS DECIMAL(18,2))) AS VARCHAR) FROM PresuTto"
        ),
    }
    out: dict[str, str] = {}
    cursor = conn.cursor()
    for label, sql in queries.items():
        try:
            value = cursor.execute(sql).fetchone()[0]
        except Exception:
            value = None
        if value is None:
            out[label] = "—"
        else:
            out[label] = str(value)
    return out


def _detect_risks(conn: pyodbc.Connection, inv: SourceInventory):
    if len(inv.tenant_labels) > 1:
        yield Risk(
            code="multi_tenant",
            severity="error",
            message=(
                f"{len(inv.tenant_labels)} distinct Guid_Tenant values detected. "
                "DPMF refuses to mix tenants; rerun with a per-tenant filter."
            ),
        )

    # Sentinel-date prevalence in Patient FecNacim
    cursor = conn.cursor()
    try:
        sentinel = cursor.execute(
            "SELECT COUNT(*) FROM Pacientes WHERE FecNacim < '1925-01-01'"
        ).fetchone()[0]
        if sentinel:
            yield Risk(
                code="patient.fecnacim.sentinel",
                severity="warn",
                message=(
                    f"{sentinel:,} Pacientes rows carry an implausible FecNacim "
                    "(before 1925). They will decode to None."
                ),
            )
    except Exception:
        pass

    # IdCentro=-1 sentinel
    try:
        no_center = cursor.execute("SELECT COUNT(*) FROM Pacientes WHERE IdCentro = -1").fetchone()[
            0
        ]
        if no_center:
            yield Risk(
                code="patient.idcentro.sentinel",
                severity="info",
                message=(
                    f"{no_center:,} Pacientes rows reference IdCentro = -1 "
                    "(legacy 'no centro' sentinel)."
                ),
            )
    except Exception:
        pass
