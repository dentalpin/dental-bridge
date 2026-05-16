# Interoperability scope

This document complements `NOTICE.md` by stating, in operational
language, what `dental-bridge` does and does not do with respect to
third-party software.

## What `dental-bridge` is

A migration toolkit that connects to a dental practice's own database,
reads tables the practice owns, and emits a normalised file in an open
format (DPMF) that any downstream PMS can import.

The toolkit is:

- Independently authored. No code in this repository was copied,
  decompiled, or derived from any third-party PMS executable, library
  or installer.
- Free of charge. There is no paid edition, no commercial licence,
  no support contract that conditions the right to use the tool.
- Destination-agnostic. The DPMF file is the only output. Importers
  for that file may be written by anyone. A reference importer for
  Dentalpin will be published in a separate repository.

## What the schema-discovery work covers

The Gesdén origin adapter relies on documentation of factual elements of
the Gesdén database: table names, column names, types, foreign keys,
value semantics. That documentation was produced by:

- Running standard SQL Server catalog queries (`sys.tables`,
  `sys.columns`, `sys.foreign_keys`, `sys.indexes`) against databases
  the clinic owns.
- Querying the clinic's own application tables by name to observe
  value distributions.
- Visually comparing observed values to behaviour in the Gesdén UI to
  infer the semantics of opaque encodings (e.g. integer-encoded dates,
  bit-mask columns).

This is interoperability work in the sense of:

- Article 6 of EU Directive 2009/24/EC.
- Article 100.5 of the Spanish Intellectual Property Law.
- CJEU C-406/10 (SAS v WPL): functionality, programming language and
  file format are not protected expression.
- CJEU C-13/20 (Top System v État belge): lawful users have a right to
  decompile for error correction within Article 5(1) limits — a right
  this project does NOT need to invoke, since no decompilation has
  taken place.

## What the schema-discovery work does NOT cover

Explicitly excluded:

- Reading or copying any source-code-equivalent artefact from a Gesdén
  installation: stored procedures, scalar/inline functions, views,
  triggers, CLR assemblies, SSIS packages or any other object whose
  body constitutes Infomed-authored T-SQL or other code.
- Disassembling, decompiling, decrypting, instrumenting or
  patching any Gesdén executable, DLL, installer or distribution
  artefact.
- Copying any user-facing or documentation asset from Gesdén:
  screenshots, manuals, help files, marketing copy.
- Extracting personal data from any clinic database for any purpose
  other than the migration that clinic itself requested.

## What the operator commits to

When an operator runs `dental-bridge` against a clinic's database,
they accept the terms in `TERMS.md`. In particular, they confirm that
they have authorisation from the clinic to perform the migration, that
they are not using the tool to circumvent or interfere with Gesdén's
own executable, and that they accept responsibility for compliance with
data-protection law over the data they extract.

## Good-faith handling of concerns

If a rights holder identifies content in this repository that they
believe exceeds the interoperability scope described above, contact
legal@dentalpin.com. The maintainers commit to responding promptly,
investigating in good faith, and removing or rephrasing material that
is not necessary for interoperability.
