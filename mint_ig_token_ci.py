"""CI-friendly version of the IG token mint helper.

Reads inputs from env (set by the workflow):
    META_APP_ID
    META_APP_SECRET
    AUTH_CODE       -- the `code` value from https://localhost/?code=XXXX

Writes the minted IG_ACCESS_TOKEN and IG_USER_ID to $GITHUB_STEP_SUMMARY
so they appear in the workflow run summary on github.com (private repo →
visible only to you). Delete the run after copying the values into secrets.
"""

from __future__ import annotations

import os
import sys

import requests


REDIRECT_URI = "https://localhost/"


def main() -> int:
    app_id = os.environ["META_APP_ID"]
    app_secret = os.environ["META_APP_SECRET"]
    code = os.environ["AUTH_CODE"].strip()
    if "&" in code:
        code = code.split("&", 1)[0]
    if code.endswith("#_"):
        code = code[:-2]
    if not code:
        print("AUTH_CODE is empty", file=sys.stderr)
        return 1

    print("Exchanging code for short-lived token...")
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
        print(f"code exchange failed [{r.status_code}]: {r.text}", file=sys.stderr)
        return 1
    short = r.json()
    short_token = short["access_token"]
    user_id = str(short.get("user_id") or "")
    print(f"  short token: {short_token[:12]}...  user_id: {user_id}")

    print("Exchanging short -> long-lived (60-day) token...")
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
        print(f"long-lived exchange failed [{r.status_code}]: {r.text}", file=sys.stderr)
        return 1
    long_ = r.json()
    long_token = long_["access_token"]
    expires_days = int(long_.get("expires_in", 0)) // 86400
    print(f"  long token: {long_token[:12]}...  expires in ~{expires_days} days")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("## Instagram tokens minted\n\n")
            f.write("Copy these into repo secrets, then **delete this workflow run**.\n\n")
            f.write("### `IG_ACCESS_TOKEN`\n\n```\n")
            f.write(long_token)
            f.write("\n```\n\n")
            f.write("### `IG_USER_ID`\n\n```\n")
            f.write(user_id)
            f.write("\n```\n\n")
            f.write(f"Long-lived token expires in ~{expires_days} days. ")
            f.write("Re-run this workflow before then with a fresh authorization code.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
