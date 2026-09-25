# Second pass: who lets an AI change a delivery, outside the English-language West

Research run 25 Sep 2026. Same source classes as 01:
**COMPANY-FILED**, **COMPANY** (own press release or site), **REGULATOR / INDEPENDENT**,
**JOURNALISM**, **VENDOR** (weakest). Plus **BLOG** for content sites with no primary source.

---

## 0. WHY THIS PASS EXISTS, AND WHAT IT OVERTURNS

The first pass (01) was run mostly in English and mostly on Western carriers. It concluded that
**Japan Post is the only clean precedent** for an AI taking a delivery action, and the market scan
said "across the whole public record, exactly one". That does not survive a search in the
carriers' own languages:

- **Yamato Transport** (Japan's largest parcel carrier) has had conversational AI on LINE that
  changes the delivery date, time and place **since 27 June 2016**. [COMPANY]
- **JD Logistics** runs a voice robot that books bulky-item deliveries by phone and changes the
  delivery time on request: 1.93 million calls over Singles' Day 2021. [JOURNALISM, promotional]
- **SF Express, CJ Logistics and Delhivery** let customers change a delivery inside a chat or
  WhatsApp, mostly through menus, buttons or scripted replies rather than free conversation.

**The corrected finding:** changing a delivery inside the chat app people already use is
established in East Asia. The West kept it on a web form, behind a chatbot that answers. An AI
that understands free language and then changes the record remains rare: three verified cases,
two of them voice.

**For a UAE operator this points one way.** East Asia's chat app is LINE, WeChat or KakaoTalk;
the UAE's is WhatsApp (see 01 section 0: WhatsApp is 7X's only 24/7 channel).

---

## 1. Method

- One question per carrier: can its customer-facing AI (chat, voice, messaging) **change** a
  delivery (date, address, redirect), or does it only answer?
- Searched in the carrier's language: Chinese, Japanese, Korean, French, German, English.
- Every positive claim was read from the **raw page**, not from a search summary. Two summaries
  were wrong: one invented content on a Chinese page (JD), one attributed an illustrative sentence
  to UPS that UPS never published (below). Raw reads caught both.
- "Searched, nothing found" is recorded as a result. It is not proof of absence.

---

## 2. Tier 1: conversational AI that changes the delivery

| Operator | What it does | Channel | Since | Class |
|---|---|---|---|---|
| **Yamato Transport** (JP) | 会話AI: check a parcel and change delivery date, time and place "as if in conversation"; the AI proposes the change mid-dialogue | **LINE** | 27 Jun 2016 | COMPANY |
| **Japan Post** (JP) | Voice AI books redelivery; later, pickups (already in 01) | Voice | 1 Nov 2020 | COMPANY |
| **JD Logistics** (CN) | 言犀 voice robot places outbound calls to book bulky-item delivery; confirms address and time and **changes the delivery time** on request. 1,931,000 calls over 11.11 2021, 176,000 a day | Voice, outbound | Dec 2021 | JOURNALISM (state media, promotional tone) |

**Yamato, verbatim** (Yamato Holdings press release, 平成28年6月27日):
> 「ヤマト運輸」LINE公式アカウントで、会話をするような感覚で荷物状況の確認やお届け日時・場所の変更ができます。
> 会話のなかでお届け日時や場所の変更を自然に提案されるので、お客さまはより都合の良い受け取り方法へスムーズに変更できます。

https://www.yamato-hd.co.jp/news/h28/h28_36_01news.html (Shift-JIS page; decode accordingly)

**JD, verbatim** (央广网, 17 Dec 2021):
> 目前，言犀已广泛应用于京东物流配送外呼场景，由语音机器人自动进行大件商品配送的电话预约。除确认地址、配送时间等基础信息外，能支持消费者更改配送时间等个性化需求

https://tech.cnr.cn/techph/20211217/t20211217_525690592.shtml (GBK page)

---

## 3. Tier 2: chat or WhatsApp that changes the delivery through menus or scripts

| Operator | What it does | Since | Class |
|---|---|---|---|
| **SF Express** (CN) | 丰小满 chat assistant: "一键解决运单详情查询、配送地址/时间修改等问题" (one-click address and time changes). WeChat, mini-program, web, app | 2016 | VENDOR (Tencent Qidian case study, undated) |
| **CJ Logistics** (KR) | "AI chatbot 2.0" with intent understanding; quick menu includes 배송일정 and **주소변경**; books pickups and returns end to end. **Chatbot share of all customer inquiries: 10.5% (2019) to 22% (2022)**. Whether the bot executes the address change or passes it to the driver is not stated | 14 Jun 2022 | COMPANY |
| **Delhivery** (IN) | After a failed attempt, a templated WhatsApp message; the customer's reply triggers a re-attempt or cancellation. Scripted, not AI | current | COMPANY (Delhivery One help) |
| China Post EMS (CN) | 朱雀 tool used by branch staff in merchant WeChat groups for 改址 / 拦截 requests. **Business customers, not consumers**; unclear whether it executes | 2020 | VENDOR / BLOG |
| Ninja Van (SEA) | Reported in-transit address change and rescheduling in chat; the company's own page mentions only updates, self-help options and a live agent | 2019 | JOURNALISM (tech blog); **unverified** |
| Saudi Post, SPL (SA) | "90% of inquiries resolved on WhatsApp" | undated | VENDOR (Route Mobile blog); **action unverified** |

Sources:
- https://qidian.qq.com/customercase/sf001.html
- https://www.cjlogistics.com/ko/newsroom/news/NR_00000951
- https://help.delhivery.com/docs/communication
- https://pitchhub.36kr.com/project/1713086258292992 and https://zhuanlan.zhihu.com/p/1916058447180436317
- https://nasilemaktech.com/ninja-van-ninja-chat/ and https://www.ninjavan.co/en-my/support/consignee-support/ninja-chat
- https://routemobile.com/blog/whatsapp-logistics-customer-service/

---

## 4. Tier 3: answers only, or a web form with no AI

| Operator | Finding | Class |
|---|---|---|
| **UPS** (US) | 18 Jun 2026 release: "more than 98% of customer service requests... using AI and human expertise... AI-enabled intelligent assistants in more than 20 countries". **No rescheduling claim.** A DigitalDefynd "case study" says the chatbot offers "options to reschedule"; that is an illustration on a course-marketing site, not a UPS statement. **Discarded.** | COMPANY |
| FedEx (US) | Tracking+ / Returns+ answer questions (already in 01); agentic AI is internal workflow, target 50% of workflows by 2028 | COMPANY / JOURNALISM |
| USPS (US) | AI chatbot for **employees** (Jul 2025); redelivery is a web form | COMPANY |
| Amazon (US) | Reschedule is a button in Your Orders; no Alexa+ delivery-change capability found | COMPANY |
| Australia Post (AU) | GPT virtual assistant **proof of concept**, answers a parcel query in a demo, 19 Jul 2023. Nothing later found | JOURNALISM (iTnews) |
| DHL Paket (DE) | Chatbot "Marie", also on WhatsApp, answers; redirection and preferred day are web and app self-service | JOURNALISM / COMPANY |
| DPD (UK) | Generative chat element disabled after the Jan 2024 incident (already in 03) | JOURNALISM |
| La Poste (FR) | Delivery changes via web or app form | COMPANY |
| Swiss Post (CH) | Delivery changes in the My Post portal | COMPANY |
| PostNord (Nordics) | Chatbot, widely complained about; AI used in sorting | BLOG / JOURNALISM |
| Evri (UK) | Microsoft AI tools, internal and personalisation (Jul 2026) | JOURNALISM |
| Coupang (KR) | AI routes callers to the right agent; returns and refunds are one-click in the app | COMPANY |

**Searched, nothing found:** Cainiao, InPost, GLS, bpost, Poste Italiane, An Post, Austrian Post,
StarTrack, Aramex Australia, CouriersPlease. (Sendle closed in January 2026.)

Sources:
- https://finance.yahoo.com/technology/ai/articles/proof-over-promises-upss-bold-120000985.html
- https://digitaldefynd.com/IQ/ups-use-ai-case-study/ (discarded)
- https://news.usps.com/2025/07/14/new-chat-tool-answers-surface-visibility-logistics-questions/
- https://www.amazon.com/gp/help/customer/display.html?nodeId=GBMXZPW3VTZHDBSJ
- https://www.itnews.com.au/news/australia-post-is-six-weeks-into-its-first-gpt-experiment-598125
- https://www.giga.de/tech/bei-problemen-mit-dhl-lieferung-whatsapp-hilft-euch-weiter--01J5QRDVSZ499Q34G9C6JCEX3B
- https://www.laposte.fr/outils/modification-livraison
- https://www.post.ch/en/receiving-mail/manage-consignment/manage-one-off
- https://retailtechinnovationhub.com/home/2026/7/19/parcel-delivery-giant-evri-taps-microsoft-ai-powered-tools-for-efficiency-and-personalisation-push
- https://news.coupang.com/archives/29410/
- https://www.pymnts.com/artificial-intelligence-2/2026/fedex-plans-agent-workforce-in-over-50percent-of-workflows-by-2028/

---

## 5. One number worth carrying into the value case

**CJ Logistics: the chatbot's share of all customer inquiries went from 10.5% in 2019 to 22%**
(company press release, 14 Jun 2022). A real, company-reported self-service share for a parcel
carrier, sitting between Gartner's 14% (all industries) and the 50% the value case assumes.

---

## 6. Coverage, and its limits

Covered: the largest carriers in the US, China, Japan, Korea, Europe, Australia, India and the
Gulf (about 33 operators across both passes), each searched in its own language.

Not covered: Latin America, Africa, most of South-East Asia (J&T, SingPost), India Post, Sagawa,
and Gulf carriers other than Saudi Post and Emirates Post / Aramex.

Several tier 2 claims rest on vendor or blog sources and are marked so. Claim what the table
supports: "among the largest carriers in these markets", never "anywhere in the world".
