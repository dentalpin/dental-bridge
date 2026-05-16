"""HTML report generation for analyze and verify modes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, select_autoescape


@dataclass(slots=True, frozen=True)
class VerifyDiscrepancy:
    """One mismatch between source and DPMF for a given entity."""

    entity_type: str
    source_count: int
    dpmf_count: int
    delta: int

    @property
    def severity(self) -> str:
        return "error" if self.delta != 0 else "ok"


_ANALYZE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dental-bridge analyze — {{ tenant_label }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1100px; margin: 2em auto; padding: 0 1em; color: #222; }
  h1 { border-bottom: 2px solid #2c5aa0; padding-bottom: 0.3em; }
  h2 { color: #2c5aa0; margin-top: 1.5em; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { padding: 0.4em 0.7em; border-bottom: 1px solid #eee; text-align: left; }
  th { background: #f7f9fc; font-weight: 600; }
  tr:hover { background: #fafbfd; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .risk { padding: 0.6em 1em; margin: 0.3em 0; border-radius: 4px; }
  .risk.info  { background: #eff6ff; border-left: 4px solid #3b82f6; }
  .risk.warn  { background: #fef3c7; border-left: 4px solid #f59e0b; }
  .risk.error { background: #fee2e2; border-left: 4px solid #ef4444; }
  .meta { color: #666; font-size: 0.9em; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 12px;
          background: #e5e7eb; font-size: 0.8em; }
  footer { margin-top: 3em; padding-top: 1em; border-top: 1px solid #eee;
           color: #888; font-size: 0.85em; }
</style>
</head>
<body>
<h1>analyze — {{ tenant_label }}</h1>
<p class="meta">
  Generated at {{ generated_at }} ·
  Source fingerprint: <code>{{ fingerprint }}</code> ·
  {{ inventory.total_rows }} source rows across {{ inventory.entities|length }} entity types
</p>

<h2>Tenants</h2>
{% if inventory.tenant_labels %}
  {% for t in inventory.tenant_labels %}
  <span class="pill">{{ t }}</span>
  {% endfor %}
{% else %}
  <p class="meta">No Guid_Tenant values detected.</p>
{% endif %}

<h2>Detected risks</h2>
{% if inventory.risks %}
  {% for r in inventory.risks %}
  <div class="risk {{ r.severity }}">
    <strong>[{{ r.severity }}]</strong> {{ r.code }} — {{ r.message }}
  </div>
  {% endfor %}
{% else %}
  <p class="meta">No risks detected.</p>
{% endif %}

<h2>Source counts per canonical entity</h2>
<table>
  <thead><tr><th>Canonical entity</th><th>Source table</th><th class="num">Rows</th></tr></thead>
  <tbody>
  {% for e in inventory.entities %}
    <tr>
      <td>{{ e.entity_type }}</td>
      <td><code>{{ e.source_table }}</code></td>
      <td class="num">{{ "{:,}".format(e.row_count) if e.row_count >= 0 else "—" }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<h2>Financial totals (source)</h2>
<table>
  <thead><tr><th>Metric</th><th class="num">Value</th></tr></thead>
  <tbody>
  {% for label, value in inventory.financial_totals.items() %}
    <tr><td>{{ label }}</td><td class="num">{{ value }}</td></tr>
  {% endfor %}
  </tbody>
</table>

<footer>
  Produced by dental-bridge {{ version }} ·
  This report describes the source database as it exists at the time of analysis.
  No data has been written or modified.
</footer>
</body>
</html>
"""


_VERIFY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dental-bridge verify — {{ tenant_label }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1100px; margin: 2em auto; padding: 0 1em; color: #222; }
  h1 { border-bottom: 2px solid #2c5aa0; padding-bottom: 0.3em; }
  h2 { color: #2c5aa0; margin-top: 1.5em; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { padding: 0.4em 0.7em; border-bottom: 1px solid #eee; text-align: left; }
  th { background: #f7f9fc; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .ok { color: #15803d; font-weight: 600; }
  .err { color: #b91c1c; font-weight: 600; }
  .meta { color: #666; font-size: 0.9em; }
  .stamp { background: #f7f9fc; padding: 1em; border-radius: 4px;
           font-family: ui-monospace, "SF Mono", monospace; font-size: 0.85em; }
  footer { margin-top: 3em; padding-top: 1em; border-top: 1px solid #eee;
           color: #888; font-size: 0.85em; }
</style>
</head>
<body>
<h1>verify — {{ tenant_label }}</h1>
<p class="meta">Generated at {{ generated_at }}</p>

<h2>DPMF file</h2>
<div class="stamp">
  Path: {{ dpmf_path }}<br>
  Size: {{ "{:,}".format(dpmf_size_bytes) }} bytes<br>
  SHA-256 (integrity hash): {{ dpmf_integrity_hash }}<br>
  Source fingerprint: {{ source_fingerprint }}
</div>

<h2>Overall</h2>
<p>
  Status:
  {% if discrepancies %}
    <span class="err">FAIL — {{ discrepancies|length }} entity count mismatch{{ "es" if discrepancies|length > 1 else "" }}</span>
  {% else %}
    <span class="ok">PASS — all source counts match the DPMF.</span>
  {% endif %}
</p>

<h2>Row-count reconciliation</h2>
<table>
  <thead>
    <tr><th>Entity</th><th class="num">Source</th><th class="num">DPMF</th><th class="num">Δ</th></tr>
  </thead>
  <tbody>
  {% for r in rows %}
    <tr>
      <td>{{ r.entity_type }}</td>
      <td class="num">{{ "{:,}".format(r.source_count) if r.source_count >= 0 else "—" }}</td>
      <td class="num">{{ "{:,}".format(r.dpmf_count) }}</td>
      <td class="num {{ 'ok' if r.delta == 0 else 'err' }}">{{ r.delta }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<h2>Financial-total reconciliation</h2>
<table>
  <thead><tr><th>Metric</th><th class="num">Source</th><th class="num">DPMF</th><th>Status</th></tr></thead>
  <tbody>
  {% for m in financial %}
    <tr>
      <td>{{ m.label }}</td>
      <td class="num">{{ m.source }}</td>
      <td class="num">{{ m.dpmf }}</td>
      <td>
        {% if m.match %}<span class="ok">match</span>{% else %}<span class="err">diff</span>{% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<footer>
  Produced by dental-bridge {{ version }} ·
  Archive this file alongside the DPMF as proof of the migration's integrity.
</footer>
</body>
</html>
"""


def _env() -> Environment:
    return Environment(autoescape=select_autoescape(["html"]), keep_trailing_newline=True)


def render_analyze_report(
    inventory: Any,
    *,
    tenant_label: str,
    version: str,
    output_path: Path,
) -> Path:
    template = _env().from_string(_ANALYZE_TEMPLATE)
    html = template.render(
        inventory=inventory,
        tenant_label=tenant_label,
        version=version,
        fingerprint=inventory.fingerprint,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path


def render_verify_report(
    *,
    rows: list[Any],
    financial: list[dict[str, Any]],
    dpmf_path: Path,
    dpmf_size_bytes: int,
    dpmf_integrity_hash: str,
    source_fingerprint: str,
    tenant_label: str,
    version: str,
    output_path: Path,
) -> Path:
    template = _env().from_string(_VERIFY_TEMPLATE)
    discrepancies = [r for r in rows if r.delta != 0]
    html = template.render(
        rows=rows,
        financial=financial,
        discrepancies=discrepancies,
        dpmf_path=str(dpmf_path),
        dpmf_size_bytes=dpmf_size_bytes,
        dpmf_integrity_hash=dpmf_integrity_hash,
        source_fingerprint=source_fingerprint,
        tenant_label=tenant_label,
        version=version,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path
