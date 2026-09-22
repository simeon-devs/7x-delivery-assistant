# Vendor notes (partial, 21 Sep 2026)

Two deep profiles landed first. The full landscape pass is still running.
[VENDOR] = self-published by the vendor. [3P] = third party. Everything unlabelled is a fact
from primary documentation.

---

## Ada (ada.cx)

**Write actions: yes, first-class and fully documented.** Not retrieve-and-answer only.
- Mechanism: **"API tools" (formerly "Actions")**, full GET/POST/PUT/PATCH/DELETE. POST/PATCH/
  PUT/DELETE all require auth. Composed by **"Processes"** and **"Playbooks"**, extended by
  **"Code tools"** (sandboxed Python) and **"MCP tools"**. Credentials in a "Token Vault".
- Their own docs give a refund example: validate the items, check them against refund policy
  (total amount, time since delivery), **then execute an Action to process the refund**.
- MCP tools doc, verbatim: "Take an action in your system: create, update, or cancel a record."
- https://docs.ada.cx/docs/automation/actions/action-control
- https://docs.ada.cx/docs/automation/processes/process-management
- https://docs.ada.cx/docs/automation/tools/mcp-tools

**Closest thing to a logistics proof point: Dott** (shared e-scooters, 400+ cities incl. Dubai).
Real-time **trip closure** and **refund processing** via "25 API-powered automations connecting
directly to Dott's backend systems". Claimed AR 32% to 77%, containment 91%, +17 CSAT, ~2M
contacts/year. All vendor self-reported. https://www.ada.cx/case-study/dott/
**Loop Earplugs**: "from order edits to invoice retrieval" plus multi-carrier tracking. Order
editing is a write. https://www.ada.cx/case-study/loop-earplugs/

**GAP worth raising in any procurement review:** no documented mandatory human confirmation
before a destructive or irreversible write, no rollback/undo for external writes. Their
change-set/revert machinery applies to **agent configuration**, not to writes the agent makes
in your systems. Their MCP docs do advise "Start with read-only tools before enabling write
capabilities", which is guidance, not a gate.

**Models:** multi-provider, disclosed only in the legal subprocessor list (updated 9 Jul 2026):
OpenAI, Anthropic, Azure OpenAI, Cohere, plus **Groq and Baseten as inference hosts** (implies
open-weight or fine-tuned models on latency-sensitive paths). No Ada-built frontier model.
https://www.ada.cx/legal/subprocessors/

**Pricing: contact-sales, no published rates.** Only methodologically stated third-party figure:
**Vendr, Feb 2026, median ACV $72,000/yr across 114 purchases, range $36,079 to $309,200**,
volume-based not per-seat. https://www.vendr.com/marketplace/ada
Sacra estimates $0.99 to $1.50 per resolved interaction. [3P]

**Credibility notes.** Ada's own two pages contradict each other on total interactions (6.4B vs
4B) and on customer count (550+ vs 350+). Every resolution percentage is self-graded with no
published methodology. Ada itself published a post on 1 Sep 2026 attacking containment rate as
a metric.

**Funding:** $130M Series C, May 2021, $1.2B valuation (Spark Capital led per BetaKit/VCJ;
Sacra says Tiger Global). **No new round or valuation mark since May 2021**, through layoffs in
2020 (23%), Sep 2022 (16%, 78 people) and Feb 2023. A 2021 paper valuation carried five years
through the CX-AI repricing.

**Postal or parcel carrier customers: none found. MEA/Gulf customers: none found. No Gulf data
residency** (AWS hosting disclosed for USA, Canada, Europe only). Closest Gulf touchpoint is
Dott serving Dubai.

---

## PolyAI (poly.ai)

**Voice-first, genuinely omnichannel.** Agent Studio (launched ~Apr 2025), plus webchat, SMS,
RCS, email, WebRTC in-browser voice, iOS/Android SDKs.

**Write actions: strong and real.**
- **Functions** are Python scripts. Their docs, verbatim: "Functions let your agent perform
  actions during a conversation, looking up a booking, calling an API, validating input, or
  **writing to a CRM**." Runtime ships `requests`, `jsonschema`, `urllib3`.
  https://docs.poly.ai/tools/introduction
- `conv.api` for configured API integrations with auth handling, **Secrets Vault** for runtime
  credentials, **End tool** for asynchronous post-call writes, **External Events API** to feed
  "payments, bookings, verifications" back into a live conversation, **Outbound API** to dial.
- Documented writes: **Stripe refunds and coupons**, OpenTable `make_booking`, Salesforce case
  management, Zendesk ticket operations. Card payments are **delegated to PCI Pal**, the agent
  does not execute the card transaction itself.
- Order management use case markets exactly our problem: "**Take, edit or cancel orders over the
  phone**", returns, refund status, **delivery rescheduling**. No named customer on that page.
  https://poly.ai/use-cases/order-management

**MCP: shipped in both directions, ahead of most of the field.** Hosted **Builder MCP** and
**Data MCP** servers (`X-API-KEY`, four regions, documented for Claude Code, Cursor, Claude
Desktop, Codex), and Agent Studio as an **MCP client** that discovers and invokes third-party
MCP tools mid-conversation (header, query-param or OAuth2 client-credentials auth, 1-30s
timeout). Also states A2A protocol use. https://docs.poly.ai/mcp/overview

**The logistics proof point, and its caveat: FedEx.** Three-part interview series with **Paul
Pugal, MD of Customer Experience, FedEx UK & Ireland**, recorded at PolyAI's VOX 2023. Deployed
across **four major FedEx regions**, claimed "the world's first enterprise voice assistant that
speaks over 10 languages", started in the UK. FedEx evaluated Nuance, Salesforce and Genesys
first. **No containment or deflection numbers given.**
**CAVEAT: FedEx appears in 2023-2024 material and is ABSENT from the Dec 2025 Series D customer
list** (Marriott, Caesars, PG&E, UniCredit, Foot Locker, Fogo de Chão, The Melting Pot).
Whether the deployment is still live is UNVERIFIED. Also named: **HM Passport Office**.
https://poly.ai/blog/how-to-scale-your-voice-assistant-interview-with-fedexs-paul-pugal/

**Models:** in-house **Raven 3.5** (24+ languages, sub-300ms) and **Dialog-RSN-1** (audio-native,
launched 30 Jul 2026, p50 latency 280ms vs GPT Realtime-2's 860ms, 6.9% WER). Important:
Dialog-RSN-1 is **post-trained on open weights (Gemma, GPT-OSS, Qwen, Mistral)**, which
complicates the "fully proprietary stack" narrative. Also supports OpenAI GPT-5.x, Anthropic
Claude via Bedrock, and bring-your-own endpoints.
Raven 3.5 "beats GPT-5 and Claude Sonnet 4.6" is measured **on PolyAI's own benchmark**, never
reproduced by a third party. The Dialog-RSN-1 latency and WER numbers were repeated verbatim by
CMSWire, SiliconANGLE and TechTimes with **no independent testing**. Press repetition is not
verification.

**Pricing:** "priced on a **per-minute basis**" is the only concrete statement. No rates
anywhere. https://poly.ai/pricing

**Funding:** Series C $50M, 16 May 2024 (led by Hedosophia, NVentures/NVIDIA, **Zendesk**).
**Series D $86M at a $750M valuation, 15 Dec 2025**, co-led by Georgian, Hedosophia, Khosla,
with the **British Business Bank** participating. Total >$200M. London HQ, CEO Nikola Mrkšić.

**The "391% ROI, $10.3M average savings" figure is a Forrester Total Economic Impact study,
commissioned and paid for by PolyAI.** It is not a Forrester Wave. No Gartner Magic Quadrant or
Forrester Wave placement found for PolyAI.

**MEA/Gulf: nothing.** Their sitemap contains no URL referencing Middle East, UAE, Dubai, Saudi
or Gulf. Data regions are **US, UK, EU only**.

---

## Maven AGI (mavenagi.com)

Boston, founded early 2023. CEO **Jonathan Corbin** (ex-HubSpot), CTO Sami Shalabi (ex-Google
News), CPO/CAIO Eugene Mann (ex-Stripe Applied ML). $28M Seed+Series A (2024, M13 led),
**$50M Series B Jun 2025 led by Dell Technologies Capital** with Cisco Investments and SE
Ventures. Total $78M. Valuation undisclosed. ~80 employees as of Jun 2025, Boston only.
Note: **Dell and Cisco are both investors and named as customers/partners**, so treat the Dell
logo on their homepage as investor-adjacent.

**Write actions: confirmed in published SDK source, not just marketing.**
- Mechanism is **"Actions"** (LLM-selected tools), implemented by a **Maven App**'s
  `executeAction` handler or a UI-configured HTTP webhook. Endpoints: `PUT/GET/PATCH/DELETE
  v1/actions/...`, executed through `POST v1/conversations/{id}/ask`.
- **The design detail worth stealing.** Each action carries a flag **`userInteractionRequired`**.
  Their own doc text: "Whether the action requires user interaction to execute. **If false, and
  all of the required action parameters are known, the LLM may call the action automatically.**
  If true, an conversations ask call will return a BotActionFormResponse which must be
  submitted by an API caller." That is a per-action human-in-the-loop toggle, and it is the
  clean way to express "reschedule is automatic, address change on a COD parcel is not".
- Published types include `BotLogicActionExecutedDetail` and `BotLogicActionReviewedDetail`,
  i.e. an audit trail distinguishing executed from reviewed actions.
- https://github.com/mavenagi/mavenagi-python (SDK reference, pushed 16 Sep 2026)
- https://github.com/mavenagi-apps/http-webhook (generic write path, GET/POST/PUT/PATCH/DELETE)

**Vendor-stated writes.** Shopify: "Maven can initiate refunds, cancellations, and return
requests based on your configured policies and approval rules. **You control which actions
require human approval.**" Salesforce: "update case fields, create follow-up tasks, escalate to
specific queues, and trigger Salesforce flows... all write actions require configured
permissions and can include user confirmation steps." Voice page claims "issue a refund, lock a
card, rebook a flight, and executes it".
**Address change is not named in any Maven public doc.** "Rebook a flight" is illustrative copy,
not a documented connector method.

**MCP: client only.** Maven consumes third-party MCP servers (paste a server URL, configure
access). Verified four ways that Maven does **not** expose its own MCP server: zero `mcp`
matches in the published SDK source, no MCP repo in either GitHub org, not listed on the
integrations page. https://www.mavenagi.com/resources/model-context-protocol (9 Jul 2025)

**Models: deliberately model-agnostic, per-customer selection.** Their CAIO, 10 Sep 2026: "a
model that works flawlessly for one customer may have marginal results for another. So, we test
models to identify the best one for each customer's individual use cases." Only model named
publicly is OpenAI GPT-Live-1. "Proprietary retrieval engine" and "proprietary reasoning engine"
are orchestration claims, **not** a proprietary foundation model.

**Pricing: contact-sales, none published.** [3P] Vendr: **median $100,000/yr, range $42,000 to
$200,988**. That is ~17.5% above Ada's $72k median.
https://www.vendr.com/marketplace/maven-agi

**Credibility notes.** Maven quotes **Tripadvisor at 80%** in its dated case study (2 Dec 2024)
and **"90% of incoming queries"** on the 2026 homepage. Same customer, +10 points, no
methodology published either time. "93%" has been reused as a headline since May 2024. Series B
PR claims "100+ out-of-the-box integrations"; **31 are publicly listed.** And their own report
(16 Jul 2026) is titled "Adoption Is Nearly Universal. Resolution Isn't", so the vendor itself
argues the category over-reports the metric.

**Logistics, parcel, postal, freight, last-mile customers: NONE found.** Nearest is the Shopify
connector (refunds, cancellations, return requests, prepaid shipping labels) with no named
retail or fulfilment logo behind it.
**MEA/Gulf: none found.** No regional office, Boston-only careers page.

---

## Crescendo (crescendo.ai)

**This one is a different category, and that matters for the scan.** Crescendo is not software
you buy and run. It is **CX-as-a-service**: they run the whole support function, AI on the front
line and **their own human agents** behind it. In Oct 2024 they acquired the BPO **PartnerHero**
(~3,000 CX professionals, ~200 customers); partnerhero.com now says "PartnerHero is now powered
by Crescendo" and its About page 301-redirects to crescendo.ai.
Founders: Anand Chandrasekaran, Andy Lee, Matt Price, Dr Slava Zhakov, "hatched at General
Catalyst". **Andy Lee became CEO on 14 Jul 2026**, Price moved to board advisor.
Funding: **$50M total, Series C, 2 Oct 2024, General Catalyst led, $500M post-money**
(Bloomberg headline confirms the valuation). No round since. Self-reported **$100M+ ARR**.
Offices Portland, Greensboro, San Pedro Sula, Manila; **a Dubai office was announced as planned
in Sep 2025 and I found no confirmation it opened.**

**PRICING: the only published per-resolution number found across all four vendors.**
> "Crescendo resolves conversations from about $1.25 each... pay-per-resolution pricing,
> starting from about $1.25 per resolution."
https://www.crescendo.ai/blog/ai-agent-for-customer-support-practical-guide-cx-leaders (11 Sep 2026)
It is a "starting from" figure in a vendor-authored buyer's guide, not a rate card; their own
pricing page publishes nothing. A competitor (Macha) estimates ~$2,900/month base plus ~$1.25
per AI-resolved ticket and **$2.25 to $2.99 per human-involved ticket**. The $1.25 matches, the
rest is uncorroborated.
**Total Outcome Guarantee:** go live in 30 days or implementation is free; if AI quality does
not outperform within 30 days of go-live, that month is free; interactions rated 2 or below in
predictive CSAT are credited. No dollar figures or numeric thresholds published, and the
baseline for "outperform" is unstated, so it is weaker than it first reads.

**Write actions: yes.** Their term is the **"Safe Action Framework"**, which "determines what AI
can do autonomously and what requires human approval", plus **"governed tools"** and "Macros".
Worked example on their product page: "creates replacement order, refunds shipping, writes
signature-required flag to profile, detects third incident, **opens carrier dispute ticket**".
Elsewhere: "issuing a refund, changing an order, or updating a customer record", and explicitly
"**updating the address**".
Evidence quality: strong for MCP and the Provisioning API (documented paths and verbs), medium
for refunds/order/address changes (consistent marketing prose, no published tool schema or
permission model). **Their case studies do not corroborate transactional writes** — the Stewart
Golf story is answering, tracking and warranty queries only.
**Contradiction to note:** their Sep 2026 guide says "No change reaches a customer without human
approval", while the product page markets autonomous resolution with the Safe Action Framework
deciding the boundary. The autonomy line is configurable and set during managed onboarding.

**MCP: both directions, and independently verified.** Client side since 28 Oct 2025 (including
Shopify's storefront MCP server, where cart updates are a write), auto-detecting new tools
without admin setup. Server side at `POST /api/v1/mcp/tenants/{tenantId}/bots`, JSON-RPC 2.0
over Streamable HTTP. **API Evangelist independently probed it on 12 Aug 2026**, which is the
only third-party technical verification in this whole research run. The documented tool is
administrative (`list_bots`), not customer-transactional.

**Models:** Amazon **Nova Sonic** and **OpenAI RealTime** for speech-to-speech, plus STT-LLM-TTS
pipelines with Azure, DeepGram, ElevenLabs. Multi-LLM support. No proprietary foundation model.
Anthropic and Google are never named.

**Credibility notes.** Older marketing claims "99.8% accuracy" and "90%+ of pre-sales inquiries
without human input"; the **current homepage says "70% resolution from day one"**. The numbers
deflated as the company matured, which is worth pointing out: the older figures were best-case
single-use-case results. CX Today, 28 Aug 2026, is openly sceptical of the 30-day claim.

**Gulf: DAMAC.** Listed on their customers page under Real Estate. DAMAC is Dubai-headquartered,
though Crescendo's own page never says Dubai or UAE and publishes no case study.
**This is the only named Gulf customer across all four vendors researched.**

**Logistics, parcel, postal, freight, 3PL: none.** Closest are Good Eggs (online grocery
delivery), ezCater (catering delivery), SimpleSUB Water (subscription delivery), TaskRabbit,
EVPassport, Pied Parker. But note their product page markets "package tracking" and "opens
carrier dispute ticket" as capabilities, without a logistics logo behind them.

---

## What these four establish for the buy-vs-build section

1. **Agentic write actions are a commodity.** All four ship them, documented, with named
   customers doing refunds, order edits, trip closure and address updates. "My assistant can
   call an API" is not a differentiator in 2026 and must not be pitched as one.
2. **It is not buy vs build. It is buy vs build vs BUY THE OUTCOME.** Crescendo (AI plus its own
   3,000 human agents, priced per resolution, with a guarantee) is a genuinely different
   procurement shape from Ada/PolyAI/Maven (software you configure). A market scan that misses
   this third option is incomplete, and for an operator whose real problem is call volume, the
   outcome model is the most direct competitor to building anything at all.
3. **Pricing anchors, such as they are.** Crescendo publishes **~$1.25 per resolution** (the only
   published unit price). Sacra estimates Ada at **$0.99 to $1.50 per resolution**. Vendr's
   median annual contracts: **Ada $72k** (range $36k-$309k, n=114), **Maven $100k** (range
   $42k-$201k). PolyAI is per-minute and undisclosed. That is enough to build a value case with
   a labelled range, and nothing more.
4. **Gulf presence is close to zero AMONG THESE FOUR.** Ada hosts in USA/Canada/Europe only.
   PolyAI's regions are US/UK/EU only, and its sitemap contains no Middle East URL at all. Maven
   is Boston-only. The single named Gulf customer across these four is **DAMAC (Crescendo)**, and
   Crescendo's Dubai office was announced as planned in Sep 2025 with no confirmation it opened.
   **CORRECTED in `04-landscape-and-pricing.md`: this does NOT hold for the wider market.**
   Cognigy has **Mobily (Saudi Arabia)**, and **Unifonic is UAE/GCC-based with published local
   data residency and Aramex, Careem and HungerStation as customers.** The accurate statement is
   that the **generalist agentic-CX startups** have no Gulf footprint, while the contact-centre
   incumbents and regional CPaaS players do. The PDPL Art. 5 data-residency argument still
   stands against the startups, but it is not a blanket market gap.
5. **Nobody documents a mandatory human gate before an irreversible write, but three of four
   name the pattern.** Maven's per-action **`userInteractionRequired`** flag is the cleanest
   published expression of it, Crescendo calls it the **Safe Action Framework**, Maven's Shopify
   page says "you control which actions require human approval", and Ada's guidance is merely
   "start with read-only tools before enabling write capabilities". Ada documents **no rollback
   for external writes**. Building that gate explicitly, and demoing a refusal, is cheap
   judgment that the market itself treats as a configuration afterthought.
6. **These four have zero postal or parcel-carrier customers.**
   **CORRECTED in `04-landscape-and-pricing.md`: the wider market does not.** Cognigy has a
   **DHL** case study ("over 15 billion letters and parcels annually... around 30 million
   customer service inquiries each year") and ships first-party **`dhl`, `fedex`, `ups`,
   `parcellab`** extensions. Forethought (now Zendesk) carries a **UPS logo** and a **Lime** case
   study. Decagon has **Gopuff, Hertz, Avis**. Sierra has **RunBuggy** and **LINE MAN Wongnai**.
   The accurate finding is narrower and better: **the agentic-CX startups have no parcel
   customers, while the contact-centre incumbents do** — and even the incumbents' logistics
   references are mostly logos and tracking use cases, not documented write actions on
   shipments.
7. **Every resolution number in this market is self-graded.** No independent benchmark exists
   for AI support resolution rates. Ada's own pages contradict each other on interaction counts.
   Maven quotes the same customer at 80% and 90% on two pages. Crescendo's claims fell from
   "99.8% accuracy" to "70% resolution from day one" as it matured. And three of the four have
   published pieces attacking containment rate as a metric while selling on it.
