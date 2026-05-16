# Reverse-engineering provenance record (template)

> This template documents the chain of custody and authorisation under
> which schema-discovery work was performed. **The filled-in instance
> (`legal/PROVENANCE.md`) must NEVER be committed to the public
> repository.** It is for internal record-keeping only, to be produced
> on request in the event of a legal inquiry.

Copy this file to `legal/PROVENANCE.md` and complete the sections below
for each clinic whose database was inspected.

---

## Record #__

### Clinic / data controller

- **Legal name:**
- **NIF / VAT:**
- **Registered address:**
- **Contact person:**
- **Contact email / phone:**

### Authorisation

- **Document type:** (engagement letter / service agreement / DPA / other)
- **Document date:**
- **Document reference / file location (off-repo):**
- **Scope of authorisation:** (e.g. "migrate clinical data from Gesdén
  installation at <address> to Dentalpin SaaS, with read access to the
  Gesdén SQL Server database during the period <dates>")
- **Authorised individuals:** (names of operator-side staff covered by
  the authorisation)

### Data Processing Agreement

- [ ] DPA executed between clinic (controller) and operator (processor)
- [ ] DPA executed between operator and any sub-processors
- **DPA reference / file location (off-repo):**
- **Effective date:**
- **Sub-processors disclosed in DPA:**

### What was inspected

- **Gesdén version / build:**
- **SQL Server version:**
- **Database file name:**
- **Inspection window (dates):**
- **Tools used:** (e.g. SQL Server Management Studio, DBeaver,
  `sql/exploration/*.sql` from this repository)
- **What was NOT inspected:** (confirm: no Gesdén binary disassembled,
  no Gesdén DLL decompiled, no Gesdén stored procedures source extracted
  unless they were already exposed via `sys.sql_modules` and are
  procedural code authored by Infomed — in which case, document and
  exclude from any derivative work)

### Outputs produced

- **Schema documentation lines committed to repo:** (link to commits)
- **Migration plan (if any):** (off-repo reference)
- **DPMF file produced (if any):** (off-repo reference, hash)

### Retention

- **Authorisation documents retained until:** (date)
- **Where retained:** (off-repo storage location)
- **Retention rationale:**

### Sign-off

- **Operator representative:** (name, role, signature/initials)
- **Date:**

---

## Notes for future records

- Add a new "Record #N" block per clinic / engagement.
- Keep the filled-in file (`legal/PROVENANCE.md`) in encrypted storage
  with restricted access, not on shared drives or in the public repo.
- The fact that this template exists in the public repo is itself a
  signal of due diligence; the filled-in records demonstrate the chain
  of custody if ever asked.
