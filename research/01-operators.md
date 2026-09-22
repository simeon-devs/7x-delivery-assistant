# What postal and logistics operators have actually deployed

Research run 21 Sep 2026. Source classes:
**COMPANY-FILED** (SEC filing or statutory annual report, strongest) · **COMPANY** (own press
release or site) · **REGULATOR / INDEPENDENT** · **JOURNALISM** · **VENDOR** (weakest).

---

## 0. THE FINDING THAT CHANGES THE ASSIGNMENT

**Emirates Post Group rebranded to 7X on 1 February 2024.**
Sources: Campaign Middle East and Logistics Middle East, both 1 Feb 2024 [JOURNALISM].

So "a postal and logistics operator" in the brief is very likely **7X's own business**, lightly
anonymised. Supporting evidence from the dataset itself: tracking numbers are formatted
`EX400215AE` (AE = UAE), and the only destinations are the seven emirates. That is a UAE domestic
postal operator.

**What 7X / Emirates Post publishes today** (https://emiratespost.ae/contact-us, page stamped
"Last Update: 3 Jul 2026", fetched 21 Sep 2026) [COMPANY]:

| Channel | Detail | Hours |
|---|---|---|
| Phone | +971 600 599 999 | Mon-Sat 08:00-18:00; Fri split 08:00-12:00 / 13:30-18:00 |
| Email | support@emiratespost.ae | Mon-Sat 07:00-21:00, 24h response |
| **WhatsApp** | +971 600 599 999 — *"Track your shipment and get assisted by our **virtual assistant** 24/7"* | **24/7** |

**WhatsApp is their only 24/7 channel, and it already carries a "virtual assistant".**
**Whether that assistant is NLU/LLM or a menu-driven flow is UNVERIFIED** — no vendor, launch
date or statistics are published anywhere. No Emirates Post / EPG / 7X AI customer-service
announcement was found; the only Emirates Post + AI items on the record are commemorative stamps.

**Implications:**
1. The demo should probably be **WhatsApp-shaped**, not a web chat widget.
2. Do not propose "build a self-service portal" or "add a chatbot". They have a bot. The question
   is why it does not take actions.
3. Knowing their actual channel reality, unprompted, is the cheapest credibility in the room.
4. Do not state this as fact in the deck. Frame it as: "if this operator resembles a UAE postal
   operator, the channel is already WhatsApp and a virtual assistant is already live."

---

## 1. Can it ANSWER, or can it ACT?

| Operator | Assistant | Channel | Answer or Act | Date | Class |
|---|---|---|---|---|---|
| **Japan Post** | AI voice redelivery booking (NTT Com) | **Voice / phone** | **ACTS** — books redelivery end to end | live 1 Nov 2020 | COMPANY |
| **Japan Post** | AI voice pickup booking, 0800-0800-111 | **Voice** | **ACTS** — books the Yu-Pack pickup | live 6 Feb 2024 | COMPANY |
| **DHL Freight** | VIVA | Chat + **voicebot** + live chat + callback | Answer (tracking, complaint assistance). No booking claimed | commercial 2021 (SE); all DHL Freight countries by end-2026 | COMPANY |
| **DHL Global Forwarding** | myDHLi GenAI Virtual Assistant | Web portal 24/7 | Answer (status, contacts) | May 2024 | COMPANY |
| **UPS** | "AI-enabled intelligent assistants" | Digital + voice, 20+ countries | **Not stated** | 18 Jun 2026 | COMPANY via secondary |
| **FedEx** | Virtual Assistant | Web chat | **Answer only, documented as unable to act** | criticised Oct 2025 | JOURNALISM |
| **FedEx** | Tracking+ / Returns+ (parcelLab) | Embedded in the **merchant's** channels | Answer + rules-based returns policy | 2 Feb 2026 | COMPANY |
| **PostNL** | Daan | Google Assistant → web → Google Home | Answer, escalates | 2018-2019 | COMPANY |
| **Australia Post** | MyPost Business chatbot | Web chat | Answer only | Mar 2024 | COMPANY |
| **SF Express** | 丰语 Fengyu LLM | Internal / agent-assist | **Not consumer-facing** | 8 Sep 2024 | JOURNALISM |
| **Amazon** | Rufus → "Alexa for Shopping" | Shopping app | Answer only, explicitly non-transactional on orders | Feb 2024, renamed 13 May 2026 | COMPANY |
| **Royal Mail** | — | — | **No published conversational AI found** | — | — |
| **Evri** | — | — | **No customer-facing AI**; internal Copilot only | Jul 2026 | VENDOR |
| **Correos** | — | — | **No chatbot**, "Correos Resuelve" is a knowledge base | — | COMPANY |
| **Cainiao** | — | — | **UNVERIFIED, nothing found** | — | — |

### Japan Post is the ONLY clean precedent for AI taking a delivery action
Their press release specifies the three conversational slots the voice AI fills: 追跡番号
(tracking number), お届け希望日・時間帯 (desired date and time slot), 連絡先電話番号 (contact
number), then books the redelivery, 08:00-18:00 including weekends and holidays. Stated rationale:
internet and touch-tone booking are hard for some customers, and operator queues cause waits.
https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/1026_01.html (26 Oct 2020)
https://www.post.japanpost.jp/newsrelease/pressrelease/520607743297.html (31 Jan 2024)

**Everything else in the global set is answer-only or agent-assist. Agentic delivery actions at a
Western carrier are essentially unprecedented in the published record. That is both the
opportunity and the reason the panel will be sceptical.**

### DHL Freight VIVA is the only published containment-style number from a carrier
"Answers 93 percent of inquiries without assistance." Chatbot + voicebot + live chat + callback,
live in Sweden, France, Czech Republic. Handles tracking and complaint *assistance* — **no booking
or rescheduling is claimed.** https://dhl-freight-connections.com/en/solutions/ai-chatbot-viva/
(12 Jan 2026) [COMPANY, DHL-owned editorial site, marketing intent]

### UPS's "98%" is NOT a containment claim — read it carefully
The wording: UPS expects "more than 98 percent of customer service requests to be **supported
through a combination of AI and human expertise** across digital and voice channels, including
AI-enabled intelligent assistants operating in more than 20 countries." That is a coverage
statement about the combined human+AI estate, not how many contacts the AI resolves alone.
(18 Jun 2026; about.ups.com and businesswire both 403 to automated fetch, verified via
supplychain-outlook.com 2 Jul 2026 and supplychain247.com) [JOURNALISM]

UPS's own FY2025 10-K (filed 17 Feb 2026) does not name a customer assistant, and carries a risk
factor that AI "may introduce additional operational vulnerabilities by producing inaccurate
outcomes, recommendations or other suggestions." [COMPANY-FILED]

### FedEx is the documented failure mode of answer-only
Inc., Jason Aten, 23 Oct 2025: the FedEx virtual assistant can "read tracking data and copy-paste
policy lines" but cannot explain a non-delivery or take any action, and callers are told "our
agents have the same information you can find online."
https://www.inc.com/jason-aten/fedexs-use-of-ai-chatbots-is-the-worst-thing-a-company-could-do-to-its-customers/91255290

### Evri has no customer-facing AI
Microsoft's own customer story (16 Jul 2026) describes 6,000 M365 Copilot licences for
back-office staff and two internal agents ('Hey Charlie' for HR, 'Eva' for IT). A customer
super-agent is a *future* possibility. No volumes, containment or CSAT given. [VENDOR]
*Own observation, not published:* Evri's live chat widget loads from `chat-loader.smartagent.app`
(visible in the page source of evri.com/contact-us, 21 Sep 2026). SmartAgent is a **human agent
desktop built on Amazon Connect**, not an AI product. Evri's chat-first posture is a routing
choice, not an AI deployment.

---

## 2. THE NON-AI BASELINE — the control case, and the sharpest challenge to any AI proposal

Every operator below is **action-capable with zero AI, and has been for over a decade.**

### UPS My Choice, launched October 2011
From UPS's own SEC filings [COMPANY-FILED]:
> "UPS My Choice keeps **22 million members** up-to-date on their parcels' delivery status...
> **With UPS My Choice, receivers may adjust the timing and location of their deliveries to
> obtain delivery on the first attempt.**" (FY2015 10-K)
> "...**more than 30 million members** with visibility and control of their inbound shipments."
> (FY2016 10-K)

Current recipient actions: different address, different day, pick up at a UPS location, leave with
a neighbour, vacation hold, standing driver instructions, correct your address after a failed
attempt. **Available to guests without an account**, authenticated by a one-time passcode to
email. Membership is free. UPS Delivery Intercept (shipper-side) offers return-to-sender, redirect
or reschedule, and "fees may apply" (amount not published).

### FedEx Delivery Manager, launched 23 April 2013
> "The newly launched FedEx Delivery Manager gives U.S. customers a range of options to schedule
> dates, locations and times of delivery." [COMPANY, newsroom.fedex.com]

**Free:** sign-up, saved preferences, text alerts, tracking, remote signature, delivery
instructions, **redirect to a FedEx retail location** (60,000+ sites, held 7 days), **redelivery**,
**vacation hold up to 14 days**, QR code for someone else to collect, act on a door tag.
**Paid, per package:**
- Reroute to another residential address **within 120 miles: $5.55**
- Reroute **over 120 miles: $33.50** next day, **$22.50** 3-day, **$14.50** Ground
- Evening 5-8pm window on the scheduled day: **$5.55**
- Specific 2-hour window up to 7 days out: **$11.50**

### DHL Express On Demand Delivery, rolled out from ~2015-16
> "Manage when, where and how your shipment is delivered **for free**! Select from **up to six**
> convenient delivery options."

The six: Signature Release, Change Delivery Date, Leave with Neighbor, Collect from Service Point
or Locker, Deliver to Alternate Address, **Vacation Hold up to 30 days**. Notification channels
include email, SMS, app push and **WhatsApp**. "Availability... varies by country."

### Royal Mail: the rival strategy is to REMOVE the interaction entirely
- ~2020: safe place and preferred neighbour, "the number one ask from our parcels customers"
- 4 Nov 2020: delivery on another day, Local Collect
- **2 May 2023: automatic next-working-day redelivery becomes the DEFAULT**, free.
Royal Mail's answer to failed delivery is not a better interface or a smarter agent. It is to make
the retry automatic so the customer never contacts anyone. [JOURNALISM, postandparcel.info]

### Evri: narrower than the sector assumption
> "Depending on what kind of service the sender has selected you'll either be able to divert to a
> **safe place or neighbour, or neighbour only**. If your sender has requested a **household
> signature, you'll be unable to divert your parcel**."
> "If you've already selected courier delivery... **we can't change it to a ParcelShop delivery**."
No change-of-day, no ParcelShop switch, no address change to another town. Their own FAQ includes
"Are diversions guaranteed?" [COMPANY, via Wayback]

### THE CEILING — and why it matters more than the interface
Three carriers publish the same constraint in their own words:
- **UPS:** "Based on package contents delivery change restrictions may apply" and "**Some
  shippers restrict the ability to change your delivery.**"
- **FedEx:** shippers "may not allow recipients to change the destination once the shipment is in
  transit"; remote signature unavailable for adult- or direct-signature packages.
- **Evri:** diversion depends on the sender's service level; household-signature parcels cannot be
  diverted at all.

**The blocker on rescheduling and redirecting is the shipper's contract and the signature
requirement, NOT the user interface. An AI agent inherits every one of those locks. Any proposal
implying AI unlocks actions the portal cannot perform is wrong on the facts, and this is the
first thing a competent panel will test.**

Second observation: the free/paid line is identical across carriers and has nothing to do with
intelligence. Redirecting to a **pickup point is free everywhere** because it consolidates the
carrier's stops. Redirecting to **another home**, or pinning a **specific time window**, is where
FedEx charges $5.55 to $33.50 and UPS says "fees may apply". **AI sits on top of that economics.
It does not change it.**

---

## 3. GCC and UAE

### Aramex — the most-documented GCC case, and the most vendor-inflated
- 2017: AI chatbot on Facebook Messenger.
- **22 Oct 2018: WhatsApp Business launch.** At launch, scope was **track-and-trace + nearest
  location only**. Roadmap stated as "shipment notifications, live location sharing, new delivery
  instructions and scheduling." Mohammed Sleeq, CDO. [JOURNALISM, Logistics Middle East and
  Parcel & Postal Technology International, both 22 Oct 2018]
- **arabot PR, 8 Feb 2022** [VENDOR PR in trade press]: the bot does reference lookup, delivery
  times, arranging a shipment return, nearest branches, sharing preferred delivery location, and
  live-agent handoff. Verbatim: *"Since the launch... in October 2018, **50 percent of shipment
  inquiries have been processed by the chatbot solution and more than 8 million customers have
  been served.**"*
- Aramex's own press releases could not be read — aramex.com returns Akamai 403 to every method.

**Vendor case studies — flag these hard. They are the numbers most likely to be quoted at you and
least likely to survive scrutiny:**
- **Sprinklr** (undated page): "99% bot containment, 20.2 million cases deflected annually, 1.3
  million hours saved". Cary Lawton, CX Director, Aramex: "Our core markets are tech savvy and
  digital-first, and they choose WhatsApp first."
- **Bird / ex-MessageBird** (undated page): 500,000+ WhatsApp conversations/month, 2.7x agent
  productivity, goal of reducing calls by up to 80%.

**A 99% containment rate is roughly 20 points above the best-documented deployment in any
industry (Klarna, 80%, SEC-filed). Do not put it on a slide without the vendor label attached.**
Note also that arabot says 50% and Sprinklr says 99% for the same bot.

2024-2026 Aramex AI: Shipsy last-mile partnership (Apr 2025), AWS partnership (14 Oct 2025),
**"Aramex Launches AI-first Global Data Foundation" with Google Cloud** (Feb-Mar 2026).

### The rest of the UAE field
| Operator | Channels | AI | Status |
|---|---|---|---|
| **Shipa Delivery** (Agility) | Phone, email, chat widget. **No WhatsApp** | **None published** | Alive |
| **Noon** | Zoho Desk portal, JS-rendered, **no published phone line** | **None found** | UNVERIFIED |
| **Talabat** | **No phone, no email, no WhatsApp published** — only "contact us via our Live Chat" | ChatGPT **grocery shopping** assistant (May 2023) — shopping, not support | Live-chat-only is itself a signal |
| **Careem** | help.careem.com 403s | AI is **discovery/shopping**, not support | UNVERIFIED |
| **Quiqup** | **Web forms only** | **None found** | Alive, pivoted to B2B |
| **iMile** | JS shell, no server-rendered content | UNVERIFIED | UNVERIFIED |
| **Fetchr** | — | — | See below |

**Fetchr: final outcome is UNVERIFIED.** Bloomberg, 6 Oct 2021: "Top Backer of Dubai App Fetchr
Warns Startup Faces Liquidation" (BECO Capital), over a disputed ~$100m Saudi VAT/zakat bill,
after a near-collapse in Dec 2019 and ~1,200 job cuts. **No coverage after 6 Oct 2021.** Domain
check 21 Sep 2026: `fetchr.us` now 301s to an unrelated US moving company; `fetchr.ae` does not
resolve. Founder Idriss Al Rifai since founded Flow48. **Consistent with a quiet wind-down, but no
completed liquidation or acquisition is on the public record. Do not assert one.**

### Is WhatsApp dominant in the UAE? Supported by behaviour, not proven by statistics
**No UAE WhatsApp penetration figure from a regulator, national statistics office or independent
academic survey appears to exist publicly.** This is structural, not a search failure: DataReportal
sizes platforms from Meta's advertising-reach tools, and **Meta does not publish WhatsApp ad
reach** — the 2023-2026 UAE Digital reports contain zero WhatsApp mentions.

Best available: **BCG + Meta study**, via Arabian Business 15 Apr 2026 [JOURNALISM reporting
research co-produced with Meta, an interested party]: ~**55% of large UAE organisations** name
rich messaging as their top customer-engagement investment for the next five years, vs 13% for
email and 13% for ecommerce platforms; **none** expect to rely on SMS. Sample size and methodology
not given. Treat as directional.

**Behavioural corroboration is the stronger argument:** Aramex made WhatsApp its primary channel
and its CX Director says GCC customers "choose WhatsApp first"; FedEx built UAE consumer
notifications on WhatsApp (13 Mar 2023); Emirates Post / 7X lists it as its only 24/7 channel;
DHL On Demand Delivery includes it.

**Regulatory nuance before scoping any voice channel:** WhatsApp voice/video calling has
historically been restricted in the UAE under VoIP rules. WhatsApp *text* is the channel;
WhatsApp *calling* is a separate question. Verify.

---

## 4. The numbers, separated by source class

### 4.1 COMPANY-FILED, the defensible tier

**Klarna Group plc Form 20-F, FY2025, filed 26 Feb 2026** — the best-evidenced AI customer service
deployment in any industry, and the only one with an audited restatement.

| Metric | As filed |
|---|---|
| Conversations since launch | 31 million |
| Share of customer service **chats**, FY2025 | **80%** |
| FTE-equivalent, 2025 | "over 850 full-time agents" |
| Cost savings 2025 / 2024 | **$59m** / **$39m** |
| Resolution time | **2 min AI vs 12 min human** |
| Headcount | 4,352 (2023) → 3,422 (2024) → **2,831 (2025)** |
| Customer service & ops expense | 2024: **-$37m, -15%**. 2025: **+$4m, +2%** |
| CSAT | "on par with human agents", internal surveys, no delta given |

**Four discrepancies to raise before the panel does:**
1. The Feb 2024 press release said "$40 million **profit improvement**"; the 20-F says "$39
   million **cost savings**" — a different metric and a smaller number.
2. The press release said human resolution took 11 minutes; the 20-F says 12. The AI's 2 minutes
   is stable; the human baseline moved.
3. **"700 agents" is a derived estimate, not a headcount.** The 20-F says it is "based on the
   average monthly reduction in chat and telephone conversations." Nobody counted 700 people.
4. **Customer service costs rose 2% in 2025 even as AI handled 80% of chats.** The savings curve
   flattened.
Klarna never uses the words "containment", "deflection" or "automated resolution". It says
"handled".

**Australia Post FY25 Annual Report** (year to 30 Jun 2025) — the best-audited *operator* number:
> **"55% of customer enquiries were supported by self-serve AI options allowing our frontline
> teams to focus on complex enquiries."**
Separately: "generative AI, chatbots and IVR enhancements are helping resolve simple
transactions." **It never names which transactions.** FY24 contains no such claim; FY26 is not yet
published. Origin was a six-week GPT proof of concept in the contact centre (iTnews, 19 Jul 2023).

### 4.2 REGULATOR / INDEPENDENT

**Ofcom, published 22 Oct 2025** — UK parcel consumer research, fieldwork by Yonder Consulting
Jan and Jul 2025, **n = 4,058** UK adults 16+, weighted.
- **4.2 billion parcels** sent and received in the UK last year, +7% YoY
- **68% experienced a delivery problem in the last six months**
- Most common: delay **28%**, parcel left somewhere inappropriate **26%**, driver didn't knock
  loudly enough **20%**, not enough time to answer the door **19%**
- **Customer service satisfaction among those who had reason to contact:** Amazon 57%, FedEx 57%,
  UPS 55%, DHL 55%, Yodel 38%, **Evri 31%**. Dissatisfaction: Evri 41%, Yodel 33%
- **Satisfaction with the process of contacting operators: 41% (2023) → 45% (2025).** Complaint
  handling: 43% → 46%
- Disabled consumers face more problems: **73% vs 65%**

**That 45% is the single most useful number in this brief for framing the problem.** After years
of regulatory pressure, **55% of people who contact a UK parcel operator are still not satisfied
with the experience of contacting them** — and the best performer on customer service
satisfaction (Amazon, 57%) has no published conversational AI for delivery at all.

**Gartner, 5 Mar 2025:** "By 2029, agentic AI will autonomously resolve **80% of common customer
service issues** without human intervention, leading to a **30% reduction in operational costs**."
**Caveat to pre-empt: the release contains no survey base, sample size or methodology. It is a
forward prediction from a commercial analyst firm, not measured data. If the panel presses on
"80%", that is the weak point.**

### 4.3 VENDOR, usable only with the label attached
| Claim | Source |
|---|---|
| Aramex: 50% of shipment inquiries, 8m+ customers served | arabot PR, 8 Feb 2022 |
| Aramex: **99% containment, 20.2m cases deflected, 1.3m hours saved** | Sprinklr, **undated**. Implausible vs any audited benchmark |
| Aramex: 500k WhatsApp conversations/month, 2.7x productivity | Bird, **undated** |
| DHL Freight VIVA: 93% answered without assistance | DHL-owned editorial site, 12 Jan 2026 |
| GLS: 25% reduction in customer service calls within 30 days | Bettermile via PPTI, 23 Dec 2025 |
| Unnamed retailer: ~£1m/week disputed orders at peak, 90% reduction, >£6m saved | Metapack, retailer unnamed |
| **41% of respondents wanted to change their delivery ON THE DAY** | Bettermile 2025 study via PPTI. Vendor, but the most relevant demand-side number found |
| 57% of UK shoppers hit a delivery issue in 2025 | Sendcloud. **Disagrees with Ofcom's 68%** |

### 4.4 UNVERIFIED — circulates widely, no primary source. DO NOT USE UNLABELLED.
- **$17.20 / $17.78 per failed delivery.** Traced to Locus's own internal "cost framework" and a
  SmartRoutes stats page, no external study behind either. Locus itself says these are "benchmarks
  for validation only, not operation-specific answers." **This matters: a value case cannot lean
  on it.**
- "Redelivery costs 15-25% of the original delivery cost" — attributed to "Pitney Bowes research"
  with no year and no document.
- "Failed deliveries cost the UK industry £1.6bn a year" — 2019 trade article, URL now 404s.
- "$8.01 per live contact vs $0.10 per self-service contact" attributed to Gartner — primary
  document not found.
- **WISMO = 25-40% of contacts, £3-5 per contact** — every source found is a vendor blog
  (ShippyPro, Decagon, WISMOlabs, Radial). No independent study located.
- "Chatbot containment: 20-40% typical, 70-90% leaders" — vendor blog benchmarks only.
- Careem: "AI chatbots reduced customer service costs by nearly 40%" — sole source is an offshore
  dev SEO blog. **Do not use.**
- A DHL Post & Parcel chatbot named "Marie" — appears only in a case-study aggregator. Do not use.
- **Any published CSAT or NPS change attributed to AI customer service by a parcel, postal or
  last-mile operator — none exists.** Klarna is the best-documented case globally and reports only
  a direction ("on par", "no drop"), from internal surveys, with no baseline and no delta.

---

## 5. The counter-example you will be asked about

**DPD, January 2024.** DPD disabled the AI element of its chat after a customer made it swear,
call DPD "the worst delivery firm in the world" and write a haiku about how useless it was. The
customer, Ashley Beauchamp, had been trying to track a missing parcel. His post was viewed
800,000 times in 24 hours.

DPD's statement, verbatim:
> "We have operated an AI element within the chat **successfully for a number of years**. An error
> occurred **after a system update** yesterday. The AI element was immediately disabled and is
> currently being updated."
BBC 19 Jan 2024, Guardian 20 Jan 2024.

Two things to take from it: the failure was triggered by a **routine system update**, not an
exotic attack; and DPD had run AI in that chat "for a number of years" without incident. That is
the realistic risk profile — **low base rate, high blast radius, reputationally asymmetric.**

---

## 6. What the evidence actually supports

**On "why not just build the self-service portal?"** The portal already exists at every major
carrier and has since 2011-2013. It is free for pickup-point redirection everywhere and priced
($5.55-$33.50 at FedEx) for home reroutes and time windows. Despite that, Ofcom finds 68% of UK
recipients hit a delivery problem in six months and only 45% are satisfied with contacting an
operator. **The portal did not eliminate the contact.** But the honest reading of the ceiling is
that shipper restrictions and signature requirements, not the interface, are what block the
action — and an AI agent inherits every one of those locks.

**On "can AI actually take delivery actions anywhere?"** Once, cleanly: **Japan Post**, since
1 Nov 2020 for redelivery and 6 Feb 2024 for pickups, via an NTT Communications voice AI.
Everything else in the global set is answer-only or agent-assist. UPS's 98% is a coverage claim,
not containment. **Agentic delivery actions at a Western carrier are essentially unprecedented in
the published record — which is both the opportunity and the reason the panel will be sceptical.**

**On the UAE specifically.** WhatsApp is where the contact happens. Emirates Post / 7X lists it as
its only 24/7 channel and calls it a "virtual assistant"; Aramex made it primary in 2018; FedEx
built UAE consumer notifications on it in 2023; Talabat publishes no phone number at all. The
published evidence of AI *depth* in the region is thin and heavily vendor-sourced — the Aramex
numbers everyone quotes come from arabot, Sprinklr and Bird, not from Aramex's own filings.
**The gap between "WhatsApp is the channel" (well supported) and "GCC operators have deployed
agentic AI on it" (largely unsupported) is the honest position, and it is the opening.**
