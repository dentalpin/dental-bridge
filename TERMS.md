# Terms of use — `dental-bridge`

> By downloading, installing, building from source or executing
> `dental-bridge`, you agree to the following terms in addition to the
> Apache 2.0 License under which the code is distributed.

These terms exist to make explicit who is responsible for what when this
toolkit is used against a real clinical database. They do not replace
the Apache 2.0 License — they sit alongside it, in plain language, so the
operator knows what they are committing to.

## 1. Who is "the operator"

"The operator" is the natural or legal person who executes
`dental-bridge` against a database. The operator may be the clinic
itself, an IT integrator hired by the clinic, or any other authorised
party. The authors and contributors of `dental-bridge` are **not** the
operator merely by virtue of having written the code.

## 2. Authorisation over source data

By executing `dental-bridge` against a database, the operator represents
and warrants that:

a. The clinic that owns the data has authorised the migration, either
   directly (the operator is the clinic) or through a contractual
   relationship that grants the operator the right to access the data
   for the purpose of migrating it.

b. The database file or live database the operator points the tool at
   was lawfully obtained, contains data the clinic is entitled to
   process, and is being inspected only to enable the migration the
   clinic has asked for.

c. The operator complies with all applicable data-protection legislation
   — including but not limited to the EU General Data Protection
   Regulation (GDPR), the Spanish Organic Law 3/2018 (LOPDGDD), and the
   Spanish Law 41/2002 on patient autonomy and clinical-record
   retention — in respect of the patient data extracted.

d. If the operator is not the clinic itself, the operator has a Data
   Processing Agreement ("contrato de encargado del tratamiento")
   in place with the clinic that covers the migration work.

## 3. Lawful interoperability

The operator acknowledges and agrees that `dental-bridge`:

a. Is published as a free, open-source tool to enable lawful
   interoperability between dental practice management systems.

b. Is not sold, sublicensed for fee, or otherwise commercialised by
   its authors. The authors do not receive payment from operators
   for using the tool.

c. Is used by the operator solely to extract data the clinic owns,
   transform it into the open DPMF format, and import it into another
   PMS of the clinic's choice.

The operator agrees not to use `dental-bridge` to:

- Circumvent technological measures protecting Gesdén software itself
  (as distinct from the data the clinic owns).
- Reproduce, redistribute, reverse-engineer or otherwise interfere
  with Gesdén's executable code.
- Extract data from a database the operator is not authorised to
  access.

## 4. No warranty, no liability

The Apache 2.0 License under which `dental-bridge` is distributed
already provides that the software is offered "AS IS" without warranty
of any kind, and that the authors are not liable for damages arising
from its use. These terms restate that disclaimer in operator-facing
language:

- The authors do not guarantee that `dental-bridge` will correctly
  migrate every record in every database. The operator is expected to
  run the `analyze` and `verify` modes, and to inspect the output,
  before relying on the migration in production.

- The authors are not liable for any data loss, data corruption,
  regulatory penalty, contractual penalty, business interruption or
  other damage suffered by the operator or by the clinic as a result
  of using `dental-bridge`. The operator assumes all such risk.

- The operator is responsible for retaining the original source
  database intact until the migration has been verified end-to-end in
  the destination PMS.

## 5. No professional advice

Nothing in this repository — including the schema documentation, the
migration order, the odontograma decoding notes and these terms —
constitutes legal advice, regulatory advice, medical advice or
accounting advice. Where the operator needs such advice, they must
obtain it from a qualified professional in the relevant jurisdiction.

## 6. Trademarks

The operator may not use the names "Gesdén", "Infomed", "Dentalpin" or
any related trademark to suggest a partnership, sponsorship or
endorsement that does not exist. Nominative reference to these
trademarks — i.e. to identify the systems involved in a migration — is
permitted and is in fact necessary for the tool to be usable.

## 7. Changes to these terms

Future versions of `dental-bridge` may amend these terms. The version of
these terms that applies to a given build of `dental-bridge` is the
version shipped in that build's source tree.

## 8. Governing law and venue

These terms are governed by the laws of Spain. Any dispute arising out
of or in connection with these terms shall be submitted to the
competent courts of Madrid, Spain, without prejudice to mandatory
consumer-protection rules that may grant the operator additional rights
in the jurisdiction of their habitual residence.
