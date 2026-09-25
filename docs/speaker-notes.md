# Speaker notes: the five slides, and the questions behind them

For the person presenting. The slides show; this is what you say. Not for sending.

---

## 1. Who lets an AI change a delivery  (about 2 min)

- Say the finding: **in Asia the chat changes the delivery; in the West it only answers.**
- Top row, conversational AI that changes a delivery: **Yamato** on LINE since June 2016 (company press release: customers change the date, time or place "as if in conversation", and the AI proposes the change), **Japan Post** by voice since 2020, **JD Logistics** by outbound voice calls since 2021 (1.93 million calls over Singles' Day 2021).
- Middle row, a chat menu or script that changes it: **SF Express** on WeChat (one-click address and time changes), **CJ Logistics** (22% of all its customer inquiries go through its chatbot), **Delhivery** (a scripted WhatsApp reply books the re-attempt; not AI).
- Bottom row: UPS, FedEx, DHL, USPS, PostNL, Royal Mail, La Poste and Australia Post answer, or send the customer to a web form.
- The point for this operator: in Asia the change happens inside the messaging app people already use (LINE, WeChat). In the UAE that app is WhatsApp.
- Covered: the largest carriers in the US, Europe, Australia, China, Japan, Korea, India and the Gulf, each searched in its own language. Not covered: Latin America, Africa. Say that before anyone asks.
- Two numbers people will quote at you: DHL's "93% answered without assistance" is from its own marketing and covers no booking. UPS's "more than 98%" counts what humans and AI touch together.
- The ceiling is not the model. UPS, FedEx and Evri all publish the same limit: the sender's contract decides whether an address can change. An AI inherits every one of those locks.
- The flip: this operator's customers complain about what they were **not allowed** to do (17.2%); other UAE carriers' customers complain they **could not reach anyone** (28.4%). That points at actions, not a better FAQ bot.

## 2. MVP: reschedule and change address  (about 2 min)

- Every dot is one of the 349 open shipments in their file, run through the prototype's own rules.
- 201 can get a new date or a new address with nobody involved. 61 can get a new date but not a new address, because there is cash to collect. 87 need a person whatever the model says: 46 have no phone to verify, 35 have hit the attempt limit, 6 have records that disagree. Ten fail more than one rule; each is counted once, by the first rule it fails.
- "6 in 10": 86 of the 141 failed deliveries can be rebooked with no person.
- Out of scope, with the cost of each cut. Say where the two percentages come from:
  > "We analysed 454 negative app-store reviews of UAE delivery companies. About 10% are about
  > the app itself breaking, and 13% about a parcel that went wrong: lost, delivered to the wrong
  > place, or a delivery attempt that never happened. An assistant can't fix either, so we left
  > them out."
  - App bugs, 9.9% (45 of 454): login, verification codes, crashes, registration.
  - Parcel went wrong, 13.0% (59 of 454): lost, misdelivered, or an attempt the customer says
    never happened. **Not "damaged"**: damaged parcels are only about 1% of complaints.
  - These are shares of all UAE carriers' reviews, not only this operator's. Slide 1 splits
    the same reviews by company.
  - Approval queue: cash-on-delivery address changes go to a person instead.
  - Dashboards: there is no data to chart yet. What to measure is on slide 5.

## 3. Live demo  (about 5 min)

Demo in this order:
1. **WhatsApp, reschedule.** Arrives already verified by the number. Ask where the parcel is, ask to move it, confirm. The console shows the change written to the record.
2. **Queue, case C-1004.** No phone on file, so no change. The case says why it stopped and what the customer asked for.
3. **Takeover.** One switch. The assistant goes quiet; a person replies in the same thread.

The link and the password are on slide 3 of the PDF, ready to copy. Change the password on Render once the assessment is over: anyone the deck is forwarded to can get in.

## 4. Target architecture  (about 2 min)

- Read it top to bottom: channels, access, AI, control, data. Operations sees every layer.
- Solid runs in the demo. Dashed is the target and is **not built**: say that before anyone asks.
  - WhatsApp in the demo is a lookalike page. Production is Meta's WhatsApp Cloud API calling our server through a webhook.
  - SMS codes: the demo shows the code on screen, labelled as a demo. Production sends it by SMS.
  - Their shipment system, helpdesk, knowledge base, dashboards: none are connected.
- **The control layer is the part you build.** The door is the only thing that writes. The rules are worked out from the record, in code, never from the prompt. The model can ask; it cannot act.
- **Swapping the model.** Only the model layer changes. Honestly: one file is rewritten, not zero, because the code uses Claude's tool format, caching and effort settings.
- **On-premises is a data decision, not a cost one.** Measured, the model costs 1.3 cents a conversation. Owning GPUs only pays at very high volume, and open models are weaker at Gulf Arabic, which is already the weak spot. It becomes worth it when the data must not leave the building.
- **Knowledge base is a buy.** Answering FAQs is the solved part of the market. Buy it; build the rules.
- Stack: Python, FastAPI, SQLite, plain HTML pages, one Render service. The Anthropic SDK with its own tool loop, no agent framework. Model: Claude Sonnet 5 at low effort.

## 5. Value case, per 1,000 shipment calls  (about 2 min)

- No call volume was supplied, so it is per 1,000 shipment calls.
- 50% are about a date or an address: **assumed** (the brief says these drive most calls). 61% of those the rules allow: **measured**. 50% finish in the chat: **assumed**. Two real reference points: CJ Logistics reports 22% of **all** its customer inquiries go through its chatbot, and Gartner measured 14% self-service across industries. Our 50% applies to a narrower group, customers asking for a change the rules allow, so higher is plausible, but it is the number a pilot must test first.
- Range: 5% low (30%, 61%, 30%), 15% central, 37% high (70%, 75%, 70%). A pilot's job is to find out which.
- **$0.055 a conversation, measured**: all eight demo conversations run live and costed. Model $0.013, WhatsApp $0.042 (about three replies at Meta's UAE rate of $0.0157 from 1 October 2026; Meta's own calculator still showed 0 on 21 September, so the rate follows its announced rule).
- Break-even: 500 conversations x $0.055 = $27.50, divided by 153 calls avoided = **$0.18 a call**. If a person's call costs more than 18 cents, it pays. Cost is not the risk; adoption and data quality are.
- Judge the pilot by records changed, customers who call anyway within 7 days, a holdout group with no assistant, and second attempts that get delivered. **Not** containment: that counts a customer who gave up as a win.

---

## Questions you should expect

**"Is the WhatsApp real?"** No. It is a lookalike page; slide 4 shows it dashed. The server already treats WhatsApp as a channel that arrives with a verified number, so connecting Meta's API is a channel adapter, not a redesign.

**"What stops the AI doing something wrong?"** It cannot write anything. Every change goes through one door that checks the rules against the record first. If the rules say no, it opens a case with the reason instead.

**"Why Claude Sonnet 5 and not a bigger model?"** Two actions, well-defined tools, and the rules live in code. We measured it: at low effort, all eight test conversations ended the same way, at 1.3 cents each.

**"Can we run our own model?"** Yes, by rewriting the model layer. The rules, the door, the data and the console do not change. Do it for data residency, not to save money, and test Gulf Arabic first.

**"How do you know 61%?"** It is the prototype's rules run over their file: 86 of 141 failed deliveries.

**"Why not buy Intercom or Zendesk?"** Buy the platform: channels, handover, reporting. Build the rules, because they depend on facts only you hold (cash owed, attempts made, records that disagree) and they are what you are liable for.

**"Nobody else does this?"** They do, in Asia: Yamato on LINE since 2016, Japan Post and JD by voice, SF and CJ through chat menus. In the West, the carriers' assistants answer and the change happens on a web form. That is the gap this prototype closes, on WhatsApp.

**"Are Intercom, Zendesk and the others logistics companies?"** No. They sell the same assistant to every industry. Carriers use them to answer questions (DHL runs on Cognigy). What nobody sells is the delivery rules and the link to the shipment record, and that is what we built.

**"What's the biggest risk?"** Customers not finishing in the chat (assumed 50%, against 22% at CJ and 14% in Gartner's study), and the data: 6.6% of complaints describe a delivery attempt that never happened, which matches contradictory rows in the file.

**"Why is the model so cheap?"** The instructions are cached, so each call re-reads them at a tenth of the price, and it runs at low effort. Most of the cost is Meta's message fee, not the AI.
