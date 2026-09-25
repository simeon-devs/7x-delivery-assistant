"""Collect public UAE delivery-app reviews into data/reviews_raw.csv.

Public data only: Google Play's public listing and Apple's public RSS review feed.
No logins, no authenticated endpoints, no block evasion. Capped deliberately small.

Independent of the MOHRE project: its own venv, its own data directory, nothing shared.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reviews_raw.csv"

SINCE = pd.Timestamp("2025-01-01")
ARABIC = re.compile(r"[؀-ۿ]")

# operator = the client. sector = comparators for complaint language.
PLAY_APPS = [
    # (package, label, role, cap)
    ("ae.emiratespost.app", "EMX Express", "operator", 300),
]

APPSTORE_APPS = [
    # (itunes id, label, role, page cap)
    (1511692321, "EMX Express", "operator", 10),
    (6449459572, "Emirates Post", "operator", 10),
    (1582766717, "iMile", "sector", 6),
    (1090897073, "Shipa", "sector", 6),
    (535780764, "Aramex", "sector", 6),
]


def google_play(pkg: str, label: str, role: str, cap: int) -> list[dict]:
    """Newest-first, both language storefronts, stop at the cap or the date floor."""
    rows: list[dict] = []
    for lang in ("en", "ar"):
        token = None
        while len(rows) < cap:
            try:
                if token is None:
                    batch, token = reviews(
                        pkg, lang=lang, country="ae", sort=Sort.NEWEST, count=100
                    )
                else:
                    batch, token = reviews(pkg, continuation_token=token)
            except Exception as error:  # noqa: BLE001 - report and move on
                print(f"  play {label} ({lang}): stopped early, {type(error).__name__}")
                break
            if not batch:
                break
            rows += [
                {
                    "app": label,
                    "role": role,
                    "source": "google_play",
                    "review_id": r["reviewId"],
                    "date": r["at"],
                    "rating": r["score"],
                    "text": r["content"] or "",
                    "app_version": r.get("appVersion"),
                    "has_reply": bool(r.get("replyContent")),
                }
                for r in batch
            ]
            if batch[-1]["at"] < SINCE or token is None or getattr(token, "token", None) is None:
                break
            time.sleep(0.5)
    return rows[:cap]


def app_store(itunes_id: int, label: str, role: str, pages: int) -> list[dict]:
    """Apple's public RSS feed. Stops at 10 pages by Apple's own limit."""
    rows: list[dict] = []
    for page in range(1, pages + 1):
        url = (
            f"https://itunes.apple.com/ae/rss/customerreviews/"
            f"page={page}/id={itunes_id}/sortby=mostrecent/json"
        )
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                entries = json.load(resp).get("feed", {}).get("entry", [])
        except Exception as error:  # noqa: BLE001
            print(f"  appstore {label} p{page}: stopped early, {type(error).__name__}")
            break
        entries = [e for e in entries if "im:rating" in e]
        if not entries:
            break
        for e in entries:
            rows.append(
                {
                    "app": label,
                    "role": role,
                    "source": "app_store",
                    "review_id": e["id"]["label"],
                    "date": pd.to_datetime(e["updated"]["label"], utc=True).tz_localize(None),
                    "rating": int(e["im:rating"]["label"]),
                    "text": f'{e["title"]["label"]}. {e["content"]["label"]}',
                    "app_version": e.get("im:version", {}).get("label"),
                    "has_reply": None,
                }
            )
        time.sleep(0.5)
    return rows


def main() -> None:
    rows: list[dict] = []

    for pkg, label, role, cap in PLAY_APPS:
        got = google_play(pkg, label, role, cap)
        print(f"play      {label:<16} {len(got):>4}")
        rows += got

    for itunes_id, label, role, pages in APPSTORE_APPS:
        got = app_store(itunes_id, label, role, pages)
        print(f"appstore  {label:<16} {len(got):>4}")
        rows += got

    df = pd.DataFrame(rows).drop_duplicates("review_id")
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"] >= SINCE) & (df["text"].str.strip().str.len() > 0)]
    df["language"] = df["text"].map(lambda t: "ar" if ARABIC.search(t) else "en")
    df = df.sort_values("date", ascending=False)

    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"\nSaved {len(df)} reviews to {OUT.relative_to(ROOT)}")
    print(df.groupby(["app", "source", "language"]).size().to_string())
    print(f"\nDate range: {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")
    print(f"\nRating mix:\n{df.groupby('app')['rating'].value_counts().unstack(fill_value=0).to_string()}")


if __name__ == "__main__":
    main()
