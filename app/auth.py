"""
One password over the whole site.

A-27. This is not staff login, which A-05 cuts on purpose and which belongs behind the client's
own SSO. It is a lock on a public URL that reaches real customer records and a spendable API key.
Two different problems, and only the second one is ours.

    SEVENX_PASSWORD unset  ->  no gate at all, and /healthz says so
    SEVENX_PASSWORD set    ->  every route needs it except the ones listed in OPEN

Signing in always lands on the landing page, whatever link brought you to the door.

The cookie is a signed expiry, not a stored session: HMAC-SHA256 over the expiry with the
password as the key. Nothing to keep server-side, it survives a restart, and changing the
password invalidates every cookie ever issued -- which is the behaviour you want from the one
credential everybody shares.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

COOKIE = "sevenx"
HOURS = 12
LOGIN = Path(__file__).parent / "static" / "login.html"

# Reachable without the password, and nothing else is.
#   /login       the door itself, or nobody can open it
#   /healthz     Render's health check, which must answer before anyone has signed in
#   theme.css    the door's stylesheet. A palette, no data
OPEN = frozenset({"/login", "/healthz", "/static/theme.css"})


def password() -> str:
    return os.environ.get("SEVENX_PASSWORD", "").strip()


def _sign(exp: int, secret: str) -> str:
    return hmac.new(secret.encode(), f"v1:{exp}".encode(), hashlib.sha256).hexdigest()


def issue(secret: str) -> str:
    exp = int(time.time()) + HOURS * 3600
    return f"{exp}.{_sign(exp, secret)}"


def accepted(token: str | None, secret: str) -> bool:
    """A cookie is good if it has not expired and was signed by this password."""
    if not token or "." not in token:
        return False
    raw_exp, sig = token.split(".", 1)
    try:
        exp = int(raw_exp)
    except ValueError:
        return False
    if exp < time.time():
        return False
    return hmac.compare_digest(sig, _sign(exp, secret))


# Signing in always lands on the landing page, never on whichever surface was asked for.
# The demo is meant to be walked in order -- what it is, then the customer, then the console --
# and a link passed around should not drop someone straight into a staff tool. It also means
# there is no caller-supplied redirect target at all, so the open-redirect question never arises.
HOME = "/"


def page(error: str = "") -> HTMLResponse:
    html = LOGIN.read_text()
    if error:
        html = html.replace(
            "<!--ERROR-->", f'<p class="bad" role="alert"><i></i>{error}</p>'
        )
    # A wrong password must never be answered out of a cache.
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def install(app) -> None:
    """Mount the gate and the door. Called once, from main."""

    @app.middleware("http")
    async def gate(request: Request, call_next):
        secret = password()
        if not secret or request.url.path in OPEN:
            return await call_next(request)
        if accepted(request.cookies.get(COOKIE), secret):
            return await call_next(request)

        # An API call gets an answer it can act on; a person gets the door.
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "not signed in"}, status_code=401)
        return RedirectResponse("/login", status_code=303)

    @app.get("/login")
    def login_page():
        if not password():
            return RedirectResponse(HOME, status_code=303)
        return page()

    @app.post("/login")
    async def login_submit(request: Request):
        secret = password()
        if not secret:
            return RedirectResponse("/", status_code=303)

        # Parsed by hand rather than with fastapi.Form: that needs python-multipart, and a
        # plain HTML form is one fewer dependency and one fewer thing to fail without JS.
        form = parse_qs((await request.body()).decode("utf-8", "replace"))
        given = (form.get("password") or [""])[0]

        if not hmac.compare_digest(given, secret):
            # A speed bump, not a defence. One shared password on a demo URL; a real
            # deployment wants per-IP lockout, which belongs with the SSO A-05 cuts.
            time.sleep(0.4)
            return page("That password doesn't match. Ask whoever sent you the link.")

        out = RedirectResponse(HOME, status_code=303)
        out.set_cookie(
            COOKIE, issue(secret), max_age=HOURS * 3600, httponly=True, samesite="lax",
            secure=request.url.scheme == "https", path="/",
        )
        return out

    @app.get("/healthz")
    def healthz():
        """Public on purpose: Render checks it before anyone has signed in. `protected` is
        how you tell from outside that the password actually took effect on this deploy."""
        return {"ok": True, "protected": bool(password())}
