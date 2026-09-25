"""
Render a document in docs/ to PDF, and enforce its page limit.

    python docs/render-pdf.py market-scan.html 7X-market-scan.pdf --max-pages 3
    python docs/render-pdf.py deck.html 7X-deck.pdf --max-pages 5 --slides

The brief caps the market scan at 2-3 pages, so the cap is checked by the script rather
than by eye: edit the source, re-render, and the run fails loudly if the document has
grown past its limit. Scope discipline is part of what is being marked.

Build-time only. Needs `pip install playwright` and a local Chrome; neither is a runtime
dependency of the application, so neither is in requirements.txt.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOCS = Path(__file__).parent


def page_count(pdf: Path) -> int:
    """Count page objects without a PDF library: /Type /Page but not /Type /Pages."""
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def render(src: Path, out: Path, slides: bool = False) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # The system Chrome, not the bundled shell: headless_shell has no PDF backend.
        browser = p.chromium.launch(channel="chrome")
        # A slide is laid out at 1280x720 and its page size comes from its own @page rule.
        page = browser.new_page(viewport={"width": 1280, "height": 720}) if slides \
            else browser.new_page()
        page.goto(src.as_uri())
        # Google Fonts must arrive before the layout is measured, or the PDF is set in
        # the fallback face and paginates differently from what was designed.
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(3000)
        if slides:
            page.pdf(path=str(out), prefer_css_page_size=True, print_background=True)
        else:
            page.pdf(path=str(out), format="A4", print_background=True)
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="HTML file in docs/")
    ap.add_argument("output", help="PDF file to write in docs/")
    ap.add_argument("--max-pages", type=int, default=0, help="fail if the PDF is longer")
    ap.add_argument("--slides", action="store_true", help="16:9 pages sized by the document")
    args = ap.parse_args()

    src, out = DOCS / args.source, DOCS / args.output
    if not src.exists():
        print(f"no such file: {src}")
        return 1

    render(src, out, args.slides)
    n = page_count(out)
    size = out.stat().st_size / 1024
    print(f"{out.name}  {n} page{'s' if n != 1 else ''}  {size:.0f} KB")

    if args.max_pages and n > args.max_pages:
        print(f"FAIL: {n} pages, limit is {args.max_pages}. Cut something.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
