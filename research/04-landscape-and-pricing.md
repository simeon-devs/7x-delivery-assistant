# AI vendor landscape, pricing, and buy vs build

Research run 21 Sep 2026. [V] = vendor self-published. [I] = independent reporting.
[A] = analyst firm. [3P] = third-party data. UNVERIFIED = a real gap, not an estimate.

Method caveat to state if pressed: web-search quota ran out partway, later verification was
direct URL fetch only. **Parloa, Crescendo and Maven AGI gate or block their technical docs, so
their architecture cannot be diligenced from public sources. That is itself a finding.**

---

## 0. The three things a panel will press on

1. **A "resolution" costs $0.99 to $2.00 in 2026, but the four vendors who publish a number
   define the billable unit differently enough that the numbers are not comparable.** Salesforce
   bills per *conversation* whether or not it resolves. Intercom and Zendesk bill only on
   success. Zendesk adds an independent LLM verifier. Compare cost per *resolved* contact, never
   the sticker price.
2. **Raw model inference is roughly 3 to 15% of a platform's per-resolution price.** You are not
   buying tokens. You are buying channels, connectors, QA, guardrails, analytics, handoff, and
   the liability transfer in an outcome-priced contract.
3. **Vendor resolution claims (76 to 93%) cannot be reconciled with the only public agentic
   benchmarks.** See τ-bench in §4.6.

---

## 1. THE TEN-DAY FACT: WhatsApp service messages stop being free on 1 October 2026

Verbatim from Meta's own docs, accessed 21 Sep 2026
(https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/non-template-messages):

> "Effective October 1, 2026, Meta will charge on a per-message basis for service messages,
> consistent with how Meta charges for template messages."
> "Effective October 1, 2026, Meta will charge on a per-message basis for utility messages sent
> in response to users within an open 24-hour customer service window."

Service rates will match utility/authentication rates per market, **with no volume tiers**.

**Why this matters.** Since 1 Nov 2024, inbound-driven customer service on WhatsApp has been
effectively free of Meta fees. Every WhatsApp CX business case built in 2025-26 assumed that.
From 1 Oct 2026, **every agent turn in a support conversation carries a Meta per-message fee.**
Any ROI model that does not reprice for this is out of date, and it goes out of date ten days
from today.

### UAE and MEA rate card, USD per delivered message
Source: Meta's pricing JSON endpoint behind the calculator at
https://whatsappbusiness.com/products/platform-pricing/, retrieved 21 Sep 2026.
**CAVEAT: a re-fetch of that endpoint returned HTTP 400. Re-confirm on Meta's live calculator
before quoting externally.**

| Market | Marketing | Utility | Authentication | Service |
|---|---|---|---|---|
| **UAE (+971)** | **0.0499** (no tiers) | **0.0157** (0.0118 >80M/mo) | 0.0157 | 0 until 1 Oct 2026 |
| Saudi Arabia | 0.0501 | 0.0107 | 0.0107 | 0 |
| Qatar | 0.0341 | 0.0120 | 0.0120 | 0 |
| Rest of Middle East | 0.0341 | 0.0091 | 0.0091 | 0 |
| Egypt | 0.0644 | 0.0036 | 0.0036 | 0 |

UAE in AED: marketing 0.1832, utility/service 0.0576.
UAE marketing is ~3.2x UAE utility. Template categorisation is worth real money at volume.

### BSP markup, the three published models
| BSP | Model | Published number |
|---|---|---|
| **360dialog** | Flat monthly per number, **no per-message markup** | EUR 49 / 99 / 500 per number/mo |
| **Gupshup** | Per message | **$0.0010** per message, in and out |
| **Twilio** | Per message | **$0.005** per message, in and out |
| Infobip, Unifonic | Not published | infobip.com/pricing/whatsapp returns 403 |

At 1M messages/month: Twilio $5,000, Gupshup $1,000, 360dialog EUR 500 flat. Against UAE utility
at $0.0157, Twilio's markup is ~32% on top of Meta, 360dialog's is ~0.03%.
**For a high-volume UAE deployment, BSP choice is a bigger cost lever than model choice.**

### Messaging limit tiers
250 → 2,000 → 10,000 → 100,000 → unlimited unique recipients per rolling 24h. Business
verification moves you off 250. Auto-scaling needs high quality **and** "in the last 7 days,
your business has utilized at least half of your current messaging limit."
Business Verification specifics and green-tick criteria: **UNVERIFIED**, help-centre page
unreadable to the fetcher.

### Meta Business Agent
Reportedly launches 1 Jul 2026, charged per token from 1 Aug 2026 at **$2.00 per 1M tokens**
(~4-5 cents/message). **UNVERIFIED, could not confirm directly.** If true, Meta is selling a
first-party agent inside the channel it also taxes.

### UAE regulatory position
**UNVERIFIED, and the absence is the finding.** No published TDRA regulation on A2P or OTT
commercial messaging was located; only an SMS Spam complaint service. Consumer Protection
Regulations v2.0 (25 Jul 2023) bind licensed telecom operators, not OTT senders. Whether a UAE
deployment needs a local aggregator or A2P approval is unknown. Get written legal advice.
Separately, UAE VoIP restrictions matter for any *voice* channel; WhatsApp messaging is not
affected.

---

## 2. CORRECTION: the logistics and Gulf gaps are NOT total

Two earlier conclusions in `02-vendors-notes.md` were wrong and are corrected here.

### Cognigy (now NiCE Cognigy) has DHL, and ships parcel-carrier connectors
- **DHL** case study: "managing over 15 billion letters and parcels annually, deals with around
  **30 million customer service inquiries each year**", agent named "Paula".
  https://www.cognigy.com/en/case-study/dhl [V]
- **First-party extensions exist for `dhl`, `fedex`, `ups`, `parcellab`.** Parcel tracking is a
  supported out-of-the-box pattern, not a custom build.
  https://github.com/Cognigy/Extensions/tree/master/extensions [V, code]
- Other transport references: **BVG** (Berlin transit), **Openreach**, **Lufthansa** (16+ agents,
  16M+ conversations/yr), **Frontier Airlines** (800K/mo), Swiss, Vueling, Sixt.
- **MEA reference: Mobily (Etihad Etisalat, Saudi Arabia)** — 8 social channels including
  WhatsApp and Apple Business Chat, "unified agentic orchestration layer connected to internal
  systems", payments and credit recharges. https://www.cognigy.com/case-study/mobily
  **Arabic quality is not stated on that page. For a KSA telco deployment, that omission is
  conspicuous.** No Dubai or UAE office on their about page.

**Write actions, four documented mechanisms** (the best-documented write surface in the scan):
1. **HTTP Request Node** — POST "creates a new resource", PATCH "updates partial data", PUT
   "replaces an existing resource", DELETE. Auth via encrypted Connections.
2. **Code Node** — JavaScript/TypeScript in-flow.
3. **Extensions** (npm, `@cognigy/extension-tools`) — worked CRUD example is the ServiceNow
   Table API extension: `Post To Table`, `Patch Record In Table`, `Delete From Table`.
4. **AI Agent Node + Tool Node** — LLM function calling, arguments at `input.aiAgent.toolArgs`.
**Governance gap: no documented human-in-the-loop approval gate on writes.** Guardrails are
instruction-level, not a transactional approval primitive. UNVERIFIED whether one exists.

**MCP, with an asymmetry worth knowing:** client is **GA since 17 Apr 2025**; server is
**EXPERIMENTAL** and their docs warn verbatim "The MCP Server Endpoint is experimental and isn't
recommended for production use", with no user-level authentication. Anyone claiming "Cognigy is
a production MCP server" is overstating it.

**Models: genuinely BYO-LLM.** Azure OpenAI, OpenAI, Anthropic, Google Vertex, Bedrock, Mistral,
Aleph Alpha, plus proprietary Cognigy Nexus. Release 2026.19 (15 Sep 2026) added `claude-opus-5`
with a candid engineering note: use it "for complex, non-real-time Flow steps rather than for
the conversation itself" given latency and per-token cost.

**Corporate:** NICE acquired Cognigy for **~$955M**, announced 28 Jul 2025, closed 8 Sep 2025.
**Analyst split worth raising:** Gartner MQ 2025 **Leader** → MQ 2026 **Visionary** (downgraded,
Gartner citing "the potential for roadmap deviations and R&D reductions that can follow a major
corporate transaction"), while Forrester's Q2 2026 Wave named it a **Leader** with a 4.5/5
strategy score, **in the same quarter**. The downgrade is absent from Cognigy's own analyst page.

**Pricing, and this is the only enterprise list price found anywhere:** AWS Marketplace list
price **$43,080 / 12 months for 60K conversations ≈ $0.72 per conversation**, plus Voice Gateway
$53,916, and an ELA at **$1,000,000 for up to 10M/yr ≈ $0.10 per conversation**.
https://aws.amazon.com/marketplace/pp/prodview-6c25zypcl2fro

### Unifonic is UAE/GCC based and has Aramex
- "The AI-native platform for end-to-end customer experiences", GCC focus, **"cloud deployment,
  local data residency, and built-in controls"**. Agents "interpret intent, trigger workflows,
  and complete customer tasks across systems". Claims to handle "up to 85% of support
  interactions". https://www.unifonic.com/ [V]
- **Logistics and delivery customers: Aramex, Careem, HungerStation.**
- Pricing not published.
- **Arabic claim: "95%+ Arabic dialect recognition", with no published methodology and no test
  set named. UNVERIFIED.**

### Forethought (now Zendesk) has UPS, Lime, and the single most useful admission in the scan

**Acquired by Zendesk.** Announced 11 Mar 2026, **completed 26 Mar 2026**. Price officially
undisclosed; **Reuters, citing the New York Times, reported "north of $200 million"** (headline
retrievable, body not — treat as press-reported, not confirmed). Described as Zendesk's largest
acquisition in about two decades. Now sold as "Forethought AI agents by Zendesk".
**Whether it remains available to non-Zendesk customers is UNVERIFIED** — several secondary blogs
claim it does, but neither Zendesk's press release nor the founder's post says so, and Zendesk's
own help doc routes all purchasing through Zendesk Sales.

**THE LINE TO PUT ON A SLIDE.** From Forethought's own help centre, guidance on when to use the
deterministic "Classic" builder instead of the agentic "Autoflows" mode:
> "Classic is recommended when: When you want strict control over the responses (e.g. sensitive
> information, **business-critical Actions such as refunds, cancellations**, requires an absolute
> verbatim response, medical information)"
(support.forethought.ai article 20916865674131, updated 29 May 2024, via Wayback)

**A vendor selling agentic AI tells its own customers to keep refunds and cancellations on the
deterministic path.** Their docs also cap Autoflows at **"<3 Actions, <3 context variables"** for
reliability. That is the whole argument for a guarded action layer, made by someone with every
commercial incentive to say the opposite.
Related honesty from the same FAQ: *"Does Autoflows use my knowledge base or past tickets to
generate responses? **A: No.**"*

**Write actions: yes, three mechanisms.**
- **Action Builder** — REST **GET, POST, PUT, DELETE**, Bearer-token auth only. `$`-prefixed
  context variables in, JMESPath response parsing out.
- **Autoflows** — natural-language policy, the LLM decides which Action to call.
- **Browser Agent** (2026) — computer use where no API exists: "log in, navigate, click, type,
  and complete real tasks inside any browser-based system". Self-reported beta: **16,800+ tasks,
  95% success**. Unaudited.

**Logistics evidence, stated at its real strength:**
- **UPS** — **logo only**, on the homepage and about page (verified in raw HTML). **No case study,
  no press release, no named contract.** Do not overstate it.
- **Lime** (micromobility) — **full case study**. Triage + Solve across chat, email, web form,
  phone and the app. Vendor-reported: 77% reduction in time to first response, 27% case
  automation, 98% of tickets auto-tagged, **1.7M tickets/yr**. Runs RPA-guided workflows for
  **damaged vehicles, payment issues and receipts**.
- **MeUndies** — **the best documented write-action case study found anywhere in this research**:
  Action Builder doing **order cancellation across Shopify + a third-party logistics provider +
  NetSuite**, checking the intercept window, plus subscription skip/cancel/retention.
  Vendor-reported 80% chat containment, 11 agents doing the work of 41.
- **Whiplash** (a 3PL) ships as an **`Action`-type connector** ("Used for Actions only"), so an
  out-of-the-box write path into a fulfilment system exists.

**Models, from the subprocessor list (contractual, not marketing):** AI-model subprocessors are
**OpenAI, Groq, Mistral**. **No Anthropic, no Google Gemini.** "SupportGPT" was never an in-house
model — their own doc says it "will bring **OpenAI's Large Language Model behind ChatGPT**
directly into Forethought's platform".

**Pricing:** "a blend of **platform access fees and an outcome-based pricing cost**". A release
note confirms **per-deflection billing is a real SKU**. [3P, second-hand, Vendr-derived via two
blogs] median **~$59,500/yr**, range $40,000-$155,000, **$0.12 per deflection** negotiable to
**$0.07** at volume, ~22% average negotiated discount. **Caveat: Vendr's live public page shows
no numbers today**, so these are second-hand. Stated minimums: **20,000+ historical tickets and
2,000+ tickets/month**, 30-90 day setup, no free trial.

**MCP:** listed as a connector, added ~Mar 2026 (inferred from asset timestamps). **Direction
undocumented.** Circumstantial placement in the "Actions only" bucket suggests **client**. Do not
claim server support. Their docs site 403s all programmatic clients, so 2026-era documentation is
a genuine blind spot.

**MEA: none found.** No Middle East customer, case study or office. Post-acquisition, Gulf
coverage would run through Zendesk.

### So the corrected position is
Not "nobody serves logistics". It is: **the generalist agentic-CX vendors (Ada, Maven, Crescendo,
Decagon) have no parcel or postal customers, while the contact-centre incumbents do** — Cognigy
has DHL and ships carrier connectors, and the regional CPaaS players have the Gulf logistics
names. That is a sharper and more defensible finding than the one it replaces.

### And a conflict to handle honestly
The PolyAI-FedEx reference came back **two different ways in two passes**. A PolyAI-specific pass
found a three-part interview series with **Paul Pugal, MD of Customer Experience, FedEx UK &
Ireland**, on PolyAI's own blog (VOX 2023), claiming deployment across four FedEx regions. This
landscape pass reports it is **absent from PolyAI's own case-study index** and marks it
UNVERIFIED. Both are true. Net position: the blog interviews exist and are citable **as 2023
vendor-published interviews**, FedEx is **absent from PolyAI's Dec 2025 Series D customer list**,
and there is no evidence it is live today. Do not lead with it.

---

## 3. The rest of the landscape, briefly

**Sierra.** Multi-channel, Agent SDK (agents as code, Git/CI-CD), simulation-based regression
testing. **Logistics customers: RunBuggy (vehicle transportation), LINE MAN Wongnai (SE Asia
delivery super-app).** $950M Series E at >$15B, ARR $100M → $150M. Forrester Wave Q2 2026 Strong
Performer. MCP: UNVERIFIED, not mentioned on the Agent SDK page.
Horizon (16 Jul 2026), verbatim: *"With Horizon, you don't pay for tokens, you pay for business
outcomes delivered. We bear the burden of managing token spend."*

**Decagon.** Agent Operating Procedures (natural-language procedures compiled to executable
logic, Git-versioned). **MCP explicitly supported.** Logistics-adjacent logos: **Gopuff, Hertz,
Avis, 1-800-Flowers**, Mercado Libre, American Airlines, Delta. $250M Series D at $4.5B, Jan
2026 (reported via headlines, primary articles not fetched). No published pricing.
⚠️ **Decagon and Sierra both publish Chime as a customer with a ~70% resolution figure.** Either
a split deployment or one is stale.

**Intercom / Fin — being acquired by Salesforce for ~$3.6B**, signed 15 June 2026, expected to
close in Salesforce's fiscal Q4 2027. Fin executes **Procedures**, "multi-step workflows that
update accounts, process payments and refunds... reading and writing to third-party systems via
API, Data Connectors, or **MCP**". Proprietary **Apex 1.0** models. ⚠️ Salesforce's release says
"more than 30,000 companies", fin.ai says "12,000+ customers". **Both Fin-sourced, and they
disagree.**

**Zendesk.** Relate 2026 (19 May 2026): "Autonomous Service Workforce", Resolution Learning
Loop trained on ~20 billion ticket interactions, voice in 60+ languages, **MCP support**.
**Specialized Industry Agents (14 Sep 2026) connect to Shopify, Narvar, Stripe, Riskified** —
Narvar is post-purchase delivery tracking, so shipment-status automation is first-class.
Acquired **Forethought** (completed 26 Mar 2026, its largest deal in two decades), Unleash, beams.
**Forethought is no longer an independent vendor. Evaluating it as one in late 2026 is invalid.**

**Salesforce Agentforce.** The only vendor with a fully public rate card. Writes via Flows,
MuleSoft connectors, Apex/JavaScript. **Native MCP client.** "Over 18K companies". Named:
Heathrow, Finnair, OpenTable, SharkNinja. Forrester Wave Q1 2026 **Leader**, Gartner MQ 2026
**Leader**.

**Parloa.** Docs at `docs.amp.parloa.com` redirect (HTTP 307) into a GitBook Auth0 login.
**Write mechanisms, API surface, connectors and MCP posture all UNVERIFIED and unobtainable
without a vendor login. Funding and valuation UNVERIFIED.** Gartner MQ 2026 honourable mention
only, absent from the Forrester Wave. For a brief defended in front of a panel, that opacity is
the finding.

**PolyAI.** Gartner MQ 2026 **Niche Player**, with a criticism worth quoting: *"Outside of voice,
prebuilt connectors are limited, and the platform is cloud-only, which rules it out for
enterprises with on-premise requirements or complex omnichannel environments."* Forrester Wave
Q2 2026 Strong Performer (first inclusion). Homepage cites an unnamed **"Global delivery company
— 100% of calls resolved without human agents"**, which is an extraordinary claim with no name
attached.

**Yellow.ai.** The only MEA-active vendor publishing a resolution price: 500/month free, then
**$0.99 per resolution**. Gartner MQ 2026 Niche Player.

**Infobip.** **MCP supported** — "Pull data from your CRMs, databases, APIs, and business tools
directly into conversations through Model Context Protocol", plus custom tools. MEA customer:
Nissan Saudi Arabia. Pricing not published.

---

## 4. Pricing: what a resolution actually costs

### 4.1 Every published number found
| Vendor | Billable unit | Published price |
|---|---|---|
| **Intercom / Fin** | Outcome | **$0.99** (qualification $9.99, 50-outcome/mo minimum off-Intercom) |
| **Yellow.ai** | Resolution | **$0.99** after 500 free/mo |
| **Zendesk** | Automated resolution | **$1.50** |
| **Salesforce Agentforce** | **Action** (checked 25 Sep 2026: the $2.00 conversation plan is now "for existing Agentforce Conversations customers" only) | was $2.00/conversation; Flex Credits $500/100k; action = $0.10; **voice action = $0.15**; $5/user/mo |
| **Cognigy** | Conversation | **$0.72** (AWS list, 60K/yr) down to **$0.10** (ELA, 10M/yr) |
| **Crescendo** | Resolution | **"from about $1.25"** (vendor buyer's guide, not a rate card) |
| Sierra, Decagon, Ada, PolyAI, Parloa, Maven AGI, Haptik, Infobip, Unifonic | — | **None published** |

Seats, for the hybrid model: Intercom $29 / $85 / $132 per seat/mo. Zendesk $19 / $55 / $115 per
agent/mo yearly, plus **Copilot $50/agent/mo**.

### 4.2 Sierra's outcome pricing, what is actually on the record
Bret Taylor, verbatim (Cheeky Pint, 10 Mar 2026):
> "If the AI agent resolves the case, no human intervention, there's a pre-negotiated rate for
> that. If we do have to escalate to a person, that's free."
He grounds it against a human-handled call at "$10, $20", but **discloses no Sierra rate**. The
$1 to $2.50 figures circulating are third-party and unsourced. Mark UNVERIFIED.

### 4.3 THE COMMERCIAL CRUX: the definitions are not comparable
| Vendor | What triggers the charge | What is free |
|---|---|---|
| **Intercom / Fin** | "No further help is requested after the last AI answer", or a Procedure completes. **One outcome per conversation max** | Escalations from frustration detection, **failed procedures**, abandoned conversations, greetings |
| **Zendesk** | Only a **"Verified Resolution"**, confirmed by an **independent LLM evaluation** | "Assisted Escalation" and "Contained Resolution" both do not count |
| **Salesforce** | **Every conversation**, resolved or not | Nothing at conversation level |
| **Sierra** | Resolution without human intervention | **Escalations to a human** |

**Say this to the panel:** Salesforce's $2.00 is not "twice Intercom's $0.99". At a 70% resolution
rate, Salesforce's effective cost per *resolved* issue is **~$2.86**, while Intercom's stays at
**$0.99**. Normalise every quote to cost-per-resolved-contact before comparing.

**The buyer-side corollary:** outcome pricing transfers model-cost risk to the vendor, and
transfers **measurement control** to the vendor too. Zendesk's LLM verifier and Intercom's "one
outcome per conversation" rule are both vendor-defined and vendor-audited. Contract for an audit
right and a disputed-resolution process.
Keith Kirkpatrick, Futurum, 20 May 2026: *"If Zendesk's agents can't deliver verifiable,
auditable outcomes at scale, outcome-based pricing could backfire, eroding both trust and
revenue."*

---

## 5. Build on a frontier API: the real numbers

### 5.1 Frontier API pricing, per million tokens, 21 Sep 2026
| Model | Input | Output | Cache read | Cache write |
|---|---|---|---|---|
| Claude Opus 5 | $5.00 | $25.00 | $0.50 | $6.25 |
| Claude Sonnet 5 | $2.00 | $10.00 | $0.20 | $2.50 |
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.10 | $1.25 |
| GPT-5 | $1.25 | $10.00 | $0.125 | — |
| gpt-5-mini | $0.25 | $2.00 | $0.025 | — |
| Gemini 3.8 Flash | $0.75 | $3.75 | $0.075 | — |

### 5.2 Modelled token cost per AI-handled conversation
**MY CALCULATION, not a sourced figure. Assumptions stated so they can be attacked:** 8 model
calls per conversation (user turns plus tool round trips), a stable cached prefix of 6,000
tokens written once and read 7x, 4,500 uncached input tokens per call, 250 output tokens per
call.

| Model | Total per conversation |
|---|---|
| Gemini 3.8 Flash | **≈ $0.042** |
| Claude Haiku 4.5 | **≈ $0.058** |
| GPT-5 | **≈ $0.078** |
| Claude Sonnet 5 | **≈ $0.115** |
| Claude Opus 5 | **≈ $0.289** |

So **$0.04 to $0.29 per conversation, ~$0.10 at a sensible mid-point.**

### 5.3 The comparison that matters
Platforms bill per *resolution*. You pay tokens on *every* conversation, including the ones that
escalate. Per 100 conversations at a 70% resolution rate:

| Approach | Cost per 100 conversations |
|---|---|
| **Build** | 100 x $0.10 = **$10 of inference** |
| **Buy, Intercom $0.99** | 70 x $0.99 = **$69** |
| **Buy, Zendesk $1.50** | 70 x $1.50 = **$105** |
| **Buy, Agentforce, ~3 actions at $0.10** (was $2.00/conversation, closed to new customers 25 Sep 2026) | 100 x 3 x $0.10 = **$30** |

**Inference is ~5 to 10% of the platform bill. Anyone arguing "build is cheaper because tokens
are cheap" is answering a question nobody asked. The other 90% is the actual product.**

Two adjustments the other way: voice adds STT/TTS and telephony (Agentforce prices a voice
action at $0.15 vs $0.10 digital); and **from 1 Oct 2026 WhatsApp service messages add roughly
$0.0157 x (agent turns) per UAE conversation to *either* approach** — about $0.06 to $0.13 for a
4 to 8 turn conversation, comparable to the entire inference cost.

### 5.4 Engineering cost to build — MODELLED, NOT SOURCED
No credible published figure exists, and inventing one would be worse than saying so. As a
structured estimate to be challenged: 2 senior engineers plus ~0.5 FTE of CX-ops design, 4 to 6
months to a single production channel with 5 to 10 working write integrations, then **1 to 2 FTE
of permanent maintenance** for knowledge freshness, prompt and model drift, connector breakage
and channel API changes. **The build is a project. The maintenance is a headcount line forever.**

### 5.5 What a platform gives you that a raw API does not
1. **Channel management.** Each channel is a separate API, session model, media path and
   compliance regime.
2. **Prebuilt write connectors.** Cognigy ships `dhl`, `fedex`, `ups`, `parcellab`, `stripe`,
   `service-now`. Zendesk ships Shopify/Narvar/Stripe/Riskified. Months of work you skip.
3. **Human handoff with context.** Sierra: automatic conversation summaries on handoff.
4. **Simulation and regression testing.** Sierra simulations, Decagon "simulations at scale".
   **This is the hardest thing to build yourself and it decides whether you can ship a prompt
   change on a Friday.**
5. **QA and outcome verification.** Zendesk Quality Score and the independent LLM evaluator.
6. **Analytics and operational memory.** Zendesk Context Graph, Sierra Agent Data Platform.
7. **Multilingual coverage.** Zendesk: 80 languages text, 60+ voice with mid-conversation
   switching.
8. **Compliance exposure you cannot outsource either way.** Aithos testing found leading models
   "broke the law in over a third of cases" in realistic EU compliance scenarios. Nadia Kadhim,
   Aithos: *"There is still responsibility to make sure that its behavior is legal"*, build or buy.

### 5.6 THE RELIABILITY EVIDENCE NOBODY MARKETS
**τ-bench** (arXiv 2406.12045, 17 Jun 2024, Yao, Shinn, Razavi, Narasimhan — **Sierra-affiliated
authors**): agents interacting with simulated users *and programmatic APIs* under domain policy.
> "Even state-of-the-art function calling agents (like gpt-4o) succeed on **<50% of the tasks**,
> and are quite inconsistent (**pass^8 <25% in retail**)."
Success is scored on **final database state**, not conversation quality. It measures exactly the
write actions this assignment is about.

**τ²-bench** (arXiv 2506.07982, 9 Jun 2025) adds dual control, where agent *and* user both mutate
shared state: "significant performance drops when agents shift from no-user to dual-control."

**Use this to frame the whole thing honestly:** the hard part is not calling the model. It is
getting a write action right reliably, repeatedly, under policy. That is what the 90% you pay a
platform for actually buys, and it is why you demand a pilot on your own tasks instead of
accepting a 76%-resolution slide.

---

## 6. Independent evidence on buy vs build

| Source | Date | Finding |
|---|---|---|
| **Menlo Ventures**, State of GenAI in the Enterprise | 9 Dec 2025 | Enterprise genAI spend **$37B in 2025, up from $11.5B (3.2x)**. In 2024, 47% of AI solutions were built internally, 53% purchased. In 2025, **76% of use cases are purchased, internal builds fell 47% → 24% in one year.** Also: 47% of AI deals reach production vs 25% for traditional SaaS. |
| **Gartner** | 25 Jun 2025 | **Over 40% of agentic AI projects cancelled by end-2027** on cost, unclear value, inadequate risk controls. Warns of **"agent washing"** and estimates **only ~130 of thousands of agentic AI vendors are real.** |
| **Gartner** | 26 Aug 2025 | 40% of enterprise apps will feature task-specific AI agents by end-2026, up from <5% in 2025. |
| **CX Today**, build vs buy | 26 Jun 2026 | Dhwani Soni (8x8): *"Off-the-shelf agents are built for the average workflows. However, most companies don't have standard average workflows."* Simon Ellis (Pets at Home): *"Buy the commodity if the platform's there and it's good... then you build your secret sauce, what makes you different."* |
| **Forrester Wave, Customer Service Q1 2026** | 9 Apr 2026 | **Leaders:** Salesforce, Microsoft, Pegasystems, ServiceNow. **Strong Performers:** Zendesk, Oracle, Creatio, Freshworks. **Contenders:** Intercom, SAP, Zoho, HubSpot. Kate Leggett: *"The role of AI and the CSR flips: AI addresses the majority of the work, while CSRs assist AI."* |
| **Forrester Wave, Conversational AI Q2 2026** | Apr 2026 | **Leaders:** NiCE Cognigy, Kore.ai, Omilia. **Strong Performers:** Sierra, Uniphore, Intercom, Rasa, PolyAI, LivePerson. |
| **Gartner MQ, Conversational AI 2026** | 7 Jul 2026 | **Leaders:** Google, Salesforce, Kore.ai, SoundHound. **Visionaries:** NiCE Cognigy (downgraded), IBM, Omilia. **Niche:** PolyAI, Sprinklr, Druid, Avaamo, Yellow.ai. Ada, Crescendo, Maven AGI **not positioned at all.** |
| **Forrester Predictions 2026** | 5 Nov 2025 | **"Thirty percent of enterprise app vendors will launch their own MCP servers"**, creating "an open ecosystem where businesses aren't locked into a single AI provider." |

**Synthesis: buy the platform, build the differentiator.** Menlo's 47% → 76% swing toward buying
in a single year is the strongest quantitative signal available. Gartner's cancellation and
agent-washing warnings apply to **both** paths, because they are about operationalisation and
governance, not about who wrote the code. And MCP is making "buy" less lock-in-shaped than it
was: Salesforce, Zendesk, Decagon, Infobip, Ada and Cognigy are all MCP clients, so proprietary
tools stay yours and the platform becomes the orchestration and compliance layer rather than the
integration monopoly.

**The defensible recommendation:** buy the platform for channel management, connectors, QA and
outcome measurement. Build only what is genuinely yours — the write actions against your own
systems, exposed to the platform over MCP or a REST tool contract. That keeps the integration
surface in your repo and under your tests while the vendor carries channel, compliance and
measurement.

---

## 7. UNVERIFIED register: what a panel could legitimately attack

1. **Sierra's per-resolution rate.** Structure confirmed by the CEO; $1-$2.50 figures are
   third-party and unsourced.
2. **Meta UAE rate card.** From Meta's pricing JSON endpoint; re-fetch returned HTTP 400.
3. **Meta Business Agent** (1 Jul 2026 launch, $2.00/1M tokens). Not independently confirmed.
4. **UAE / TDRA A2P and local-aggregator requirements.** No regulation located.
5. **Arabic quality.** No independent benchmark exists anywhere. Unifonic's "95%+ dialect
   recognition" has no published methodology.
6. **Meta Business Verification and green-tick criteria.** Page unreadable to the fetcher.
7. **PolyAI-FedEx.** See the conflict note in §2.
8. **Decagon's $4.5B Series D.** Headlines only, primary articles not fetched.
9. **Parloa's entire technical architecture, funding and valuation.** Docs auth-gated.
10. **Crescendo's funding.** "$50M round" vs "$50M total financing" vs "Series C at $500M" do not
    reconcile. A ~$2.2B valuation is unsupported.
11. **Maven AGI's action mechanism and MCP posture.** Docs return 403/404.
12. **Cognigy's human-in-the-loop write approval.** No such primitive documented.
13. **Fin's customer count.** Salesforce says "more than 30,000 companies", fin.ai says "12,000+".
    Both Fin-sourced, and they disagree.
14. **Chime** appears as a ~70% resolution reference for **both** Sierra and Decagon.
15. **All vendor resolution rates (76-93%)** are self-reported and unaudited, and sit uneasily
    beside τ-bench's <50% and pass^8 <25%.
16. A **"Forrester: 3 of 4 agentic AI builds will fail"** claim circulates widely. **It is not in
    the Forrester Predictions 2026 post and could not be sourced. Do not use it.**
