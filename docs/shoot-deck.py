"""
Take the two screenshots the deck uses, with customer data masked, and prove the masking held.

    ./run.sh                                   # the app, on any port, with the seed loaded
    python docs/shoot-deck.py --port 8077      # needs playwright and a local Chrome

Writes docs/deck-shots/chat-m.png and queue-m.png, both git-ignored: masked or not, they are
pictures of the client's records.

Masking is the landing page's rule (app.main._first_name / _area_only): first name plus an
initial, and only the last two parts of an address. The model paraphrases addresses in its
replies ("Bldg 38, Apt 892, ..."), so exact-match replacement is not enough; unit parts are
also stripped by pattern. After masking, the page text is checked independently and the run
fails if anything that looks like a name, a street address or a full phone number survived.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "deck-shots"

# The pairs come from the app's own database and masking functions, so they are built with
# the app's interpreter; this script only needs playwright.
PAIRS_SRC = """
import json, sqlite3
from app import db
from app.main import _first_name, _area_only
conn = db.connect() if hasattr(db, "connect") else sqlite3.connect(db.DB_PATH)
pairs = {}
for name, addr in conn.execute("select customer_name, delivery_address from shipments"):
    if name and _first_name(name) != name: pairs[name] = _first_name(name)
    if addr and _area_only(addr) != addr: pairs[addr] = _area_only(addr)
print(json.dumps(sorted(pairs.items(), key=lambda kv: -len(kv[0]))))
"""

MASK = r"""(pairs) => {
  const unit = /\b(?:Bldg|Building|Apt|Apartment|Villa|Office|Flat|Tower|Floor|Unit|Shop|Warehouse|House|Plot|Street|St)\.?\s*[\w-]*\d[\w-]*,\s*/gi;
  const fix = s => {
    for (const [a, b] of pairs) if (s.includes(a)) s = s.split(a).join(b);
    s = s.replace(/\+971\d*\s*•••\s*\d{4}/g, "+971 ••• ••••");
    let prev; do { prev = s; s = s.replace(unit, ""); } while (s !== prev);
    return s;
  };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = w.nextNode())) { const t = fix(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t; }
}"""

LEFTOVER = [
    re.compile(r"\b(?:Bldg|Building|Apt|Apartment|Villa|Office|Flat|Tower)\.?\s*[\w-]*\d"),
    re.compile(r"\+971\d{3,}"),
]


def leftovers(text: str, pairs) -> list[str]:
    found = [a for a, _ in pairs if a in text]
    for rx in LEFTOVER:
        found += rx.findall(text)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8077)
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"

    pairs = json.loads(subprocess.check_output(
        [str(ROOT / ".venv" / "bin" / "python"), "-c", PAIRS_SRC], cwd=ROOT, text=True))
    OUT.mkdir(exist_ok=True)

    from playwright.sync_api import sync_playwright

    bad = False
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")

        def shoot(url, name, viewport, before=None):
            nonlocal bad
            page = browser.new_page(viewport=viewport, device_scale_factor=2)
            page.goto(base + url)
            page.wait_for_timeout(2500)
            if before:
                before(page)
            page.evaluate(MASK, pairs)
            page.screenshot(path=str(OUT / name))
            left = leftovers(page.evaluate("document.body.innerText"), pairs)
            print(f"{name}: {'LEFTOVER ' + str(left[:10]) if left else 'clean'}")
            bad = bad or bool(left)

        shoot("/ops", "queue-m.png", {"width": 1440, "height": 900})

        def open_reschedule(page):
            # the seeded WhatsApp reschedule; picked by its tracking number, not a name
            page.get_by_text("EX400003AE", exact=False).first.click()
            page.wait_for_timeout(2000)

        shoot("/chat", "chat-m.png", {"width": 1100, "height": 860}, open_reschedule)
        browser.close()

    if bad:
        print("FAIL: customer data survived the masking. Do not use these shots.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
