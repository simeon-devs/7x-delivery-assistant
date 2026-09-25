# 7X — conversational delivery assistant

Take-home for the 7X AI Lab Forward Deployed Engineer assignment.

A customer assistant that **reschedules a delivery** and **changes a delivery address** against
real records, with guardrails computed from the shipment file rather than written into a prompt,
and a staff console where every action it took or refused is visible in plain English.

> **Code decides whether an action is allowed. The model only decides what to say about it.**

---

## The four segments

The work splits into four parts. Each one produced its own artefact, and each can be read on its
own.

### 1 · Market scan — `research/`

Desk research plus **primary research**: 718 public app-store reviews collected from Google Play
and Apple's public RSS feed, of which **454 negative ones were labelled by hand-written rules**
and hand-checked at ~82% agreement.

| File | What is in it |
|---|---|
| `01-operators.md` | What carriers actually ship. Japan Post is the only one worldwide with a published AI that takes a delivery action. Plus the ceiling: UPS, FedEx and Evri all restrict diversion, and an assistant inherits every lock |
| `02-vendors-notes.md` | Ada, PolyAI, Maven AGI, Crescendo. Per-action approval flags, published unit pricing, contract medians |
| `03-what-fails.md` | DPD, *Moffatt v Air Canada*, OLG Hamm, Klarna's reversal, ForcedLeak (CVSS 9.4) |
| `04-landscape-and-pricing.md` | Cognigy/DHL, first-party carrier extensions, τ-bench, inference as 5–10% of the platform bill |
| `05-whatsapp-mea-arabic.md` | WhatsApp service messages stop being free 1 Oct 2026. UAE rates. Gulf Arabic is the weakest region for every frontier model |
| `06-failed-delivery-economics.md` | Why the widely-quoted $17.78 per failed delivery is vendor marketing, and what to use instead |
| `07-review-findings.md` | **The primary research.** 22% of complaints are that the customer could not reach a human. 6.6% describe a delivery attempt that never happened |

### 2 · Data — `analysis/`, `DECISIONS.md`

The shipment file cleaned and reconciled before a line of the assistant was written.

```
866 rows in  =  8 quarantined test records + 18 superseded duplicates + 840 clean
```

`DECISIONS.md` records **D-01 to D-09**: what was decided, why, **what was rejected**, and what it
risks. Mapped to the DAMA UK data-quality dimensions, except D-07, which is labelled a policy call
rather than borrowing that authority.

The headline finding is the project's scope:

| | |
|---|---|
| Real shipments | **840** |
| Still open | **349** |
| Can be rescheduled | **262** |
| Can have the address changed | **201** |
| Open but needing a human | **87** |
| Open with no phone on file, so unverifiable | **46** (13.2%) |

### 3 · Prototype — `app/`

| File | Role |
|---|---|
| `db.py` | SQLite loaded from the cleaned file. One clock. `reset()` as a first-class function |
| `gates.py` | **Every rule, one place**, computed live from the record rather than read from a stored boolean |
| `actions.py` | **The one door** plus the five tools. Nothing reaches the database any other way |
| `agent.py` | A plain tool-use loop on the Anthropic SDK. No framework |
| `convo.py` | What happens to a conversation outside the model: opening it, verifying, a person replying, handing back |
| `cast.py` | The cast. Eight seeded conversations and six picker rows, pinned by tracking number. Names and addresses stay in the data file |
| `demo.py` | Records the eight conversations once, replays them at every reset, checks the result |
| `prompts/customer_assistant.md` | The system prompt. **Contains no shipment data at all** |
| `main.py` | FastAPI serving the API and both surfaces. One deploy, one URL |
| `auth.py` | One password over every route, or none at all when `SEVENX_PASSWORD` is unset |
| `static/` | The landing page, the customer chat, the operations console, the shared theme |
| `test_engine.py` | Engine checks. No API key needed |
| `chat_cli.py` | The same eight scenarios in the terminal, with measured token cost |

`DESIGN.md` records **A-01 to A-27**, the system decisions, in the same format.

### 4 · Deliverables

Built from the three segments above rather than written separately.

| Deliverable | Where |
|---|---|
| Working demo link | `https://sevenx-delivery-assistant-sov5.onrender.com` — password-gated (A-27) |
| Market scan, 2–3 pages | **`docs/7X-market-scan.pdf`** — source `docs/market-scan.html` |
| Summary deck, max 5 slides | **`docs/7X-deck.pdf`**, five slides, source `docs/deck.html`, kept out of git (see below) |

The market scan condenses the 23,000 words in `research/` to three pages. Re-render it with
`python docs/render-pdf.py market-scan.html 7X-market-scan.pdf --max-pages 3`; the script fails if
the document grows past the brief's page limit, so the cap is enforced rather than eyeballed.

The deck is rendered the same way, with `--slides`:
`python docs/render-pdf.py deck.html 7X-deck.pdf --max-pages 5 --slides`. Its demo slide uses
screenshots of the live product, taken by `docs/shoot-deck.py` with names and addresses masked by
the landing page's rule; the script checks the page text afterwards and fails if anything survived.
Masked or not, those screenshots are pictures of the client's records, so they and the deck PDF
stay local.

---

## Running it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # then add ANTHROPIC_API_KEY, and SEVENX_PASSWORD to lock it

.venv/bin/python -m analysis.clean_shipments   # 866 in → 840 clean, reconciled
.venv/bin/python -m app.test_engine            # engine checks, no API key needed
.venv/bin/python -m app.demo record --all      # once: the eight seeded conversations
./run.sh                                       # http://127.0.0.1:8077, seeded on first start
```

`app.test_engine` proves the permissions computed live from the database agree **exactly** with
the ones the cleaning layer produced, that an allowed action really changes a row, and that a
blocked one really refuses, raises a case, and leaves the record untouched.

`app.chat_cli --list` shows the scripted scenarios. They are the eight in `cast.py` -- the same
eight the console opens with -- so the terminal and the browser cannot tell different stories
about the same parcel. With no `--scenario` it offers the six picker rows and you type the
conversation yourself. Either way it prints the row before and after, every tool call, and the
measured token cost.

---

## What makes it agentic rather than a chatbot

**The test is not what it says. It is whether a row is different afterwards** — which is how
τ-bench scores agents, on final database state rather than on the transcript.

Three decisions enforce it:

1. **No shipment data reaches the system prompt.** The assistant cannot answer from context, so
   it has to call a tool to learn anything at all.
2. **It is never shown the rules.** Nothing it sees says whether an action is permitted. It finds
   out by attempting, and the gate answers. It cannot reason around a rule it was never given.
3. **One door.** Every write passes through a single function that re-reads the record at the
   moment of the write, checks the gate, writes, and logs either way.

---

## What is deliberately NOT in this repository

The client's brief, the client's shipment file, and everything under `data/`.

`data/` holds customer names, phone numbers and addresses derived from the client's file, plus
scraped public reviews. None of it is committed. Every file in it is reproduced by the scripts in
`analysis/`, so **the code is the artefact, not the data**. The seed recordings are in
`data/seed.json` for the same reason: `app.demo record --all` reproduces them.
