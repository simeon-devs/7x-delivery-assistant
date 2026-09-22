"""Turn the raw shipment export into something an assistant is allowed to read.

Principle: every one of the 866 input rows ends in exactly one of three places -
clean, quarantined, or superseded by a duplicate. Nothing is silently dropped, and the
reconciliation in the report proves it.

Second principle, taken from the customer reviews: where the data contradicts itself we
FLAG it, we never narrate it. 6.6% of negative reviews describe a delivery attempt the
customer says never happened, and this file contains rows with exactly that shape.

Decisions D-01 to D-09 are recorded in DECISIONS.md.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "FDE_Assignment_Shipment_Dataset.xlsx"
CLEAN = ROOT / "data" / "shipments_clean.csv"
QUARANTINE = ROOT / "data" / "shipments_quarantine.csv"
REPORT = ROOT / "data" / "cleaning_report.md"

TODAY = date(2026, 9, 22)
EXCEL_EPOCH = date(1899, 12, 30)  # the 1900 system, including its leap-year bug

# --- D-02: 22 written statuses collapse to 6 real states ---------------------
STATE_OF = {
    "delivered": "delivered",
    "delivered ok": "delivered",
    "failed delivery": "failed",
    "failed": "failed",
    "undelivered": "failed",
    "failed customer not available": "failed",
    "in transit": "in_transit",
    "transit": "in_transit",
    "out for delivery": "out_for_delivery",
    "returned to sender": "returned",
    "return to sender": "returned",
    "rts": "returned",
    "scheduled for redelivery": "redelivery_scheduled",
    "re delivery scheduled": "redelivery_scheduled",
    "redelivery": "redelivery_scheduled",
    "test": "test",
}
TERMINAL = {"delivered", "returned"}
RESCHEDULABLE = {"failed", "redelivery_scheduled", "out_for_delivery", "in_transit"}
MAX_ATTEMPTS = 3

# --- D-04: date formats, each one inferred from the data, not assumed --------
# NN-NN-NN is month-first: values like 06-19-26 and 07-30-26 put 19 and 30 second.
# NN/NN/NNNN and NN.NN.NNNN are day-first: values reach 30 and 29 in the first slot.
DATE_FORMATS = [
    ("%Y-%m-%d", "iso"),
    ("%d/%m/%Y", "dd/mm/yyyy"),
    ("%m-%d-%y", "mm-dd-yy"),
    ("%d.%m.%Y", "dd.mm.yyyy"),
    ("%d %b %Y", "dd mon yyyy"),
]


def norm_status(raw: str) -> str:
    s = re.sub(r"[-_]+", " ", str(raw).lower())
    return re.sub(r"\s+", " ", s).strip()


def parse_date(raw) -> tuple[date | None, str]:
    """Return (date, format_tag). format_tag is 'missing' or 'unparseable' on failure."""
    if pd.isna(raw):
        return None, "missing"
    s = str(raw).strip()
    if re.fullmatch(r"\d{5}", s):  # D-04: Excel serial number stored as text
        return EXCEL_EPOCH + timedelta(days=int(s)), "excel_serial"
    for fmt, tag in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date(), tag
        except ValueError:
            continue
    return None, "unparseable"


def parse_cod(raw) -> float | None:
    """D-07: the column mixes int, float and strings like 'AED 745.72'."""
    if pd.isna(raw):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).upper().replace("AED", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_phone(raw) -> str | None:
    """D-08: stored as float64, which is wrong for a phone number. Cast to E.164 text."""
    if pd.isna(raw):
        return None
    digits = re.sub(r"\D", "", f"{raw:.0f}" if isinstance(raw, float) else str(raw))
    return f"+{digits}" if digits else None


def build() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw = pd.read_excel(SRC, sheet_name="shipments")
    stats: dict = {"input_rows": len(raw)}

    df = pd.DataFrame(index=raw.index)
    df["tracking_number"] = raw["tracking_number"].astype(str).str.strip()
    df["customer_name"] = raw["customer_name"].astype(str).str.strip()
    df["emirate"] = raw["emirate"].astype(str).str.strip()
    df["service_type"] = raw["service_type"].astype(str).str.strip()
    df["weight_kg"] = raw["weight_kg"]
    df["notes"] = raw["notes"]
    df["delivery_attempts"] = raw["delivery_attempts"].astype(int)

    df["raw_status"] = raw["status"]
    df["state"] = raw["status"].map(lambda s: STATE_OF.get(norm_status(s), "unmapped"))

    df["phone"] = raw["phone"].map(parse_phone)
    df["delivery_address"] = raw["delivery_address"]
    df["cod_amount_aed"] = raw["cod_amount_aed"].map(parse_cod)

    for col in ("shipment_date", "last_attempt_date"):
        parsed = raw[col].map(parse_date)
        df[col] = pd.to_datetime([p for p, _ in parsed], errors="coerce")
        df[f"{col}_format"] = [t for _, t in parsed]
        df[f"{col}_raw"] = raw[col]  # never destroy the source value

    # --- D-01: quarantine test records, do not delete them -------------------
    is_test = (df["state"] == "test") | (
        raw["notes"].astype(str).str.strip().str.lower() == "test record"
    )
    quarantine = df[is_test].copy()
    quarantine["quarantine_reason"] = "test_record"
    unmapped = df[(df["state"] == "unmapped") & ~is_test].copy()
    if len(unmapped):
        unmapped["quarantine_reason"] = "unmapped_status"
        quarantine = pd.concat([quarantine, unmapped])
    df = df[~df.index.isin(quarantine.index)].copy()
    stats["quarantined"] = len(quarantine)

    # --- D-05, D-06: consistency flags ---------------------------------------
    df["flag_unparseable_date"] = (df["shipment_date_format"] == "unparseable") | (
        df["last_attempt_date_format"] == "unparseable"
    )
    both = df["shipment_date"].notna() & df["last_attempt_date"].notna()
    df["flag_impossible_dates"] = both & (df["last_attempt_date"] < df["shipment_date"])
    now = pd.Timestamp(TODAY)
    df["flag_future_date"] = (df["shipment_date"] > now).fillna(False) | (
        df["last_attempt_date"] > now
    ).fillna(False)
    # attempts disagree with status, or with the presence of an attempt date
    claims_attempt = df["state"].isin({"failed", "redelivery_scheduled", "delivered"})
    df["flag_attempts_unreliable"] = (
        (claims_attempt & (df["delivery_attempts"] == 0))
        | ((df["delivery_attempts"] > 0) & df["last_attempt_date"].isna())
        | ((df["delivery_attempts"] == 0) & df["last_attempt_date"].notna())
    )
    df["flag_missing_phone"] = df["phone"].isna()
    df["flag_missing_address"] = df["delivery_address"].isna()

    # --- D-03: one row per tracking number -----------------------------------
    # Survivorship rule: most recent credible event wins (standard MDM recency strategy).
    # Fail-safe override: if duplicates disagree about a TERMINAL state, refuse to act.
    df["_recency"] = df[["last_attempt_date", "shipment_date"]].max(axis=1)
    dup_keys = df["tracking_number"][df["tracking_number"].duplicated(keep=False)].unique()
    stats["duplicate_tracking_numbers"] = len(dup_keys)

    conflicted: set[str] = set()
    for key in dup_keys:
        states = set(df.loc[df["tracking_number"] == key, "state"])
        if states & TERMINAL and len(states) > 1:
            conflicted.add(key)
    stats["duplicate_terminal_conflicts"] = len(conflicted)

    df = df.sort_values("_recency", ascending=False, na_position="last")
    superseded = df[df["tracking_number"].duplicated(keep="first")].copy()
    superseded["quarantine_reason"] = "superseded_duplicate"
    df = df[~df["tracking_number"].duplicated(keep="first")].copy()
    stats["superseded"] = len(superseded)

    df["flag_duplicate_resolved"] = df["tracking_number"].isin(dup_keys)
    df["flag_duplicate_conflict"] = df["tracking_number"].isin(conflicted)

    # --- Derived fields: the only thing the assistant is allowed to read -----
    df["is_open"] = ~df["state"].isin(TERMINAL)
    df["can_authenticate"] = ~df["flag_missing_phone"]
    df["data_confidence"] = [
        "suspect" if bad else "clean"
        for bad in (
            df["flag_impossible_dates"]
            | df["flag_attempts_unreliable"]
            | df["flag_future_date"]
            | df["flag_unparseable_date"]
        )
    ]

    def block_reasons(r) -> str:
        out = []
        if r["flag_duplicate_conflict"]:
            out.append("duplicate_conflict")
        if r["delivery_attempts"] >= MAX_ATTEMPTS:
            out.append("attempt_limit_reached")
        if not r["can_authenticate"]:
            out.append("no_phone_on_file")
        return "|".join(out)

    df["block_reasons"] = df.apply(block_reasons, axis=1)
    df["requires_human"] = df["block_reasons"] != ""

    df["can_reschedule"] = (
        df["is_open"] & df["state"].isin(RESCHEDULABLE) & ~df["requires_human"]
    )
    # D-07: COD is a money decision, so it needs a person. This is a policy call, not a
    # data-quality rule, and the deck says so.
    df["can_change_address"] = df["can_reschedule"] & (df["cod_amount_aed"].fillna(0) == 0)

    df = df.drop(columns=["_recency"]).sort_values("tracking_number")
    quarantine = pd.concat([quarantine, superseded])
    return df, quarantine, stats


def write_report(clean: pd.DataFrame, quarantine: pd.DataFrame, stats: dict) -> None:
    n_in = stats["input_rows"]
    lines = [
        "# Cleaning report",
        "",
        f"Source: `{SRC.name}`, sheet `shipments`. Run {TODAY:%d %b %Y}.",
        "",
        "## Reconciliation",
        "",
        "Every input row is accounted for. Nothing was silently dropped.",
        "",
        "| | rows |",
        "|---|---|",
        f"| Input | {n_in} |",
        f"| Quarantined (test records) | {stats['quarantined']} |",
        f"| Superseded duplicates | {stats['superseded']} |",
        f"| **Clean, one per tracking number** | **{len(clean)}** |",
        f"| Check: {stats['quarantined']} + {stats['superseded']} + {len(clean)} |"
        f" **{stats['quarantined'] + stats['superseded'] + len(clean)}** |",
        "",
        "## States after collapsing 22 written statuses to 6",
        "",
        "| state | shipments |",
        "|---|---|",
    ]
    for state, n in clean["state"].value_counts().items():
        lines.append(f"| {state} | {n} |")

    open_n = int(clean["is_open"].sum())
    lines += [
        "",
        "## What the assistant can actually act on",
        "",
        f"- Open shipments: **{open_n}** of {len(clean)} "
        f"({open_n / len(clean) * 100:.1f}%). The rest are closed and need nothing.",
        f"- Can reschedule: **{int(clean['can_reschedule'].sum())}**",
        f"- Can change address: **{int(clean['can_change_address'].sum())}**",
        f"- Requires a human: **{int(clean['requires_human'].sum())}**",
        "",
        "Block reasons:",
        "",
        "| reason | shipments |",
        "|---|---|",
    ]
    reasons = (
        clean.loc[clean["block_reasons"] != "", "block_reasons"]
        .str.split("|")
        .explode()
        .value_counts()
    )
    for reason, n in reasons.items():
        lines.append(f"| {reason} | {n} |")

    lines += [
        "",
        "## Data quality flags",
        "",
        "Mapped to the six data quality dimensions (DAMA UK 2013 / ISO 25012).",
        "",
        "| flag | dimension | shipments |",
        "|---|---|---|",
    ]
    dims = {
        "flag_duplicate_resolved": "Uniqueness",
        "flag_duplicate_conflict": "Uniqueness",
        "flag_impossible_dates": "Accuracy",
        "flag_future_date": "Accuracy",
        "flag_attempts_unreliable": "Consistency",
        "flag_unparseable_date": "Validity",
        "flag_missing_phone": "Completeness",
        "flag_missing_address": "Completeness",
    }
    for flag, dim in dims.items():
        lines.append(f"| {flag.replace('flag_', '')} | {dim} | {int(clean[flag].sum())} |")

    lines += [
        "",
        f"Confidence: **{int((clean['data_confidence'] == 'clean').sum())} clean**, "
        f"**{int((clean['data_confidence'] == 'suspect').sum())} suspect**.",
        "",
        "## Date formats found in one file",
        "",
        "| format | values |",
        "|---|---|",
    ]
    fmts = pd.concat(
        [clean["shipment_date_format"], clean["last_attempt_date_format"]]
    ).value_counts()
    for fmt, n in fmts.items():
        lines.append(f"| {fmt} | {n} |")
    lines += [
        "",
        "The file mixes **day-first** (`30/06/2026`, `29.07.2026`) and **month-first**",
        "(`06-19-26`) formats. Only 26 values disambiguate it, by putting 19 or 30 in the",
        "day position. Parsing this file with a single `dayfirst` setting corrupts one group",
        "or the other silently.",
        "",
    ]
    REPORT.write_text("\n".join(lines))


def main() -> None:
    clean, quarantine, stats = build()
    CLEAN.parent.mkdir(exist_ok=True)
    clean.to_csv(CLEAN, index=False)
    quarantine.to_csv(QUARANTINE, index=False)
    write_report(clean, quarantine, stats)

    total = stats["quarantined"] + stats["superseded"] + len(clean)
    print(f"input              {stats['input_rows']}")
    print(f"quarantined        {stats['quarantined']}")
    print(f"superseded dupes   {stats['superseded']}")
    print(f"clean              {len(clean)}")
    print(f"reconciles         {total} == {stats['input_rows']}  "
          f"{'OK' if total == stats['input_rows'] else 'MISMATCH'}")
    print()
    print(f"duplicate tracking numbers : {stats['duplicate_tracking_numbers']}")
    print(f"  of which terminal conflict: {stats['duplicate_terminal_conflicts']}")
    print()
    print(clean["state"].value_counts().to_string())
    print()
    print(f"open              {int(clean['is_open'].sum())}")
    print(f"can_reschedule    {int(clean['can_reschedule'].sum())}")
    print(f"can_change_addr   {int(clean['can_change_address'].sum())}")
    print(f"requires_human    {int(clean['requires_human'].sum())}")
    print(f"suspect data      {int((clean['data_confidence'] == 'suspect').sum())}")
    print(f"\nreport -> {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
