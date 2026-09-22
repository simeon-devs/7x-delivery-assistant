"""Label negative delivery-app reviews into intents and themes.

The rules below were written after reading all 454 negative reviews by hand, so they encode
an actual reading rather than guessed keywords. Multi-label on theme, single primary intent.

Deliberately rule-based, not LLM-based: it costs nothing to run, it is auditable line by line,
and anyone on the panel can re-run it and get the same answer. Accuracy is checked by hand on a
random sample (see check_sample()) and the measured agreement is reported with the results.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "reviews_negative.csv"
OUT = ROOT / "data" / "reviews_labelled.csv"


def rx(*parts: str) -> re.Pattern:
    return re.compile("|".join(parts), re.IGNORECASE)


# --- Themes -----------------------------------------------------------------
# Arabic terms are included because 84 of the 718 reviews are Arabic.
THEMES: dict[str, re.Pattern] = {
    # the assistant's would-be job
    "no_human_contact": rx(
        r"no (?:any )?(?:customer )?(?:service|support|care)", r"can.?t (?:contact|reach|talk|speak|call)",
        r"unable to (?:contact|reach|connect|talk|speak)", r"no (?:any )?(?:contact|phone|customer care) number",
        r"nobody (?:answer|reply|respond)", r"no ?body to contact",
        r"no one (?:answer|reply|respond|pick|join)", r"never answer", r"impossible to (?:reach|get|use)",
        r"no way to (?:contact|reach|call|talk|raise|connect)", r"no direct (?:call|agent|contact|point)",
        r"(?:difficult|hard|struggl)[^.]{0,30}(?:to )?(?:contact|reach|communicat|get (?:an?\s)?(?:acctual|actual)?\s?(?:human|agent|hold))",
        r"no response", r"without any response", r"no live chat", r"no agent", r"no (?:real )?human",
        r"real human being", r"actual person", r"speak (?:to|with) (?:an? )?(?:agent|human|person|representative)",
        r"live chat[^.]{0,30}(?:not|never|takes|useless|slow)", r"waiting? (?:for )?(?:an )?(?:agent|hours)",
        r"no medium to reach", r"call cent(?:er|re)[^.]{0,30}(?:no|never|bad|worst)",
        r"لا يوجد رقم", r"صعب التواصل", r"صعوبه التواصل", r"لا أحد يرد", r"ما يردون", r"لا يجيبون",
        r"محد يرد", r"عجز عن التواصل", r"يصعب التواصل", r"ماعندهم خدمة", r"ماعندهم خدمه",
        r"لا تواصل", r"لا يوجد طريقة للتواصل", r"لا يمكننا التحدث", r"وسيله. اتصال",
        r"لا يوجد خدمة عملاء", r"يتهربون من الاتصال", r"لا يرد",
    ),
    # Deliberately excludes a bare "bad service": that is sentiment, not an access complaint.
    # Requires the word customer, or support/care, so it means "the support channel failed me".
    "cs_quality_poor": rx(
        r"(?:poor|bad|worst|terrible|horrible|awful|useless|ineffective|weak|zero|no|0)\s+"
        r"(?:customer\s+(?:service|support|care)|support|care\s+service)",
        r"customer\s+(?:service|support|care)\s+(?:is\s+)?"
        r"(?:poor|bad|terrible|awful|useless|zero|0|nonexistent|non-existent|practically|completely)",
        r"customer (?:service|support|care)[^.]{0,25}(?:never|doesn.?t|didn.?t|not )",
        r"خدمة العملاء", r"خدمه العملاء", r"خدمة سيئة", r"خدمه سيئه", r"اسوء خدمه", r"اسوأ خدمة",
    ),
    "damaged": rx(
        r"damag", r"broken", r"arrived (?:extremely )?hot", r"melted", r"tالف",
        r"تالف", r"الطلب تالف", r"مكسور",
    ),
    "bot_useless": rx(
        r"\bbots?\b", r"chat ?bot", r"automated (?:system|response|assistant|reply)",
        r"auto ?machine", r"ai assistant", r"virtual assistant", r"robot",
        r"الرد الآلي", r"الذكاء الاصطناعي",
    ),
    "false_attempt": rx(
        r"fake deliver", r"faked the deliver", r"false (?:info|reason|update)", r"no attempts? made",
        r"(?:said|says|say|marked|mentioned|update[ds]?|claim(?:ed)?|showing|shows|show)[^.]{0,40}"
        r"(?:not available|unavailable|no one answer|couldn.?t reach|customer was not|wrong address|attempted|delivered)",
        r"attempt(?:ed)? deliver[^.]{0,40}(?:no one|nobody|never|but)",
        r"nobody (?:call|knock)", r"no one (?:called|knocked|came|turned up|showed)",
        r"never (?:called|knocked|came)", r"didn.?t (?:even )?(?:try to )?(?:call|knock|come)",
        r"without (?:calling|knocking)", r"delivery attempt finished",
        r"لم يتم التواصل", r"يدعي", r"تم محاولة التوصيل", r"لم نتمكن من التواصل", r"كلو كذب",
    ),
    "reschedule_problem": rx(
        r"resched", r"re-?schedul", r"change the date", r"postpone", r"another day",
        r"not (?:adhere|following|committed) to (?:the )?(?:date|schedule|time)",
        r"don.?t deliver as scheduled", r"schedule[^.]{0,30}without", r"not as per schedule",
        r"didn.?t adhere", r"changed? (?:it|the date|my delivery)",
        r"تأجيل", r"جدوله", r"إعادة جدولة", r"الموعد", r"بدون الرجوع للعميل",
    ),
    "address_problem": rx(
        r"address", r"location", r"landmark", r"wrong (?:house|flat|building)",
        r"العنوان", r"الموقع", r"لوكيشن",
    ),
    "time_slot_missed": rx(
        r"time slot", r"slot", r"between \d{1,2}\s?(?:am|pm|:)", r"\d{1,2}\s?(?:am|pm)[^.]{0,20}\d{1,2}\s?(?:am|pm)",
        r"whole day", r"all day", r"waited? (?:the )?(?:whole|entire|all)", r"wasted my (?:whole )?day",
        r"day off", r"stay(?:ed)? home", r"انتظر", r"طوال اليوم",
    ),
    "driver_unreachable": rx(
        r"driver(?:.s)? (?:number|phone|detail|contact)", r"rider detail", r"courier(?:.s)? number",
        r"can.?t (?:contact|reach|call) (?:the )?(?:driver|courier|rider|delivery (?:guy|man|boy))",
        r"driver.{0,20}(?:doesn.?t|didn.?t|not) (?:pick|answer|respond)",
        r"hanging up", r"hung up", r"drop the call", r"miss ?calls?",
        r"رقم المندوب", r"التواصل مع المندوب", r"السايق", r"المندوب",
    ),
    "delay_wismo": rx(
        r"delay", r"late", r"still (?:waiting|not received|haven.?t)", r"no update", r"not on time",
        r"never (?:on time|arrive)", r"taking (?:so|too) long", r"\b\d+ (?:days?|weeks?|months?)\b",
        r"slow", r"pending", r"stuck", r"where is my",
        r"تأخير", r"التأخير", r"متأخر", r"لم تصل", r"لم اصلني", r"بطء", r"يتاخرو",
    ),
    "lost_or_misdelivered": rx(
        r"lost", r"missing", r"never (?:received|arrived|got)", r"didn.?t receive",
        r"deliver(?:ed)? to (?:the )?wrong", r"wrong address", r"someone else", r"no where to be found",
        r"marked (?:as )?deliver(?:ed)?[^.]{0,40}(?:never|didn.?t|not)", r"left (?:it )?(?:in|at) (?:the )?doorstep",
        r"ضاع", r"ضيعو", r"مفقود", r"لم استلم", r"عدم استلام", r"وصل لشخص",
    ),
    "payment_cod": rx(
        r"\bcash\b", r"\bcod\b", r"card payment", r"online payment", r"pay(?:ment)? (?:again|twice|by card)",
        r"double payment", r"refund", r"customs", r"charged? (?:me )?again", r"duties",
        r"الدفع", r"المبلغ", r"فلوسي", r"استرد",
    ),
    "app_login_bug": rx(
        r"can.?t (?:log ?in|login|register|sign ?in)", r"log ?in (?:doesn.?t|not|error|issue|problem)",
        r"\botp\b", r"verification (?:code|puzzle|problem)", r"email already (?:exists|in use)",
        r"user (?:not found|doesn.?t exist)", r"uae ?pass", r"password", r"sign ?up",
        r"app(?:lication)? (?:is )?(?:crash|not (?:open|work|stable)|doesn.?t (?:open|work|load|start|reflect)"
        r"|won.?t (?:open|load|start)|will not (?:load|open)|keeps loading)",
        r"crash", r"glitch", r"buggy", r"not stable", r"after (?:the )?(?:new )?update",
        r"new version", r"(?:worst|bad|useless|poor|weak) (?:app|application)", r"app (?:sucks|is trash)",
        r"not (?:user.)?friendly", r"invalid number", r"links? doesn.?t work",
        r"تسجيل الدخول", r"التطبيق لا يعمل", r"مايشتغل", r"التطبيق نفسه سيئ", r"لا يعمل",
    ),
    "staff_attitude": rx(
        r"rude", r"attitude", r"disrespect", r"insult", r"unprofessional behaviour",
        r"lazy", r"not (?:polite|courteous)", r"bad (?:treatment|behavior|behaviour)",
        r"وقح", r"سيء التعامل", r"غير محترم", r"تعامل سيء", r"بأسلوب وقح",
    ),
}

# --- Primary intent ---------------------------------------------------------
# Order matters: the first match wins, so the most decision-relevant intents come first.
# Delivery substance outranks an app mention on purpose: if a review complains about both a
# broken login AND a week-late parcel, the assistant can still help with the parcel. So
# "app_bug" ends up meaning "purely an app problem, nothing an assistant could resolve",
# which is the number worth knowing when deciding what to cut.
INTENT_ORDER = [
    ("recovery", ["false_attempt", "lost_or_misdelivered", "damaged"]),
    ("action", ["reschedule_problem", "address_problem", "time_slot_missed"]),
    ("access", ["no_human_contact", "bot_useless", "driver_unreachable", "cs_quality_poor"]),
    ("information", ["delay_wismo"]),
    ("payment", ["payment_cod"]),
    ("conduct", ["staff_attitude"]),
    ("app_bug", ["app_login_bug"]),
]


def label(text: str) -> tuple[str, list[str]]:
    hits = [name for name, pattern in THEMES.items() if pattern.search(text)]
    for intent, needed in INTENT_ORDER:
        if any(h in hits for h in needed):
            return intent, hits
    return "other", hits


def main() -> None:
    df = pd.read_csv(SRC)
    df["text"] = df["text"].fillna("").astype(str)

    labelled = df["text"].map(label)
    df["intent"] = [i for i, _ in labelled]
    df["themes"] = ["|".join(t) for _, t in labelled]
    for name in THEMES:
        df[f"t_{name}"] = df["themes"].str.contains(name, regex=False)

    df.to_csv(OUT, index=False)
    print(f"Labelled {len(df)} negative reviews -> {OUT.relative_to(ROOT)}\n")

    print("PRIMARY INTENT")
    counts = df["intent"].value_counts()
    for intent, n in counts.items():
        print(f"  {intent:<14} {n:>4}  {n / len(df) * 100:>5.1f}%")

    print("\nTHEME PREVALENCE (multi-label, % of the 454)")
    for name in THEMES:
        n = int(df[f"t_{name}"].sum())
        print(f"  {name:<22} {n:>4}  {n / len(df) * 100:>5.1f}%")

    print("\nINTENT BY OPERATOR ROLE")
    print(pd.crosstab(df["intent"], df["role"]).to_string())

    print("\nTHEME BY APP (operator vs sector)")
    ops = df[df["role"] == "operator"]
    sec = df[df["role"] == "sector"]
    print(f"{'theme':<22}{'operator':>10}{'sector':>10}")
    for name in THEMES:
        a = ops[f"t_{name}"].mean() * 100 if len(ops) else 0
        b = sec[f"t_{name}"].mean() * 100 if len(sec) else 0
        print(f"  {name:<22}{a:>8.1f}%{b:>9.1f}%")


def check_sample(n: int = 40, seed: int = 11) -> None:
    """Print a random labelled sample so the rules can be checked by hand."""
    df = pd.read_csv(OUT)
    for _, r in df.sample(n, random_state=seed).iterrows():
        text = " ".join(str(r["text"]).split())[:150]
        print(f"[{r['intent']:<11}] {text}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_sample()
    else:
        main()
