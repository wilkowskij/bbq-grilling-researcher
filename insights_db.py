"""Thin REST wrapper for the `posts` and `post_insights` Supabase tables.

We don't pull in supabase-py since the rest of the codebase already uses
direct PostgREST/storage REST calls via `requests`. Same pattern here:
service-role key in the Authorization header, JSON in/out.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v


def _headers() -> dict[str, str]:
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest(path: str) -> str:
    return f"{_env('SUPABASE_URL').rstrip('/')}/rest/v1{path}"


def record_post(
    *,
    media_id: str,
    topic: str,
    caption_preview: str,
    image_url: str,
    style_tag: str = "recipe_card",
    featured_handle: str | None = None,
) -> int:
    payload = {
        "media_id": media_id,
        "topic": topic,
        "caption_preview": caption_preview[:500],
        "image_url": image_url,
        "style_tag": style_tag,
        "featured_handle": featured_handle,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    r = requests.post(_rest("/posts"), headers=_headers(), json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"record_post failed [{r.status_code}]: {r.text}")
    rows = r.json()
    return int(rows[0]["id"])


def list_recent_posts(days: int = 30) -> list[dict[str, Any]]:
    params = {
        "select": "id,media_id,posted_at,topic,style_tag",
        "order": "posted_at.desc",
        "limit": "200",
    }
    r = requests.get(_rest("/posts"), headers=_headers(), params=params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"list_recent_posts failed [{r.status_code}]: {r.text}")
    return r.json()


def recent_featured_handles(n: int = 7) -> list[str]:
    """Return the featured_handle values from the last `n` posts (newest first).

    Used to enforce the source-diversity rule: a pitmaster handle that
    appears in this list MUST NOT be featured again in the brief about to
    be synthesized. NULLs are skipped, so a post that didn't pick a
    featured source doesn't burn a slot in the rolling window.
    """
    params = {
        "select": "featured_handle,posted_at",
        "order": "posted_at.desc",
        "limit": str(n),
    }
    r = requests.get(_rest("/posts"), headers=_headers(), params=params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"recent_featured_handles failed [{r.status_code}]: {r.text}")
    return [row["featured_handle"] for row in r.json() if row.get("featured_handle")]


def record_insights(*, post_id: int, media_id: str, metrics: dict[str, int | None]) -> None:
    payload = {
        "post_id": post_id,
        "media_id": media_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        **{k: metrics.get(k) for k in
           ("reach", "impressions", "saved", "likes", "comments", "shares", "profile_visits")},
    }
    r = requests.post(_rest("/post_insights"), headers=_headers(), json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"record_insights failed [{r.status_code}]: {r.text}")


def latest_insights_by_post(days: int = 7) -> list[dict[str, Any]]:
    """For the digest: pick the latest insights row per post over the window,
    joined with post topic + style_tag."""
    params = {
        "select": "*,post:posts(topic,style_tag,posted_at,featured_handle)",
        "order": "fetched_at.desc",
        "limit": "500",
    }
    r = requests.get(_rest("/post_insights"), headers=_headers(), params=params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"latest_insights_by_post failed [{r.status_code}]: {r.text}")
    rows = r.json()
    seen: set[int] = set()
    out = []
    for row in rows:
        if row["post_id"] in seen:
            continue
        seen.add(row["post_id"])
        out.append(row)
    return out
