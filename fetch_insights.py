"""Snapshot Instagram insights for every recently-published post.

Reads recent posts from Supabase, calls graph.instagram.com for each media
ID, writes one insights snapshot per post to the post_insights table.

Required permission on the IG token: instagram_business_manage_insights.

Two API calls per post — one for the lifetime fields (likes, comments),
one for the insights endpoint (reach, saved, shares). They're cheap and
parallelism doesn't buy much at this scale; we just loop sequentially.

Run on a daily cron. Each run appends a new snapshot row so we can track
how metrics evolve in the 24h / 7d / 30d window after posting.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import requests

from insights_db import list_recent_posts, record_insights


GRAPH_BASE = "https://graph.instagram.com/v21.0"
SNAPSHOT_AGE_DAYS = 30  # only re-fetch posts younger than this
INSIGHT_METRICS = ["reach", "saved", "shares", "views"]
FIELD_LIST = "like_count,comments_count,permalink"


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v


def _fetch_fields(media_id: str, token: str) -> dict:
    r = requests.get(
        f"{GRAPH_BASE}/{media_id}",
        params={"fields": FIELD_LIST, "access_token": token},
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"fields fetch failed [{r.status_code}]: {r.text}")
    return r.json()


def _fetch_insights(media_id: str, token: str) -> dict:
    r = requests.get(
        f"{GRAPH_BASE}/{media_id}/insights",
        params={"metric": ",".join(INSIGHT_METRICS), "access_token": token},
        timeout=30,
    )
    if not r.ok:
        # Insights endpoint can return 400 for very old posts, posts with no
        # data yet, or carousel children — don't crash the whole batch.
        print(f"  [warn] insights {media_id} [{r.status_code}]: {r.text[:200]}", file=sys.stderr)
        return {"data": []}
    return r.json()


def _flatten_insights(insights_resp: dict) -> dict[str, int | None]:
    out: dict[str, int | None] = {k: None for k in
        ("reach", "impressions", "saved", "likes", "comments", "shares", "profile_visits")}
    for item in insights_resp.get("data", []):
        name = item.get("name")
        values = item.get("values") or [{}]
        val = values[0].get("value")
        if name == "saved":
            out["saved"] = val
        elif name == "reach":
            out["reach"] = val
        elif name == "shares":
            out["shares"] = val
        elif name in ("views", "impressions"):
            out["impressions"] = val
    return out


def _post_age_days(posted_at: str) -> float:
    dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0


def main() -> int:
    token = _env("IG_ACCESS_TOKEN")
    posts = list_recent_posts()
    if not posts:
        print("no posts in db yet — nothing to snapshot")
        return 0

    snapshotted = 0
    skipped = 0
    failed = 0
    for post in posts:
        media_id = post["media_id"]
        try:
            age = _post_age_days(post["posted_at"])
        except Exception:
            age = 0.0
        if age > SNAPSHOT_AGE_DAYS:
            skipped += 1
            continue

        try:
            fields = _fetch_fields(media_id, token)
            insights = _flatten_insights(_fetch_insights(media_id, token))
            insights["likes"] = fields.get("like_count")
            insights["comments"] = fields.get("comments_count")
            record_insights(post_id=post["id"], media_id=media_id, metrics=insights)
            snapshotted += 1
            print(f"  [+] {media_id} age={age:.1f}d "
                  f"reach={insights.get('reach')} saved={insights.get('saved')} "
                  f"likes={insights.get('likes')} comments={insights.get('comments')}")
        except Exception as e:
            failed += 1
            print(f"  [-] {media_id} failed: {e}", file=sys.stderr)
        time.sleep(0.5)  # gentle on the API

    print(f"snapshotted={snapshotted} skipped(too_old)={skipped} failed={failed}")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"## Insights snapshot\n\n"
                    f"- Snapshotted: **{snapshotted}** posts\n"
                    f"- Skipped (>{SNAPSHOT_AGE_DAYS}d old): {skipped}\n"
                    f"- Failed: {failed}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
