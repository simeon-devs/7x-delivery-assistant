# 7X — conversational delivery assistant

Take-home work for the 7X AI Lab Forward Deployed Engineer assignment.

A customer assistant that can **reschedule a delivery** and **change a delivery address** against
real records, with the guardrails computed from the data rather than written into a prompt, and a
staff console where every action it took or refused is visible in plain English.

---

## What is in here

```
research/     market scan, and primary research on 718 public app reviews
analysis/     the cleaning layer, and the review collection and labelling scripts
app/          the assistant: database, gates, tools, prompt
DECISIONS.md  every data decision: what, why, what was rejected, what it risks
DESIGN.md     every system decision, same format
```

## What is deliberately NOT in here

The client's brief and shipment file, and everything under `data/`.

`data/` holds customer names, phone numbers and addresses derived from the client's file, plus
scraped public reviews. None of it is committed. Every file in it is reproduced by the scripts in
`analysis/`, so **the code is the artefact, not the data**.

---

## The idea in one line

> Code decides whether an action is allowed. The model only decides what to say about it.

The permissions are columns computed from the shipment file before any conversation exists, and
the tool re-checks them at the moment it writes. A prompt injection can change what the assistant
says. It cannot change a boolean in a database.

The assistant also starts every conversation knowing **nothing** about any parcel. No shipment
data goes into the system prompt, so there is no way for it to answer from context. It has to act
to know anything, which is what makes it agentic rather than a chatbot with a table pasted in.

---

## Running it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # then add your ANTHROPIC_API_KEY

.venv/bin/python -m analysis.clean_shipments   # 866 rows in → 840 clean, reconciled
.venv/bin/python -m app.test_engine            # engine checks, no API key needed
```

`app.test_engine` proves the permissions computed live from the database agree exactly with the
ones the cleaning layer produced (349 open, 262 reschedulable, 201 address-changeable, 87 needing
a human), that an allowed action really changes a row, and that a blocked one really refuses,
raises a case, and leaves the record untouched.

---

## The numbers this is built on

| | |
|---|---|
| Rows in the client file | 866 |
| Real shipments after cleaning | 840 |
| Still open | 349 |
| Can be rescheduled | 262 |
| Can have the address changed | 201 |
| Open but needing a human | 87 |
| Open with no phone on file, so unverifiable | 46 (13.2%) |

866 = 8 quarantined test records + 18 superseded duplicates + 840 clean. Checked on every run.
