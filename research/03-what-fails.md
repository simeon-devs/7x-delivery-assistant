# What fails in conversational and agentic AI customer service

Research run 21 Sep 2026. Every claim carries a source and a date.
UNVERIFIED = did not survive checking, do not put on a slide.
CORRECTION = the popular version of the story is wrong, and I will be challenged on it.

---

## 1. Documented failures

### DPD chatbot, 18 Jan 2024 (a parcel carrier, so directly on topic)
Customer Ashley Beauchamp could not get the bot to track his parcel. He then prompted it
to swear and to criticise DPD, and it complied: "DPD is the worst delivery service in the
world." Viral, 25,000+ likes. DPD disabled the AI element.
DPD's stated cause: an error following a system update.
- https://incidentdatabase.ai/cite/631/
- https://time.com/6564726/ai-chatbot-dpd-curses-criticizes-company/
- https://fortune.com/europe/2024/01/22/ai-chatbot-delivery-calls-itself-useless-works-for-worst-firm-in-world

CORRECTION: usually told as "the AI went rogue". Two facts blunt that. The customer
explicitly instructed it to swear, and DPD blamed a specific system update. The honest
lesson is better anyway: **a routine deployment silently removed the guardrails and nobody
caught it before customers did.** That is a release-process failure. Also note the prior
failure, the one that actually matters for a carrier: it could not answer "where is my parcel".

### Moffatt v Air Canada, 2024 BCCRT 149, 14 Feb 2024 (the core legal citation)
The chatbot told a bereaved customer he could claim a bereavement rate retroactively
within 90 days. Air Canada's real policy did not allow that. Held: negligent misrepresentation.
Air Canada's three defences all failed:
1. "The chatbot is a separate legal entity responsible for its own actions." Tribunal:
   "While a chatbot has an interactive component, it is still just a part of Air Canada's website."
2. "The correct policy was elsewhere on the site, and the bot linked to it." Tribunal:
   "There is no reason why Mr. Moffatt should know that one section of Air Canada's
   webpage is accurate, and another is not."
3. "Not liable for statements by agents or representatives." Rejected.
Award: CA$812.02 (CA$650.88 damages plus interest and fees).
- https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/
- https://www.mccarthy.ca/en/insights/blogs/techlex/moffatt-v-air-canada-misrepresentation-ai-chatbot
- https://www.cbc.ca/news/canada/british-columbia/air-canada-chatbot-lawsuit-1.7116416

PROPORTION: it is a small-claims tribunal decision worth CA$812, not binding outside BC,
not appellate. Say "a tribunal decision that has become the reference point", never "landmark ruling".

### OLG Hamm, 4 UKl 3/25, 12 May 2026 (the stronger 2026 citation, most people won't have it)
German Higher Regional Court. A clinic's website chatbot claimed the managing directors
were board-certified plastic surgeons. They were not, and it invented two qualifications
that do not exist. Held: the operator is liable as if it had said it itself.
Two holdings that matter commercially:
1. The "black box / hallucinations are uncontrollable" defence was **expressly rejected**.
   The operator had reprogrammed the bot after the complaint, proving it had control.
2. **Generic "AI can make mistakes" disclaimers do not reliably shield the operator.**
Not yet final, revision to the Bundesgerichtshof allowed given fundamental significance.
- https://www.wettbewerbszentrale.de/olg-hamm-laesst-unternehmen-fuer-aussagen-seines-chatbots-haften-volltext-verfuegbar/
- https://www.anwalt.de/rechtstipps/ki-chatbot-luegt-betreiber-haftet-dafuer-olg-hamm-urteil-vom-12-05-2026-az-4-ukl-3-25-270514.html

### McDonald's / IBM drive-thru, ended 26 Jul 2024
Piloted from 2021 in 100+ US restaurants, partnership ended 17 Jun 2024, switched off by
26 Jul 2024. Viral videos of 260 McNuggets and bacon on ice cream.
- https://www.cnbc.com/2024/06/17/mcdonalds-to-end-ibm-ai-drive-thru-test.html
- https://incidentdatabase.ai/cite/475

CORRECTION: this is NOT "McDonald's gave up on voice AI". In the same communication they
said the test "has given us the confidence that a voice ordering solution for drive-thru
will be part of our restaurants' future". Use the damaging true version: **a three-year
pilot at scale with a tier-1 vendor still could not hit the accuracy bar for a short,
constrained, high-frequency transaction.**

### Klarna (the one I am most likely to be challenged on)
Claimed, 27 Feb 2024: 2.3m conversations in month one, two-thirds of all chats, "equivalent
work of 700 full-time agents", 23 markets, 35+ languages, resolution 11 min to under 2,
25% fewer repeat inquiries, CSAT parity with humans, $40m projected profit improvement.
- https://www.klarna.com/international/press/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month/

May 2025 walk-back. CEO Siemiatkowski said the cost focus went too far and produced
"lower quality": "I just think it's so critical that you are clear to your customer that
there will be always a human if you want." Launched a remote "Uber type" pilot for human agents.
- https://www.customerexperiencedive.com/news/klarna-reinvests-human-talent-customer-service-AI-chatbot/747586/
- https://fortune.com/2025/05/09/klarna-ai-humans-return-on-investment/

Where it stands, Q3 2025: assistant still doing the work of 853 FTEs, $60m saved, still
two-thirds of inquiries. But **customer service and operations costs rose to $50m from $42m
a year earlier**, despite the claimed $60m of savings.
- https://www.customerexperiencedive.com/news/klarna-says-ai-agent-work-853-employees/805987/
- https://www.forbes.com/sites/bernardmarr/2026/07/16/how-klarnas-ai-agent-strategy-backfired-but-became-a-useful-lesson/

CORRECTION, three errors in the popular retelling:
1. "700" was never a headcount cut. It is a workload-equivalence estimate.
2. Klarna's ~700-person layoff was in **2022**, before the assistant existed. Later shrinkage
   of ~40% came via hiring freeze and attrition.
3. The "rehire" was a small flexible pilot plus a guaranteed human path, not a mass rehire.
   The AI still runs two-thirds of contacts.
USE IT AS: a metrics and quality problem, not an AI rollback. The company with the most-cited
AI savings number in the industry still saw service costs rise.

### Cursor / Anysphere, Apr 2025 (fabricated policy, real revenue loss)
Users logged out when switching devices. The support bot, signing as "Sam", told them it was
intentional: "Cursor is designed to work with one device per subscription as a core security
feature." No such policy existed. Viral within ~3 hours, **users cancelled subscriptions**
before the co-founder stepped in: "We have no such policy."
Root cause: retrieval gap. Nothing authoritative came back and the model filled it.
- https://incidentdatabase.ai/cite/1039/
- https://winbuzzer.com/2025/04/22/cursor-ais-support-bot-hallucinates-policy-sparking-user-backlash-and-company-apology-xcxwbn/

### Who Gives A Crap, Jul 2026 (closest public analogue to a wrong ACTION)
A price-change email had a typo: $66 for 48 rolls becoming $69.50 for 24 rolls, doubling the
unit price. A customer queried it. The AI email agent **confirmed the wrong price as correct**
instead of correcting or escalating. Company shut the agent down.
"People remain at the heart of this business, and we're not replacing human judgment."
- https://www.smartcompany.com.au/retail/who-gives-a-crap-suspends-ai-agent-email-error-prices-would-double/
This is the failure mode that matters here: the assistant did not merely say something wrong,
it **exercised delegated authority to ratify an error**, turning a typo into a confirmed
commercial commitment. Pair with Moffatt and OLG Hamm.

### Chevrolet $1 Tahoe, Dec 2023 - DO NOT USE AS A LIABILITY EXAMPLE
Prompt injection demo. Never honoured, no claim brought, the bot had no authority to price
or close. Constantly cited next to Air Canada as if both show binding liability. Cite only
under prompt injection.
- https://incidentdatabase.ai/cite/622/

### Meta AI fake case ID, Apr 2026 - UNVERIFIED
Single local-news source relayed by a trade blog. No corroboration. Do not lead with it.

### GAP TO STATE HONESTLY
There is **no well-documented public incident** of a customer service agent with write access
autonomously issuing wrong refunds, cancelling wrong orders or changing wrong addresses at
scale. The 2026 blog posts describing "a mid-size e-commerce company" with "$500 refund
authority" have no named company, no date, no source. They are marketing fiction. The real
agentic-action evidence is on the security side (section 4).

---

## 2. Legal and liability

### Is a company bound by what its assistant tells a customer?
Direction of travel is one way: yes, with no working "the AI did it" defence.

| Jurisdiction | Instrument | Date | Holding |
|---|---|---|---|
| Canada (BC) | Moffatt v Air Canada, 2024 BCCRT 149 | 14 Feb 2024 | Chatbot is part of the website. Operator liable. Correct info elsewhere is no defence. |
| Germany | OLG Hamm, 4 UKl 3/25 | 12 May 2026 | Statements attributed to the operator. Black-box defence rejected. Disclaimers do not protect. BGH appeal allowed. |
| US | Garcia v Character Technologies, M.D. Fla. | May 2025 | An AI chatbot app can be treated as a **product** for product liability, not shielded as speech. Settled Jan 2026. |

US regulator posture: FTC **Operation AI Comply**, launched 25 Sep 2024, 5 actions, more than
a dozen Section 5 AI actions since, under both administrations. One action (Air AI) targeted
"conversational AI" marketed as replacing human reps, ~$19m taken on deceptive claims.
- https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes

LINE FOR THE DECK: every jurisdiction that has ruled has attributed the assistant's statements
to the operator. No court has accepted that model unpredictability transfers the risk.
Disclaimers have been tested once, in Hamm, and failed.

### UAE - several commonly asserted things are OUT OF DATE as of Sep 2026

**a) The regulator changed in 2026.** On **14 Jun 2026** a **Federal Authority for Artificial
Intelligence and Data** was approved, consolidating the UAE AI Office, **TDRA's Information
and Digital Government Sector**, and the Emirates Data Office. Led by the Minister of State for AI.
Two cautions from the firms covering it: it has **no published instrument granting direct
enforcement powers over the private sector** yet, and TDRA continues as telecom regulator.
- https://www.morganlewis.com/pubs/2026/06/uae-establishes-federal-authority-for-artificial-intelligence-and-data
- https://www.glaco.com/blog/the-uae-artificial-intelligence-and-data-authority-what-it-means-for-ai-data-and-digital-governance/

DO NOT say "TDRA AI rules" in late 2026. Say the digital government and AI policy functions
moved into the new Federal AI and Data Authority in June 2026. If anyone in the room works in
UAE govtech, this detail lands.

**b) UAE Charter for the Development and Use of AI, mid-2024. Non-binding.** 12 principles.
Relevant wording: transparency ("a clear understanding of AI and how systems operate and make
decisions"), human oversight ("the irreplaceable value of human judgment"), safety ("encourages
modifying or removing systems that pose risks").
- https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/policies/Ai/The-UAE-Charter-for-the-Development-and-Use-of-Artificial-Intelligence

**c) There is no binding federal AI statute in the UAE.** Non-binding frameworks plus existing
law. Abu Dhabi has its own AI and Advanced Technology Council under Law No. 3 of 2024.
- https://www.lw.com/en/insights/ai-in-the-uae-understanding-the-regulatory-landscape-and-key-authorities

**d) UAE Consumer Protection Law, Federal Law 15/2020 (amended by Decree-Law 5/2023). The real hook.**
"Misleading Advertisement" covers advertising a good or service on deceptive information, **or
omitting essential or basic information**, which leads the consumer into a contract he would
not otherwise have entered. Penalties for failing to provide clear information or advertising
false data: **up to 2 years imprisonment and fines up to AED 2 million.**
- https://www.moet.gov.ae/documents/20121/0/Law_15_2020_pdf.pdf
- https://u.ae/en/information-and-services/justice-safety-and-the-law/consumer-protection

ARGUMENT: the UAE has no AI-specific liability statute, so an assistant that states a wrong
price, delivery promise or policy is assessed under **ordinary consumer protection law about
misleading information**, which does not contemplate or excuse an automated speaker.
UNVERIFIED: no UAE court decision or Ministry of Economy action about an AI assistant to date.

**e) PDPL, Federal Decree-Law 45/2021.** In force 2 Jan 2022. Art. 5 processing controls (fair,
transparent, lawful; specified purpose; **accuracy**; minimisation; secure retention). Art. 6
consent conditions.
CORRECTION: several 2026 sources claim the Executive Regulations are issued with a 1 Jan 2027
deadline. **UNVERIFIED and contradicted** by Chambers' UAE guide (current to Mar 2026, "have
yet to be issued") and GLA (27 Aug 2026, "have not been formally issued... the enforcement
regime remains uncertain").
DIFC is the exception: **DIFC Regulation 10, Sep 2023**, covers autonomous and semi-autonomous
systems, requiring ethical use, risk assessment, transparency and user notification. DIFC only.
- https://practiceguides.chambers.com/practice-guides/data-protection-privacy-2026/uae/trends-and-developments

Applied to an assistant handling a phone number and an address, three exposures:
1. **Minimisation.** Sending a full address and number to a model provider for a query that
   only needs an order ID is hard to justify. The model vendor is a **processor**.
2. **Accuracy (Art. 5).** Sits badly with writing back to an address field from free text.
3. **Transparency.** No PDPL rule that the customer must be told they are talking to a machine,
   but the Charter points that way and the EU now makes it a hard rule.
The absence of Executive Regulations is a timing advantage, not a permanent exemption.

### EU AI Act, in case they ask
Art. 50(1): providers must ensure people are **informed that they are interacting with an AI
system**, "in a clear and distinguishable manner at the latest at the time of the first
interaction". Only carve-out is where it is obvious to a reasonably well-informed person; a
support bot does not qualify. **Applies from 2 August 2026, so it is live now.**
Penalty tier up to **EUR 15m or 3% of worldwide annual turnover**.
A support chatbot is **not** automatically high-risk. Art. 50 transparency may be its whole
obligation: a cheap bar to clear and a bad one to fail.
- https://artificialintelligenceact.eu/article/50/
- https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act

---

## 3. The metrics trap: containment is not resolution

**Deflection** = never reached a human. Counts abandoned chats.
**Containment** = ended without handoff. Cannot tell a satisfied customer from one who gave up.
**Resolution** = the issue was actually solved.

Intercom's own Fin docs argue against the metric their industry sells on:
"High resolution rate paired with a high reopen rate is, functionally, a containment rate
wearing better clothes." - https://fin.ai/learn/resolution-rate-vs-deflection-rate

### The strongest number available
**Gartner, 19 Aug 2024, survey of 5,728 customers (fielded Dec 2023):**
- **Only 14% of customer service issues are fully resolved in self-service.**
- **73%** of customers use self-service at some point.
- For issues customers themselves called "very simple", only **36%** fully resolved.
- **Nearly 9 in 10 journeys that begin in self-service end up resolved across multiple channels.**
- https://www.gartner.com/en/newsroom/press-releases/2024-08-19-gartner-survey-finds-only-14-percent-of-customer-service-issues-are-fully-resolved-in-self-service

Caveat honestly: fielded Dec 2023, so it measures the self-service estate as it existed, not
today's best LLM agents.

### Preference for humans
Metrigy, Customer Experience Optimization 2025-26, n=503:
- **84.7%** prefer a human over an AI agent.
- **80.1% still prefer a human even if assured their issue would be resolved.**
- 46% accept AI in select cases: routing (50.4%), shipping/order confirmations (49.6%),
  scheduling (46.9%).
- Positive experiences with AI text agents rose 35.9% (late 2024) to 48.9% (late 2025).
- https://www.nojitter.com/customer-experience/consumers-overwhelmingly-prefer-human-agents-in-the-era-of-ai

Tension to be ready for: Klarna reported CSAT parity. Stated preference and measured
satisfaction disagree. Honest reading: preference is a **retention and churn** signal, not a
proxy for per-interaction satisfaction.

### Trust after a bot error
Defensible claim is NOT "one error destroys trust". It is that **recovery design determines
the trust outcome, and most deployments have no recovery design at all.**
- https://onlinelibrary.wiley.com/doi/full/10.1002/mar.22051 (Psychology & Marketing, 2024)
- https://link.springer.com/article/10.1007/s12525-023-00673-0 (Electronic Markets: solution-
  oriented recovery drives competence, empathy-seeking drives warmth)
- https://www.nature.com/articles/s41599-024-03879-5

### Repeat contact and channel switching - be careful
Gartner's 9-in-10 figure is solid. Beyond that:
UNVERIFIED, no primary source, content-marketing origin: "85% of handoffs lose context",
"90% of customers repeat themselves", "only 13% carry context between channels".
Use as a finding: **the escalation-failure story is repeated everywhere and measured almost
nowhere.** That is itself the argument for instrumenting resolution instead of trusting a
vendor's containment dashboard.
Counter-datapoint to acknowledge: Klarna reported a **25% drop in repeat inquiries**.

---

## 4. Operational failure modes

### 4.1 Hallucinated delivery dates
Mechanism is established (Cursor is the archetype: retrieval returns nothing, the model fills
the gap). A delivery estimate is a factual claim, so a fabricated date means the customer plans
around fiction, and under Law 15/2020 and Moffatt it is a representation the operator owns.
HONEST CAVEAT: **no named, dated public incident of a carrier's assistant hallucinating an ETA.**
Present it as an engineering risk with a clear causal chain and legal consequence. If asked for
the case, say there isn't one publicly, and point to Who Gives A Crap as the nearest analogue.

### 4.2 Stale or contradictory backend data
Moffatt is not really a hallucination case. The finding was that a **customer cannot be expected
to know which part of a company's own surface is authoritative.** Where the assistant reads one
source and the policy page says another, the operator eats the difference.
Directly relevant to a shipment table where one tracking number has two contradictory rows.

### 4.3 Identity verification and social engineering
Help desks are **already the primary account-takeover vector** before AI. Scattered Spider's
method is calling support, impersonating an employee, getting MFA reset. Used against MGM
Resorts to reach Okta Super Admin. CISA advisory AA23-320A updated 29 Jul 2025; FBI warned in
June 2025 about expansion into airlines.
ReliaQuest: "Scattered Spider's initial access methods expose a critical weakness in many
organizations: reliance on human-centric workflows for identity verification."
- https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a

Synthetic voice raises volume. Pindrop 2025 report: $12.5bn lost to fraud in 2024, 2.6m fraud
events, and a claimed +1,300% surge in deepfake fraud attempts in contact centres (about one
per month to seven per day). CAVEAT FIRST: Pindrop sells deepfake detection, this is vendor
telemetry. Neutral corroboration: **Gartner 2025 AI Risk Management Survey (n=302) found 62%
of organisations experienced a deepfake incident in the prior 12 months.**

STRUCTURAL POINT: an AI assistant is a help desk that never gets suspicious, never escalates on
a hunch, and runs 24/7 at machine speed. Every verification weakness is inherited and scaled.

### 4.4 Prompt injection against agents with write access (the strong 2026 evidence)
**OWASP LLM01:2025, prompt injection is the number one risk.** OWASP states plainly that
"it is unclear if there are fool-proof methods of prevention for prompt injection". For
tool-enabled systems it warns of "unauthorized access to functions available to the LLM",
"executing arbitrary commands in connected systems", "manipulating critical decision-making
processes". Its mitigations lean on **least privilege and human approval for high-risk actions**,
which is an admission that technical defences alone are insufficient.
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/

**ForcedLeak, Salesforce Agentforce, disclosed 25 Sep 2025, CVSS 9.4.**
Malicious instructions embedded in a **Web-to-Lead form submission** (42,000-char Description
field), executed later by Agentforce during **normal employee use**. Exfiltrated CRM lead data
via an image tag. It worked because `my-salesforce-cms.com` was on Salesforce's CSP allowlist
but had **expired**, and researchers bought it for **$5**.
Reported 28 Jul 2025, fix shipped 8 Sep 2025, public 25 Sep 2025.
- https://thehackernews.com/2025/09/salesforce-patches-critical-forcedleak.html
- https://noma.security/blog/forcedleak-agent-risks-exposed-in-salesforce-agentforce

**This is exactly the delivery-support threat model: a customer-submitted free-text field,
processed later by an agent acting with staff privilege.** A delivery note saying "leave at
reception" is the same shape as that Description field.

**ServiceNow Now Assist, second-order prompt injection, AppOmni, 19 Nov 2025.**
A benign agent fed a crafted prompt **recruits more capable agents via agent-to-agent discovery**
to exfiltrate data, modify records and escalate privilege, invisibly. Now Assist agents run with
the privilege of **the user who started the interaction**, not the user who planted the prompt.
Three **default** settings enable it. ServiceNow's response: the system **"works as intended"**,
documentation updated rather than a fix shipped.
AppOmni's line to quote: "this isn't a bug in the AI; it's expected behavior as defined by
certain default configuration options."
Related: CVE-2025-12420 "BodySnatcher", CVSS 9.3, patched Jan 2026.
- https://thehackernews.com/2025/11/servicenow-ai-agents-can-be-tricked.html
- https://appomni.com/ao-labs/ai-agent-to-agent-discovery-prompt-injection/

Two tier-1 enterprise platforms shipped customer-facing agentic AI with defaults that let
untrusted customer input drive privileged actions. That is a platform-maturity argument, not
an anti-AI argument, and it is far more persuasive.

### 4.5 Language
**Arabic dialects.** DialectalArabicMMLU (arXiv:2510.27543, rev. Mar 2026, LREC 2026). MMLU-Redux
manually translated into Syrian, Egyptian, **Emirati**, Saudi, Moroccan. 22,000 QA pairs, 32
domains, 19 models. Finding: "substantial performance variation across dialects" and "persistent
gaps in dialectal generalization". Models score higher on MSA than on dialect across all tasks.
82% of all Arabic NLP benchmarks were released in 2024-2025, meaning this was essentially
unmeasured until recently.
HONEST FRAMING: these benchmarks measure academic QA, not support intent in Gulf dialect with
code-switching. Do not invent an "X% worse at support" figure.

**Hindi, Urdu, Malayalam.** "Better To Ask in English?" (arXiv:2504.20022, 28 Apr 2025), GPT-4o,
Gemma-2, Llama-3.1 across 19 Indic languages: "LLMs often perform better in English, even for
questions rooted in Indic contexts. Notably, we observe a higher tendency for hallucination in
responses generated in low-resource Indic languages."
**THE KEY ASYMMETRY: the model does not fail loudly in these languages, it hallucinates more.**
A support assistant confidently wrong in Malayalam is worse than one that says "I don't understand."
Performance tiering: Hindi moderate, Malayalam low, **Urdu extremely low** (arXiv:2509.11570).
**Tagalog: UNVERIFIED**, no citation found. Do not assert a figure.
Klarna counterpoint to expect: "35+ languages". Answer: "supports the language" and "matches
English-level factual accuracy in that language" are different claims.

---

## 5. Realistic rates vs vendor claims

**Gartner, 5 Mar 2025 (the line in every vendor deck):** "By 2029, agentic AI will autonomously
resolve **80% of common customer service issues** without human intervention, leading to a 30%
reduction in operational costs." It is a **prediction**. The load-bearing word is "common".
- https://www.gartner.com/en/newsroom/press-releases/2025-03-05-gartner-predicts-agentic-ai-will-autonomously-resolve-80-percent-of-common-customer-service-issues-without-human-intervention-by-20290

**Intercom Fin** publishes a **76% average resolution rate**, top performers 80-84%. Three
problems: it is **self-graded** (their own page concedes vendors grading their own work is a
conflict of interest), two different numbers sit on two Intercom-owned pages simultaneously
(71% and 76%), and **no third-party validation exists**.
Counter-claims of 38-53% in production come from **competitor marketing pages**. UNVERIFIED,
do not use the numbers. The legitimate and more damaging statement: **published independent
benchmarks for AI support resolution rates do not exist. Every number in circulation is either
a vendor's self-assessment or a competitor's counter-marketing.**

| Source | Date | Finding |
|---|---|---|
| Gartner, n=5,728 | 19 Aug 2024 | **14%** fully resolved in self-service. 36% even for "very simple". ~9 in 10 go multi-channel. |
| Gartner, 3,400+ orgs | 25 Jun 2025 | **Over 40% of agentic AI projects will be cancelled by end of 2027**, on cost, unclear value, inadequate risk controls. |
| Klarna, self-reported | Nov 2025 | Work of 853 FTEs, $60m saved, **yet service and ops costs rose $42m to $50m YoY**. |
| Cisco / CarShield, vendor | 2026 | 66% **containment**, not resolution. |

**THE CLEANEST LINE AVAILABLE:** Gartner predicts 80% autonomous resolution by 2029. Gartner
also measured 14% actual resolution, and predicts 40% of agentic AI projects will be cancelled
by 2027. All three numbers are Gartner's. **The gap between them is the delivery risk you are
being asked to price.**

**CORRECTION on the "MIT 95% of AI pilots fail" stat.** Project NANDA, *The GenAI Divide*, 2025.
Contested and misreported. Success was defined as deployment beyond pilot with measured P&L
impact at six months, excluding efficiency, churn and conversion effects. Futuriom called the
methodology "irresponsible and unfounded". The 5% comes from a funnel for one narrow category
(custom embedded tools). The **same report** found general-purpose tools converting from pilot
to implementation at **above 80%**. Not customer-service specific.
If referenced at all, reference it as **a statistic that was widely misreported**, which
demonstrates rigour and is worth more in the room than the number.
- https://80000hours.org/podcast/episodes/ai-workplace-mit-study/
- https://www.marketingaiinstitute.com/blog/mit-study-ai-pilots

---

## 6. Quick reference

**SOLID, cite freely.** Moffatt (14 Feb 2024, CA$812.02, the three failed defences). OLG Hamm
4 UKl 3/25 (12 May 2026, disclaimers do not protect). DPD (18 Jan 2024, system-update cause).
McDonald's/IBM (off by 26 Jul 2024, plus their stated confidence in voice ordering's future).
Klarna's own figures with dates. Gartner 14% (n=5,728). Gartner 40% cancellation by 2027.
Gartner 80%-by-2029 **as a prediction**. EU AI Act Art. 50 live since 2 Aug 2026, EUR 15m / 3%.
UAE Law 15/2020 misleading information, AED 2m / 2 years. PDPL Arts. 5 and 6. Charter
non-binding. Federal AI and Data Authority approved 14 Jun 2026 absorbing TDRA's digital
government sector. ForcedLeak (CVSS 9.4, $5 expired domain). ServiceNow "works as intended".
OWASP LLM01:2025 "no fool-proof methods of prevention". Cursor "Sam" (Apr 2025). Who Gives A
Crap (Jul 2026). Metrigy 84.7% / 80.1% (n=503). Scattered Spider help-desk vector.

**SOFT OR WRONG, handle with care.**
- "Klarna fired 700 people for AI then rehired them." WRONG on three counts.
- "Chevrolet was legally bound to sell a Tahoe for $1." WRONG. Never honoured, no claim.
- "McDonald's proved voice AI does not work." OVERSTATED, they said the opposite.
- "MIT: 95% of AI pilots fail." CONTESTED, misreported, not CX-specific.
- "UAE PDPL Executive Regulations are issued with a Jan 2027 deadline." UNVERIFIED, contradicted.
- "TDRA regulates AI in the UAE." OUT OF DATE since June 2026.
- "85% of handoffs lose context" / "90% repeat themselves" / "13% carry context." UNVERIFIED.
- Fin at "38-53% in production." UNVERIFIED, competitor marketing. The defensible claim is that
  no independent benchmark exists at all.
- Meta AI fake case ID, Apr 2026. UNVERIFIED, single local source.
- Tagalog LLM performance. No citation found.
- A documented case of a support agent autonomously issuing wrong refunds at scale. **Does not
  exist publicly.** The circulating stories are fabricated.
