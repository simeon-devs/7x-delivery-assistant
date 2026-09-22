# Decisions log

Every judgement call, why it was made, what was rejected, and what it risks.
Written as the work happened, not reconstructed afterwards.

**Framework.** Data-quality decisions are mapped to the six data quality dimensions —
Completeness, Uniqueness, Timeliness, Validity, Accuracy, Consistency — published by the
**DAMA UK Working Group (October 2013)** and formalised in **ISO/IEC 25012**. Where a decision is
*not* a data-quality decision, it says so explicitly rather than borrowing the authority.

---

## D-01: Test records are quarantined, not deleted
**Dimension:** Validity
**Decided:** 8 rows (6 with `status = TEST`, plus rows whose notes read `test record`) are written
to `shipments_quarantine.csv` with a reason, not dropped.
**Because:** deleting rows makes the output impossible to reconcile against the input. A reader
cannot tell the difference between "removed on purpose" and "lost by accident".
**Rejected:** silent deletion (unauditable); leaving them in (they are not real shipments and
would pollute every rate calculation).
**Risk:** none material.

## D-02: 22 written statuses collapse to 6 real states
**Dimension:** Consistency
**Decided:** normalise case, underscores and hyphens, then map to `delivered`, `failed`,
`in_transit`, `out_for_delivery`, `returned`, `redelivery_scheduled`.
`Delivered` / `DELIVERED` / `delivered` / `delivered_ok` / `Delivered ` (trailing space) are one
state. `Failed Delivery` / `FAILED_DELIVERY` / `Failed` / `Undelivered` /
`failed - customer not available` are one state.
**Because:** 22 spellings of 6 things is a presentation artefact of an operational system, not 22
business states. Any rate computed on the raw column is wrong.
**Rejected:** treating `Undelivered` as distinct from `Failed Delivery` — nothing in the data
supports a difference, and inventing one would be a guess dressed as precision.
**Risk:** if the operator genuinely distinguishes `Undelivered` from `Failed Delivery` internally,
this merge hides it. Worth one question to the client on a real engagement.

## D-03: One row per tracking number, by recency, but refuse to act on conflicts
**Dimension:** Uniqueness
**Decided:** 18 tracking numbers appear twice. The row with the most recent credible event
(`last_attempt_date`, falling back to `shipment_date`) survives; the other is written to
quarantine as `superseded_duplicate`. **Additionally: where the duplicate rows disagree about a
terminal state — one says Delivered or Returned and the other does not — the shipment is marked
`requires_human` and the assistant is forbidden from acting on it.** That is 12 of the 18.
**Because:** two rules, two sources.
1. *Recency* is a standard master-data survivorship strategy for building a golden record from
   conflicting duplicates. The operational system's most recent event is the closest available
   proxy for what the operation last knew.
2. *Refusing to act* follows the **fail-safe defaults** principle from Saltzer and Schroeder,
   *The Protection of Information in Computer Systems* (1975): base decisions on permission
   rather than exclusion, and deny when the state is unknown.
The split matters. You may tell a customer where their parcel probably is. You must not
reschedule a parcel that might already have been delivered.
**Rejected:** merging both rows into one (invents a state that never existed in the system);
showing the customer both (pushes the operator's data problem onto the customer); picking the
most advanced status (would systematically favour `Delivered`, the single most dangerous wrong
answer).
**Risk:** `last_attempt_date` is itself unreliable on 25 rows (see D-05), so "most recent" is not
always genuinely most recent. Those rows carry `data_confidence = suspect`.

## D-04: Date formats are inferred from the data, not assumed
**Dimension:** Validity
**Decided:** five formats plus Excel serial numbers are parsed explicitly:
`YYYY-MM-DD` (1519 values) · `DD/MM/YYYY` (28) · `MM-DD-YY` (26) · `DD.MM.YYYY` (19) ·
`DD Mon YYYY` (18) · five-digit **Excel serials** such as `46175` (16), converted from the 1900
epoch. The original string is kept alongside every parsed date.
**Because:** the formats were determined by evidence, not preference. `DD/MM/YYYY` and
`DD.MM.YYYY` are day-first because values reach 30 and 29 in the first position. `MM-DD-YY` is
month-first because values reach 19 and 31 in the *second* position.
**This file mixes day-first and month-first in the same column.** Only 26 values disambiguate it.
Parsing with a single `dayfirst` setting silently corrupts one group or the other.
**Rejected:** `pd.to_datetime(..., errors="coerce")` with default inference — it would produce
plausible wrong dates rather than failures, which is the worst outcome.
**Risk:** values where neither position exceeds 12 are genuinely ambiguous and were assigned by
their format family. If the source system's locale differs, some dates are wrong by up to 11
months.

## D-05: Impossible dates are flagged, and the attempt data is distrusted
**Dimension:** Accuracy
**Decided:** where `last_attempt_date` precedes `shipment_date`, or either date is in the future,
the shipment is flagged and marked `data_confidence = suspect`.
**Because:** a delivery cannot be attempted before it ships. The row is internally impossible, so
at least one of its two dates is wrong and there is no way to tell which.
**Rejected:** correcting the dates by swapping them (invents data); dropping the rows (they are
real shipments with real customers).
**Risk:** suspect rows are still served to customers for information. They are not blocked from
action. That is a deliberate trade — blocking them would deny service on rows whose only defect
may be a typo in a field the action does not depend on.

## D-06: Where attempts contradict status, the assistant stays silent about attempts
**Dimension:** Consistency
**Decided:** flag `attempts_unreliable` where a status claiming an attempt (`delivered`,
`failed`, `redelivery_scheduled`) has `delivery_attempts = 0`, or where the attempt count and the
attempt date disagree about whether anything happened. **The assistant never states that a
delivery was attempted when the attempt count is zero.**
**Because:** when two fields in the same record contradict each other, the correct treatment is
not to pick a winner. Neither field is trustworthy until reconciled, so the record is marked
low-confidence and excluded from any assertion that depends on it.
This is reinforced by two independent findings:
1. **Customer evidence.** 6.6% of 454 negative UAE delivery-app reviews describe an attempt the
   customer says never happened: *"No attempts made and they update customer was not available"*;
   *"they simply faked the delivery attempt"*. See `research/07-review-findings.md`.
2. **Liability.** In *Moffatt v Air Canada* (2024 BCCRT 149) the tribunal held the operator
   responsible for what its chatbot told a customer, rejecting the argument that the bot was a
   separate entity.
An assistant that reads out "Failed — customer not available" on these rows would be telling a
measurable number of people something they know to be false.
**Rejected:** trusting `status` over `delivery_attempts` (that is the field customers dispute);
trusting `delivery_attempts` over `status` (no basis for it either).
**Risk:** the assistant is less informative on these rows. That is the intended trade.

## D-07: Cash-on-delivery blocks an address change — and this is a POLICY call, not a data rule
**Dimension:** none. This is a business risk decision and is labelled as such.
**Decided:** any shipment with `cod_amount_aed > 0` cannot have its address changed by the
assistant. It routes to a human. The COD column itself is parsed from three storage types —
`int` (665), `float` (171), and strings such as `"AED 745.72"` (30) — which *is* a Validity fix.
**Because:** there is no data-cleaning standard that says block COD address changes, and dressing
a risk decision up as a data standard would be dishonest. The justification is industry practice
on irreversible financial actions:
- **OWASP LLM01:2025** states plainly that there is no fool-proof defence against prompt
  injection, and falls back on least privilege and **human approval for high-risk actions**.
- **Maven AGI** ships a per-action flag named `userInteractionRequired`.
- **Forethought's own documentation** advises keeping "business-critical Actions such as refunds,
  cancellations" on the deterministic path rather than the agentic one.
**Rejected:** a value threshold (unjustifiable without the operator's own risk appetite);
allowing it with a confirmation step (a confirmation is not an authorisation).
**Risk:** blocks a legitimate action on some shipments. Acceptable for an MVP, and it is a cut
that can be argued rather than a gap that cannot.

## D-08: Phone numbers become text, and a missing number blocks action
**Dimension:** Completeness
**Decided:** the column is stored as `float64`, which is wrong for a phone number; it is cast to
E.164 text. **71 shipments have no phone number at all, and those cannot be authenticated, so the
assistant will not act on them.**
**Because:** a float loses leading zeros and risks precision artefacts on long numbers. And if
identity is verified against a phone number, a shipment without one cannot be verified. That is
8% of the file.
**Rejected:** authenticating on tracking number alone (a tracking number is printed on the parcel
and visible to anyone who handles it — it is an identifier, not a secret).
**Risk:** 8% of customers cannot self-serve. This is a real service gap and belongs on the slide,
not hidden. It is also an argument for a second verification factor in a later phase.

## D-09: Missing address is flagged but does not block an address change
**Dimension:** Completeness
**Decided:** 5 shipments have no delivery address. They are flagged, but this does not block the
change-address action.
**Because:** for a shipment with no address on file, supplying an address is the remedy, not a
risk. Blocking it would deny the one action that fixes the problem.
**Risk:** low. Volume is 5.

---

## Reconciliation

866 input rows = 8 quarantined (test records) + 18 superseded duplicates + **840 clean**.
Verified on every run; the run fails loudly if it does not balance.

Of the 840: **349 are open**, 262 can be rescheduled, 201 can have an address changed, and 87 of
the open shipments require a human (46 no phone, 42 at the attempt limit, 9 duplicate conflicts).
28 carry `data_confidence = suspect`.
