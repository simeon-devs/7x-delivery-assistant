# System design decisions

Companion to `DECISIONS.md`. That file covers the **data**: what was cleaned, why, and what
was rejected. This file covers the **system**: what gets built, what does not, and why.

Same format. Decided / Because / Rejected / Risk.

Written as the decisions were made, before the build started.

---

## Part 1 — Scope

### A-01: Two surfaces. A customer chat and an operations console
**Decided:** a customer chat, plus a staff console with three tabs (queue, trace log, data
readiness). Not a single chat widget, and not an analytics dashboard.

**Because:** two reasons, and the second is stronger than the first.
1. **The escalation needs a destination.** 100 of 454 negative reviews (22%) are customers saying
   they could not reach a human or the bot was useless. An assistant that says "I'm passing you to
   our team" into an empty room *is* that complaint, rebuilt.
2. **A decision maker who cannot see inside a system cannot approve it.** This is the real blocker
   in enterprise AI procurement, and the market scan shows it twice: **Klarna** announced the work
   of 700 agents automated, then the 20-F (26 Feb 2026) showed customer service costs rose **+2%
   in 2025** anyway — nobody could see what was actually happening until the accounts arrived.
   **ForcedLeak** (Salesforce Agentforce, CVSS 9.4) was an agent executing instructions typed into
   a web form; only a log a human reads catches that on day one.

**Rejected:** chat only (leaves the escalation fake, and leaves the buyer blind); an analytics
dashboard with charts, CSAT and deflection rate (see A-02).

**Risk:** two surfaces is more to build than one. Mitigated by keeping the console to three
read-only screens plus one reply box.

### A-02: The console shows what happened. It never shows what I hope will happen
**Decided:** every number on the console is something the system actually did. No satisfaction
score, no deflection rate, no cost-saved counter, no time-series charts.

**Because:** the projections belong on the value slide, labelled as assumptions, where they can be
argued. On a screen that looks like it is *measuring* something, an estimate is a fabrication.
The review research explicitly states it does not support a CSAT claim or a containment claim —
putting either on a live dashboard would contradict my own methods section.

**Rejected:** charts over time (a static file has no real time dimension); a deflection gauge
(nothing in the data measures it).

**Risk:** the console looks plainer than a BI tool. That is the intended trade.

### A-03: Escalation is a record, not a message
**Decided:** escalating creates a case with an ID, a status, a timestamp, the session, the
shipment, the customer's request, and the reason the assistant stopped. It is not a chat message
saying "escalated".

**Because:** if escalation is only a message, there is no queue, nothing to assign, nothing to
resolve, and no way to count how often it happens.

**Risk:** none.

### A-04: Human takeover, with a toggle, defaulting to OFF
**Decided:** a staff member can reply directly into the customer's conversation. When a case is
escalated, the assistant goes **silent in that thread by default**. A switch in the case panel
turns it back on. The switch is manual only — no timeout ever re-enables the assistant.
The customer sees a line both ways: *"Ali from 7X joined this conversation"* /
*"Ali handed this back to the assistant"*.

**Because:** three things.
1. **One voice per conversation.** If both reply, the customer cannot tell who is real.
2. **Default off is the same fail-safe rule as D-03.** When the situation is unclear, do nothing
   until a person decides. Saltzer & Schroeder (1975): base decisions on permission, not exclusion.
3. **A control is what the operations buyer is actually purchasing.** They are not buying an AI,
   they are buying an AI they can switch off. A one-way door would also waste the human: after
   they resolve a COD problem, "when will it arrive?" is a question the assistant handles fine.

**Rejected:** permanent handover (kills automation for the rest of the conversation, wastes the
agent); automatic resume after N minutes of silence (a person switched it off for a reason).

**Risk:** low. The state is one flag on the session.

### A-05: No login. Two URLs
**Decided:** `/chat` and `/ops`, no passwords, no accounts, no roles.

**Because:** authentication is solved and it is not what the brief asks to see. It is a day of
work worth zero marks that adds a component which can fail on the day.

**Rejected:** a login screen for realism (realism theatre).

**Risk:** none for assessment. **The line to say:** "In production this sits behind your existing
staff SSO. I spent that time on the guardrails instead."

**Note:** this is *staff* login. **Customer identity is a different thing and is not cut** — see
A-06.

---

## Part 2 — Identity and permission

### A-06: Identity is a one-time code sent to the phone number ALREADY ON THE RECORD
**Decided:** the customer enters a tracking number. The system looks up the record, shows the
masked phone number from that record, and sends a code **to that stored number** — never to a
number the customer types. Entering the code verifies the session.

**Because:** a tracking number is **printed on the parcel**. So is the recipient name, and so is
the address. Anyone who handles the box, or photographs the label, has all three. So a
knowledge-based check ("give us your tracking number and last name", the airline model) proves
nothing — it is a question, not a check. Knowledge-based verification has been deprecated in
identity guidance for years for exactly this reason.

Sending the code to the number *on the record* is what makes it real: a person holding the parcel
can read the masked number but cannot receive the message.

**Rejected:** tracking number + name (both on the label); tracking number + a phone the customer
types (proves only that they own a phone); no verification at all (see A-07).

**Risk:** the demo cannot send a real SMS. Handled by a visible `DEMO MODE · SMS not sent · code
is NNNN` strip — labelled, not hidden. Shown once, at the start of one conversation.

**The pitch this unlocks:** *"On the website we send a code, because the web proves nothing about
who you are. On WhatsApp that step disappears — the channel has already verified the number, so
the customer starts with the assistant already knowing which parcels are theirs. Same system. The
channel decides how much friction the customer sees."* 7X's only 24/7 channel is WhatsApp.

### A-07: Information is open. Action requires verification
**Decided:** three levels.

| Level | Can do | Requires |
|---|---|---|
| **Track** | See status and location | The tracking number |
| **Verified** | Reschedule, change address | A code sent to the number on record |
| **Human** | COD, contradictory records, attempt limit reached | A person decides |

**Because:** status is **already public**. UPS, FedEx and DHL all show tracking status to anyone
with the number, no login. Requiring verification to answer "where is my parcel" would add
friction that protects nothing. Changing the parcel is a different category.

This also serves the **71 shipments with no phone on file** (D-08): they cannot verify, so they
cannot act, but they can still see where their parcel is. A limited answer beats a dead end.

**Rejected:** verifying before showing status (friction with no security gain); allowing action
after tracking-number-only (the number is on the box).

**Risk:** someone who finds a parcel can see its status. Same exposure as every carrier's existing
public tracking page. **Not a new hole.**

### A-08: Third-level gates are inherited from the data, not invented here
**Decided:** `requires_human` comes straight from the cleaning layer. COD (D-07), attempt limit
reached, duplicate rows that disagree about a terminal state (D-03), no phone on file (D-08).

**Because:** the guardrails were computed from the file before any conversation existed. They are
columns, not instructions.

**Known gap to state out loud:** the review research found 20 reviews (4.4%) about bank cards,
Emirates ID and visa documents — signature-required, high-stakes items where a matching phone
should still not be enough. **The dataset carries no declared-value or signature-required field**,
so COD is used as the closest available proxy. In production those two fields join the same gate.

### A-23: Two channels in the demo — web and WhatsApp — sharing one agent
**Decided:** the customer surface runs in two modes, chosen when a session is created.

| | **Web** | **WhatsApp** |
|---|---|---|
| Start | Cold. Knows nothing | Warm. The number arrives with the message |
| Steps to a useful answer | **4** — tracking number → masked phone → code → verified | **0** |
| Identity from | A code sent to the number on the record | The SIM, verified by the channel at registration |
| Payoff after verifying | Sees every parcel on that phone, not just the one typed | Same, immediately |
| Skin | 7X tracking page header, web chat panel | Phone frame, WhatsApp styling |

**Because:**
1. **It turns the WhatsApp argument from a sentence into a demonstration.** 7X's only 24/7 channel
   is WhatsApp. Showing what that channel removes is worth more than describing it.
2. **It proves the agent does not live in the channel.** Same agent, tools, gates and database
   behind two front doors. That is a channel adapter, not two products, and an FDE audience reads
   that instantly.
3. **It connects the prototype to the value case.** WhatsApp service messages stop being free on
   **1 Oct 2026**; UAE utility and service messages run **~$0.0157**. The demo can state what a
   conversation costs on that channel, with a source.

**The rule that keeps it one system:**
> The channel decides how you get in and what it looks like. It **never** decides what the agent
> can do.

Both doors produce the same artefact: **a verified phone number**. After that the agent cannot
tell which door was used, and the gates are byte-identical. If gates ever differed by channel,
that would be a security hole.

**Honesty label, stated before anyone asks:** *"This is not connected to the WhatsApp Business
API. It is the same agent behind a WhatsApp-shaped door, so you can see what the integration
looks like and what it removes."* The brief permits mocked backends; a mocked channel sits inside
that permission. Presenting it as live would not.

**The claim to make, and the one to avoid:** say *"four steps on the web, zero on WhatsApp"* —
a count of this build, not an estimate. Do **not** claim a drop-off or conversion improvement;
there is no data for it.

**Rejected:** a third channel (width); one channel only (loses the strongest commercial argument);
separate chat implementations per channel (two codebases and divergent gates).

**Risk:** low. Cost is one `channel` field on the session, two extra entry screens on the web path,
and a skin. A channel icon appears in the session sidebar and on each case in the console.

---

## Part 3 — Architecture

### A-09: No agent framework. Anthropic SDK, tool use, a manual loop
**Decided:** roughly 120 lines. No LangChain, no LangGraph, no CrewAI, no multi-agent.

**Because:**
- **The flow is not a graph.** Identify shipment → check gate → act or refuse. That is a function.
  A graph library for a function is a dependency that cannot be justified when asked "why did you
  need this?", and MVP scope discipline is 25% of the score.
- **Under challenge, I need to open one file and point at one line.** Any abstraction layer sits
  between me and the thing I am claiming is safe.
- **The market scan argues for it.** Forethought's own documentation tells its customers to keep
  business-critical actions (refunds, cancellations) on the deterministic path. τ-bench
  (arXiv 2406.12045) measures function-calling agents succeeding on **under 50%** of tasks,
  pass^8 under 25% in retail. The thesis is *LLM for language, deterministic code for decisions* —
  a framework that blurs that boundary undercuts the argument.

**Rejected:** LangGraph (a graph for a straight line); LangChain (abstraction over a request I can
write myself); CrewAI / multi-agent (the exact overbuilding the brief warns about).

**Risk:** none material. `client.beta.messages.tool_runner` in the Anthropic SDK is the fallback if
per-turn hooks become useful for the audit log.

### A-10: Stack — Python, FastAPI, SQLite, static frontend, one deploy
**Decided:**

| Layer | Choice | Why |
|---|---|---|
| Data | **SQLite**, loaded from `shipments_clean.csv` at boot | Real UPDATEs. State genuinely changes |
| Backend | **FastAPI** | The cleaning layer is already pandas. Do not split languages |
| Agent | `anthropic` SDK | See A-09 |
| Frontend | One static page, modern CSS, vanilla JS | No npm, no build step, no time lost to tooling |
| Deploy | One container, one URL | A hosted link beats a recorded video |

**Because:** splitting into Next.js on Vercel plus Python elsewhere means two deploys, CORS, and
an evening gone. One Python service serving its own frontend is one deploy and one link.

**Rejected:** Streamlit / Gradio (looks like an internal tool, and presentation quality counts);
Next.js + separate Python (two deploys); Node end to end (would orphan the pandas work).

**Risk:** vanilla JS is more manual than React across two surfaces. Acceptable at this size.
Vite + React building to static, served by the same FastAPI, is the upgrade path that keeps one
deploy.

### A-11: Model — `claude-sonnet-5`
**Decided:** Sonnet 5 for the agent.

**Because:** strong tool use, low latency (latency is a feature in chat), and cheap enough that
the value case survives a calculator. Two well-defined tools do not need Opus.

**Cost, measured rather than assumed:** all eight seeded conversations were run live twice and
their token usage recorded. As first built, a conversation cost **$0.0161** in model fees; 13 of 37
calls were thinking, because leaving `thinking` unset on Sonnet 5 turns adaptive thinking on. With
effort `low` and the whole conversation cached, it costs **$0.0131**, and all eight ended in the same
actions and the same cases. On WhatsApp the bigger number is Meta's: about three replies at $0.0157
each from 1 October 2026, **$0.042**, three times the model. Low effort rather than thinking disabled,
because with thinking off the model can write a tool call into its reply instead of making it.

**On Arabic:** the UI supports RTL and the model answers in the customer's language. **No Arabic
parity is claimed.** Published benchmarks put every frontier model at **42.7–53.1%** on Gulf
Arabic, the weakest Arabic region, and the dominant failure mode is *ambiguous framing* (37.3%),
not hallucination (11.2%). Stated position: *"I tested English. Gulf Arabic is a known weak spot
with published numbers around 50%. I would run a dialect eval on real 7X logs before going live."*

### A-12: NO RAW SHIPMENT DATA IN THE SYSTEM PROMPT
**Decided:** the model starts with zero knowledge of the dataset. Every fact about every shipment
arrives through a tool call. The system prompt contains role, tone, rules and escalation policy —
and not one row.

**Because:** **this is the single mechanism that forces the system to be agentic rather than a
chatbot with a table pasted into its context.** If the data is in the prompt, the model answers
from it and never calls anything, and the result is a retrieval chatbot wearing an agent's name.
If the data is reachable only behind tools, the model has no choice but to act.

**Rejected:** putting a shipment summary in the prompt "for context" (this is the exact thing that
quietly turns an agent into a lookup).

**Risk:** more tool calls per conversation, so slightly higher latency and cost. Worth it.

### A-13: The screen never trusts what the model says
**Decided:** every status, date and address displayed in either surface is read from the database.
Never from the model's text.

**Because:** the most common fake-agent failure is the model announcing *"Done! I've rescheduled
that to Thursday"* when no tool was called and nothing changed. If the UI renders the model's
claim, that failure is invisible. If the UI renders the row, it is impossible.

**Risk:** none. This is what makes the demo proof instead of theatre.

### A-14: One door for every action
**Decided:** all actions pass through a single function that re-reads the record, checks the gate,
writes, logs, and returns a result. Not each tool doing its own thing.

**Because:** a single chokepoint means the trace log can never be inconsistent, the gate can never
be skipped, and adding a third action later is ten minutes instead of an afternoon.

### A-15: Every tool returns the same shape
**Decided:** `{ ok, data, reason, escalate }` — every time, every tool.

**Because:** otherwise the UI grows a different branch for every action.

### A-16: Sessions are first-class from line one
**Decided:** a session ID on every message, every log line, every case. Multiple conversations
live at once, listed in a sidebar, each tied to one customer. Old sessions stay open.

**Because:**
- A support system that holds one conversation at a time is not a support system.
- **The console needs it to mean anything.** A queue with one case is a sentence. A log with one
  conversation is not a log.
- **It rescues the demo.** Prepared sessions (clean reschedule / COD refusal / duplicate conflict /
  Arabic / no phone on file) turn a live tightrope into a controlled walkthrough, each point made
  in 15 seconds instead of 90. Those conversations really happened against real records — choosing
  which to show is not faking.
- **Cheap now, expensive Thursday.** Retrofitting session identity means rewriting the store, the
  log and the queue.

**Rejected:** one conversation (not a system); sessions as user accounts with login (A-05).

### A-17: One clock
**Decided:** a single place decides what "today" is, and it can be overridden. The cleaning layer
already pins `TODAY = date(2026, 9, 22)`.

**Because:** the data was cleaned on 22 Sep and the presentation is later. Without one clock, dates
drift quietly and something that worked on Tuesday looks broken on the day.

### A-18: Reset is a real feature, built early
**Decided:** one button restores the database, clears the sessions, and empties the queue.

**Because:** this demo will run fifty times in practice and once live. Built at the end it will be
half-working on the day it matters.

---

## Part 4 — Interface

### A-19: The customer surface is WhatsApp-shaped, in a phone frame
**Decided:** the chat is styled as WhatsApp, inside a phone frame. The console gets the design
ambition.

**Because:** **WhatsApp is 7X's only 24/7 channel today** — their own contact page describes a
virtual assistant there. A WhatsApp-shaped demo says *"this drops into the channel you already
run"*, not *"here is a new app you must convince customers to install"*. That is a commercial
argument made visually. It also makes the side-by-side layout deliberate: phone left, operations
right.

### A-20: The console uses the three-pane agent workspace layout
**Decided:** queue left · conversation centre · shipment context right. Plus two more tabs:
trace log, and data readiness.

**Because:** Intercom, Front and Zendesk all look like this. Using the shape people already know
reads as *"this person has seen a real support tool"*, which is worth more than an original layout.
The right-hand pane exists so the human never has to make the customer repeat themselves.

### A-21: The UI rules are derived from the complaints, not from taste
**Decided:** seven design rules, each one traceable to a verbatim review in the research pack.

| Verbatim complaint | Rule it produces |
|---|---|
| "WA chat bot doesn't see shipment number" | The parcel stays pinned on screen throughout, status read live from the DB |
| "keeps repeating the shipment update which is invalid" | Never restate a status without offering a next step |
| "impossible to get urgent help" | The route to a human is visible from message one, never hidden |
| "they send me 'schedule your delivery' but the link does not open" | No links out. Everything happens inside the thread |
| "they simply faked the delivery attempt" | On contradictory records, never assert that an attempt happened (D-06) |
| "Asked for delivery address 10 times??!!!" | Never ask for something already on the record. Show it, ask them to confirm |
| 62 Arabic reviews (13.7%) | RTL built properly, not a mirrored afterthought |

**Because:** this makes the interface evidence rather than preference, and it is the same move as
the data work, applied to the screen.

### A-22: The trace log is written in human sentences, not developer output
**Decided:** `Refused to change address on EX400312AE. Parcel has 745.72 AED to collect on
delivery. Sent to the human queue.`
**Not:** `GATE_DENY cod_amount_aed=745.72 policy=D07`

**Because:** same information, but one of them a non-technical decision maker reads and
immediately understands, and the other makes them feel locked out — which is the exact feeling the
console exists to remove. It costs nothing. It is word choice.

### A-24: The console's visual system — one ink band, and white beneath it
**Decided:** every tab of the console opens with a 96px band in the landing page's ink, carrying
the tab title and that tab's figures in Archivo at display size over the pixel mesh. Everything
below it is white, hairlines and a type scale of seven roles: 34, 24 and 18 for display, 13.5
body, 12.5 small, 11.5 meta, 10.5 micro, with the band's title and figures restated at 20 and 26
under 1240px. The rail stays light. The shipment is a record card shaped like the waybill, whose
three figures are the three things the gate checks.

**Because:** the landing page and the console read as two products, and the console had no
element that carried weight. The band is built from the three things the hero is made of —
ground, mesh, display face — so it is the same object shrunk into the tool. The reference for
the light theme was Stripe's dashboard: white, the numbers as the headline, a quiet sidebar with
an edge. Archivo only earns its keep above 18px; before this it was used at 19 and 20. Seventeen
distinct type sizes became nine, in seven roles.

**Rejected:** an ink rail (the heaviest thing on the page would be four links); the ink waybill
card (weight in the smallest pane, and only the Queue has a shipment); decorative gradients on
the work surfaces (noise by hour two); a dark theme. The design is an ink band over a white
page, and inverting the page dissolves the one contrast it is built on. A second theme also meant
every screen was checked twice or broke once: the scenario picker's names had been black on navy
for weeks and nobody had looked. The tokens, the switch and the `?theme=` link were removed.

**Risk:** 96px of height on every tab. One theme, and the device preference is ignored, so a
reader on a dark desktop gets a light page. Two fields crossed the "no
Python" line: the card API now returns the shipment's `customer_name`, because the card showed
the conversation's name over another person's address; and the scenario picker's API names each
person's `outcome` (allowed, refused, unclear), because the chat page was guessing it from the
label's wording.

---

### A-25: Staff see every conversation. The Queue stays what needs them
**Decided:** the console answers two questions on two tabs, from the same three panes.

| | **Queue** | **Conversations** |
|---|---|---|
| Answers | What needs a person | What is happening |
| Holds | Cases only | Every session, case or not |
| Ordered by | Open first, then newest | Who spoke last |
| In the seeded demo | 4 open, 1 resolved | 8 |

Staff may open and take over **any** conversation at any moment, not only one the assistant has
handed off. Replying switches the assistant off and puts the staff member's name on the thread;
handing back switches it on again.

Three states, out of two facts, because *the assistant is off* on its own is ambiguous:

| State | The two facts |
|---|---|
| **Assistant answering** | `assistant_enabled` |
| **Waiting for a person** | not enabled, nobody has replied |
| **With a person** | not enabled, someone replied and has not handed back |

**Because:**
1. **The top complaint in the review research is that the customer could not reach a human** —
   **22%** of the negative reviews, more than any delivery failure. A console where a person can
   only enter after the assistant decides to invite them reproduces exactly that, in the tool
   built to fix it.
2. **A work queue that holds everything stops being a work queue.** The Queue's whole value is
   that its length is the amount of work outstanding. The moment conversations that need nobody
   appear in it, the number means nothing and staff stop reading it.
3. **Part of the demo was invisible.** Three of the eight seeded conversations raise no case at
   all — the assistant finished them — and a fourth's case is already resolved. Those are the
   ones that prove the thing works, and until this tab existed there was no way to open one.

**Rejected:** escalated cases only, which is the common build and the reason staff consoles feel
like a complaints desk; and one merged list with a filter, which makes the open-case count a
thing you compute instead of a thing you read.

**Risk:** every staff member can read every conversation. In production that needs roles and an
audit trail, which A-05 cuts. And the tab **shows** but does not **alert** — nothing marks a
conversation as going badly unless a case is raised, so a customer being handled poorly but
politely is still invisible. The honest answer is that sentiment on a live thread is the next
feature, not that the tab already covers it.

---

### A-26: The demo opens mid-shift. Recorded once, replayed through the real door
**Decided:** eight conversations are run **once** against the real model and stored
(`python -m app.demo record --all`, a few tens of cents, written to `data/seed.json`). Every reset
replays them through the same functions the live application calls — `convo.new_session`,
`convo.verify_start/confirm`, `agent.save`, `agent.run_tool`, `convo.staff_reply` — with the
clock frozen so each lands at a fixed age. A reset takes a fraction of a second (measured:
**0.04s**) and costs nothing.

The opening state, every time: **8 conversations · 4 open cases · 1 resolved · 9 actions logged
(7 done, 2 refused) · 840 shipments.**

**Because:**
1. **An empty console proves nothing.** The first thing a reviewer sees is the product mid-shift,
   with a queue that has a shape, not a blank page and an invitation to type.
2. **Recorded, not generated live.** Running eight conversations at every reset would pay that
   cost again each time and produce a different demo each time. Recording once fixes both: the
   demo is identical on the fiftieth run, and the model's variance is spent before the meeting
   rather than during it. `app.chat_cli` prints the measured cost of any single conversation —
   the two-turn one is **$0.0228**.
3. **Replayed through the door, not written into the database.** The cases, the action log and the
   changed shipment rows are produced by the same code the live path uses. A fixture would let
   the demo assert behaviour the code no longer has.

> The seed is a recording of real behaviour, not a fixture. `python -m app.demo check` re-asserts
> all eight expectations — final state, scheduled date, address, cases, verification — after
> every reset.

**Rejected:** rows written straight into the database, which is faster to build and starts lying
the first time a rule changes; and generating live at each reset, which is that cost again and a
coin-flip every time someone presses the button.

**Risk:** the recordings capture one model version at one moment. Change the prompt or the model
and the seeded replies are what the assistant *used to* say — `check` still passes, because it
asserts the record, not the wording. Re-record and they are current again. The recordings live in
`data/` and are not committed, for the same reason nothing else derived from the client's file
is: a fresh clone must be given `seed.json` or record its own.

---

### A-27: One password over the whole site, and it is not a login
**Decided:** `SEVENX_PASSWORD` gates every route. Unset, there is no gate and `/healthz` says
`protected: false`, so a deploy that forgot it is visible from outside. Three paths stay open,
and nothing else: `/login`, `/healthz` for Render's check, and `theme.css`, which is a palette.

The cookie is a **signed expiry**, not a stored session — HMAC-SHA256 over the expiry with the
password as the key. Nothing to keep server-side, it survives a restart, and changing the
password invalidates every cookie ever issued, which is what you want from one shared credential.

Signing in always lands on the **landing page**, whatever link reached the door. The demo is
meant to be walked in order — what it is, then the customer, then the console — and a link passed
around should not drop someone straight into a staff tool. It also means no caller ever names a
redirect target, so the open-redirect question does not arise.

**Because:**
1. **The URL is public and the data is real.** Names, addresses and balances from the client's
   file, and an API key that spends money on every message. A-05 cuts staff login as a solved
   problem with no marks in it. That is still true, and it is a different problem: this is a lock
   on a public URL, not an identity system, and conflating them is how the lock never gets built.
2. **Masking the landing page was not enough.** The waybill shows a first name and a district
   (A-26's sibling decision), but the console shows whole records, because that is a working
   surface. The gate is what actually closes it.
3. **It is a door, not a dialog.** Browser Basic Auth needs no design and was the obvious cut.
   It also states nothing, and the one thing worth stating is *why* the demo is locked — that it
   runs on real records. The door is the landing page's waybill made out to the demo itself, so
   the first screen already speaks the language of the rest.

**Rejected:** HTTP Basic Auth (twenty minutes, generic chrome, no room to explain); leaving the
landing page public (a second class of route to classify, and a hole every time one is added).

**Risk:** one password, shared, with a 0.4s delay on a wrong answer and no lockout — a speed bump,
not a defence, and it is written down here rather than implied. Per-IP lockout, rotation and an
audit trail belong with the SSO A-05 cuts. The cookie is `HttpOnly` and `Secure` over HTTPS, but
anyone with the password has everything, including the ability to spend the API key.

---

## Part 5 — What is deliberately NOT built

Each of these is a cut that can be argued, not a gap that cannot.

| Cut | Why | What it costs |
|---|---|---|
| **Approval queue** (agent proposes, human commits) | Correct future home for COD address changes, but it doubles the state machine | COD routes straight to a human instead. Phase two, when volume justifies the staff time |
| **Staff login, roles, permissions** | Solved problem, zero marks, one more thing to break | Sits behind existing SSO in production |
| **Analytics: CSAT, deflection, cost saved, trend charts** | No data source exists for any of them | They live on the value slide, labelled as assumptions |
| **App bug handling** (login loops, OTP failures, crashes) | **9.9% of all negative reviews** — and none of it is something an assistant can fix | Measured, named, and cut with a number attached |
| **Recovery cases** (lost, misdelivered, damaged) | **13.0% of negative reviews.** Needs an investigation and a human, not a conversation | Routed to the queue |
| **Declared value / signature-required gate** | The fields do not exist in the dataset | COD used as proxy. Named as a gap (A-08) |
| **Search, filters, tags, archive on the session list** | A list and a New button is the whole requirement | Nothing |

---

## The rule underneath all of it

> **Code decides whether an action is allowed. The model only decides what to say about it.**

The gates were computed from the file before any conversation existed, and the tool re-checks them
on every call. **OWASP LLM01:2025** states plainly that there is no fool-proof defence against
prompt injection, and falls back on least privilege plus human approval for high-risk actions.

So the answer to *"what if someone talks it into changing an address?"* is not "I wrote a good
prompt". It is:

> "You can talk the model into anything. You cannot talk it past the gate, because the gate is a
> boolean computed from the data before the conversation started, and the tool re-checks it on
> every call. The worst a successful injection achieves is a rude sentence."
