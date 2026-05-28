"""One-time helper to mint a long-lived Instagram User access token via
Instagram Business Login OAuth.

Run this locally after you've enabled Instagram Business Login in your Meta
app and set the redirect URI to https://localhost/.

Usage:
    export META_APP_ID=1832946314333428
    export META_APP_SECRET=...
    python mint_ig_token.py

The script prints an authorization URL. Open it in your browser, log in to
@jerseysmokebbq, approve the scopes. Instagram redirects to
https://localhost/?code=XXXX — the page won't load (that's fine), copy the
`code` value from the URL bar and paste it back into the script. It then
exchanges the code for a short-lived token, exchanges that for a long-lived
(60-day) token, fetches your IG user ID, and prints both — copy them into
GitHub secrets as IG_ACCESS_TOKEN and IG_USER_ID.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlencode

import requests


REDIRECT_URI = "https://localhost/"
SCOPES = "instagram_business_basic,instagram_business_content_publish"


def auth_url(app_id: str) -> str:
    params = {
        "client_id": app_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "force_reauth": "true",
    }
    return f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"


def exchange_code(app_id: str, app_secret: str, code: str) -> dict:
    r = requests.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"code exchange failed [{r.status_code}]: {r.text}")
    return r.json()  # {"access_token": "...", "user_id": ...}


def exchange_long_lived(app_secret: str, short_token: str) -> dict:
    r = requests.get(
        "https://graph.instagram.com/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"long-lived exchange failed [{r.status_code}]: {r.text}")
    return r.json()  # {"access_token": "...", "token_type": "bearer", "expires_in": 5184000}


def main() -> int:
    app_id = os.environ.get("META_APP_ID")
    app_secret = os.environ.get("META_APP_SECRET")
    if not app_id or not app_secret:
        print("Set META_APP_ID and META_APP_SECRET env vars first.", file=sys.stderr)
        return 1

    print("\n1. Open this URL in your browser, log in to @jerseysmokebbq, approve scopes:")
    print(f"\n{auth_url(app_id)}\n")
    print("2. After approving, Instagram redirects to https://localhost/?code=XXXX")
    print("   (the page won't load — that's fine, the code is in the URL bar)\n")
    code = input("Paste the `code` value here: ").strip()
    if "&" in code:
        code = code.split("&", 1)[0]
    if code.endswith("#_"):
        code = code[:-2]
    if not code:
        print("No code provided, aborting.", file=sys.stderr)
        return 1

    print("\n3. Exchanging code for short-lived token...")
    short = exchange_code(app_id, app_secret, code)
    short_token = short["access_token"]
    user_id = str(short.get("user_id") or "")
    print(f"   short-lived token (1h life): {short_token[:12]}…")
    print(f"   IG user id: {user_id}")

    print("\n4. Exchanging for long-lived (60-day) token...")
    long_ = exchange_long_lived(app_secret, short_token)
    long_token = long_["access_token"]
    expires_days = int(long_.get("expires_in", 0)) // 86400
    print(f"   long-lived token: {long_token[:12]}… (expires in ~{expires_days} days)")

    print("\n" + "=" * 60)
    print("Save these to GitHub repo secrets (Settings → Secrets → Actions):")
    print("=" * 60)
    print(f"\nIG_ACCESS_TOKEN = {long_token}")
    print(f"IG_USER_ID      = {user_id}")
    print("\nThe long-lived token expires in ~60 days. Re-run this script before")
    print("then, or implement a refresh-token cron (graph.instagram.com/refresh_access_token).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
