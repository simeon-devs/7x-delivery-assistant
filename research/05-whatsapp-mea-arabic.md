# WhatsApp economics, MEA vendors, and Arabic quality

Research run 21 Sep 2026. [VENDOR] = vendor's own site/docs/PR. [INDEPENDENT] = press, academic,
or a third party with no commercial interest. UNVERIFIED = could not be sourced, not guessed.

**Provenance of the Meta rate card, state this if challenged:** rates were pulled directly from
Meta's pricing endpoint (`https://whatsappbusiness.com/wp-json/wab/v1/pricing`, 21 Sep 2026), then
cross-checked against Twilio's embedded pass-through data ("current as of August 2026") and Bird's
bundled totals. **All three agree to four decimal places.**

---

## 1. Three structural changes in 2026 that invalidate most published analysis

1. **The free 24-hour service window ends 1 October 2026.** Meta: *"Any non-template message is
   charged as of October 1, 2026."* Service messages (free since 1 Nov 2024) and non-template
   utility messages (free since 1 Jul 2025) become chargeable at the same per-market rate as
   utility and authentication. **No volume tiers on service.**
   https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/non-template-messages
   Corroborated independently by 360dialog's docs and by Bird already listing "Service (effective
   October 1st)" as a priced line.
2. **Meta is selling its own agent inside WhatsApp.** Meta Business Agent launched 1 Jul 2026,
   charged per token from 1 Aug 2026 at **$2.00 per 1M tokens**, which Meta estimates at
   *"approximately 4-5 cents per message (20,000-25,000 tokens)"*. It *"becomes the primary
   responder on a WhatsApp phone number"* — a displacement of the vendor's agent, not a
   complement. **Meta now competes with every CX vendor on the channel it also taxes.**
   Excluded verticals: **Finance, Government, Health, Alcohol, Gambling, OTC drugs, matrimony.**
3. **On-Premises API is gone.** Final version expired 23 Oct 2025; Cloud API is the only path.
   Any "we host it in-region on-prem" story from a BSP is obsolete.

---

## 2. The UAE and MEA rate card

USD per delivered message, list rate (tier 1), effective 1 Jul 2026:

| Market | Marketing | Utility | Auth | **Auth-International** | Service |
|---|---|---|---|---|---|
| **UAE** | **0.0499** | **0.0157** | **0.0157** | **0.0510** | 0 until 1 Oct 2026 |
| Saudi Arabia | 0.0501 | 0.0107 | 0.0107 | 0.0598 | 0 |
| Qatar | 0.0341 | 0.0120 | 0.0120 | n/a | 0 |
| Egypt | 0.0644 | 0.0036 | 0.0036 | 0.0650 | 0 |
| Nigeria | 0.0516 | 0.0067 | 0.0067 | 0.0750 | 0 |
| South Africa | 0.0379 | 0.0076 | 0.0076 | 0.0200 | 0 |
| Rest of Middle East | 0.0341 | 0.0091 | 0.0091 | n/a | 0 |
| Rest of Africa | 0.0225 | 0.0040 | 0.0040 | n/a | 0 |

**UAE in AED:** marketing 0.1832, utility 0.0576, auth 0.0576 (consistent with the 3.6725 peg).
UAE utility volume tiers: 0.0157 → 0.0149 (>100K) → 0.0141 (>1M) → 0.0133 (>4.5M) → 0.0126
(>40M) → 0.0118 (>80M). Tiers aggregate **at business-portfolio level across all WABAs**, apply
only within each band, and reset monthly.

### The MEA cost trap: authentication-international
Applies to exactly **nine countries: Egypt, India, Indonesia, Malaysia, Nigeria, Pakistan, Saudi
Arabia, South Africa, UAE** — when the sending business is based **elsewhere**. Triggers at 750K+
messages/month sent outside service windows, with 30 days' notice.
**A non-UAE business sending OTPs into the UAE pays $0.0510 instead of $0.0157, a 3.2x penalty.
Into Nigeria it is $0.0750 instead of $0.0067, an 11x penalty.**

### OPEN ITEM, close this before modelling
Meta said it would announce service rates by 1 Sep 2026, and the rule is "same as utility and
auth by market". **As of 21 Sep 2026 Meta's own calculator still returns 0 for Service in every
market queried.** By rule the UAE service rate should be **$0.0157 from 1 Oct 2026**, but the
published figure is still 0. Verify before putting it in a value case.

### Correction to a widely circulated figure
The "1,000 free service messages per business phone number" claim in third-party blogs **is not
in Meta's documentation**. Meta says *"you can open an **unlimited** number of service
conversations at no charge"* (until 1 Oct 2026). The 1,000-free figure is an **Infobip commercial
term**, not a Meta rule. Do not attribute it to Meta.

---

## 3. Template categorisation: a 3.2x cost swing decided by copywriting

- **Marketing** — awareness, sales, retargeting. Always charged.
- **Utility** — must be *"non-promotional"* **and** either *"specific to or requested by the
  user"* or *"essential or critical to the user."*
- **Authentication** — OTP only, **alphanumeric codes only**, no URLs, media or emojis,
  parameters capped at 15 characters.

**The default is against you.** Templates with *"mixed content"* (utility + marketing) or unclear
content **default to marketing**. In the UAE that is $0.0499 vs $0.0157.

**Misuse enforcement ladder, four stages:** written warning (utility→marketing changes become
instant) → rate limiting of utility volume → **utility restriction: all approved utility
templates recategorised to marketing and new utility creation disabled, 7 days, 30 for repeat** →
portfolio-level restriction across all WABAs, 30 days.
**Stage 3 is the one to model: it converts an entire utility book to marketing rates overnight,
a 3.2x cost increase across all transactional traffic in the UAE.**

### A hard platform ceiling on Arabic
WhatsApp templates support exactly **`ar`, `ar_EG`, `ar_AE`, `ar_LB`, `ar_MA`, `ar_QA`**.
**There is no `ar_SA`, `ar_KW`, `ar_BH` or `ar_OM`.** Saudi, Kuwaiti, Bahraini and Omani
localisation must ride on generic `ar` or `ar_AE`, regardless of model quality.
https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages

---

## 4. Messaging limits and the service window

**Customer service window:** opens when the user messages the business, **24 hours from their
last message**. Templates are *"the only type of message that can be sent outside a customer
service window."*
**Free entry point:** responding within 24h to a click-to-WhatsApp ad or Page CTA opens a
**72-hour** window where all message types are free. Runs independently of the CSW.

**Messaging limit tiers: 250 → 2,000 → 10,000 → 100,000 → unlimited**, at **business-portfolio
level, shared across all phone numbers**. Path off 250: verify your business, have a partner
verify it, or send 2,000 delivered template messages to unique recipients outside service windows
in a 30-day moving period with high quality rating. Auto-increase needs high quality **and**
*"in the last 7 days, your business has utilized at least half of your current messaging limit"*,
then one level within 6 hours.

**Operational note:** the WhatsApp Business Calling API requires a daily messaging limit of at
least **2,000 unique recipients** before calling can be enabled.

**Business Messaging Policy:** opt-in required. Automation must offer *"prompt, clear, and direct
escalation paths"* to a human agent, phone or email. **That is a policy requirement, not a design
preference — an assistant with no escalation path is non-compliant with Meta's own policy.**

**UNVERIFIED:** Meta Business Verification document requirements, Official Business Account /
green-tick criteria, phone-number eligibility specifics. All render client-side. Do not state
them as fact.

---

## 5. BSP markup: a 5x spread on the same Meta base

| Vendor | Model | Per-message fee | Monthly |
|---|---|---|---|
| **Twilio** | Pass-through + flat fee | **$0.005** in/out, **flat across all 140 countries** | none |
| **Gupshup** | Pass-through + flat fee | **$0.0010** | none (self-serve) |
| **360dialog** | Flat monthly per number | **$0.000** utility/auth; **+7% on marketing** via `/messages` | €49/$59 Regular, €99/$119, €249/$299 |
| **Bird** | Bundled, not decomposed | **Derived: exactly $0.0050** | none published |
| Infobip, Unifonic | Enterprise quote only | Not published | Not published |

**Bird's hidden fee, derived:** subtracting the Meta component from Bird's published totals gives
**exactly $0.0050 in every market tested** (UAE, Saudi, Nigeria, South Africa, Egypt, Kenya,
India). 

**360dialog's "zero markup" is conditional.** Their own docs: *"**Marketing Message Surcharge:**
Sending marketing content via the standard `/messages` endpoint instead of the official Marketing
Messages API results in a **7% increase over Meta's standard rates**."* The marketing site says
"zero markup on Meta fees" without that qualifier.
**Breakeven vs the flat-fee tier: $59 ÷ $0.005 = 11,800 messages per number per month.** A UAE
service deployment on one number clears that easily.

### A flat per-message fee is structurally regressive in MEA
$0.005 against the Meta base:

| Market | Markup on marketing | Markup on **utility/auth** |
|---|---|---|
| **UAE** | +10.0% | **+31.8%** |
| Saudi Arabia | +10.0% | +46.7% |
| Nigeria | +9.7% | **+74.6%** |
| Egypt | +7.8% | **+138.9%** |

**A customer-service deployment is utility- and service-heavy, not marketing-heavy, so the flat
fee lands on exactly the traffic mix in scope.** From 1 Oct 2026 every newly-chargeable service
message also picks up the BSP fee.

**The procurement question is not "do you mark up Meta?" — all four can answer that defensibly
while charging very differently. It is: "decompose your quoted rate into Meta's rate and your
fee, per country, per category."**

---

## 6. MEA vendor notes

| | Yellow.ai | Gupshup | Haptik | Infobip | Unifonic | Twilio | 360dialog |
|---|---|---|---|---|---|---|---|
| **LLM tool selection documented?** | **Yes, explicit** | Product page only, **not in dev docs** | Yes, algorithm undocumented | **Yes, explicit** | **Marketing only** | Yes, but you build the agent | N/A, sells Meta's |
| **Write primitive** | API node GET/POST/PUT/DELETE | API node, methods undocumented | Code Node (Python) + Static Step POST | API element GET/POST/PUT/PATCH/DELETE/HEAD, **mTLS, retries** | None public | `@function_tool` | REST connectors |
| **MCP** | Docs-only server; **client "coming soon"** | None native | **UNVERIFIED** | **~18 write-capable servers** | **None found** | Supported = **read-only docs** | Infra only |
| **Pricing published** | $0.99/resolution | **$0.0010/msg** | No | No | No | **$0.005/msg** | **€49/$59 per number** |
| **Gulf footprint** | Abu Dhabi (Yas Island) | **Dubai + KSA entity** | **None** | **Dubai 2012 + Riyadh DC** | **Riyadh HQ, Dubai, Cairo** | **No MEA region at all** | GCC customers, no entity |
| **Names Arabic specifically?** | **No** | **No** | **No** | Yes | **Yes, loudly** | No | No |

**Infobip has the strongest documentation and the strongest residency position.** API element
supports six HTTP verbs with mTLS client certificates and retry logic on 408/500/502/503/504.
~18 production remote MCP servers under `mcp.infobip.com/*`, OAuth 2.1, write-capable (send
templates, create/edit/delete templates, manage WhatsApp Flows, mutate CDP profiles).
**Saudi data centre in Riyadh since Jun 2024, plus an in-Kingdom AI data centre announced 5 Mar
2026** where AI workloads *"run directly within Saudi Arabia... without being transferred beyond
national borders"*. Gartner CPaaS Magic Quadrant **Leader, fourth consecutive year**.
**UAE data centre: UNVERIFIED. Saudi is confirmed, UAE is not.**

**Twilio has no MEA region at all.** Twilio Regions are **US1 (United States), IE1 (Ireland), AU1
(Australia). That is the complete list.** Against Infobip's Riyadh in-Kingdom data centre this is
the sharpest single differentiator in the scan.
Also: **Twilio AI Assistants is dead** — Developer Preview, never GA, *"retiring in July 2026"*.
The replacement is **Agent Connect**, GA 6 May 2026, a **self-hosted Python/TypeScript SDK**, not
a platform. And note: *"Twilio Agent Connect is not PCI compliant or a HIPAA Eligible Service."*
**Twilio's *supported* MCP is a documentation search tool for coding agents** — verbatim: *"It
does not execute API calls on your behalf."* Write-capable MCP exists only in `twilio-labs`,
unsupported. Do not conflate the two.

**Gupshup is the most MEA-present pure-play, with the biggest open question.** 12 offices
including Dubai and West Africa; **Saudi entity "Gupshup Technology Gulf Limited" since 21 Oct
2024**. Its Saudi launch release names **ADCB, Emaar, Talabat, Bayut** as existing UAE clients.
But its product page claims agents *"execute... ticket cancellations, appointment bookings"*
while its **AI Node docs are retrieval-only** (*"Response can be stored in JSON Variable only"*,
no tools documented). **Whether Gupshup's "Tools" is genuine function calling or journey-bound
API nodes is UNVERIFIED in developer documentation.**

**Unifonic has the strongest regional credentials and the weakest documentation.** Riyadh HQ,
Dubai and Cairo offices, CST-licensed in Saudi, and certifications including **ISO 42001 (AI
Management System) and an SDAIA AI Accreditation Certificate** — a genuinely differentiated
AI-governance position for a Gulf regulated or public-sector buyer. But the public developer
portal documents **no tool-calling schema, no function-calling reference, no agent-action API**.
Write actions are marketing-only. **UAE TDRA licence: UNVERIFIED, do not claim it. Data
residency: UNVERIFIED, the trust centre names no hosting regions.** Logo wall names **Aramex** and
**Careem** — defensible as "Unifonic names Aramex as a customer", **not** as "Aramex runs
WhatsApp AI on Unifonic".

**Yellow.ai corporate risk:** going public via SPAC with **Bluerock Acquisition Corp (Nasdaq:
BLRK)**, announced 3 Aug 2026, ~$550M pro forma equity value against **disclosed unaudited
revenue of $34M+**. Transaction not closed. Its **Lion Parcel** case study (Indonesian courier,
15,000 couriers) integrates the courier's **Order Management System to generate tickets**, and
its **Lulu Hypermarket UAE** case study is WhatsApp-primary in **English + Arabic**.

**Haptik has the best logistics depth and no MEA presence.** **Blue Dart** (Indian express
courier) automates *delivery scheduling and customer availability confirmation to optimise route
clustering* — 3.2M conversations, claimed 78% end-to-end automation. **Jio-bp Freight4U** does
genuine in-chat writes (post truck inventories, place bids, upload documents). But offices are
Mumbai, Frisco TX, Singapore only. **No UAE, Middle East or Africa office.** Hard ceiling in
their docs: *"A bot can support up to 128 actions."*

---

## 7. ARABIC: the three findings that survive hostile questioning

### 7.1 Gulf Arabic is the WEAKEST region for Arabic LLMs, not the strongest
ArabicMMLU's regional breakdown puts **UAE-contexted content last for every model tested**: Jais
48.4%, AceGPT 46.9%, BLOOMZ 29.7% — against Lebanon at 69.5% / 62.8% / 55.6%.
[INDEPENDENT] arXiv:2402.12840 (ACL 2024), Table 5.

A 2026 expert-rubric benchmark on Saudi dialect and culture (31 expert-authored prompts, 124
evaluations) puts **Claude Opus 5, Gemini 3.7, GPT-5.6 and Kimi K3 all between 42.7% and 53.1%
macro-average — none above 55%**, every model scoring negatively on at least one prompt.
Of 466 errors across 9 types, **"Ambiguous Framing" is 37.3% and hallucination only 11.2%.**
[INDEPENDENT] arXiv:2608.29990 (30 Aug 2026)

**The dominant failure mode is register and pragmatics, not factuality. And register IS the
product in customer service.**

### 7.2 Dialect routing is the weakest link, and it is measurable
- Best-in-competition **written** multi-label Arabic dialect identification: **50.57 F1**
  (NADI 2024, arXiv:2407.04910)
- Best **spoken** dialect ID: **79.8% accuracy**; dialectal ASR **35.68 WER / 12.20 CER**
  (NADI 2025)
- NADI 2026 moved deliberately to **out-of-domain** spoken dialect ID because organisers judge
  in-domain results overfit. **Results are not out — the conference runs 24-29 Oct 2026.**

**Anyone quoting >90% dialect accuracy must publish the task definition first.**

### 7.3 Arabic CX economics and safety are both measurably worse than English
- **Token inflation of 1.6x to nearly 4x vs English**, varying by tokenizer, which *"mechanically
  increases inference costs, constrains access to contextual space"*. Character normalization
  recovers up to 12.8% fertility. [INDEPENDENT] arXiv:2602.18468, AraToken arXiv:2512.18399
- **Safety alignment does not transfer.** An 801-prompt human-curated Arabic red-team benchmark
  across 8 categories found *"most models fail to defend against 50% of unsafe prompts"* —
  **including GPT-4o and Claude 3.7 Sonnet** — because English safety alignment does not carry
  over to Arabic. [INDEPENDENT] ASAS, arXiv:2608.21985 (22 Aug 2026)

### 7.4 MSA leakage: the bot answers textbook Arabic when the customer writes Khaliji
Measured at **32.63%** in untuned ALLaM-7B-Instruct, reduced to **6.21%** by LoRA on 5,466
Najdi/Hijazi instruction pairs; dialect output rate rose 47.97% → 84.21%.
[INDEPENDENT] arXiv:2508.13525 (19 Aug 2025)

The mechanism is named in AL-QASIDA (9 LLMs x 8 dialects, authors including Cohere): *"LLMs do
not produce DA as well as they understand it, not because their DA fluency is poor, but because
they are **reluctant to generate DA**"* — post-training appears to bias **against** dialect.
[INDEPENDENT] arXiv:2412.04193
**This is an alignment-induced behaviour, not a prompt bug.**

### 7.5 THE FINDING THAT LANDS HARDEST HERE
On **real logistics customer-service logs** (~30K de-identified queries from 600K records, in
English, Spanish and **Arabic**): *"translated test sets substantially overestimate performance on
noisy native queries"*, worst for long-tail intents.
[INDEPENDENT] arXiv:2603.23172 (24 Mar 2026)

**If a vendor shows you Arabic accuracy from a translated test set, the number is inflated by an
unknown margin — and this was measured on logistics support data specifically.**

### 7.6 Vendor Arabic claims, and the pattern
| Vendor | Claim | Assessment |
|---|---|---|
| **Unifonic** | *"95%+ Arabic dialect recognition"*, *"Arabic-first, trained on real GCC conversations"* | **Strongest Arabic claim in the set and entirely unbacked.** No dataset, dialect list, methodology or audit. Best open **spoken** dialect ID is 79.8%; best **written** multi-label is 50.57 F1. **Ask: 95% of what, on which dialects, against which reference?** |
| **Infobip** | Arabic is one of only five languages with built-in NLP stop words | **Most concretely evidenced.** No dialect or RTL claim. |
| **Haptik** | "100+ languages" | Makes **no specific Arabic claim**. |
| **Yellow.ai** | "500+ languages" | Makes **no specific Arabic claim** (though its Lulu UAE case study cites English + Arabic). |
| **Gupshup** | ACE LLM "100+ languages including Arabic" (2023) | **Its own docs contradict it:** Bot Studio multilingual page states *"Currently, Portuguese and Spanish are supported along with the English language"* — **no Arabic NLU in Bot Studio.** |
| **Twilio** | No Arabic marketing claim | **Honest by omission, and verifiable.** `<Say>` supports **ar-AE Polly neural voices Hala and Zayd**. |

**The pattern to put to the client: the three vendors with the loudest conversational-AI positioning
quote a large language count and never name Arabic. The two that do name it are a regional player
with an unverifiable dialect number and a CPaaS with documented but generic support. Nobody
publishes an Arabic benchmark number you can check.**

### 7.7 Arabic ASR, and a live architectural trap
| System / setting | WER |
|---|---|
| Best system, multidialectal Arabic, NADI 2025 | **35.68 WER / 12.20 CER** |
| **Whisper zero-shot, Sudanese dialect** | **78.8% WER** |
| Whisper large-v2/v3, Algerian-French-English code-switched | **0.538 WER** |
| Arabic-English code-switching (SAGE) | **31.1% WER** |
| Whisper large-v3, Levantine **child** speech | **0.66** vs <0.20 for adults |

**For a Gulf voice CX workload, off-the-shelf Whisper is not a candidate.**

Commercial coverage:
- **Azure AI Speech: 18 Arabic STT locales** (ar-AE, ar-BH, ar-DZ, ar-EG, ar-IL, ar-IQ, ar-JO,
  ar-KW, ar-LB, ar-LY, ar-MA, ar-OM, ar-PS, ar-QA, ar-SA, ar-SY, ar-TN, ar-YE). **Broadest
  documented Gulf coverage found.**
- **Deepgram Nova-3: 17 Arabic locales** incl. ar-AE, ar-SA, ar-QA, ar-KW. **But Nova-2 does not
  list Arabic, and Flux — Deepgram's purpose-built conversational model — has no Arabic at all.**
  **THE TRAP: Twilio ConversationRelay defaults to Deepgram, so an Arabic voice bot on that stack
  must be pinned to Nova-3 and forfeits Flux's turn-taking behaviour.**

### 7.8 Regional models worth knowing
- **Falcon-H1-Arabic** (TII, Abu Dhabi) — 3B/7B/34B, hybrid Mamba-Transformer, 256K context.
  **Licence is the TII Falcon License, NOT Apache 2.0.** Falcon 180B separately requires a licence
  for **"Hosting Use"** (offering shared instances or managed services via API). **If you resell
  Arabic CX as a managed service on a Falcon model, read that model's licence.** Circulating OALL
  figures of 71.47% / 75.36% appear only in a vendor blog and **could not be verified — do not
  slide them.**
- **Jais 2** (Inception/G42, MBZUAI, Cerebras, Abu Dhabi) — 70B, largest open Arabic-centric LLM
  trained from scratch. **Most CX-deployable regional model:** in the **Azure AI Foundry catalog**
  under the Core42 collection with serverless inference, Entra ID auth, Content Safety, and
  **Data Zone / Regional deployment types for residency control**. Caveat: it is a partner model,
  **so support and SLA come from the provider, not Microsoft.**
- **ALLaM** (SDAIA, Saudi) — deployable via IBM watsonx.ai as `allam-1-13b-instruct`, *"Deploy on
  demand only"*. **Lower hallucination than multilingual models** (AraHalluEval, arXiv:2509.04656).
- **Fanar** (QCRI, Qatar) — Fanar-27B from a Gemma-3-27B backbone, **CC BY 4.0**, full stack with
  FanarGuard safety and Aura speech. Strongest sovereignty posture of any model here. The same
  paper notes **Arabic is ~0.5% of available web data.**

### 7.9 Benchmark quality is itself contested
**QIMMA** (TII-affiliated) was built because established Arabic benchmarks have *"systematic
quality issues"*. **Treat any pre-2026 Arabic benchmark number as contested by this paper.**
Also note **AraGen's judge is Claude-3.5-Sonnet**, so any AraGen ranking is judge-coupled to one
frontier vendor. Say this before the client does.
**ArabicMMLU-Pro: UNVERIFIED** — arXiv full-text search returned zero results for that string.

**The one Arabic CX-tone benchmark that exists:** **ADAB**, an Arabic politeness benchmark, 10,000
samples from social media, e-commerce and **customer-service platforms**, MSA + Gulf + Egyptian +
Levantine + Maghrebi, 16 politeness feature categories, inter-annotator κ = 0.703.
[INDEPENDENT] arXiv:2602.13870 (LREC 2026). That this is the closest thing to a native Arabic
CX-tone benchmark **is itself the answer** to "is there a good Arabic customer-service benchmark?"

### 7.10 RTL rendering and Arabic NER: UNVERIFIED
No independent paper documenting RTL failure in Arabic conversational AI was found. It is a
genuine engineering concern (bidi algorithm with mixed LTR order numbers, URLs and tracking codes
inside RTL text) but **present it as an untested integration risk, not a documented finding.**
No Arabic-specific NER degradation rate is documented either. Do not assert a number.

---

## 8. UAE regulatory position, handled carefully

**Verified:**
- **PDPL, Federal Decree-Law 45/2021**, effective 2 Jan 2022, *"prohibits the processing of
  personal data without the consent of its owner"* and sets cross-border transfer requirements.
- **Consumer Protection, Federal Law 15/2020** *"prohibits suppliers from using"* consumer data
  *"for marketing."*
- Free zones are separate regimes: DIFC Data Protection Law 5/2020, Dubai Data Law 26/2015.
- **TDRA Consumer Protection Regulations v2.0 (25 Jul 2023)** — I downloaded and searched the full
  74-page text. **It binds "Licensees", the licensed telecom operators, not third-party OTT
  senders.** Its messaging provisions concern SMS/USSD subscription services and operator conduct.
  **It does not regulate a business sending WhatsApp messages to its own customers.**
- TDRA's only consumer-facing channel on unsolicited messaging is a complaint service, "SMS Spam",
  with no published rules or penalties.

**UNVERIFIED, state explicitly rather than inferring:**
- **Whether the UAE requires a local aggregator or TDRA approval for A2P messaging.** TDRA's full
  published regulations index contains **no A2P, bulk-messaging, sender-ID-registration or
  value-added-services regulation**. The sender-ID registration practice operated by e& and du is
  a commercial/operator practice; no TDRA instrument mandating it was found. Whether any of it
  extends to OTT WhatsApp traffic is unknown — and since WhatsApp is IP-borne rather than carried
  as SMS, extension should not be assumed either way.
- **TDRA VoIP policy.** No VoIP regulatory policy document appears on TDRA's index. **Do not
  assert either a restriction or its removal.**
- **PDPL Executive Regulations** — the government portal does not state they have been issued.

**Verified and relevant to voice:** WhatsApp **business-initiated** calling is unavailable in
**United States, Canada, Egypt, Vietnam, Nigeria**. **The UAE is not on the exclusion list.**
User-initiated calls are free everywhere Cloud API operates; business-initiated bills in six-second
pulses, rate cards in AED and SAR.

---

## 9. Open items to close before presenting

1. **Meta's service-message rate card for 1 Oct 2026.** Rule says UAE → $0.0157; Meta's calculator
   still returns 0. **Confirm before modelling.**
2. Twilio help-centre notice "Changes to WhatsApp's Pricing (October 2026)" — unretrieved.
3. **Gupshup's "Tools"** — product page vs dev docs contradiction. Changes the entire agentic
   assessment of the most MEA-present pure-play vendor.
4. **Unifonic's "95%+ Arabic dialect recognition"** and its write actions. Both marketing-only,
   both central to its pitch.
5. Haptik MCP — never searched, UNVERIFIED on doc coverage alone.
6. **Yellow.ai MCP-client contradiction** — Tools page says "coming soon", Voice page lists MCP as
   supported, same doc set, same date.
7. Meta Business Verification requirements and green-tick criteria — render client-side.
8. **UAE A2P and VoIP regulatory position** — needs legal counsel or a direct TDRA enquiry, not
   more web research.
9. Live OALL v2 standings, Falcon-H1-Arabic OALL scores, Jais 2 benchmark table — all blocked by
   JS shells or 401s. Open in a browser before quoting any Arabic leaderboard number.
10. Infobip UAE data centre (Saudi confirmed, UAE not).
