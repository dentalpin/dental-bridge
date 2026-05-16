# NOTICE

`dental-bridge` — open source migration toolkit for dental practice
management systems.

Copyright 2026 dental-bridge contributors.

Licensed under the Apache License, Version 2.0 (see `LICENSE`).

## Acknowledgements

- Sponsored and initially maintained by [Dentalpin](https://dentalpin.com).
- This project does not sell, license commercially, or otherwise monetise
  the migration toolkit itself. It is published gratis to facilitate
  legitimate interoperability between dental practice management systems
  and to respect dental clinics' right to portability of their own data.

## Interoperability scope

The schema-discovery work that informs the Gesdén origin adapter was
conducted under the right of independently created computer programs to
interoperate, as recognised in:

- **Article 6 of EU Directive 2009/24/EC** of 23 April 2009 on the legal
  protection of computer programs.
- **Article 100.5 of the Spanish Intellectual Property Law** (Real Decreto
  Legislativo 1/1996), the Spanish transposition of that directive.
- **CJEU judgment of 2 May 2012 in C-406/10 SAS Institute v World
  Programming Ltd** ("the SAS judgment"), which clarified that neither the
  functionality of a computer program, nor the programming language in
  which it is expressed, nor the format of its data files constitute a
  form of expression protected by copyright.
- **CJEU judgment of 6 October 2021 in C-13/20 Top System v État belge**,
  confirming the lawful user's right to decompile a program when necessary
  to correct errors, subject to the conditions of Article 5(1) of the
  Directive.

## What this project does NOT contain

To make the interoperability boundary explicit, none of the following
appear anywhere in this repository:

- Source code, binaries, executables, installers or DLLs of Gesdén,
  Infomed or any other third-party PMS.
- Decompiled, disassembled or reconstructed source code of any such
  program.
- Stored procedures, triggers, scalar functions, views or any other
  procedural T-SQL extracted from a Gesdén installation.
- Database files (`*.MDF`, `*.LDF`), backups, exports or data dumps of any
  clinic's Gesdén database. These are excluded by `.gitignore` and have
  never been committed.
- Patient-identifying information, professional-identifying information,
  or any other personal data.
- Screenshots, manuals, training materials, marketing assets, logos,
  icons, fonts or other copyrighted media belonging to Gesdén, Infomed or
  their affiliates.

## What this project DOES contain, and why it is lawful

- Documentation of **factual elements** of the Gesdén database schema
  observed in customer-owned installations: table names, column names,
  data types, foreign-key relationships, value ranges. Under both EU and
  Spanish law (and consistent with the SAS judgment cited above), these
  are facts about a system's interface, not protected expression.
- Independently authored queries against the standard SQL Server catalog
  views (`sys.tables`, `sys.columns`, `sys.foreign_keys`) and against the
  observed Gesdén tables by name, written for the sole purpose of
  achieving interoperability.
- An independently authored canonical data model and migration container
  format ("DPMF") that is destination-agnostic and is published as an
  open specification.

## How the schema work was performed

The schema documentation in `docs/` was produced exclusively by:

1. Operating against database files **owned by the clinic that is the
   data controller** ("responsable del tratamiento") of those data, in
   the course of providing that clinic with assistance migrating off
   Gesdén at the clinic's request.
2. Running standard, read-only SQL introspection queries against the
   database's own system catalog and the clinic's own application tables.
3. Recording the observable shape of those tables and the relationships
   between them.

No Gesdén binary was disassembled, decompiled, decrypted, instrumented or
otherwise reverse-engineered as code. The interoperability work concerns
*data the clinic owns*, not *software Infomed owns*.

## Trademarks

- "Gesdén" is a trademark of Infomed S.A. or its affiliates. Use in this
  repository is **strictly nominative** — necessary to identify the
  third-party software with which `dental-bridge` interoperates. No
  affiliation, sponsorship, endorsement or partnership with Infomed is
  implied.
- "Dentalpin" is a trademark of its owner. Reference implementations and
  default destination configurations targeting Dentalpin are provided as
  examples; the project is otherwise destination-agnostic.

## Scope of liability

This software is provided on an "AS IS" basis under the Apache 2.0
License. The authors and contributors of `dental-bridge` are **not data
processors** ("encargados del tratamiento") within the meaning of the EU
GDPR / Spanish LOPDGDD, because they do not themselves operate the tool
against any clinic's data. Operators who execute this software against
clinical databases are solely responsible for:

- A lawful basis for processing the patient data they extract.
- Data Processing Agreements with any third party they engage to assist
  them.
- Retention obligations under healthcare legislation (e.g. Spanish Law
  41/2002, art. 17 on clinical-record retention).
- Verifying the output prior to relying on it for production use in
  another PMS.

See `TERMS.md` for the operator's terms of use.

## Telemetry and data sent over the network

This project does not collect telemetry. The optional post-extract prompt
that may forward a migration summary to Dentalpin is **off by default**
and requires explicit user confirmation including a preview of the exact
JSON payload to be sent.

## Reporting security issues

Email security@dentalpin.com or open a private security advisory on
GitHub. A formal `SECURITY.md` will be added in v0.1.

## Reporting good-faith concerns from rights holders

If you represent a rights holder (in particular Infomed S.A.) and have a
good-faith concern that any element of this repository goes beyond the
interoperability scope described above, please contact
legal@dentalpin.com. We will respond promptly and, where the concern is
well-founded, remove the offending material.
