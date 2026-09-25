# What UAE delivery customers actually complain about

Primary research, 22 Sep 2026. **718 public app-store reviews, of which 454 are negative (1-2
star), Jan 2025 to Sep 2026.** Collected from Google Play and Apple's public RSS feed. No logins,
no authenticated endpoints, no block evasion. Data held locally.

---

## Method, and its limits (state these before anyone asks)

| | |
|---|---|
| Sample | 718 reviews; **454 negative** analysed |
| Operator | **EMX Express** (7X's parcel app, Play + App Store) and **Emirates Post** retail app |
| Sector comparators | **Aramex, iMile, Shipa** |
| Period | 1 Jan 2025 to 20 Sep 2026 |
| Language | 392 English, **62 Arabic (13.7%)** |
| Labelling | Rule-based classifier, rules written after reading all 454 by hand |
| **Accuracy** | **~82% agreement** with my own labels on a 40-review hand check |

**Three caveats that matter:**

1. **Written reviews are a complaint channel, not a satisfaction measure.** EMX Express holds a
   4.73 App Store rating across 3,830 ratings, but its recent *written* reviews run 136 one-star
   against 182 five-star. Aramex averages 4.55 across 74,502 ratings, yet its recent written
   reviews are 236 one-star against 39 five-star. **Never present this sample as a rating.**
2. **App reviewers are not all customers with a live shipment problem.** Some are reviewing the
   app. The classifier separates those out deliberately (see `app_bug` below).
3. **Arabic is under-represented here (13.7%) relative to the UAE population.** App reviews skew
   to English writers. This is not evidence that the phone channel skews English.

Reproduce with `analysis/collect_reviews.py` then `analysis/label_reviews.py`.

---

## Headline: what the 454 complaints are actually about

| Primary intent | n | % | Can an assistant resolve it? |
|---|---|---|---|
| **other** (content-free anger, "worst service") | 116 | 25.6% | No. Nothing to act on |
| **access** (cannot reach a human, bot useless) | 100 | **22.0%** | Partly, and this is the trap |
| **information** (where is it, no update) | 64 | 14.1% | **Yes, fully** |
| **action** (reschedule, address, time slot) | 59 | **13.0%** | **Yes, with guardrails** |
| **recovery** (false attempt, lost, misdelivered) | 59 | 13.0% | No. Needs a human and an investigation |
| **app_bug** (login, OTP, crash, registration) | 45 | 9.9% | No. Out of scope entirely |
| payment / COD | 6 | 1.3% | No |
| staff conduct | 5 | 1.1% | No |

**Theme prevalence** (multi-label, % of 454): delay or "where is it" **31.9%** · cannot reach a
human **18.3%** · app or login bug **14.1%** · customer service quality **13.0%** · address
problem **10.6%** · false delivery attempt **6.6%** · lost or misdelivered **6.4%** · reschedule
problem **5.9%** · staff attitude 5.1% · **bot explicitly called useless 4.6%** · time slot missed
3.3% · payment or COD 2.9% · driver unreachable 2.6% · damaged 1.3%.

---

## Finding 1 — THE WARNING. The top complaint is about the assistant they already have

**22% of complaints are that the customer could not reach a human, or that the automated
assistant was useless.** This is the largest actionable category in the sample, and it is
*caused by* the thing this project proposes to build more of.

Verbatim, all from the public record:

> "I can't speak with any person in the call centre?! **They transferred the call to AI
> assistant !!! And this is pointless**" — Aramex

> "their WhatsApp bot is not useful at all, **keeps repeating the shipment update which is
> invalid**" — Aramex

> "Terrible customer service, **they just send you to a bot to talk to, which doesn't solve any
> problems**" — Aramex

> "every attempt to reach customer support is handled **only through an automated system, making
> it impossible to get urgent help**" — EMX Express

> "**WA chat bot doesn't see shipment number**" — Aramex

> "The app itself is bad and unhelpful, and **the WhatsApp service is also useless — it tells me
> there is no shipment linked to my data, although I actually have a shipment with Emirates
> Post**" (translated from Arabic) — EMX Express / Emirates Post

**7X already runs a virtual assistant on WhatsApp, their only 24/7 channel. Customers say it
cannot see their shipment.** That is the gap, and it is not a language-understanding gap. It is a
data and permissions gap. The assistant talks but cannot look anything up or do anything.

**Consequence for the MVP:** a proposal that increases containment is proposing more of the thing
generating 22% of the complaints. The design has to lead with **resolution and a guaranteed
escalation path**, not deflection. Meta's own Business Messaging Policy requires "prompt, clear,
and direct escalation paths" to a human anyway, so this is a compliance requirement, not a
preference.

---

## Finding 2 — For 7X specifically, ACTION requests are the top solvable category

Splitting operator from sector changes the picture, and in your favour:

| Intent | **7X (EMX + Emirates Post)** | Sector (Aramex, iMile, Shipa) |
|---|---|---|
| **action** | **17.2%** | 10.9% |
| information | 15.9% | 13.2% |
| app_bug | 12.6% | 8.6% |
| recovery | 11.3% | 13.9% |
| **access** | **9.3%** | **28.4%** |

**7X's customers complain about things they could not do (17.2%) more than about not reaching
anyone (9.3%). The sector's customers are the reverse.**

So for this operator, **reschedule and change-address are the correct two actions**, and that is
now an evidence-backed decision rather than an assumption. Supporting quotes:

> "**no option to update delivery address**" — EMX Express

> "Three times my credit card delivery scheduled and they are not delivering on time, **also they
> are changing my delivery location by themselves**" — EMX Express

> "they send me a WhatsApp message 'schedule your delivery' but **the link does not open**"
> — EMX Express

> "I have scheduled delivery in slot between 9am till 1pm. **at the moment is 5.45pm** and I still
> did not receive my parcel. 3x I call customer service" — EMX Express

> "It is difficult to communicate with Aramex when you want to postpone a shipment to a specific
> day. There is no easy way — **only the automated reply, which does not serve the purpose at
> all**. We hope for a live chat like other companies" (translated from Arabic) — Aramex

> "It's complicated, **I'm unable to make any changes in the address**" — Aramex

> "**Asked for delivery address 10 times??!!!**" — Aramex

---

## Finding 3 — The dataset's "dirty" rows are a real operational phenomenon

This is the strongest connection in the whole research pack.

The shipment dataset contains **17 rows marked Delivered with 0 attempts**, **2 Failed or
Redelivery rows with 0 attempts**, and **25 rows where the last attempt predates the shipment
date**. Those look like data-entry noise. **The reviews say they are not.**

> "**No attempts made and they update customer was not available**" — Aramex

> "I set delivery date and time. Waited the whole day. When I checked the app, **they said I am
> not available at home. They don't even try to call me or knock the door.** Wasted my whole day."
> — Aramex

> "So you expect a shipment. They show the driver number. **You call the driver 3 times, he
> doesn't pick up. The app shows that you attempted 3 successful calls with the driver.** Minutes
> later you receive a message that they attempted delivery" — Aramex

> "I spent all the day waiting for delivery at home but **they simply faked the delivery
> attempt**" — EMX Express

> "tracking is not reliable... **keep saying they tried to deliver but no call or sms from rider
> at all**... I even chose 'leave by the door' but still unsuccessful for 2 days" — EMX Express

> "When their delivery drivers don't feel like delivering your order that day **they can just mark
> it as a 'wrong address' then call your number for a few seconds** so you have no chance of
> replying" — iMile

> "**Showing delivery attempt finished but nobody calls me.** My address is in the parcel already"
> — iMile

**6.6% of all negative reviews describe a delivery attempt that the customer says did not
happen.** The impossible rows in the dataset are the database fingerprint of exactly this.

**Consequence for the prototype:** an assistant that reads `status = "Failed delivery — customer
not available"` and repeats it to the customer will be telling a significant number of people
something they know to be false, and will make them angrier than no assistant at all. The
cleaning layer must **flag contradictory rows rather than narrate them**, and the assistant must
be able to say "the record says an attempt was made, and I can see that may not be right — let me
get this to a person."

---

## Finding 4 — Three things worth knowing

**Bank cards and ID documents are a distinct, high-stakes segment.** 20 reviews (4.4%) mention a
bank card, credit or debit card, ATM card, Emirates ID or visa document — split evenly between
EMX (11) and Aramex (9). These are signature-required, time-critical, and cannot simply be left
at a door. They are a natural **guardrail case**: exactly the shipment type where an address
change should require a human.

> "Unfortunately, the shipment contains a Citibank card, which is of critical importance and
> directly affects my financial activities" — EMX Express

**Calling is still the reflex.** 22.7% of negative reviews mention calling or a phone call;
only 4.4% mention WhatsApp. People try the phone and fail, then write the review.

**A tenth of the complaints are pure app bugs the assistant cannot touch (9.9%).** EMX's
registration loop in particular is a real product defect:

> "When I try to register, I receive 'The email already exists.' However, when I try to recover
> the password using the same email, I receive 'The user doesn't exist'" — EMX Express

That is worth one line in the deck as something **deliberately out of scope**, with the number
attached. It shows you measured what you cut.

---

## What this supports, and what it does not

**Supports:**
- Two actions: **reschedule delivery** and **change address**, for this operator specifically
  (17.2% action intent, highest solvable category)
- Leading with **resolution and escalation**, not containment
- **Guardrails on bank cards and signature-required items**
- A **cleaning layer that flags contradictory rows** instead of reciting them
- Cutting app bugs (9.9%) and recovery cases (13.0%) from scope, with numbers

**Does NOT support:**
- Any claim about call volume. These are app reviews. **There is no contact-volume data here.**
- Any satisfaction or CSAT claim. This is a complaint sample by construction.
- Any Arabic-share claim about the phone or WhatsApp channels. 13.7% Arabic here is a fact about
  app reviewers, nothing more.
- A containment or deflection target. Nothing in this data measures that.
